# app.py - Construction Estimating Tool
# Install required packages first by running in terminal:
# pip install flask psycopg2-binary sqlalchemy flask-sqlalchemy

from flask import Flask, render_template, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json
import io
import csv
import urllib.request
import urllib.error
import re

app = Flask(__name__)

# Database connection - update password to match your PostgreSQL setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Builder@localhost:5432/estimator_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─────────────────────────────────────────
# DATABASE MODELS
# ─────────────────────────────────────────

class CSILevel1(db.Model):
    __tablename__ = 'csi_level_1'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subcodes = db.relationship('CSILevel2', backref='division', lazy=True)

class CSILevel2(db.Model):
    __tablename__ = 'csi_level_2'
    id = db.Column(db.Integer, primary_key=True)
    csi_level_1_id = db.Column(db.Integer, db.ForeignKey('csi_level_1.id'), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(255), nullable=False)
    project_number = db.Column(db.String(100))
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    assemblies = db.relationship('Assembly', backref='project', lazy=True)

class Assembly(db.Model):
    __tablename__ = 'assemblies'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assembly_label = db.Column(db.String(100), nullable=False)
    assembly_name = db.Column(db.String(255), nullable=False)
    csi_level_1_id = db.Column(db.Integer, db.ForeignKey('csi_level_1.id'))
    csi_level_2_id = db.Column(db.Integer, db.ForeignKey('csi_level_2.id'))
    description = db.Column(db.Text)
    quantity = db.Column(db.Numeric(10, 2))
    unit = db.Column(db.String(50))
    is_template = db.Column(db.Boolean, default=False)
    measurement_params = db.Column(db.Text)  # JSON: {"lf":500,"height":12,"depth":0,"width":0}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    line_items = db.relationship('LineItem', backref='assembly', lazy=True)
    composition = db.relationship('AssemblyComposition', backref='assembly', lazy=True,
                                  order_by='AssemblyComposition.sort_order')

class AssemblyComposition(db.Model):
    __tablename__ = 'assembly_composition'
    id = db.Column(db.Integer, primary_key=True)
    assembly_id = db.Column(db.Integer, db.ForeignKey('assemblies.id'), nullable=False)
    library_item_id = db.Column(db.Integer, db.ForeignKey('library_items.id'))
    description = db.Column(db.String(255), nullable=False)
    unit = db.Column(db.String(50))
    qty_formula = db.Column(db.String(50), default='fixed')
    qty_divisor = db.Column(db.Numeric(10, 4), default=1)
    qty_manual = db.Column(db.Numeric(10, 2), default=0)
    production_rate = db.Column(db.Numeric(10, 2), default=1)
    material_cost_per_unit = db.Column(db.Numeric(10, 2))
    labor_cost_per_hour = db.Column(db.Numeric(10, 2))
    equipment_cost_per_hour = db.Column(db.Numeric(10, 2))
    sort_order = db.Column(db.Integer, default=0)

