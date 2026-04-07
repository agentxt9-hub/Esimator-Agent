# routes_takeoff.py — Takeoff module blueprint
# Registered in app.py at the bottom via app.register_blueprint(takeoff_bp)
# All models imported from app.py — safe because this module is only imported
# after all models and helpers are fully defined in app.py.

import os
import uuid
import json
from datetime import datetime, timezone

from flask import (Blueprint, render_template, request, jsonify,
                   abort, send_file, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# These imports work because routes_takeoff.py is only loaded at the
# bottom of app.py after db, models, and helpers are all defined.
from app import (db, TakeoffPlan, TakeoffPage, TakeoffItem,
                 TakeoffMeasurement, get_project_or_403, Project)

takeoff_bp = Blueprint('takeoff', __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {'pdf'}
MAX_PDF_BYTES = 100 * 1024 * 1024  # 100 MB


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _plan_dir(project_id):
    base = os.path.join(current_app.root_path, 'static', 'uploads',
                        'takeoff', str(project_id))
    os.makedirs(base, exist_ok=True)
    return base



def _get_plan_or_403(plan_id):
    plan = TakeoffPlan.query.get_or_404(plan_id)
    if plan.company_id != current_user.company_id:
        abort(403)
    return plan


def _get_item_or_403(item_id):
    item = TakeoffItem.query.get_or_404(item_id)
    if item.company_id != current_user.company_id:
        abort(403)
    return item


# ── main viewer ──────────────────────────────────────────────────────────────

@takeoff_bp.route('/project/<int:project_id>/takeoff')
@login_required
def viewer(project_id):
    project = get_project_or_403(project_id)
    plans = (TakeoffPlan.query
             .filter_by(project_id=project_id, company_id=current_user.company_id)
             .order_by(TakeoffPlan.uploaded_at)
             .all())

    plans_data = []
    for plan in plans:
        # Explicit query (not plan.pages relationship) to guarantee correct results
        pages = (TakeoffPage.query
                 .filter_by(plan_id=plan.id)
                 .order_by(TakeoffPage.page_number)
                 .all())
        pages_data = [
            {
                'id': p.id,
                'page_number': p.page_number,
                'page_name': p.page_name,
                'thumbnail_url': None,   # always None — rendered client-side by PDF.js
                'scale_set': p.scale_pixels_per_foot is not None,
                'scale_method': p.scale_method,
            }
            for p in pages
        ]
        plans_data.append({
            'id': plan.id,
            'original_filename': plan.original_filename,
            'page_count': plan.page_count,
            'pages': pages_data,
        })

    return render_template(
        'takeoff/viewer.html',
        project=project,
        plans_data=plans_data,
    )


# ── PDF upload ────────────────────────────────────────────────────────────────

@takeoff_bp.route('/project/<int:project_id>/takeoff/upload', methods=['POST'])
@login_required
def upload_pdf(project_id):
    project = get_project_or_403(project_id)

    if 'pdf' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    f = request.files['pdf']
    if not f or not _allowed(f.filename):
        return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400

    # Size check (read into memory once)
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    if size > MAX_PDF_BYTES:
        return jsonify({'success': False, 'error': 'File exceeds 100 MB limit'}), 400

    pdf_path = None  # tracked so we can clean up on any failure after save
    try:
        safe_orig = secure_filename(f.filename)
        stored_name = f'{uuid.uuid4().hex}_{safe_orig}'
        plan_dir = _plan_dir(project_id)
        pdf_path = os.path.join(plan_dir, stored_name)
        f.save(pdf_path)

        # Create DB plan record first (need plan.id for thumbnail naming)
        plan = TakeoffPlan(
            project_id=project_id,
            company_id=current_user.company_id,
            filename=stored_name,
            original_filename=safe_orig,
            uploaded_by=current_user.id,
        )
        db.session.add(plan)
        db.session.flush()  # get plan.id before commit

        # Count pages with PyMuPDF — thumbnails render client-side via PDF.js
        pages_data = []
        try:
            import fitz
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
        except Exception:
            total_pages = 1  # last-resort fallback

        plan.page_count = total_pages

        for idx in range(1, total_pages + 1):
            page_record = TakeoffPage(
                plan_id=plan.id,
                page_number=idx,
                page_name=f'Page {idx}',
                thumbnail_path=None,
            )
            db.session.add(page_record)
            db.session.flush()
            pages_data.append({
                'id': page_record.id,
                'page_number': idx,
                'page_name': page_record.page_name,
                'thumbnail_url': None,  # rendered client-side
            })

        db.session.commit()
        return jsonify({
            'success': True,
            'plan_id': plan.id,
            'original_filename': plan.original_filename,
            'page_count': plan.page_count,
            'pages': pages_data,
        })

    except Exception as e:
        db.session.rollback()
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)
        current_app.logger.error(f'PDF upload failed, cleaned up {pdf_path}: {e}')
        return jsonify({'success': False, 'error': 'Upload failed. Please try again.'}), 500


# ── serve raw PDF ─────────────────────────────────────────────────────────────

@takeoff_bp.route('/project/<int:project_id>/takeoff/plan/<int:plan_id>/pdf')
@login_required
def serve_pdf(project_id, plan_id):
    get_project_or_403(project_id)
    plan = _get_plan_or_403(plan_id)

    pdf_path = os.path.join(current_app.root_path, 'static', 'uploads',
                            'takeoff', str(project_id), plan.filename)

    # Debug: log path details to help diagnose 0-byte responses
    exists = os.path.exists(pdf_path)
    size = os.path.getsize(pdf_path) if exists else -1
    current_app.logger.info(
        f'serve_pdf plan={plan_id} project={project_id} '
        f'path={pdf_path!r} exists={exists} size={size}'
    )

    if not exists:
        abort(404)

    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=plan.original_filename,
    )


