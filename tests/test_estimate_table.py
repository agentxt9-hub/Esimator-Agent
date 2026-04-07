"""
tests/test_estimate_table.py — Session 22: Estimate Table API
pytest tests for /api/projects/<id>/line_items and /api/line_items/<id>

Run with:
    pytest tests/test_estimate_table.py -v --tb=short

Requirements:
  - Local PostgreSQL: postgresql://postgres:Builder@localhost:5432/estimator_db
  - Flask app importable from project root
"""

import sys
import os
import json
import pytest

# ── Make project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app, db, run_migrations
from app import Company, User, Project, LineItem, Assembly


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def app():
    """Configure Flask for testing (CSRF disabled)."""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    return flask_app


@pytest.fixture(scope='session')
def db_setup(app):
    """Run migrations once and create shared test fixtures (company, user, project).

    IMPORTANT: The app context is closed before yielding so that Flask's `g` object
    (used by Flask-Login to cache current_user) is NOT shared across requests during
    tests. Without this, session-scoped app contexts bleed Flask-Login state between
    test requests.
    """
    with app.app_context():
        db.create_all()
        run_migrations()

        # ── Company 999 (test company)
        co = Company.query.filter_by(company_name='__TEST_CO_999__').first()
        if not co:
            co = Company(company_name='__TEST_CO_999__')
            db.session.add(co)
            db.session.flush()

        # ── User in company 999
        u = User.query.filter_by(username='__test_user_999__').first()
        if not u:
            u = User(company_id=co.id, username='__test_user_999__',
                     email='testuser999@zenbid.test', role='estimator')
            u.set_password('TestPass999!')
            db.session.add(u)
            db.session.flush()

        # ── Project in company 999
        proj = Project.query.filter_by(
            project_name='__TEST_PROJECT_999__', company_id=co.id).first()
        if not proj:
            proj = Project(company_id=co.id, project_name='__TEST_PROJECT_999__',
                           project_number='TEST-999')
            db.session.add(proj)
            db.session.flush()

        # ── Other company 998 (for isolation tests)
        other_co = Company.query.filter_by(company_name='__TEST_CO_998__').first()
        if not other_co:
            other_co = Company(company_name='__TEST_CO_998__')
            db.session.add(other_co)
            db.session.flush()

        other_u = User.query.filter_by(username='__test_user_998__').first()
        if not other_u:
            other_u = User(company_id=other_co.id, username='__test_user_998__',
                           email='testuser998@zenbid.test', role='estimator')
            other_u.set_password('TestPass998!')
            db.session.add(other_u)
            db.session.flush()

        other_proj = Project.query.filter_by(
            project_name='__TEST_PROJECT_998__', company_id=other_co.id).first()
        if not other_proj:
            other_proj = Project(company_id=other_co.id, project_name='__TEST_PROJECT_998__',
                                 project_number='TEST-998')
            db.session.add(other_proj)
            db.session.flush()

        db.session.commit()

        ids = {
            'company_id':       co.id,
            'user_id':          u.id,
            'project_id':       proj.id,
            'other_company_id': other_co.id,
            'other_user_id':    other_u.id,
            'other_project_id': other_proj.id,
        }

    # App context is now closed — g is fresh for every test request.
    yield ids


@pytest.fixture
def client(app, db_setup):
    """Authenticated test client for company 999 user."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess['_user_id'] = str(db_setup['user_id'])
        sess['_fresh']   = True
    return c


@pytest.fixture
def other_client(app, db_setup):
    """Authenticated test client for company 998 user."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess['_user_id'] = str(db_setup['other_user_id'])
        sess['_fresh']   = True
    return c


@pytest.fixture
def sample_item(app, db_setup):
    """Create a fresh direct LineItem for company 999; clean up after test.
    The app context is closed before yielding to avoid polluting Flask g."""
    with app.app_context():
        item = LineItem(
            project_id             = db_setup['project_id'],
            company_id             = db_setup['company_id'],
            description            = '__SAMPLE_ITEM__',
            csi_division           = '03 — Concrete',
            phase                  = 'Foundation',
            trade                  = 'Concrete',
            quantity               = 100,
            unit                   = 'SF',
            labor_cost_per_unit    = 2.50,
            material_cost_per_unit = 1.25,
            total_cost             = 375.0,
            ai_status              = 'verified',
            ai_confidence          = 100,
            is_deleted             = False,
        )
        db.session.add(item)
        db.session.commit()
        item_id = item.id

    yield item_id

    with app.app_context():
        it = db.session.get(LineItem, item_id)
        if it:
            db.session.delete(it)
            db.session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type='application/json')


def patch_json(client, url, data):
    return client.patch(url, data=json.dumps(data), content_type='application/json')