class LibraryItem(db.Model):
    __tablename__ = 'library_items'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    csi_level_1_id = db.Column(db.Integer, db.ForeignKey('csi_level_1.id'))
    csi_level_2_id = db.Column(db.Integer, db.ForeignKey('csi_level_2.id'))
    unit = db.Column(db.String(50))
    production_rate = db.Column(db.Numeric(10, 2))
    production_unit = db.Column(db.String(50))
    material_cost_per_unit = db.Column(db.Numeric(10, 2))
    labor_cost_per_hour = db.Column(db.Numeric(10, 2))
    equipment_cost_per_hour = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class LineItem(db.Model):
    __tablename__ = 'line_items'
    id = db.Column(db.Integer, primary_key=True)
    assembly_id = db.Column(db.Integer, db.ForeignKey('assemblies.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    production_rate = db.Column(db.Numeric(10, 2))
    production_unit = db.Column(db.String(50))
    material_cost_per_unit = db.Column(db.Numeric(10, 2))
    material_cost = db.Column(db.Numeric(12, 2))
    labor_hours = db.Column(db.Numeric(10, 2))
    labor_cost_per_hour = db.Column(db.Numeric(10, 2))
    labor_cost = db.Column(db.Numeric(12, 2))
    equipment_hours = db.Column(db.Numeric(10, 2))
    equipment_cost_per_hour = db.Column(db.Numeric(10, 2))
    equipment_cost = db.Column(db.Numeric(12, 2))
    total_cost = db.Column(db.Numeric(12, 2))
    trade = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.route('/')
def index():
    projects = Project.query.all()
    total_value = db.session.query(db.func.sum(LineItem.total_cost)).scalar() or 0
    active_count = db.session.query(Project.id)\
        .join(Assembly, Assembly.project_id == Project.id)\
        .join(LineItem, LineItem.assembly_id == Assembly.id)\
        .distinct().count()
    return render_template('index.html', projects=projects,
                           total_value=float(total_value),
                           active_count=active_count)

@app.route('/project/new', methods=['GET', 'POST'])
def new_project():
    if request.method == 'POST':
        project = Project(
            project_name=request.form['project_name'],
            project_number=request.form['project_number'],
            description=request.form['description'],
            location=request.form['location']
        )
        db.session.add(project)
        db.session.commit()
        return jsonify({'success': True, 'project_id': project.id})
    return render_template('new_project.html')

@app.route('/project/<int:project_id>')
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    assemblies = Assembly.query.filter_by(project_id=project_id).all()
    csi1_list = CSILevel1.query.order_by(CSILevel1.code).all()
    csi2_list = CSILevel2.query.order_by(CSILevel2.code).all()
    csi1_map = {d.id: d for d in csi1_list}
    csi2_map = {s.id: s for s in csi2_list}
    csi2_data = [{'id': s.id, 'parent': s.csi_level_1_id, 'code': s.code, 'title': s.title}
                 for s in csi2_list]
    assemblies_data = [{'id': a.id, 'label': a.assembly_label, 'name': a.assembly_name,
                        'csi_level_1_id': a.csi_level_1_id, 'csi_level_2_id': a.csi_level_2_id,
                        'description': a.description or '', 'quantity': float(a.quantity or 0),
                        'unit': a.unit or ''} for a in assemblies]
    return render_template('project.html', project=project, assemblies=assemblies,
                           csi1_list=csi1_list, csi2_json=json.dumps(csi2_data),
                           csi1_map=csi1_map, csi2_map=csi2_map,
                           assemblies_json=json.dumps(assemblies_data))

@app.route('/project/<int:project_id>/assembly/new', methods=['POST'])
def new_assembly(project_id):
    assembly = Assembly(
        project_id=project_id,
        assembly_label=request.form['assembly_label'],
        assembly_name=request.form['assembly_name'],
        csi_level_1_id=request.form.get('csi_level_1_id'),
        csi_level_2_id=request.form.get('csi_level_2_id'),
        description=request.form.get('description'),
        quantity=request.form.get('quantity'),
        unit=request.form.get('unit')
    )
    db.session.add(assembly)
    db.session.commit()
    return jsonify({'success': True, 'assembly_id': assembly.id})

@app.route('/assembly/<int:assembly_id>/lineitem/new', methods=['POST'])
def new_line_item(assembly_id):
    quantity = float(request.form.get('quantity', 0))
    production_rate = float(request.form.get('production_rate', 1))
    material_cost_per_unit = float(request.form.get('material_cost_per_unit', 0))
    labor_cost_per_hour = float(request.form.get('labor_cost_per_hour', 0))
    equipment_cost_per_hour = float(request.form.get('equipment_cost_per_hour', 0))

    # Calculate hours from production rate
    labor_hours = quantity / production_rate if production_rate > 0 else 0
    equipment_hours = labor_hours  # adjust if equipment hours differ

    # Calculate costs
    material_cost = quantity * material_cost_per_unit
    labor_cost = labor_hours * labor_cost_per_hour
    equipment_cost = equipment_hours * equipment_cost_per_hour
    total_cost = material_cost + labor_cost + equipment_cost

    line_item = LineItem(
        assembly_id=assembly_id,
        description=request.form['description'],
        quantity=quantity,
        unit=request.form['unit'],
        production_rate=production_rate,
        production_unit=request.form.get('production_unit'),
        material_cost_per_unit=material_cost_per_unit,
        material_cost=material_cost,
        labor_hours=labor_hours,
        labor_cost_per_hour=labor_cost_per_hour,
        labor_cost=labor_cost,
        equipment_hours=equipment_hours,
        equipment_cost_per_hour=equipment_cost_per_hour,
        equipment_cost=equipment_cost,
        total_cost=total_cost,
        trade=request.form.get('trade'),
        notes=request.form.get('notes')
    )
    db.session.add(line_item)
    db.session.commit()
    return jsonify({'success': True, 'line_item_id': line_item.id})

@app.route('/project/<int:project_id>/summary')
def project_summary(project_id):
    project = Project.query.get_or_404(project_id)
    assemblies = Assembly.query.filter_by(project_id=project_id).all()
    
    summary = {
        'total_material_cost': 0,
        'total_labor_cost': 0,
        'total_labor_hours': 0,
        'total_equipment_cost': 0,
        'total_equipment_hours': 0,
        'total_cost': 0
    }

    for assembly in assemblies:
        line_items = LineItem.query.filter_by(assembly_id=assembly.id).all()
        for item in line_items:
            summary['total_material_cost'] += float(item.material_cost or 0)
            summary['total_labor_cost'] += float(item.labor_cost or 0)
            summary['total_labor_hours'] += float(item.labor_hours or 0)
            summary['total_equipment_cost'] += float(item.equipment_cost or 0)
            summary['total_equipment_hours'] += float(item.equipment_hours or 0)
            summary['total_cost'] += float(item.total_cost or 0)

    return jsonify({'project': project.project_name, 'summary': summary})

@app.route('/project/<int:project_id>/report')
def project_report(project_id):
    project = Project.query.get_or_404(project_id)
    raw_assemblies = Assembly.query.filter_by(project_id=project_id).all()

    summary = {
        'total_material_cost': 0, 'total_labor_cost': 0, 'total_labor_hours': 0,
        'total_equipment_cost': 0, 'total_equipment_hours': 0, 'total_cost': 0
    }
    assembly_rows = []
    for asm in raw_assemblies:
        row = {'assembly': asm, 'item_count': 0, 'material_cost': 0,
               'labor_cost': 0, 'labor_hours': 0, 'equipment_cost': 0,
               'equipment_hours': 0, 'total_cost': 0}
        for item in asm.line_items:
            row['item_count'] += 1
            row['material_cost']    += float(item.material_cost or 0)
            row['labor_cost']       += float(item.labor_cost or 0)
            row['labor_hours']      += float(item.labor_hours or 0)
            row['equipment_cost']   += float(item.equipment_cost or 0)
            row['equipment_hours']  += float(item.equipment_hours or 0)
            row['total_cost']       += float(item.total_cost or 0)
        assembly_rows.append(row)
        for key in ('material_cost', 'labor_cost', 'labor_hours', 'equipment_cost', 'equipment_hours', 'total_cost'):
            summary['total_' + key] += row[key]

    return render_template('summary.html', project=project, summary=summary, assemblies=assembly_rows)

@app.route('/project/<int:project_id>/estimate')
def estimate_view(project_id):
    project = Project.query.get_or_404(project_id)
    assemblies = Assembly.query.filter_by(project_id=project_id).order_by(Assembly.assembly_label).all()

    csi1_map = {d.id: d for d in CSILevel1.query.all()}
    csi2_map = {s.id: s for s in CSILevel2.query.all()}

    items = []
    for asm in assemblies:
        csi1 = csi1_map.get(asm.csi_level_1_id)
        csi2 = csi2_map.get(asm.csi_level_2_id)
        for item in asm.line_items:
            items.append({
                'id': item.id,
                'assembly_id': asm.id,
                'assembly_label': asm.assembly_label,
                'assembly_name': asm.assembly_name,
                'csi_level_1_id': asm.csi_level_1_id,
                'csi_level_1_code': csi1.code if csi1 else '',
                'csi_level_1_title': csi1.title if csi1 else '',
                'csi_level_2_id': asm.csi_level_2_id,
                'csi_level_2_code': csi2.code if csi2 else '',
                'csi_level_2_title': csi2.title if csi2 else '',
                'description': item.description,
                'quantity': float(item.quantity or 0),
                'unit': item.unit or '',
                'production_rate': float(item.production_rate or 0),
                'labor_hours': float(item.labor_hours or 0),
                'material_cost_per_unit': float(item.material_cost_per_unit or 0),
                'material_cost': float(item.material_cost or 0),
                'labor_cost_per_hour': float(item.labor_cost_per_hour or 0),
                'labor_cost': float(item.labor_cost or 0),
                'equipment_cost_per_hour': float(item.equipment_cost_per_hour or 0),
                'equipment_hours': float(item.equipment_hours or 0),
                'equipment_cost': float(item.equipment_cost or 0),
                'total_cost': float(item.total_cost or 0),
                'trade': item.trade or '',
                'notes': item.notes or '',
            })

    assemblies_data = [{'id': a.id, 'label': a.assembly_label, 'name': a.assembly_name} for a in assemblies]
    csi1_data = [{'id': d.id, 'code': d.code, 'title': d.title}
                 for d in CSILevel1.query.order_by(CSILevel1.code).all()]
    csi2_data = [{'id': s.id, 'parent': s.csi_level_1_id, 'code': s.code, 'title': s.title}
                 for s in CSILevel2.query.order_by(CSILevel2.code).all()]

    return render_template('estimate.html',
                           project=project,
                           items_json=json.dumps(items),
                           assemblies_json=json.dumps(assemblies_data),
                           csi1_json=json.dumps(csi1_data),
                           csi2_json=json.dumps(csi2_data))


@app.route('/assembly/<int:assembly_id>/update', methods=['POST'])
def update_assembly(assembly_id):
    assembly = Assembly.query.get_or_404(assembly_id)
    assembly.assembly_label = request.form['assembly_label']
    assembly.assembly_name = request.form['assembly_name']
    assembly.csi_level_1_id = request.form.get('csi_level_1_id') or None
    assembly.csi_level_2_id = request.form.get('csi_level_2_id') or None
    assembly.description = request.form.get('description')
    assembly.quantity = request.form.get('quantity') or None
    assembly.unit = request.form.get('unit')
    assembly.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/lineitem/<int:item_id>/update', methods=['POST'])
def update_line_item(item_id):
    item = LineItem.query.get_or_404(item_id)
    data = request.get_json()

    if 'description' in data: item.description = data['description']
    if 'unit' in data:        item.unit = data['unit']
    if 'trade' in data:       item.trade = data['trade']
    if 'notes' in data:       item.notes = data['notes']

    for field in ('quantity', 'production_rate', 'material_cost_per_unit',
                  'labor_cost_per_hour', 'equipment_cost_per_hour'):
        if field in data:
            try:
                setattr(item, field, float(data[field]) if data[field] not in ('', None) else 0)
            except (ValueError, TypeError):
                pass

    # Recalculate derived values
    qty      = float(item.quantity or 0)
    rate     = float(item.production_rate or 0)
    lhrs     = qty / rate if rate > 0 else 0
    ehrs     = lhrs
    mat_cost = qty  * float(item.material_cost_per_unit or 0)
    lab_cost = lhrs * float(item.labor_cost_per_hour or 0)
    equ_cost = ehrs * float(item.equipment_cost_per_hour or 0)
    total    = mat_cost + lab_cost + equ_cost

    item.labor_hours     = lhrs
    item.equipment_hours = ehrs
    item.material_cost   = mat_cost
    item.labor_cost      = lab_cost
    item.equipment_cost  = equ_cost
    item.total_cost      = total
    item.updated_at      = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'labor_hours': lhrs, 'material_cost': mat_cost,
        'labor_cost': lab_cost, 'equipment_hours': ehrs,
        'equipment_cost': equ_cost, 'total_cost': total
    })


