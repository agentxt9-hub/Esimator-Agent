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

# ============================================================
# SESSION 2 TESTS — Scale, Measurements, Item PATCH, Security
# ============================================================

# Create a fresh item for Session 2 tests
print("\n-- S2.0: Create Session 2 test item --")
resp = client.post(
    f'/project/{PROJECT_ID}/takeoff/item',
    json={'name': 'S2-Wall-Test', 'measurement_type': 'linear', 'color': '#10B981', 'opacity': 0.6},
    content_type='application/json',
)
S2_ITEM_ID = None
try:
    s2_item_data = json.loads(resp.data)
    check("S2 item created", s2_item_data.get('success'))
    S2_ITEM_ID = (s2_item_data.get('item') or {}).get('id')
    check("S2 item id returned", S2_ITEM_ID is not None, str(S2_ITEM_ID))
except Exception as e:
    check("S2 item create parseable", False, str(e))

# Grab first page_id for measurement tests
PAGE_ID = pages[0]['id'] if pages else None

# S2.1 — Scale calibration
print("\n-- S2.1: Scale calibration --")
if PAGE_ID:
    resp = client.post(
        f'/project/{PROJECT_ID}/takeoff/page/{PAGE_ID}/scale',
        json={'pixels_per_foot': 48.0, 'method': 'manual'},
        content_type='application/json',
    )
    check("POST /page/<id>/scale -> HTTP 200", resp.status_code == 200,
          f"status={resp.status_code}")
    scale_data = json.loads(resp.data)
    check("Scale response success=True", scale_data.get('success'), str(scale_data))
    check("Scale pixels_per_foot returned", scale_data.get('pixels_per_foot') == 48.0,
          str(scale_data.get('pixels_per_foot')))

    # Verify DB updated
    with app.app_context():
        from app import TakeoffPage
        pg = TakeoffPage.query.get(PAGE_ID)
        check("DB scale_pixels_per_foot saved", pg and pg.scale_pixels_per_foot == 48.0,
              str(pg.scale_pixels_per_foot if pg else None))
        check("DB scale_method saved", pg and pg.scale_method == 'manual',
              str(pg.scale_method if pg else None))

# S2.2 — Invalid scale rejected
print("\n-- S2.2: Invalid scale rejected --")
if PAGE_ID:
    resp = client.post(
        f'/project/{PROJECT_ID}/takeoff/page/{PAGE_ID}/scale',
        json={'pixels_per_foot': -5.0},
        content_type='application/json',
    )
    check("POST scale with negative ppf -> 400", resp.status_code == 400,
          f"status={resp.status_code}")

# S2.3 — Linear measurement
print("\n-- S2.3: Linear measurement --")
S2_MEAS_ID = None
if S2_ITEM_ID and PAGE_ID:
    pts = [{'x': 0.1, 'y': 0.2}, {'x': 0.5, 'y': 0.2}, {'x': 0.5, 'y': 0.6}]
    resp = client.post(
        f'/project/{PROJECT_ID}/takeoff/measurement',
        json={
            'item_id':          S2_ITEM_ID,
            'page_id':          PAGE_ID,
            'points_json':      json.dumps(pts),
            'calculated_value': 24.5,
            'measurement_type': 'linear',
        },
        content_type='application/json',
    )
    check("POST /measurement linear -> HTTP 201", resp.status_code == 201,
          f"status={resp.status_code}")
    meas_data = json.loads(resp.data)
    check("Measurement success=True", meas_data.get('success'), str(meas_data))
    check("measurement_id returned", 'measurement_id' in meas_data,
          str(meas_data.get('measurement_id')))
    check("item_totals returned", 'item_totals' in meas_data)
    S2_MEAS_ID = meas_data.get('measurement_id')

