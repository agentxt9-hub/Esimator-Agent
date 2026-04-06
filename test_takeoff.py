"""
test_takeoff.py - Takeoff module integration tests (Session 18)

Run with:
    python test_takeoff.py

Requirements:
  - Local PostgreSQL: postgresql://postgres:Builder@localhost:5432/estimator_db
  - pdf2image + Pillow installed
  - poppler installed for thumbnails (skipped gracefully if absent)
"""
import os
import io
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app import app, db, run_migrations, Company, User, Project

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def check(label, expr, detail=""):
    ok = bool(expr)
    results.append((label, ok, detail))
    icon = PASS if ok else FAIL
    suffix = f" -- {detail}" if detail else ""
    print(f"  {icon}  {label}{suffix}")
    return ok


def _generate_test_pdf():
    """Return bytes of a simple 2-page PDF."""
    try:
        from fpdf import FPDF
        pdf = FPDF()
        for i in range(1, 3):
            pdf.add_page()
            pdf.set_font("Helvetica", size=24)
            pdf.cell(0, 20, f"Test Plan - Page {i}", ln=True)
        return pdf.output()
    except ImportError:
        pass

    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import letter
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=letter)
        for i in range(1, 3):
            c.setFont("Helvetica", 24)
            c.drawString(72, 720, f"Test Plan - Page {i}")
            c.showPage()
        c.save()
        return buf.getvalue()
    except ImportError:
        pass

    # Minimal hand-crafted 1-page PDF (no extra library needed)
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )


# ============================================================================
print("\n=== Takeoff Module - Integration Tests ===\n")

with app.app_context():
    print("[setup] Running db.create_all() + run_migrations() ...")
    try:
        db.create_all()
        run_migrations()
        print("[setup] Done.\n")
    except Exception as e:
        print(f"[setup] ERROR: {e}")
        sys.exit(1)

    # 1. Table creation
    print("-- 1. Table creation --")
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(db.engine)
    existing_tables = inspector.get_table_names()
    for tbl in ('takeoff_plans', 'takeoff_pages', 'takeoff_items', 'takeoff_measurements'):
        check(f"Table '{tbl}' exists", tbl in existing_tables)

    # 2. Test fixtures
    print("\n-- 2. Test fixtures --")
    company = Company.query.filter_by(company_name='TakeoffTest Co').first()
    if not company:
        company = Company(company_name='TakeoffTest Co')
        db.session.add(company)
        db.session.flush()
        user = User(
            company_id=company.id,
            username='tk_test_admin',
            email='tk_test@zenbid.io',
            role='admin',
        )
        user.set_password('TestPass123!')
        db.session.add(user)
        db.session.flush()

    company = Company.query.filter_by(company_name='TakeoffTest Co').first()
    test_user = User.query.filter_by(username='tk_test_admin').first()
    check("Company created/found", company is not None, f"id={company.id}")
    check("User created/found", test_user is not None, f"id={test_user.id}")

    project = (Project.query
               .filter_by(project_name='Takeoff Test Project', company_id=company.id)
               .first())
    if not project:
        project = Project(
            company_id=company.id,
            project_name='Takeoff Test Project',
            project_number='TK-001',
        )
        db.session.add(project)
        db.session.flush()
    db.session.commit()
    check("Project created/found", project is not None, f"id={project.id}")

    PROJECT_ID = project.id
    COMPANY_ID = company.id
    USER_ID    = test_user.id

# Flask test client (CSRF disabled for tests)
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

client = app.test_client()

with client.session_transaction() as sess:
    sess['_user_id'] = str(USER_ID)
    sess['_fresh']   = True

# 3. PDF upload
print("\n-- 3. PDF Upload --")
pdf_bytes = _generate_test_pdf()

resp = client.post(
    f'/project/{PROJECT_ID}/takeoff/upload',
    data={'pdf': (io.BytesIO(pdf_bytes), 'test_plan.pdf')},
    content_type='multipart/form-data',
)
check("POST /upload -> HTTP 200", resp.status_code == 200,
      f"status={resp.status_code}")

upload_data = {}
try:
    upload_data = json.loads(resp.data)
    check("Upload response success=True", upload_data.get('success'), str(upload_data))
    check("Upload plan_id returned", 'plan_id' in upload_data)
    check("Upload page_count >= 1", upload_data.get('page_count', 0) >= 1,
          f"page_count={upload_data.get('page_count')}")
    check("Upload pages list non-empty", len(upload_data.get('pages', [])) >= 1)