@app.route('/lineitem/<int:item_id>/delete', methods=['POST'])
def delete_line_item(item_id):
    item = LineItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/assembly/<int:assembly_id>/delete', methods=['POST'])
def delete_assembly(assembly_id):
    assembly = Assembly.query.get_or_404(assembly_id)
    LineItem.query.filter_by(assembly_id=assembly_id).delete()
    db.session.delete(assembly)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    for asm in project.assemblies:
        LineItem.query.filter_by(assembly_id=asm.id).delete()
    Assembly.query.filter_by(project_id=project_id).delete()
    db.session.delete(project)
    db.session.commit()
    return jsonify({'success': True})

# ─────────────────────────────────────────
# HELPER: QUANTITY FORMULA CALCULATOR
# ─────────────────────────────────────────

def calculate_qty(formula, params, divisor=1, manual_qty=0):
    """Calculate line item quantity from assembly measurements and a formula key."""
    lf     = float(params.get('lf', 0))
    height = float(params.get('height', 0))
    depth  = float(params.get('depth', 0))
    width  = float(params.get('width', 0))
    sf     = lf * height if height else 0
    div    = float(divisor) if float(divisor) > 0 else 1
    return {
        'fixed':     float(manual_qty),
        'lf':        lf,
        'lf_x_2':   lf * 2,
        'sf':        sf,
        'sf_div':    sf / div,
        'depth':     lf * depth,
        'volume_cy': (lf * (width or 1) * depth) / 27 if depth else 0,
    }.get(formula, float(manual_qty))