# ── takeoff items CRUD ────────────────────────────────────────────────────────

@takeoff_bp.route('/project/<int:project_id>/takeoff/items')
@login_required
def list_items(project_id):
    get_project_or_403(project_id)

    items = (TakeoffItem.query
             .filter_by(project_id=project_id, company_id=current_user.company_id)
             .order_by(TakeoffItem.created_at)
             .all())

    result = []
    for item in items:
        # Aggregate totals across all pages
        total = sum(m.calculated_value or 0 for m in item.measurements)
        result.append({
            'id': item.id,
            'name': item.name,
            'measurement_type': item.measurement_type,
            'color': item.color,
            'opacity': item.opacity,
            'width_ft': item.width_ft,
            'side_of_line': item.side_of_line,
            'assembly_notes': item.assembly_notes,
            'division': item.division,
            'total': round(total, 2),
            'measurement_count': len(item.measurements),
        })

    return jsonify(result)


@takeoff_bp.route('/project/<int:project_id>/takeoff/item', methods=['POST'])
@login_required
def create_item(project_id):
    get_project_or_403(project_id)
    data = request.get_json(silent=True) or {}

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    measurement_type = data.get('measurement_type', 'linear')
    if measurement_type not in ('linear', 'area', 'count', 'linear_with_width', 'segment'):
        measurement_type = 'linear'

    item = TakeoffItem(
        project_id=project_id,
        company_id=current_user.company_id,
        name=name,
        measurement_type=measurement_type,
        color=data.get('color', '#2D5BFF'),
        opacity=float(data.get('opacity', 0.5)),
        width_ft=float(data['width_ft']) if data.get('width_ft') else None,
        side_of_line=data.get('side_of_line', 'center'),
        assembly_notes=data.get('assembly_notes', ''),
        division=data.get('division', ''),
        created_by=current_user.id,
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'name': item.name,
            'measurement_type': item.measurement_type,
            'color': item.color,
            'opacity': item.opacity,
            'width_ft': item.width_ft,
            'side_of_line': item.side_of_line,
            'assembly_notes': item.assembly_notes,
            'division': item.division,
            'total': 0,
            'measurement_count': 0,
        }
    }), 201


@takeoff_bp.route('/project/<int:project_id>/takeoff/item/<int:item_id>',
                  methods=['DELETE'])
@login_required
def delete_item(project_id, item_id):
    get_project_or_403(project_id)
    item = _get_item_or_403(item_id)

    # Cascade: measurements deleted via SQLAlchemy relationship cascade
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