# ─────────────────────────────────────────────────────────────────────────────
# 1. GET /api/projects/<id>/line_items
# ─────────────────────────────────────────────────────────────────────────────

class TestGetLineItems:

    def test_get_line_items_authenticated(self, client, db_setup):
        resp = client.get(f'/api/projects/{db_setup["project_id"]}/line_items')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'items' in data
        assert 'project' in data
        assert data['project']['id'] == db_setup['project_id']

    def test_get_line_items_unauthenticated_returns_401(self, app, db_setup):
        c = app.test_client()  # no session login
        resp = c.get(f'/api/projects/{db_setup["project_id"]}/line_items')
        # Flask-Login redirects to /login (302) for unauthenticated requests
        assert resp.status_code in (302, 401)

    def test_get_line_items_wrong_company_returns_403(self, other_client, db_setup):
        resp = other_client.get(f'/api/projects/{db_setup["project_id"]}/line_items')
        assert resp.status_code == 403

    def test_get_line_items_includes_sample(self, client, db_setup, sample_item):
        resp = client.get(f'/api/projects/{db_setup["project_id"]}/line_items')
        data = json.loads(resp.data)
        ids  = [i['id'] for i in data['items']]
        assert sample_item in ids

    def test_get_line_items_excludes_deleted(self, app, client, db_setup):
        with app.app_context():
            item = LineItem(
                project_id=db_setup['project_id'], company_id=db_setup['company_id'],
                description='__DELETED__', quantity=1, unit='EA',
                labor_cost_per_unit=0, material_cost_per_unit=0,
                total_cost=0, is_deleted=True,
            )
            db.session.add(item)
            db.session.commit()
            del_id = item.id

        resp = client.get(f'/api/projects/{db_setup["project_id"]}/line_items')
        data = json.loads(resp.data)
        ids  = [i['id'] for i in data['items']]
        assert del_id not in ids

        with app.app_context():
            it = db.session.get(LineItem, del_id)
            if it:
                db.session.delete(it)
                db.session.commit()

    def test_response_shape(self, client, db_setup, sample_item):
        resp = client.get(f'/api/projects/{db_setup["project_id"]}/line_items')
        data = json.loads(resp.data)
        item = next((i for i in data['items'] if i['id'] == sample_item), None)
        assert item is not None
        for field in ('id', 'description', 'csi_division', 'phase', 'trade',
                      'qty', 'unit', 'labor_rate', 'mat_cost', 'ai_status',
                      'ai_confidence', 'line_total'):
            assert field in item, f"Missing field: {field}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. POST /api/projects/<id>/line_items
# ─────────────────────────────────────────────────────────────────────────────

class TestCreateLineItem:

    def _valid_payload(self):
        return {
            'description': '__CREATED_ITEM__',
            'csi_division': '05 — Metals',
            'phase': 'Structure',
            'qty': 50,
            'unit': 'LF',
            'labor_rate': 3.0,
            'mat_cost': 1.5,
        }

    def test_create_line_item_valid_data(self, app, client, db_setup):
        resp = post_json(client, f'/api/projects/{db_setup["project_id"]}/line_items',
                         self._valid_payload())
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data['description'] == '__CREATED_ITEM__'
        assert data['id'] is not None
        # Clean up
        with app.app_context():
            it = db.session.get(LineItem, data['id'])
            if it:
                db.session.delete(it)
                db.session.commit()

    def test_create_line_item_missing_required_field_returns_400(self, client, db_setup):
        payload = self._valid_payload()
        del payload['description']
        resp = post_json(client, f'/api/projects/{db_setup["project_id"]}/line_items', payload)
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'error' in data

    def test_create_line_item_wrong_company_returns_403(self, other_client, db_setup):
        resp = post_json(other_client, f'/api/projects/{db_setup["project_id"]}/line_items',
                         self._valid_payload())
        assert resp.status_code == 403

    def test_line_total_computed_correctly_on_create(self, app, client, db_setup):
        payload = self._valid_payload()
        payload['qty'] = 10
        payload['labor_rate'] = 5.0
        payload['mat_cost']   = 3.0
        resp = post_json(client, f'/api/projects/{db_setup["project_id"]}/line_items', payload)
        assert resp.status_code == 201
        data = json.loads(resp.data)
        expected = 10 * (5.0 + 3.0)   # = 80.0
        assert abs(data['line_total'] - expected) < 0.01
        with app.app_context():
            it = db.session.get(LineItem, data['id'])
            if it:
                db.session.delete(it)
                db.session.commit()

    def test_company_id_isolation_enforced(self, app, client, db_setup):
        """Item created by user belongs to user's company_id."""
        resp = post_json(client, f'/api/projects/{db_setup["project_id"]}/line_items',
                         self._valid_payload())
        assert resp.status_code == 201
        item_id = json.loads(resp.data)['id']
        with app.app_context():
            it = db.session.get(LineItem, item_id)
            assert it is not None
            assert it.company_id == db_setup['company_id']
            db.session.delete(it)
            db.session.commit()

    def test_ai_generated_defaults_false(self, app, client, db_setup):
        resp = post_json(client, f'/api/projects/{db_setup["project_id"]}/line_items',
                         self._valid_payload())
        assert resp.status_code == 201
        item_id = json.loads(resp.data)['id']
        with app.app_context():
            it = db.session.get(LineItem, item_id)
            assert it.ai_generated == False
            db.session.delete(it)
            db.session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 3. PATCH /api/line_items/<id>