# ─────────────────────────────────────────
# ASSEMBLY BUILDER ROUTES
# ─────────────────────────────────────────

@app.route('/project/<int:project_id>/assembly/builder')
def assembly_builder(project_id):
    project = Project.query.get_or_404(project_id)
    csi1_list = CSILevel1.query.order_by(CSILevel1.code).all()
    csi1_map = {d.id: d for d in csi1_list}
    csi2_map = {s.id: s for s in CSILevel2.query.all()}
    library_items = LibraryItem.query.order_by(LibraryItem.description).all()
    library_data = [{
        'id': i.id, 'description': i.description,
        'csi_level_1_id': i.csi_level_1_id,
        'csi_code': csi1_map[i.csi_level_1_id].code if i.csi_level_1_id and i.csi_level_1_id in csi1_map else '',
        'csi_title': csi1_map[i.csi_level_1_id].title if i.csi_level_1_id and i.csi_level_1_id in csi1_map else '',
        'unit': i.unit or '', 'production_rate': float(i.production_rate or 1),
        'material_cost_per_unit': float(i.material_cost_per_unit or 0),
        'labor_cost_per_hour': float(i.labor_cost_per_hour or 0),
        'equipment_cost_per_hour': float(i.equipment_cost_per_hour or 0),
        'notes': i.notes or ''
    } for i in library_items]

    # Pre-load from template if requested
    template_data = None
    from_template_id = request.args.get('from_template', type=int)
    if from_template_id:
        tmpl = Assembly.query.filter_by(id=from_template_id, is_template=True).first()
        if tmpl:
            params = {}
            if tmpl.measurement_params:
                try:
                    params = json.loads(tmpl.measurement_params)
                except (ValueError, TypeError):
                    pass
            template_data = {
                'label': tmpl.assembly_label,
                'name': tmpl.assembly_name,
                'description': tmpl.description or '',
                'lf':     float(params.get('lf', 0)),
                'height': float(params.get('height', 0)),
                'depth':  float(params.get('depth', 0)),
                'width':  float(params.get('width', 0)),
                'composition': [{
                    'library_item_id': c.library_item_id,
                    'description':     c.description,
                    'unit':            c.unit or '',
                    'formula':         c.qty_formula,
                    'divisor':         float(c.qty_divisor or 1),
                    'manual_qty':      float(c.qty_manual or 0),
                    'production_rate': float(c.production_rate or 1),
                    'mat_cost':        float(c.material_cost_per_unit or 0),
                    'labor_rate':      float(c.labor_cost_per_hour or 0),
                    'equip_rate':      float(c.equipment_cost_per_hour or 0),
                    'qty':             0,
                } for c in tmpl.composition],
            }

    return render_template('assembly_builder.html', project=project,
                           library_json=json.dumps(library_data),
                           template_json=json.dumps(template_data))