# S2.4 — GET page measurements returns linear measurement
print("\n-- S2.4: GET page measurements --")
if PAGE_ID and S2_MEAS_ID:
    resp = client.get(f'/project/{PROJECT_ID}/takeoff/page/{PAGE_ID}/measurements')
    check("GET /page/<id>/measurements -> HTTP 200", resp.status_code == 200)
    pg_meas_data = json.loads(resp.data)
    check("Response has measurements key", 'measurements' in pg_meas_data)
    check("Response has scale_pixels_per_foot", 'scale_pixels_per_foot' in pg_meas_data,
          str(pg_meas_data.get('scale_pixels_per_foot')))
    check("scale_pixels_per_foot is 48.0", pg_meas_data.get('scale_pixels_per_foot') == 48.0)
    meas_list = pg_meas_data.get('measurements', [])
    check("Linear measurement in list", any(m['id'] == S2_MEAS_ID for m in meas_list),
          f"count={len(meas_list)}")
    if meas_list:
        m = next((m for m in meas_list if m['id'] == S2_MEAS_ID), None)
        if m:
            check("measurement has item_name", 'item_name' in m)
            check("measurement has item_color", 'item_color' in m)
            check("measurement_type == linear", m.get('measurement_type') == 'linear',
                  str(m.get('measurement_type')))
            check("calculated_value == 24.5", m.get('calculated_value') == 24.5,
                  str(m.get('calculated_value')))

# S2.5 — Area measurement
print("\n-- S2.5: Area measurement --")
S2_AREA_MEAS_ID = None
if S2_ITEM_ID and PAGE_ID:
    area_pts = [
        {'x': 0.1, 'y': 0.1}, {'x': 0.4, 'y': 0.1},
        {'x': 0.4, 'y': 0.4}, {'x': 0.1, 'y': 0.4},
    ]
    resp = client.post(
        f'/project/{PROJECT_ID}/takeoff/measurement',
        json={
            'item_id':              S2_ITEM_ID,
            'page_id':              PAGE_ID,
            'points_json':          json.dumps(area_pts),
            'calculated_value':     144.0,
            'calculated_secondary': 48.0,
            'measurement_type':     'area',
        },
        content_type='application/json',
    )
    check("POST /measurement area -> HTTP 201", resp.status_code == 201,
          f"status={resp.status_code}")
    area_data = json.loads(resp.data)
    check("Area measurement success", area_data.get('success'))
    S2_AREA_MEAS_ID = area_data.get('measurement_id')

    # Verify DB
    with app.app_context():
        from app import TakeoffMeasurement
        am = TakeoffMeasurement.query.get(S2_AREA_MEAS_ID) if S2_AREA_MEAS_ID else None
        check("Area calculated_value == 144.0", am and am.calculated_value == 144.0,
              str(am.calculated_value if am else None))
        check("Area calculated_secondary == 48.0", am and am.calculated_secondary == 48.0,
              str(am.calculated_secondary if am else None))
        check("Area measurement_type == area", am and am.measurement_type == 'area',
              str(am.measurement_type if am else None))

# S2.6 — Count measurements
print("\n-- S2.6: Count measurements (3 placed) --")
S2_COUNT_IDS = []
if PAGE_ID:
    # Create a count-type item
    resp = client.post(
        f'/project/{PROJECT_ID}/takeoff/item',
        json={'name': 'S2-Count-Item', 'measurement_type': 'count', 'color': '#F59E0B', 'opacity': 0.8},
        content_type='application/json',
    )
    count_item_data = json.loads(resp.data)
    COUNT_ITEM_ID = (count_item_data.get('item') or {}).get('id')

    if COUNT_ITEM_ID:
        for pt in [{'x': 0.2, 'y': 0.2}, {'x': 0.5, 'y': 0.5}, {'x': 0.8, 'y': 0.3}]:
            r = client.post(
                f'/project/{PROJECT_ID}/takeoff/measurement',
                json={
                    'item_id':          COUNT_ITEM_ID,
                    'page_id':          PAGE_ID,
                    'points_json':      json.dumps([pt]),
                    'calculated_value': 1,
                    'measurement_type': 'count',
                },
                content_type='application/json',
            )
            d = json.loads(r.data)
            if d.get('success'):
                S2_COUNT_IDS.append(d['measurement_id'])

        check("3 count measurements created", len(S2_COUNT_IDS) == 3,
              f"count={len(S2_COUNT_IDS)}")

        # Verify totals via GET items
        resp2 = client.get(f'/project/{PROJECT_ID}/takeoff/items')
        items2 = json.loads(resp2.data)
        cnt_item = next((i for i in items2 if i['id'] == COUNT_ITEM_ID), None)
        check("Count item total == 3.0", cnt_item and cnt_item['total'] == 3.0,
              str(cnt_item['total'] if cnt_item else None))