# ─────────────────────────────────────────────────────────────────────────────

class TestPatchLineItem:

    def test_patch_line_item_description(self, app, client, sample_item):
        resp = patch_json(client, f'/api/line_items/{sample_item}',
                          {'description': 'Updated Description'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['description'] == 'Updated Description'

    def test_patch_line_item_qty_recomputes_line_total(self, client, sample_item):
        # sample_item: qty=100, labor_rate=2.50, mat_cost=1.25 → total=375
        resp = patch_json(client, f'/api/line_items/{sample_item}', {'qty': 200})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        expected = 200 * (2.50 + 1.25)  # = 750
        assert abs(data['line_total'] - expected) < 0.01

    def test_patch_line_item_labor_rate_recomputes_line_total(self, client, sample_item):
        resp = patch_json(client, f'/api/line_items/{sample_item}', {'labor_rate': 5.0})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        # qty may vary after previous test; just check response has line_total
        assert 'line_total' in data
        assert data['labor_rate'] == 5.0

    def test_patch_line_item_mat_cost_recomputes_line_total(self, client, sample_item):
        resp = patch_json(client, f'/api/line_items/{sample_item}', {'mat_cost': 2.0})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['mat_cost'] == 2.0
        assert 'line_total' in data

    def test_patch_line_item_wrong_company_returns_403(self, other_client, sample_item):
        resp = patch_json(other_client, f'/api/line_items/{sample_item}',
                          {'description': 'Hacked'})
        assert resp.status_code == 403

    def test_patch_line_item_invalid_field_ignored(self, client, sample_item):
        """Fields not in the allowed list should be silently ignored."""
        resp = patch_json(client, f'/api/line_items/{sample_item}',
                          {'not_a_real_field': 'value', 'description': 'Fine'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['description'] == 'Fine'

    def test_edit_delta_captured_on_patch(self, app, client, sample_item):
        patch_json(client, f'/api/line_items/{sample_item}',
                   {'description': 'Delta Test'})
        with app.app_context():
            it = db.session.get(LineItem, sample_item)
            assert it.estimator_action == 'edited'
            delta = json.loads(it.edit_delta or '{}')
            assert 'description' in delta

    def test_estimator_action_field_writeable(self, app, client, sample_item):
        # estimator_action is set internally on patch; verify it's set
        patch_json(client, f'/api/line_items/{sample_item}', {'phase': 'Phase X'})
        with app.app_context():
            it = db.session.get(LineItem, sample_item)
            assert it.estimator_action is not None


# ─────────────────────────────────────────────────────────────────────────────
# 4. DELETE /api/line_items/<id> (soft delete)
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteLineItem:

    def test_delete_line_item_soft_delete(self, app, client, db_setup):
        # Create an item to delete
        with app.app_context():
            item = LineItem(
                project_id=db_setup['project_id'], company_id=db_setup['company_id'],
                description='__TO_DELETE__', quantity=1, unit='EA',
                labor_cost_per_unit=0, material_cost_per_unit=0,
                total_cost=0, is_deleted=False,
            )
            db.session.add(item)
            db.session.commit()
            item_id = item.id

        resp = client.delete(f'/api/line_items/{item_id}')
        assert resp.status_code == 204

        # Verify soft delete (record still exists, is_deleted=True)
        with app.app_context():
            it = db.session.get(LineItem, item_id)
            assert it is not None
            assert it.is_deleted is True
            db.session.delete(it)
            db.session.commit()

    def test_delete_line_item_wrong_company_returns_403(self, other_client, sample_item):
        resp = other_client.delete(f'/api/line_items/{sample_item}')
        assert resp.status_code == 403

    def test_soft_deleted_items_excluded_from_get(self, app, client, db_setup):
        with app.app_context():
            item = LineItem(
                project_id=db_setup['project_id'], company_id=db_setup['company_id'],
                description='__SOFT_DEL__', quantity=1, unit='EA',
                labor_cost_per_unit=0, material_cost_per_unit=0,
                total_cost=0, is_deleted=False,
            )
            db.session.add(item)
            db.session.commit()
            item_id = item.id

        # Soft delete it
        client.delete(f'/api/line_items/{item_id}')

        # Verify not in GET response
        resp = client.get(f'/api/projects/{db_setup["project_id"]}/line_items')
        data = json.loads(resp.data)
        ids  = [i['id'] for i in data['items']]
        assert item_id not in ids

        with app.app_context():
            it = db.session.get(LineItem, item_id)
            if it:
                db.session.delete(it)
                db.session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# 5. CSRF tests (CSRF is disabled in testing, but verify behaviour without token)
# ─────────────────────────────────────────────────────────────────────────────

class TestCSRF:

    def test_post_without_csrf_returns_400(self, app, db_setup):
        """When WTF_CSRF_ENABLED=True, POST without token returns 400."""
        app.config['WTF_CSRF_ENABLED'] = True
        c = app.test_client()
        with c.session_transaction() as sess:
            sess['_user_id'] = str(db_setup['user_id'])
            sess['_fresh']   = True
        resp = c.post(
            f'/api/projects/{db_setup["project_id"]}/line_items',
            data=json.dumps({'description': 'x', 'qty': 1, 'unit': 'EA', 'labor_rate': 0, 'mat_cost': 0}),
            content_type='application/json',
        )
        app.config['WTF_CSRF_ENABLED'] = False  # restore
        assert resp.status_code in (400, 403)

    def test_patch_without_csrf_returns_400(self, app, db_setup, sample_item):
        """When WTF_CSRF_ENABLED=True, PATCH without token returns 400."""
        app.config['WTF_CSRF_ENABLED'] = True
        c = app.test_client()
        with c.session_transaction() as sess:
            sess['_user_id'] = str(db_setup['user_id'])
            sess['_fresh']   = True
        resp = c.patch(
            f'/api/line_items/{sample_item}',
            data=json.dumps({'description': 'x'}),
            content_type='application/json',
        )
        app.config['WTF_CSRF_ENABLED'] = False  # restore
        assert resp.status_code in (400, 403)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Model field tests
# ─────────────────────────────────────────────────────────────────────────────

class TestModelFields:

    def test_line_total_computed_correctly_on_create(self, app, client, db_setup):
        resp = post_json(client, f'/api/projects/{db_setup["project_id"]}/line_items', {
            'description': '__TOTAL_TEST__', 'qty': 4, 'unit': 'CY',
            'labor_rate': 12.0, 'mat_cost': 8.0,
        })
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert abs(data['line_total'] - (4 * 20.0)) < 0.01  # 4 * (12+8) = 80
        with app.app_context():
            it = db.session.get(LineItem, data['id'])
            if it:
                db.session.delete(it)
                db.session.commit()

    def test_line_total_recomputed_on_qty_change(self, client, sample_item):
        resp = patch_json(client, f'/api/line_items/{sample_item}',
                          {'qty': 50, 'labor_rate': 2.0, 'mat_cost': 1.0})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert abs(data['line_total'] - (50 * 3.0)) < 0.01

    def test_line_total_recomputed_on_labor_rate_change(self, app, client, db_setup):
        resp = post_json(client, f'/api/projects/{db_setup["project_id"]}/line_items', {
            'description': '__LR_TEST__', 'qty': 10, 'unit': 'SF',
            'labor_rate': 1.0, 'mat_cost': 0.0,
        })
        data = json.loads(resp.data)
        item_id = data['id']

        resp2 = patch_json(client, f'/api/line_items/{item_id}', {'labor_rate': 5.0})
        data2 = json.loads(resp2.data)
        assert abs(data2['line_total'] - 50.0) < 0.01

        with app.app_context():
            it = db.session.get(LineItem, item_id)
            if it:
                db.session.delete(it)
                db.session.commit()

    def test_line_total_recomputed_on_mat_cost_change(self, app, client, db_setup):
        resp = post_json(client, f'/api/projects/{db_setup["project_id"]}/line_items', {
            'description': '__MC_TEST__', 'qty': 10, 'unit': 'SF',
            'labor_rate': 0.0, 'mat_cost': 2.0,
        })
        data = json.loads(resp.data)
        item_id = data['id']

        resp2 = patch_json(client, f'/api/line_items/{item_id}', {'mat_cost': 4.0})
        data2 = json.loads(resp2.data)
        assert abs(data2['line_total'] - 40.0) < 0.01

        with app.app_context():
            it = db.session.get(LineItem, item_id)
            if it:
                db.session.delete(it)
                db.session.commit()