@app.route('/project/<int:project_id>/assembly/builder/save', methods=['POST'])
def save_assembly_builder(project_id):
    params_str = request.form.get('measurement_params', '{}')
    comp_str   = request.form.get('composition', '[]')
    try:
        params = json.loads(params_str)
        comp_items = json.loads(comp_str)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid JSON data'})

    # Determine assembly qty/unit from measurements
    lf     = float(params.get('lf', 0))
    height = float(params.get('height', 0))
    sf     = lf * height if height else lf
    asm_qty  = sf or lf or 1
    asm_unit = 'SF' if height else ('LF' if lf else 'LS')

    assembly = Assembly(
        project_id=project_id,
        assembly_label=request.form['assembly_label'],
        assembly_name=request.form['assembly_name'],
        description=request.form.get('description'),
        quantity=asm_qty, unit=asm_unit,
        is_template=request.form.get('is_template') == 'on',
        measurement_params=params_str
    )
    db.session.add(assembly)
    db.session.flush()  # get assembly.id

    for i, comp in enumerate(comp_items):
        formula    = comp.get('formula', 'fixed')
        divisor    = float(comp.get('divisor', 1)) or 1
        manual_qty = float(comp.get('manual_qty', 0))
        qty        = calculate_qty(formula, params, divisor, manual_qty)

        mat_per  = float(comp.get('mat_cost', 0))
        lab_hr   = float(comp.get('labor_rate', 0))
        equ_hr   = float(comp.get('equip_rate', 0))
        prod_r   = float(comp.get('production_rate', 1)) or 1

        lab_hrs  = qty / prod_r if prod_r > 0 else 0
        equ_hrs  = lab_hrs
        mat_cost = qty * mat_per
        lab_cost = lab_hrs * lab_hr
        equ_cost = equ_hrs * equ_hr
        total    = mat_cost + lab_cost + equ_cost

        db.session.add(AssemblyComposition(
            assembly_id=assembly.id,
            library_item_id=comp.get('library_item_id'),
            description=comp['description'],
            unit=comp.get('unit', ''),
            qty_formula=formula, qty_divisor=divisor, qty_manual=manual_qty,
            production_rate=prod_r,
            material_cost_per_unit=mat_per,
            labor_cost_per_hour=lab_hr,
            equipment_cost_per_hour=equ_hr,
            sort_order=i
        ))
        db.session.add(LineItem(
            assembly_id=assembly.id,
            description=comp['description'],
            quantity=qty, unit=comp.get('unit', ''),
            production_rate=prod_r,
            material_cost_per_unit=mat_per, material_cost=mat_cost,
            labor_hours=lab_hrs, labor_cost_per_hour=lab_hr, labor_cost=lab_cost,
            equipment_hours=equ_hrs, equipment_cost_per_hour=equ_hr, equipment_cost=equ_cost,
            total_cost=total
        ))

    db.session.commit()
    return jsonify({'success': True, 'assembly_id': assembly.id})

# ─────────────────────────────────────────
# TEMPLATE ROUTES
# ─────────────────────────────────────────

@app.route('/templates')
def templates_browse():
    templates = Assembly.query.filter_by(is_template=True).order_by(Assembly.assembly_name).all()
    projects = Project.query.order_by(Project.project_name).all()
    csi1_map = {d.id: d for d in CSILevel1.query.all()}

    templates_data = []
    for t in templates:
        params = {}
        if t.measurement_params:
            try:
                params = json.loads(t.measurement_params)
            except (ValueError, TypeError):
                pass
        total_cost = sum(float(item.total_cost or 0) for item in t.line_items)
        csi1 = csi1_map.get(t.csi_level_1_id)
        templates_data.append({
            'id':          t.id,
            'label':       t.assembly_label,
            'name':        t.assembly_name,
            'description': t.description or '',
            'csi_code':    csi1.code if csi1 else '',
            'csi_title':   csi1.title if csi1 else '',
            'item_count':  len(t.line_items),
            'total_cost':  total_cost,
            'lf':     float(params.get('lf', 0)),
            'height': float(params.get('height', 0)),
            'depth':  float(params.get('depth', 0)),
            'width':  float(params.get('width', 0)),
            'composition': [{'description': c.description, 'unit': c.unit or '',
                             'formula': c.qty_formula} for c in t.composition],
        })

    projects_data = [{'id': p.id, 'name': p.project_name, 'number': p.project_number or ''}
                     for p in projects]
    return render_template('templates.html',
                           templates_data=templates_data,
                           projects_data=projects_data,
                           template_count=len(templates))