# S2.7 — Measurement DELETE
print("\n-- S2.7: Measurement delete --")
if S2_MEAS_ID:
    resp = client.delete(f'/project/{PROJECT_ID}/takeoff/measurement/{S2_MEAS_ID}')
    check("DELETE /measurement/<id> -> HTTP 200", resp.status_code == 200,
          f"status={resp.status_code}")
    del_data = json.loads(resp.data)
    check("Delete measurement success=True", del_data.get('success'))
    check("item_totals returned after delete", 'item_totals' in del_data)

    # Verify measurement no longer in page list
    resp2 = client.get(f'/project/{PROJECT_ID}/takeoff/page/{PAGE_ID}/measurements')
    pg_data = json.loads(resp2.data)
    remaining_ids = [m['id'] for m in pg_data.get('measurements', [])]
    check("Deleted measurement absent from page", S2_MEAS_ID not in remaining_ids)

# S2.8 — Item PATCH
print("\n-- S2.8: Item PATCH --")
if S2_ITEM_ID:
    resp = client.patch(
        f'/project/{PROJECT_ID}/takeoff/item/{S2_ITEM_ID}',
        json={
            'name':           'WT-B Updated',
            'color':          '#EF4444',
            'opacity':        0.75,
            'assembly_notes': 'Updated spec notes',
            'division':       '09',
        },
        content_type='application/json',
    )
    check("PATCH /item/<id> -> HTTP 200", resp.status_code == 200,
          f"status={resp.status_code}")
    patch_data = json.loads(resp.data)
    check("PATCH success=True", patch_data.get('success'))
    item_out = patch_data.get('item', {})
    check("item name updated", item_out.get('name') == 'WT-B Updated',
          str(item_out.get('name')))
    check("item color updated", item_out.get('color') == '#EF4444',
          str(item_out.get('color')))
    check("item opacity updated", item_out.get('opacity') == 0.75,
          str(item_out.get('opacity')))
    check("item division updated", item_out.get('division') == '09',
          str(item_out.get('division')))

    # Verify DB
    with app.app_context():
        from app import TakeoffItem
        it = TakeoffItem.query.get(S2_ITEM_ID)
        check("DB name updated", it and it.name == 'WT-B Updated',
              str(it.name if it else None))
        check("DB color updated", it and it.color == '#EF4444',
              str(it.color if it else None))

# S2.9 — Security: measurement POST for cross-company project → 403
print("\n-- S2.9: Cross-company security --")
with app.app_context():
    from app import Company, User, Project
    other_co = Company.query.filter_by(company_name='OtherCompanyS2').first()
    if not other_co:
        other_co = Company(company_name='OtherCompanyS2')
        db.session.add(other_co)
        db.session.flush()
        other_user = User(
            company_id=other_co.id,
            username='other_s2_admin',
            email='other_s2@zenbid.io',
            role='admin',
        )
        other_user.set_password('TestPass123!')
        db.session.add(other_user)
        other_proj = Project(
            company_id=other_co.id,
            project_name='Other S2 Project',
            project_number='OTH-S2-001',
        )
        db.session.add(other_proj)
        db.session.commit()
    else:
        other_proj = (Project.query
                      .filter_by(company_id=other_co.id)
                      .first())

    if other_proj and S2_ITEM_ID and PAGE_ID:
        OTHER_PROJECT_ID = other_proj.id

# Test that our user can't create measurements on other company's project
if S2_ITEM_ID and PAGE_ID:
    with app.app_context():
        other_proj2 = (Project.query
                       .filter(Project.company_id != COMPANY_ID)
                       .first())
    if other_proj2:
        resp = client.post(
            f'/project/{other_proj2.id}/takeoff/measurement',
            json={
                'item_id':          S2_ITEM_ID,
                'page_id':          PAGE_ID,
                'points_json':      '[]',
                'calculated_value': 1.0,
                'measurement_type': 'count',
            },
            content_type='application/json',
        )
        check("Cross-company measurement POST -> 403", resp.status_code == 403,
              f"status={resp.status_code}")
    else:
        check("Cross-company security (skipped — no other project)", True, "skipped")