except Exception as e:
    check("Upload response parseable", False, str(e))

PLAN_ID    = upload_data.get('plan_id')
pages      = upload_data.get('pages', [])
PAGE_COUNT = upload_data.get('page_count', 0)

# 4. DB records
print("\n-- 4. Database records --")
with app.app_context():
    from app import TakeoffPlan, TakeoffPage
    plan = TakeoffPlan.query.get(PLAN_ID) if PLAN_ID else None
    check("TakeoffPlan record exists", plan is not None)
    if plan:
        check("plan.page_count correct", plan.page_count == PAGE_COUNT,
              f"{plan.page_count}")
        check("plan.company_id matches", plan.company_id == COMPANY_ID)
        db_pages = TakeoffPage.query.filter_by(plan_id=PLAN_ID).all()
        check("TakeoffPage records created", len(db_pages) == plan.page_count,
              f"{len(db_pages)} pages in DB")

# 5. Thumbnail generation (client-side)
print("\n-- 5. Thumbnail generation (client-side) --")
# Upload returns thumbnail_url=None; PDF.js renders thumbnails in the browser
check("All pages have thumbnail_url=None (client renders via PDF.js)",
      all(pg.get('thumbnail_url') is None for pg in pages),
      str([pg.get('thumbnail_url') for pg in pages]))

# 6. Serve PDF
print("\n-- 6. Serve PDF --")
if PLAN_ID:
    resp = client.get(f'/project/{PROJECT_ID}/takeoff/plan/{PLAN_ID}/pdf')
    check("GET /plan/<id>/pdf -> HTTP 200", resp.status_code == 200,
          f"status={resp.status_code}")
    check("Content-Type is application/pdf", 'application/pdf' in resp.content_type)

# 7. Create item
print("\n-- 7. Create Item --")
resp = client.post(
    f'/project/{PROJECT_ID}/takeoff/item',
    json={
        'name': 'WT-B Test Wall',
        'measurement_type': 'linear_with_width',
        'color': '#2D5BFF',
        'opacity': 0.5,
        'width_ft': 0.333,
        'assembly_notes': '3-5/8" 20ga framing, 5/8" Type X GWB each side',
    },
    content_type='application/json',
)
check("POST /item -> HTTP 201", resp.status_code == 201,
      f"status={resp.status_code}")
item_data = {}
try:
    item_data = json.loads(resp.data)
    check("Item success=True", item_data.get('success'))
    check("Item id returned", 'item' in item_data and 'id' in item_data['item'])
except Exception as e:
    check("Item response parseable", False, str(e))

ITEM_ID = (item_data.get('item') or {}).get('id')

# 8. List items
print("\n-- 8. List Items --")
resp = client.get(f'/project/{PROJECT_ID}/takeoff/items')
check("GET /items -> HTTP 200", resp.status_code == 200)
items_list = []
try:
    items_list = json.loads(resp.data)
    check("Items list is array", isinstance(items_list, list))
    check("New item in list", any(i['id'] == ITEM_ID for i in items_list) if ITEM_ID else False)
except Exception as e:
    check("Items list parseable", False, str(e))

# 9. Delete item
print("\n-- 9. Delete Item --")
if ITEM_ID:
    resp = client.delete(f'/project/{PROJECT_ID}/takeoff/item/{ITEM_ID}')
    check("DELETE /item/<id> -> HTTP 200", resp.status_code == 200)
    del_data = json.loads(resp.data)
    check("Delete success=True", del_data.get('success'))

    resp2 = client.get(f'/project/{PROJECT_ID}/takeoff/items')
    items2 = json.loads(resp2.data)
    check("Item no longer in list", not any(i['id'] == ITEM_ID for i in items2))

# 10. Viewer page
print("\n-- 10. Viewer page --")
resp = client.get(f'/project/{PROJECT_ID}/takeoff')
check("GET /takeoff -> HTTP 200", resp.status_code == 200,
      f"status={resp.status_code}")
check("Response contains takeoff-app", b'takeoff-app' in resp.data)
check("Response contains pdf.js script", b'pdf.min.js' in resp.data)

# Summary
print("\n" + "=" * 50)
passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
print(f"  Results: {passed}/{total} passed\n")

if passed < total:
    print("  Failed tests:")
    for label, ok, detail in results:
        if not ok:
            suffix = f" -- {detail}" if detail else ""
            print(f"    {FAIL}  {label}{suffix}")
    sys.exit(1)
else:
    print("  All tests passed.")
    sys.exit(0)