@app.route('/project/<int:project_id>/assembly/load-template/<int:template_id>', methods=['POST'])
def load_template(project_id, template_id):
    tmpl = Assembly.query.filter_by(id=template_id, is_template=True).first_or_404()
    new_label = request.form.get('assembly_label', tmpl.assembly_label)

    new_asm = Assembly(
        project_id=project_id,
        assembly_label=new_label,
        assembly_name=tmpl.assembly_name,
        description=tmpl.description,
        csi_level_1_id=tmpl.csi_level_1_id,
        csi_level_2_id=tmpl.csi_level_2_id,
        quantity=tmpl.quantity,
        unit=tmpl.unit,
        is_template=False,
        measurement_params=tmpl.measurement_params,
    )
    db.session.add(new_asm)
    db.session.flush()

    for comp in tmpl.composition:
        db.session.add(AssemblyComposition(
            assembly_id=new_asm.id,
            library_item_id=comp.library_item_id,
            description=comp.description,
            unit=comp.unit,
            qty_formula=comp.qty_formula,
            qty_divisor=comp.qty_divisor,
            qty_manual=comp.qty_manual,
            production_rate=comp.production_rate,
            material_cost_per_unit=comp.material_cost_per_unit,
            labor_cost_per_hour=comp.labor_cost_per_hour,
            equipment_cost_per_hour=comp.equipment_cost_per_hour,
            sort_order=comp.sort_order,
        ))

    for item in tmpl.line_items:
        db.session.add(LineItem(
            assembly_id=new_asm.id,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
            production_rate=item.production_rate,
            material_cost_per_unit=item.material_cost_per_unit,
            material_cost=item.material_cost,
            labor_hours=item.labor_hours,
            labor_cost_per_hour=item.labor_cost_per_hour,
            labor_cost=item.labor_cost,
            equipment_hours=item.equipment_hours,
            equipment_cost_per_hour=item.equipment_cost_per_hour,
            equipment_cost=item.equipment_cost,
            total_cost=item.total_cost,
            trade=item.trade,
            notes=item.notes,
        ))

    db.session.commit()
    return jsonify({'success': True, 'project_id': project_id, 'assembly_id': new_asm.id})


# ─────────────────────────────────────────
# LIBRARY ROUTES
# ─────────────────────────────────────────

@app.route('/library')
def library():
    items = LibraryItem.query.order_by(LibraryItem.description).all()
    csi1_list = CSILevel1.query.order_by(CSILevel1.code).all()
    csi2_list = CSILevel2.query.order_by(CSILevel2.code).all()
    csi1_map = {d.id: d for d in csi1_list}
    csi2_map = {s.id: s for s in csi2_list}
    csi2_data = [{'id': s.id, 'parent': s.csi_level_1_id, 'code': s.code, 'title': s.title}
                 for s in csi2_list]
    items_data = [{'id': i.id, 'description': i.description,
                   'csi_level_1_id': i.csi_level_1_id, 'csi_level_2_id': i.csi_level_2_id,
                   'unit': i.unit or '', 'production_rate': float(i.production_rate or 0),
                   'production_unit': i.production_unit or '',
                   'material_cost_per_unit': float(i.material_cost_per_unit or 0),
                   'labor_cost_per_hour': float(i.labor_cost_per_hour or 0),
                   'equipment_cost_per_hour': float(i.equipment_cost_per_hour or 0),
                   'notes': i.notes or ''} for i in items]
    return render_template('library.html', items=items, csi1_list=csi1_list,
                           csi2_json=json.dumps(csi2_data), csi1_map=csi1_map, csi2_map=csi2_map,
                           items_json=json.dumps(items_data))

@app.route('/library/item/new', methods=['POST'])
def new_library_item():
    item = LibraryItem(
        description=request.form['description'],
        csi_level_1_id=request.form.get('csi_level_1_id') or None,
        csi_level_2_id=request.form.get('csi_level_2_id') or None,
        unit=request.form.get('unit'),
        production_rate=request.form.get('production_rate') or None,
        production_unit=request.form.get('production_unit'),
        material_cost_per_unit=request.form.get('material_cost_per_unit') or None,
        labor_cost_per_hour=request.form.get('labor_cost_per_hour') or None,
        equipment_cost_per_hour=request.form.get('equipment_cost_per_hour') or None,
        notes=request.form.get('notes')
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'item_id': item.id})