# S2.10 — Scale route 403 on wrong project
print("\n-- S2.10: Scale route 403 on wrong project --")
if PAGE_ID:
    with app.app_context():
        other_proj3 = (Project.query
                       .filter(Project.company_id != COMPANY_ID)
                       .first())
    if other_proj3:
        resp = client.post(
            f'/project/{other_proj3.id}/takeoff/page/{PAGE_ID}/scale',
            json={'pixels_per_foot': 48.0},
            content_type='application/json',
        )
        check("Cross-company scale POST -> 403", resp.status_code == 403,
              f"status={resp.status_code}")
    else:
        check("Scale 403 cross-company (skipped)", True, "skipped")

# S2.11 — measurement_type stored correctly
print("\n-- S2.11: measurement_type column --")
with app.app_context():
    from app import TakeoffMeasurement
    if S2_AREA_MEAS_ID:
        m2 = TakeoffMeasurement.query.get(S2_AREA_MEAS_ID)
        check("TakeoffMeasurement has measurement_type attr", hasattr(m2, 'measurement_type'))
        check("Area measurement_type == 'area'", m2 and m2.measurement_type == 'area',
              str(m2.measurement_type if m2 else None))

# S2.12 — PATCH with empty name rejected gracefully
print("\n-- S2.12: PATCH empty name rejected --")
if S2_ITEM_ID:
    resp = client.patch(
        f'/project/{PROJECT_ID}/takeoff/item/{S2_ITEM_ID}',
        json={'name': '   '},
        content_type='application/json',
    )
    # Either 200 with name unchanged OR 400 — just should not crash
    check("PATCH empty name does not 500", resp.status_code in (200, 400),
          f"status={resp.status_code}")

# S2.13 — GET page measurements returns scale_pixels_per_foot
print("\n-- S2.13: GET page measurements returns scale --")
if PAGE_ID:
    resp = client.get(f'/project/{PROJECT_ID}/takeoff/page/{PAGE_ID}/measurements')
    check("GET measurements -> 200", resp.status_code == 200)
    d = json.loads(resp.data)
    check("scale_pixels_per_foot present", 'scale_pixels_per_foot' in d)
    check("scale_pixels_per_foot is numeric", isinstance(d.get('scale_pixels_per_foot'), (int, float)),
          str(type(d.get('scale_pixels_per_foot'))))

# S2.14 — DELETE non-existent measurement → 404
print("\n-- S2.14: DELETE non-existent measurement -> 404 --")
resp = client.delete(f'/project/{PROJECT_ID}/takeoff/measurement/999999999')
check("DELETE non-existent measurement -> 404", resp.status_code == 404,
      f"status={resp.status_code}")

# S2.15 — item_totals update after measurement delete
print("\n-- S2.15: item_totals update after delete --")
if S2_ITEM_ID and PAGE_ID:
    # Add a measurement so we can check totals
    resp = client.post(
        f'/project/{PROJECT_ID}/takeoff/measurement',
        json={
            'item_id': S2_ITEM_ID, 'page_id': PAGE_ID,
            'points_json': json.dumps([{'x': 0.1, 'y': 0.1}, {'x': 0.9, 'y': 0.9}]),
            'calculated_value': 10.0, 'measurement_type': 'linear',
        },
        content_type='application/json',
    )
    add_data = json.loads(resp.data)
    new_meas_id = add_data.get('measurement_id')
    check("Temp measurement created", add_data.get('success'))

    if new_meas_id:
        resp2 = client.delete(f'/project/{PROJECT_ID}/takeoff/measurement/{new_meas_id}')
        d2 = json.loads(resp2.data)
        check("Delete returns item_totals", 'item_totals' in d2)
        totals = d2.get('item_totals', {})
        check("item_id in item_totals", 'item_id' in totals)
        check("total is numeric", isinstance(totals.get('total'), (int, float)),
              str(totals.get('total')))

# ── Final summary ─────────────────────────────────────────────────────────────
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