@app.route('/library/item/<int:item_id>/update', methods=['POST'])
def update_library_item(item_id):
    item = LibraryItem.query.get_or_404(item_id)
    item.description = request.form['description']
    item.csi_level_1_id = request.form.get('csi_level_1_id') or None
    item.csi_level_2_id = request.form.get('csi_level_2_id') or None
    item.unit = request.form.get('unit')
    item.production_rate = request.form.get('production_rate') or None
    item.production_unit = request.form.get('production_unit')
    item.material_cost_per_unit = request.form.get('material_cost_per_unit') or None
    item.labor_cost_per_hour = request.form.get('labor_cost_per_hour') or None
    item.equipment_cost_per_hour = request.form.get('equipment_cost_per_hour') or None
    item.notes = request.form.get('notes')
    item.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/library/item/<int:item_id>/delete', methods=['POST'])
def delete_library_item(item_id):
    item = LibraryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})

# ─────────────────────────────────────────
# EXPORT / REPORT ROUTES
# ─────────────────────────────────────────

CSI_COLORS = {
    '01': '#7b8cde', '02': '#de9b7b', '03': '#7bde9b', '04': '#de7b9b',
    '05': '#7bbdde', '06': '#c4de7b', '07': '#de7bbd', '08': '#7bdec4',
    '09': '#debd7b', '10': '#9b7bde', '11': '#7bde7b', '12': '#de9b9b',
    '13': '#7bcfde', '14': '#debf7b', '21': '#de7b7b', '22': '#7bb8de',
    '23': '#b87bde', '25': '#de7bde', '26': '#ffd070', '27': '#7bffd4',
    '28': '#ff8a7b', '31': '#a8e6cf', '32': '#dcedc1', '33': '#ffd3b6',
    '34': '#ffaaa5', '35': '#a29bfe',
}

@app.route('/project/<int:project_id>/estimate/csv')
def estimate_csv(project_id):
    project = Project.query.get_or_404(project_id)
    assemblies = Assembly.query.filter_by(project_id=project_id).order_by(Assembly.assembly_label).all()
    csi1_map = {d.id: d for d in CSILevel1.query.all()}
    csi2_map = {s.id: s for s in CSILevel2.query.all()}

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([
        'Assembly', 'Assembly Name', 'CSI Division', 'CSI Section',
        'Description', 'Trade', 'Qty', 'Unit', 'Prod Rate (units/hr)', 'Labor Hrs',
        'Mat $/Unit', 'Material $', 'Labor $/Hr', 'Labor $',
        'Equip $/Hr', 'Equipment $', 'Total $', 'Notes'
    ])
    for asm in assemblies:
        d1 = csi1_map.get(asm.csi_level_1_id)
        d2 = csi2_map.get(asm.csi_level_2_id)
        for item in asm.line_items:
            w.writerow([
                asm.assembly_label, asm.assembly_name,
                f"{d1.code} — {d1.title}" if d1 else '',
                f"{d2.code} — {d2.title}" if d2 else '',
                item.description, item.trade or '',
                float(item.quantity or 0), item.unit or '',
                float(item.production_rate or 0), float(item.labor_hours or 0),
                float(item.material_cost_per_unit or 0), float(item.material_cost or 0),
                float(item.labor_cost_per_hour or 0), float(item.labor_cost or 0),
                float(item.equipment_cost_per_hour or 0), float(item.equipment_cost or 0),
                float(item.total_cost or 0), item.notes or ''
            ])

    safe_name = re.sub(r'[^\w\s-]', '', project.project_name).strip().replace(' ', '_')
    pnum = re.sub(r'[^\w-]', '', project.project_number or 'estimate')
    filename = f"{safe_name}_{pnum}.csv"
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@app.route('/project/<int:project_id>/report/csi')
def csi_report(project_id):
    project = Project.query.get_or_404(project_id)
    assemblies = Assembly.query.filter_by(project_id=project_id).order_by(Assembly.assembly_label).all()
    csi1_map = {d.id: d for d in CSILevel1.query.order_by(CSILevel1.code).all()}
    csi2_map = {s.id: s for s in CSILevel2.query.order_by(CSILevel2.code).all()}

    def subtotal(rows):
        return {
            'labor_hours':    sum(float(r['item'].labor_hours or 0) for r in rows),
            'material_cost':  sum(float(r['item'].material_cost or 0) for r in rows),
            'labor_cost':     sum(float(r['item'].labor_cost or 0) for r in rows),
            'equipment_cost': sum(float(r['item'].equipment_cost or 0) for r in rows),
            'total_cost':     sum(float(r['item'].total_cost or 0) for r in rows),
        }

    div_data = {}
    uncategorized = []

    for asm in assemblies:
        for item in asm.line_items:
            row = {'item': item, 'asm_label': asm.assembly_label, 'asm_name': asm.assembly_name}
            csi1_id = asm.csi_level_1_id
            csi2_id = asm.csi_level_2_id
            if not csi1_id or csi1_id not in csi1_map:
                uncategorized.append(row)
                continue
            if csi1_id not in div_data:
                div_data[csi1_id] = {'div': csi1_map[csi1_id], 'secs': {}, 'unsec': []}
            if csi2_id and csi2_id in csi2_map:
                if csi2_id not in div_data[csi1_id]['secs']:
                    div_data[csi1_id]['secs'][csi2_id] = {'sec': csi2_map[csi2_id], 'rows': []}
                div_data[csi1_id]['secs'][csi2_id]['rows'].append(row)
            else:
                div_data[csi1_id]['unsec'].append(row)

    divisions_out = []
    all_rows = []
    for csi1_id in sorted(div_data, key=lambda k: div_data[k]['div'].code):
        d = div_data[csi1_id]
        sections_out = []
        div_rows = list(d['unsec'])
        if d['unsec']:
            sections_out.append({'sec': None, 'rows': d['unsec'], 'total': subtotal(d['unsec'])})
        for csi2_id in sorted(d['secs'], key=lambda k: d['secs'][k]['sec'].code):
            sd = d['secs'][csi2_id]
            sections_out.append({'sec': sd['sec'], 'rows': sd['rows'], 'total': subtotal(sd['rows'])})
            div_rows.extend(sd['rows'])
        div_total = subtotal(div_rows)
        all_rows.extend(div_rows)
        color = CSI_COLORS.get(d['div'].code[:2], '#888')
        divisions_out.append({'div': d['div'], 'sections': sections_out, 'total': div_total, 'color': color})

    all_rows.extend(uncategorized)
    grand_total = subtotal(all_rows)

    return render_template('csi_report.html', project=project,
                           divisions=divisions_out,
                           uncategorized=uncategorized,
                           uncategorized_total=subtotal(uncategorized),
                           grand_total=grand_total,
                           now=datetime.utcnow())


# ─────────────────────────────────────────
# AI / OLLAMA ROUTES
# ─────────────────────────────────────────

@app.route('/agent/suggest', methods=['POST'])
def agent_suggest():
    data = request.get_json()
    description   = data.get('description', '')
    unit          = data.get('unit', '')
    quantity      = data.get('quantity', 0)
    location      = data.get('location', 'Unknown location')
    csi_code      = data.get('csi_code', '')
    csi_title     = data.get('csi_title', '')
    current_mat   = data.get('current_mat', 0)
    current_labor = data.get('current_labor', 0)
    current_equip = data.get('current_equip', 0)
    prod_rate     = data.get('production_rate', 0)

    prompt = f"""You are a professional construction cost estimating assistant. Suggest realistic unit pricing for the following line item.

Line item: {description}
Unit of measure: {unit}
Quantity: {quantity}
CSI Division: {csi_code} {csi_title}
Project location: {location}
Current estimator values — Material: ${current_mat}/unit, Labor: ${current_labor}/hr, Equipment: ${current_equip}/hr, Production rate: {prod_rate} units/hr

Respond with ONLY a valid JSON object, no other text, no markdown fences:
{{
  "material_cost_per_unit": <number>,
  "labor_cost_per_hour": <number>,
  "equipment_cost_per_hour": <number>,
  "production_rate": <number>,
  "reasoning": "<2-3 sentences explaining your suggestions and key factors considered>"
}}"""

    try:
        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=json.dumps({'model': 'llama3.2', 'prompt': prompt, 'stream': False}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode('utf-8'))

        response_text = result.get('response', '').strip()

        # Strip markdown code fences if model wrapped the JSON
        fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
        if fence_match:
            response_text = fence_match.group(1).strip()

        suggestion = json.loads(response_text)
        # Ensure all numeric fields are floats
        for field in ('material_cost_per_unit', 'labor_cost_per_hour',
                      'equipment_cost_per_hour', 'production_rate'):
            suggestion[field] = float(suggestion.get(field, 0) or 0)

        return jsonify({'success': True, 'suggestion': suggestion})

    except urllib.error.URLError:
        return jsonify({'success': False,
                        'error': 'Ollama is not running. Start it with: ollama serve'})
    except (json.JSONDecodeError, ValueError):
        return jsonify({'success': False,
                        'error': 'Could not parse AI response. Try again.',
                        'raw': response_text if 'response_text' in dir() else ''})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ─────────────────────────────────────────
# RUN APP
# ─────────────────────────────────────────

def run_migrations():
    """Add new columns to existing tables without dropping data."""
    with app.app_context():
        for sql in [
            'ALTER TABLE assemblies ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT FALSE',
            'ALTER TABLE assemblies ADD COLUMN IF NOT EXISTS measurement_params TEXT',
            'ALTER TABLE line_items ADD COLUMN IF NOT EXISTS trade VARCHAR(100)',
        ]:
            try:
                db.session.execute(db.text(sql))
                db.session.commit()
            except Exception:
                db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    run_migrations()
    app.run(debug=True)