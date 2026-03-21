# app.py - Construction Estimating Tool
# pip install flask psycopg2-binary sqlalchemy flask-sqlalchemy flask-login

from flask import (Flask, render_template, request, jsonify, Response,
                   send_from_directory, redirect, url_for, abort, flash)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timezone, timedelta
from functools import wraps
import os
import json
import io
import csv
import re
import secrets
import anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:Builder@localhost:5432/estimator_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'logo')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-change-this-in-production-please')
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Mail config (SendGrid SMTP or any SMTP provider)
app.config['MAIL_SERVER']   = os.environ.get('MAIL_SERVER', 'smtp.sendgrid.net')
app.config['MAIL_PORT']     = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'apikey')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@zenbid.io')

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

csrf    = CSRFProtect(app)
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[], storage_uri='memory://')
mail    = Mail(app)

# ─────────────────────────────────────────
# DATABASE MODELS
# ─────────────────────────────────────────

class Company(db.Model):
    __tablename__ = 'companies'
    id           = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    users        = db.relationship('User', backref='company', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    company_id    = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    username      = db.Column(db.String(100), unique=True, nullable=False)
    email         = db.Column(db.String(255))
    password_hash = db.Column(db.String(255), nullable=False)
    role                = db.Column(db.String(20), default='estimator')  # admin | estimator | viewer
    reset_token         = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime)
    created_at          = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class CSILevel1(db.Model):
    __tablename__ = 'csi_level_1'
    id          = db.Column(db.Integer, primary_key=True)
    code        = db.Column(db.String(10), unique=True, nullable=False)
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    subcodes    = db.relationship('CSILevel2', backref='division', lazy=True)

class CSILevel2(db.Model):
    __tablename__ = 'csi_level_2'
    id              = db.Column(db.Integer, primary_key=True)
    csi_level_1_id  = db.Column(db.Integer, db.ForeignKey('csi_level_1.id'), nullable=False)
    code            = db.Column(db.String(20), unique=True, nullable=False)
    title           = db.Column(db.String(255), nullable=False)
    description     = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Project(db.Model):
    __tablename__ = 'projects'
    id               = db.Column(db.Integer, primary_key=True)
    company_id       = db.Column(db.Integer, db.ForeignKey('companies.id'))
    project_name     = db.Column(db.String(255), nullable=False)
    project_number   = db.Column(db.String(100))
    description      = db.Column(db.Text)
    location         = db.Column(db.String(255))  # kept for backward compat
    city             = db.Column(db.String(100))
    state            = db.Column(db.String(50))
    zip_code         = db.Column(db.String(20))
    project_type_id  = db.Column(db.Integer, db.ForeignKey('global_properties.id'))
    market_sector_id = db.Column(db.Integer, db.ForeignKey('global_properties.id'))
    created_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    assemblies       = db.relationship('Assembly', backref='project', lazy=True)

class Assembly(db.Model):
    __tablename__ = 'assemblies'
    id              = db.Column(db.Integer, primary_key=True)
    project_id      = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assembly_label  = db.Column(db.String(100), nullable=False)
    assembly_name   = db.Column(db.String(255), nullable=False)
    csi_level_1_id  = db.Column(db.Integer, db.ForeignKey('csi_level_1.id'))
    csi_level_2_id  = db.Column(db.Integer, db.ForeignKey('csi_level_2.id'))
    description     = db.Column(db.Text)
    quantity        = db.Column(db.Numeric(10, 2))
    unit            = db.Column(db.String(50))
    is_template     = db.Column(db.Boolean, default=False)
    measurement_params = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    line_items      = db.relationship('LineItem', backref='assembly', lazy=True)
    composition     = db.relationship('AssemblyComposition', backref='assembly', lazy=True,
                                      order_by='AssemblyComposition.sort_order')

class AssemblyComposition(db.Model):
    __tablename__ = 'assembly_composition'
    id                     = db.Column(db.Integer, primary_key=True)
    assembly_id            = db.Column(db.Integer, db.ForeignKey('assemblies.id'), nullable=False)
    library_item_id        = db.Column(db.Integer, db.ForeignKey('library_items.id'))
    description            = db.Column(db.String(255), nullable=False)
    unit                   = db.Column(db.String(50))
    qty_formula            = db.Column(db.String(50), default='fixed')
    qty_divisor            = db.Column(db.Numeric(10, 4), default=1)
    qty_manual             = db.Column(db.Numeric(10, 2), default=0)
    production_rate        = db.Column(db.Numeric(10, 2), default=1)
    material_cost_per_unit = db.Column(db.Numeric(10, 2))
    labor_cost_per_hour    = db.Column(db.Numeric(10, 2))
    equipment_cost_per_hour= db.Column(db.Numeric(10, 2))
    sort_order             = db.Column(db.Integer, default=0)

class LibraryItem(db.Model):
    __tablename__ = 'library_items'
    id                     = db.Column(db.Integer, primary_key=True)
    company_id             = db.Column(db.Integer, db.ForeignKey('companies.id'))
    description            = db.Column(db.String(255), nullable=False)
    csi_level_1_id         = db.Column(db.Integer, db.ForeignKey('csi_level_1.id'))
    csi_level_2_id         = db.Column(db.Integer, db.ForeignKey('csi_level_2.id'))
    unit                   = db.Column(db.String(50))
    production_rate        = db.Column(db.Numeric(10, 2))
    production_unit        = db.Column(db.String(50))
    item_type              = db.Column(db.String(20), default='labor_material')
    prod_base              = db.Column(db.Boolean, default=True)
    material_cost_per_unit = db.Column(db.Numeric(10, 2))
    labor_cost_per_hour    = db.Column(db.Numeric(10, 2))
    labor_cost_per_unit    = db.Column(db.Numeric(10, 2))
    equipment_cost_per_hour= db.Column(db.Numeric(10, 2))
    equipment_cost_per_unit= db.Column(db.Numeric(10, 2))
    notes                  = db.Column(db.Text)
    created_at             = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at             = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class LineItem(db.Model):
    __tablename__ = 'line_items'
    id                     = db.Column(db.Integer, primary_key=True)
    assembly_id            = db.Column(db.Integer, db.ForeignKey('assemblies.id'), nullable=True)
    project_id             = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    description            = db.Column(db.String(255), nullable=False)
    quantity               = db.Column(db.Numeric(10, 2), nullable=False)
    unit                   = db.Column(db.String(50), nullable=False)
    csi_level_1_id         = db.Column(db.Integer, db.ForeignKey('csi_level_1.id'))
    csi_level_2_id         = db.Column(db.Integer, db.ForeignKey('csi_level_2.id'))
    item_type              = db.Column(db.String(20), default='labor_material')
    prod_base              = db.Column(db.Boolean, default=True)
    production_rate        = db.Column(db.Numeric(10, 2))
    production_unit        = db.Column(db.String(50))
    material_cost_per_unit = db.Column(db.Numeric(10, 2))
    material_cost          = db.Column(db.Numeric(12, 2))
    labor_hours            = db.Column(db.Numeric(10, 2))
    labor_cost_per_hour    = db.Column(db.Numeric(10, 2))
    labor_cost_per_unit    = db.Column(db.Numeric(10, 2))
    labor_cost             = db.Column(db.Numeric(12, 2))
    equipment_hours        = db.Column(db.Numeric(10, 2))
    equipment_cost_per_hour= db.Column(db.Numeric(10, 2))
    equipment_cost_per_unit= db.Column(db.Numeric(10, 2))
    equipment_cost         = db.Column(db.Numeric(12, 2))
    total_cost             = db.Column(db.Numeric(12, 2))
    trade                  = db.Column(db.String(100))
    notes                  = db.Column(db.Text)
    created_at             = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at             = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class GlobalProperty(db.Model):
    __tablename__ = 'global_properties'
    id         = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    category   = db.Column(db.String(50), nullable=False)  # 'trade' | 'project_type' | 'market_sector'
    name       = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, default=0)

class CompanyProfile(db.Model):
    __tablename__ = 'company_profile'
    id           = db.Column(db.Integer, primary_key=True)
    company_id   = db.Column(db.Integer, db.ForeignKey('companies.id'))
    company_name = db.Column(db.String(255))
    address      = db.Column(db.String(255))
    city         = db.Column(db.String(100))
    state        = db.Column(db.String(50))
    zip_code     = db.Column(db.String(20))
    phone        = db.Column(db.String(50))
    email        = db.Column(db.String(255))
    logo_path    = db.Column(db.String(500))

class ProductionRateStandard(db.Model):
    __tablename__ = 'production_rate_standards'
    id             = db.Column(db.Integer, primary_key=True)
    trade          = db.Column(db.String(100))
    csi_level_1_id = db.Column(db.Integer, db.ForeignKey('csi_level_1.id'))
    csi_level_2_id = db.Column(db.Integer, db.ForeignKey('csi_level_2.id'))
    description    = db.Column(db.String(255), nullable=False)
    unit           = db.Column(db.String(50))
    min_rate       = db.Column(db.Numeric(10, 2))
    typical_rate   = db.Column(db.Numeric(10, 2))
    max_rate       = db.Column(db.Numeric(10, 2))
    source_notes   = db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class WaitlistEntry(db.Model):
    __tablename__ = 'waitlist_entries'
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(255), nullable=False, unique=True)
    name       = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class WaitlistSurvey(db.Model):
    __tablename__ = 'waitlist_surveys'
    id                = db.Column(db.Integer, primary_key=True)
    waitlist_entry_id = db.Column(db.Integer, db.ForeignKey('waitlist_entries.id'), nullable=False)
    responses         = db.Column(db.Text)   # comma-separated selected option keys
    created_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class WBSProperty(db.Model):
    __tablename__ = 'wbs_properties'
    id            = db.Column(db.Integer, primary_key=True)
    project_id    = db.Column(db.Integer, db.ForeignKey('projects.id'))
    property_type = db.Column(db.String(50), nullable=False)
    property_name = db.Column(db.String(100), nullable=False)
    is_template   = db.Column(db.Boolean, default=False)
    is_custom     = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    values        = db.relationship('WBSValue', backref='wbs_property', lazy=True,
                                    order_by='WBSValue.display_order',
                                    cascade='all, delete-orphan')

class WBSValue(db.Model):
    __tablename__ = 'wbs_values'
    id              = db.Column(db.Integer, primary_key=True)
    wbs_property_id = db.Column(db.Integer, db.ForeignKey('wbs_properties.id'), nullable=False)
    value_name      = db.Column(db.String(100), nullable=False)
    value_code      = db.Column(db.String(50))
    parent_id       = db.Column(db.Integer, db.ForeignKey('wbs_values.id'))
    display_order   = db.Column(db.Integer, default=0)
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class LineItemWBS(db.Model):
    __tablename__ = 'line_item_wbs'
    id              = db.Column(db.Integer, primary_key=True)
    line_item_id    = db.Column(db.Integer, db.ForeignKey('line_items.id'), nullable=False)
    wbs_property_id = db.Column(db.Integer, db.ForeignKey('wbs_properties.id'), nullable=False)
    wbs_value_id    = db.Column(db.Integer, db.ForeignKey('wbs_values.id'), nullable=False)
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__  = (db.UniqueConstraint('line_item_id', 'wbs_property_id',
                                           name='uq_lineitem_wbs_property'),)

# ─────────────────────────────────────────
# AUTH HELPERS & DECORATORS
# ─────────────────────────────────────────

def admin_required(f):
    """Restrict route to users with role='admin'."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated

def get_project_or_403(project_id):
    """Fetch project and abort 403 if it belongs to a different company."""
    project = Project.query.get_or_404(project_id)
    if project.company_id != current_user.company_id:
        abort(403)
    return project

def get_assembly_or_403(assembly_id):
    """Fetch assembly and abort 403 if its project belongs to a different company."""
    assembly = Assembly.query.get_or_404(assembly_id)
    project = Project.query.get_or_404(assembly.project_id)
    if project.company_id != current_user.company_id:
        abort(403)
    return assembly

def get_lineitem_or_403(item_id):
    """Fetch line item and abort 403 if it belongs to a different company."""
    item = LineItem.query.get_or_404(item_id)
    if item.assembly_id:
        assembly = Assembly.query.get_or_404(item.assembly_id)
        project  = Project.query.get_or_404(assembly.project_id)
    else:
        project = Project.query.get_or_404(item.project_id)
    if project.company_id != current_user.company_id:
        abort(403)
    return item

def get_library_item_or_403(item_id):
    item = LibraryItem.query.get_or_404(item_id)
    if item.company_id != current_user.company_id:
        abort(403)
    return item

# ─────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        # Look up by email first, fall back to username for legacy accounts
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User.query.filter_by(username=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        return render_template('login.html', error='Invalid email or password', email=email)
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Self-service account creation: creates a Company + User (role=admin) and logs in."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        company_name = (request.form.get('company_name') or '').strip()
        full_name    = (request.form.get('full_name') or '').strip()
        email        = (request.form.get('email') or '').strip().lower()
        password     = request.form.get('password') or ''
        if not all([company_name, full_name, email, password]):
            return render_template('signup.html', error='All fields are required')
        if len(password) < 8:
            return render_template('signup.html', error='Password must be at least 8 characters')
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', error='Email already registered')
        # Create company, then owner user
        company = Company(company_name=company_name)
        db.session.add(company)
        db.session.flush()          # get company.id before commit
        _seed_company_properties(company.id)
        user = User(
            company_id=company.id,
            username=full_name,     # use full name as display username
            email=email,
            role='admin',
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        flash('Account created! Welcome to Zenbid.', 'success')
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─────────────────────────────────────────
# ADMIN ROUTES
# ─────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    companies = Company.query.order_by(Company.company_name).all()
    all_users = User.query.order_by(User.company_id, User.username).all()
    return render_template('admin.html', companies=companies, all_users=all_users)

@app.route('/admin/company/new', methods=['POST'])
@login_required
@admin_required
def admin_new_company():
    data = request.get_json()
    name = (data.get('company_name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Company name required'})
    company = Company(company_name=name)
    db.session.add(company)
    db.session.flush()
    # Seed default global properties for the new company
    _seed_company_properties(company.id)
    db.session.commit()
    return jsonify({'success': True, 'id': company.id})

@app.route('/admin/user/new', methods=['POST'])
@login_required
@admin_required
def admin_new_user():
    data = request.get_json()
    username   = (data.get('username') or '').strip()
    email      = (data.get('email') or '').strip()
    password   = data.get('password') or ''
    role       = data.get('role', 'estimator')
    company_id = data.get('company_id')
    if not username or not password or not company_id:
        return jsonify({'success': False, 'error': 'username, password and company are required'})
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'Username already exists'})
    if not Company.query.get(company_id):
        return jsonify({'success': False, 'error': 'Invalid company'})
    user = User(username=username, email=email or None,
                company_id=int(company_id), role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'id': user.id})

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot delete yourself'})
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/user/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    if 'role' in data:
        user.role = data['role']
    if 'email' in data:
        user.email = data['email'] or None
    if data.get('new_password'):
        user.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'success': True})

# ─────────────────────────────────────────
# PROFILE ROUTE
# ─────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    error = None
    success = None
    if request.method == 'POST':
        current_pw  = request.form.get('current_password', '')
        new_pw      = request.form.get('new_password', '')
        confirm_pw  = request.form.get('confirm_password', '')
        if not current_user.check_password(current_pw):
            error = 'Current password is incorrect.'
        elif len(new_pw) < 6:
            error = 'New password must be at least 6 characters.'
        elif new_pw != confirm_pw:
            error = 'New passwords do not match.'
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            success = 'Password changed successfully.'
    return render_template('profile.html', user=current_user, error=error, success=success)

# ─────────────────────────────────────────
# MARKETING / PUBLIC ROUTES
# ─────────────────────────────────────────

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/features')
def features():
    return redirect('/#features')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        user  = User.query.filter_by(email=email).first()
        # Always show success to avoid email enumeration
        if user:
            token   = secrets.token_urlsafe(32)
            expires = datetime.now(timezone.utc) + timedelta(hours=2)
            user.reset_token         = token
            user.reset_token_expires = expires
            db.session.commit()
            reset_url = url_for('reset_password', token=token, _external=True)
            try:
                msg = Message(
                    subject='Reset your Zenbid password',
                    recipients=[user.email],
                    body=(
                        f'Hi {user.username},\n\n'
                        f'Click the link below to reset your password. '
                        f'This link expires in 2 hours.\n\n'
                        f'{reset_url}\n\n'
                        f'If you did not request this, ignore this email.\n\n'
                        f'— The Zenbid Team'
                    )
                )
                mail.send(msg)
            except Exception:
                pass  # Don't leak mail errors; token is saved so admin can retrieve it
        return render_template('forgot_password.html', sent=True)
    return render_template('forgot_password.html', sent=False)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    now  = datetime.now(timezone.utc)
    # Normalise expires to UTC-aware for comparison
    expires = user.reset_token_expires if user else None
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if not user or not expires or now > expires:
        return render_template('reset_password.html', invalid=True)
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        if len(password) < 8:
            return render_template('reset_password.html', invalid=False,
                                   error='Password must be at least 8 characters.')
        if password != confirm:
            return render_template('reset_password.html', invalid=False,
                                   error='Passwords do not match.')
        user.set_password(password)
        user.reset_token         = None
        user.reset_token_expires = None
        db.session.commit()
        flash('Password updated. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', invalid=False)

# /app and /app/dashboard → redirect to main dashboard
@app.route('/app')
@app.route('/app/dashboard')
@login_required
def app_dashboard():
    return redirect(url_for('index'))

@app.route('/app/projects')
@login_required
def app_projects():
    return redirect(url_for('index'))

# Placeholder footer/nav links
@app.route('/about')
def about():
    return "About page — coming soon", 200

@app.route('/blog')
def blog():
    return "Blog — coming soon", 200

@app.route('/careers')
def careers():
    return "Careers — coming soon", 200

@app.route('/contact')
def contact():
    return "Contact — coming soon", 200

@app.route('/privacy')
def privacy():
    return "Privacy Policy — coming soon", 200

@app.route('/terms')
def terms():
    return "Terms of Service — coming soon", 200

@app.route('/security')
def security():
    return "Security — coming soon", 200

@app.route('/waitlist', methods=['GET', 'POST'])
def waitlist():
    success = False
    entry_id = None
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name  = request.form.get('name', '').strip()
        if not name:
            error = 'Please enter your first name.'
        elif not email or '@' not in email:
            error = 'Please enter a valid email address.'
        else:
            existing = WaitlistEntry.query.filter_by(email=email).first()
            if existing:
                error = "You're already on the waitlist — we'll be in touch!"
            else:
                entry = WaitlistEntry(email=email, name=name)
                db.session.add(entry)
                db.session.commit()
                try:
                    import requests as req
                    req.post("https://flows.zenbid.io/webhook/waitlist", json={"name": name, "email": email}, timeout=5)
                except Exception:
                    pass
                success = True
                entry_id = entry.id
    return render_template('waitlist.html', success=success, entry_id=entry_id, error=error)

@app.route('/waitlist/survey', methods=['POST'])
def waitlist_survey():
    data = request.get_json(silent=True) or {}
    entry_id  = data.get('entry_id')
    responses = data.get('responses', [])
    if not entry_id or not WaitlistEntry.query.get(entry_id):
        return jsonify({'ok': False}), 400
    survey = WaitlistSurvey(
        waitlist_entry_id=entry_id,
        responses=','.join(responses)
    )
    db.session.add(survey)
    db.session.commit()
    return jsonify({'ok': True})

# ─────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────

@app.route('/uploads/logo/<filename>')
def uploaded_logo(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ─────────────────────────────────────────
# SETTINGS / GLOBAL PROPERTIES
# ─────────────────────────────────────────

@app.route('/settings')
@login_required
def settings():
    company = CompanyProfile.query.filter_by(company_id=current_user.company_id).first()
    props = (GlobalProperty.query
             .filter_by(company_id=current_user.company_id)
             .order_by(GlobalProperty.category, GlobalProperty.sort_order, GlobalProperty.name)
             .all())
    props_json = json.dumps([{'id': p.id, 'category': p.category, 'name': p.name} for p in props])
    return render_template('settings.html', company=company, props_json=props_json)

@app.route('/settings/company/update', methods=['POST'])
@login_required
def update_company():
    company = CompanyProfile.query.filter_by(company_id=current_user.company_id).first()
    if not company:
        company = CompanyProfile(company_id=current_user.company_id)
        db.session.add(company)
    company.company_name = request.form.get('company_name', '')
    company.address      = request.form.get('address', '')
    company.city         = request.form.get('city', '')
    company.state        = request.form.get('state', '')
    company.zip_code     = request.form.get('zip_code', '')
    company.phone        = request.form.get('phone', '')
    company.email        = request.form.get('email', '')
    logo = request.files.get('logo')
    if logo and logo.filename:
        filename = secure_filename(logo.filename)
        logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        company.logo_path = filename
    db.session.commit()
    return jsonify({'success': True})

@app.route('/settings/property/new', methods=['POST'])
@login_required
def new_global_property():
    data = request.get_json()
    category = data.get('category', '').strip()
    name = data.get('name', '').strip()
    if not category or not name:
        return jsonify({'success': False, 'error': 'category and name required'})
    existing = GlobalProperty.query.filter_by(
        company_id=current_user.company_id, category=category, name=name).first()
    if existing:
        return jsonify({'success': True, 'id': existing.id, 'name': existing.name})
    prop = GlobalProperty(company_id=current_user.company_id, category=category, name=name)
    db.session.add(prop)
    db.session.commit()
    return jsonify({'success': True, 'id': prop.id, 'name': prop.name})

@app.route('/settings/property/<int:prop_id>/delete', methods=['POST'])
@login_required
def delete_global_property(prop_id):
    prop = GlobalProperty.query.get_or_404(prop_id)
    if prop.company_id != current_user.company_id:
        abort(403)
    db.session.delete(prop)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/settings/properties')
@login_required
def get_global_properties():
    props = (GlobalProperty.query
             .filter_by(company_id=current_user.company_id)
             .order_by(GlobalProperty.category, GlobalProperty.sort_order, GlobalProperty.name)
             .all())
    return jsonify([{'id': p.id, 'category': p.category, 'name': p.name} for p in props])

# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────

@app.route('/')
def landing():
    """Public landing page. Redirect authenticated users straight to the dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def index():
    cid = current_user.company_id
    projects = Project.query.filter_by(company_id=cid).order_by(Project.updated_at.desc()).all()
    total_value = (db.session.query(db.func.sum(LineItem.total_cost))
                   .join(Assembly, LineItem.assembly_id == Assembly.id)
                   .join(Project, Assembly.project_id == Project.id)
                   .filter(Project.company_id == cid)
                   .scalar() or 0)
    direct_value = (db.session.query(db.func.sum(LineItem.total_cost))
                    .join(Project, LineItem.project_id == Project.id)
                    .filter(Project.company_id == cid, LineItem.assembly_id == None)
                    .scalar() or 0)
    total_value = float(total_value) + float(direct_value)
    return render_template('app_dashboard.html',
                           projects=projects,
                           project_count=len(projects),
                           total_value=total_value)

# ─────────────────────────────────────────
# PROJECT ROUTES
# ─────────────────────────────────────────

@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        project = Project(
            company_id=current_user.company_id,
            project_name=request.form['project_name'],
            project_number=request.form.get('project_number', ''),
            description=request.form.get('description', ''),
            city=request.form.get('city', ''),
            state=request.form.get('state', ''),
            zip_code=request.form.get('zip_code', ''),
            project_type_id=request.form.get('project_type_id') or None,
            market_sector_id=request.form.get('market_sector_id') or None,
        )
        db.session.add(project)
        db.session.commit()
        _initialize_wbs(project.id)
        return jsonify({'success': True, 'project_id': project.id})
    props = (GlobalProperty.query
             .filter_by(company_id=current_user.company_id)
             .order_by(GlobalProperty.category, GlobalProperty.name).all())
    props_json = json.dumps([{'id': p.id, 'category': p.category, 'name': p.name} for p in props])
    return render_template('new_project.html', props_json=props_json)

@app.route('/project/<int:project_id>')
@login_required
def view_project(project_id):
    project = get_project_or_403(project_id)
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
    props = (GlobalProperty.query
             .filter_by(company_id=current_user.company_id)
             .order_by(GlobalProperty.category, GlobalProperty.name).all())
    props_json = json.dumps([{'id': p.id, 'category': p.category, 'name': p.name} for p in props])
    props_map = {p.id: p.name for p in props}
    return render_template('project.html', project=project, assemblies=assemblies,
                           csi1_list=csi1_list, csi2_json=json.dumps(csi2_data),
                           csi1_map=csi1_map, csi2_map=csi2_map,
                           assemblies_json=json.dumps(assemblies_data),
                           props_json=props_json,
                           project_type_name=props_map.get(project.project_type_id, ''),
                           market_sector_name=props_map.get(project.market_sector_id, ''))

@app.route('/project/<int:project_id>/assembly/new', methods=['POST'])
@login_required
def new_assembly(project_id):
    get_project_or_403(project_id)
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

def _make_line_item_from_form(form, assembly_id=None, project_id=None):
    prod_base_val = form.get('prod_base', 'true').lower() in ('true', '1', 'on', 'yes')
    item = LineItem(
        assembly_id=assembly_id,
        project_id=project_id,
        description=form['description'],
        quantity=float(form.get('quantity', 0) or 0),
        unit=form.get('unit', ''),
        item_type=form.get('item_type', 'labor_material'),
        prod_base=prod_base_val,
        production_rate=float(form.get('production_rate', 0) or 0) or None,
        material_cost_per_unit=float(form.get('material_cost_per_unit', 0) or 0),
        labor_cost_per_hour=float(form.get('labor_cost_per_hour', 0) or 0),
        labor_cost_per_unit=float(form.get('labor_cost_per_unit', 0) or 0),
        equipment_cost_per_unit=float(form.get('equipment_cost_per_unit', 0) or 0),
        trade=form.get('trade') or None,
        notes=form.get('notes') or None,
    )
    calculate_item_costs(item)
    return item

@app.route('/assembly/<int:assembly_id>/lineitem/new', methods=['POST'])
@login_required
def new_line_item(assembly_id):
    get_assembly_or_403(assembly_id)
    item = _make_line_item_from_form(request.form, assembly_id=assembly_id)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'line_item_id': item.id})

@app.route('/project/<int:project_id>/lineitem/new', methods=['POST'])
@login_required
def new_direct_line_item(project_id):
    get_project_or_403(project_id)
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data'}), 400
    prod_base_val = str(data.get('prod_base', '1')).lower() in ('true', '1', 'on', 'yes')
    csi1_id = int(data['csi_level_1_id']) if data.get('csi_level_1_id') else None
    csi2_id = int(data['csi_level_2_id']) if data.get('csi_level_2_id') else None
    item = LineItem(
        assembly_id=None,
        project_id=project_id,
        csi_level_1_id=csi1_id,
        csi_level_2_id=csi2_id,
        description=data.get('description', ''),
        quantity=float(data.get('quantity', 0) or 0),
        unit=data.get('unit', ''),
        item_type=data.get('item_type', 'labor_material'),
        prod_base=prod_base_val,
        production_rate=float(data.get('production_rate', 0) or 0) or None,
        material_cost_per_unit=float(data.get('material_cost_per_unit', 0) or 0),
        labor_cost_per_hour=float(data.get('labor_cost_per_hour', 0) or 0),
        labor_cost_per_unit=float(data.get('labor_cost_per_unit', 0) or 0),
        equipment_cost_per_unit=float(data.get('equipment_cost_per_unit', 0) or 0),
        trade=data.get('trade') or None,
        notes=data.get('notes') or None,
    )
    calculate_item_costs(item)
    db.session.add(item)
    db.session.commit()
    csi1_map = {d.id: d for d in CSILevel1.query.all()}
    csi2_map = {s.id: s for s in CSILevel2.query.all()}
    csi1 = csi1_map.get(csi1_id)
    csi2 = csi2_map.get(csi2_id)
    return jsonify({'success': True, 'item': {
        'id': item.id,
        'assembly_id': None,
        'assembly_label': '',
        'assembly_name': 'Direct Items',
        'csi_level_1_id': csi1_id, 'csi_level_1_code': csi1.code if csi1 else '', 'csi_level_1_title': csi1.title if csi1 else '',
        'csi_level_2_id': csi2_id, 'csi_level_2_code': csi2.code if csi2 else '', 'csi_level_2_title': csi2.title if csi2 else '',
        'description': item.description,
        'quantity': float(item.quantity or 0),
        'unit': item.unit or '',
        'item_type': item.item_type or 'labor_material',
        'prod_base': item.prod_base if item.prod_base is not None else True,
        'production_rate': float(item.production_rate or 0),
        'labor_hours': float(item.labor_hours or 0),
        'material_cost_per_unit': float(item.material_cost_per_unit or 0),
        'material_cost': float(item.material_cost or 0),
        'labor_cost_per_hour': float(item.labor_cost_per_hour or 0),
        'labor_cost_per_unit': float(item.labor_cost_per_unit or 0),
        'labor_cost': float(item.labor_cost or 0),
        'equipment_cost_per_unit': float(item.equipment_cost_per_unit or 0),
        'equipment_cost_per_hour': float(item.equipment_cost_per_hour or 0),
        'equipment_hours': float(item.equipment_hours or 0),
        'equipment_cost': float(item.equipment_cost or 0),
        'total_cost': float(item.total_cost or 0),
        'trade': item.trade or '',
        'notes': item.notes or '',
    }})

@app.route('/project/<int:project_id>/summary')
@login_required
def project_summary(project_id):
    project = get_project_or_403(project_id)
    summary = {
        'total_material_cost': 0, 'total_labor_cost': 0, 'total_labor_hours': 0,
        'total_equipment_cost': 0, 'total_equipment_hours': 0, 'total_cost': 0
    }
    for assembly in project.assemblies:
        for item in LineItem.query.filter_by(assembly_id=assembly.id).all():
            summary['total_material_cost']  += float(item.material_cost or 0)
            summary['total_labor_cost']     += float(item.labor_cost or 0)
            summary['total_labor_hours']    += float(item.labor_hours or 0)
            summary['total_equipment_cost'] += float(item.equipment_cost or 0)
            summary['total_equipment_hours']+= float(item.equipment_hours or 0)
            summary['total_cost']           += float(item.total_cost or 0)
    for item in LineItem.query.filter_by(project_id=project_id, assembly_id=None).all():
        summary['total_material_cost']  += float(item.material_cost or 0)
        summary['total_labor_cost']     += float(item.labor_cost or 0)
        summary['total_labor_hours']    += float(item.labor_hours or 0)
        summary['total_equipment_cost'] += float(item.equipment_cost or 0)
        summary['total_equipment_hours']+= float(item.equipment_hours or 0)
        summary['total_cost']           += float(item.total_cost or 0)
    return jsonify({'project': project.project_name, 'summary': summary})

@app.route('/project/<int:project_id>/report')
@login_required
def project_report(project_id):
    project = get_project_or_403(project_id)
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
            row['material_cost']   += float(item.material_cost or 0)
            row['labor_cost']      += float(item.labor_cost or 0)
            row['labor_hours']     += float(item.labor_hours or 0)
            row['equipment_cost']  += float(item.equipment_cost or 0)
            row['equipment_hours'] += float(item.equipment_hours or 0)
            row['total_cost']      += float(item.total_cost or 0)
        assembly_rows.append(row)
        for key in ('material_cost', 'labor_cost', 'labor_hours', 'equipment_cost', 'equipment_hours'):
            summary['total_' + key] += row[key]
        summary['total_cost'] += row['total_cost']
    return render_template('summary.html', project=project, summary=summary, assemblies=assembly_rows)

@app.route('/project/<int:project_id>/estimate')
@login_required
def estimate_view(project_id):
    project = get_project_or_403(project_id)
    assemblies = Assembly.query.filter_by(project_id=project_id).order_by(Assembly.assembly_label).all()
    csi1_map = {d.id: d for d in CSILevel1.query.all()}
    csi2_map = {s.id: s for s in CSILevel2.query.all()}

    def item_dict(item, asm=None):
        csi1_id = asm.csi_level_1_id if asm else item.csi_level_1_id
        csi2_id = asm.csi_level_2_id if asm else item.csi_level_2_id
        csi1 = csi1_map.get(csi1_id)
        csi2 = csi2_map.get(csi2_id)
        return {
            'id': item.id,
            'assembly_id': asm.id if asm else None,
            'assembly_label': asm.assembly_label if asm else '',
            'assembly_name': asm.assembly_name if asm else 'Direct Items',
            'csi_level_1_id': csi1_id,
            'csi_level_1_code': csi1.code if csi1 else '',
            'csi_level_1_title': csi1.title if csi1 else '',
            'csi_level_2_id': csi2_id,
            'csi_level_2_code': csi2.code if csi2 else '',
            'csi_level_2_title': csi2.title if csi2 else '',
            'description': item.description,
            'quantity': float(item.quantity or 0),
            'unit': item.unit or '',
            'item_type': item.item_type or 'labor_material',
            'prod_base': item.prod_base if item.prod_base is not None else True,
            'production_rate': float(item.production_rate or 0),
            'labor_hours': float(item.labor_hours or 0),
            'material_cost_per_unit': float(item.material_cost_per_unit or 0),
            'material_cost': float(item.material_cost or 0),
            'labor_cost_per_hour': float(item.labor_cost_per_hour or 0),
            'labor_cost_per_unit': float(item.labor_cost_per_unit or 0),
            'labor_cost': float(item.labor_cost or 0),
            'equipment_cost_per_unit': float(item.equipment_cost_per_unit or 0),
            'equipment_cost_per_hour': float(item.equipment_cost_per_hour or 0),
            'equipment_hours': float(item.equipment_hours or 0),
            'equipment_cost': float(item.equipment_cost or 0),
            'total_cost': float(item.total_cost or 0),
            'trade': item.trade or '',
            'notes': item.notes or '',
        }

    items = []
    for asm in assemblies:
        for item in asm.line_items:
            items.append(item_dict(item, asm))
    for item in LineItem.query.filter_by(project_id=project_id, assembly_id=None).all():
        items.append(item_dict(item, None))

    assemblies_data = [{'id': a.id, 'label': a.assembly_label, 'name': a.assembly_name} for a in assemblies]
    csi1_data = [{'id': d.id, 'code': d.code, 'title': d.title}
                 for d in CSILevel1.query.order_by(CSILevel1.code).all()]
    csi2_data = [{'id': s.id, 'parent': s.csi_level_1_id, 'code': s.code, 'title': s.title}
                 for s in CSILevel2.query.order_by(CSILevel2.code).all()]
    props = (GlobalProperty.query
             .filter_by(company_id=current_user.company_id)
             .order_by(GlobalProperty.category, GlobalProperty.name).all())
    props_json = json.dumps([{'id': p.id, 'category': p.category, 'name': p.name} for p in props])
    lib_items = LibraryItem.query.filter_by(company_id=current_user.company_id).order_by(LibraryItem.description).all()
    lib_data = [{'id': i.id, 'description': i.description,
                 'csi_level_1_id': i.csi_level_1_id,
                 'csi_level_2_id': i.csi_level_2_id,
                 'csi_level_1_code': csi1_map[i.csi_level_1_id].code if i.csi_level_1_id and i.csi_level_1_id in csi1_map else '',
                 'csi_level_2_code': csi2_map[i.csi_level_2_id].code if i.csi_level_2_id and i.csi_level_2_id in csi2_map else '',
                 'unit': i.unit or '',
                 'item_type': i.item_type or 'labor_material',
                 'prod_base': i.prod_base if i.prod_base is not None else True,
                 'production_rate': float(i.production_rate or 0),
                 'material_cost_per_unit': float(i.material_cost_per_unit or 0),
                 'labor_cost_per_hour': float(i.labor_cost_per_hour or 0),
                 'labor_cost_per_unit': float(i.labor_cost_per_unit or 0),
                 'equipment_cost_per_unit': float(i.equipment_cost_per_unit or 0),
                 'notes': i.notes or ''} for i in lib_items]

    return render_template('estimate.html',
                           project=project,
                           items_json=json.dumps(items),
                           assemblies_json=json.dumps(assemblies_data),
                           csi1_json=json.dumps(csi1_data),
                           csi2_json=json.dumps(csi2_data),
                           props_json=props_json,
                           library_json=json.dumps(lib_data))

@app.route('/assembly/<int:assembly_id>/update', methods=['POST'])
@login_required
def update_assembly(assembly_id):
    assembly = get_assembly_or_403(assembly_id)
    assembly.assembly_label = request.form['assembly_label']
    assembly.assembly_name  = request.form['assembly_name']
    assembly.csi_level_1_id = request.form.get('csi_level_1_id') or None
    assembly.csi_level_2_id = request.form.get('csi_level_2_id') or None
    assembly.description    = request.form.get('description')
    assembly.quantity       = request.form.get('quantity') or None
    assembly.unit           = request.form.get('unit')
    assembly.updated_at     = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/lineitem/<int:item_id>/update', methods=['POST'])
@login_required
def update_line_item(item_id):
    item = get_lineitem_or_403(item_id)
    data = request.get_json()
    str_fields = ('description', 'unit', 'trade', 'notes', 'item_type')
    for f in str_fields:
        if f in data: setattr(item, f, data[f] or None if f in ('trade', 'notes') else data[f])
    if 'prod_base' in data:
        item.prod_base = bool(data['prod_base'])
    if 'csi_level_1_id' in data:
        item.csi_level_1_id = int(data['csi_level_1_id']) if data['csi_level_1_id'] else None
    if 'csi_level_2_id' in data:
        item.csi_level_2_id = int(data['csi_level_2_id']) if data['csi_level_2_id'] else None
    num_fields = ('quantity', 'production_rate', 'material_cost_per_unit',
                  'labor_cost_per_hour', 'labor_cost_per_unit',
                  'equipment_cost_per_unit', 'equipment_cost_per_hour')
    for f in num_fields:
        if f in data:
            try: setattr(item, f, float(data[f]) if data[f] not in ('', None) else 0)
            except (ValueError, TypeError): pass
    calculate_item_costs(item)
    item.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({
        'success': True,
        'labor_hours':     float(item.labor_hours or 0),
        'material_cost':   float(item.material_cost or 0),
        'labor_cost':      float(item.labor_cost or 0),
        'equipment_hours': float(item.equipment_hours or 0),
        'equipment_cost':  float(item.equipment_cost or 0),
        'total_cost':      float(item.total_cost or 0),
    })

@app.route('/lineitem/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_line_item(item_id):
    item = get_lineitem_or_403(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/assembly/<int:assembly_id>/delete', methods=['POST'])
@login_required
def delete_assembly(assembly_id):
    assembly = get_assembly_or_403(assembly_id)
    LineItem.query.filter_by(assembly_id=assembly_id).delete()
    db.session.delete(assembly)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/project/<int:project_id>/update', methods=['POST'])
@login_required
def update_project(project_id):
    project = get_project_or_403(project_id)
    data = request.get_json()
    project.project_name     = data.get('project_name',     project.project_name)
    project.project_number   = data.get('project_number',   project.project_number)
    project.description      = data.get('description',      project.description)
    project.city             = data.get('city',             project.city)
    project.state            = data.get('state',            project.state)
    project.zip_code         = data.get('zip_code',         project.zip_code)
    project.project_type_id  = data.get('project_type_id',  project.project_type_id) or None
    project.market_sector_id = data.get('market_sector_id', project.market_sector_id) or None
    db.session.commit()
    return jsonify({'success': True})

@app.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = get_project_or_403(project_id)
    for asm in project.assemblies:
        LineItem.query.filter_by(assembly_id=asm.id).delete()
    LineItem.query.filter_by(project_id=project_id, assembly_id=None).delete()
    Assembly.query.filter_by(project_id=project_id).delete()
    db.session.delete(project)
    db.session.commit()
    return jsonify({'success': True})

# ─────────────────────────────────────────
# HELPER: ITEM COST CALCULATOR
# ─────────────────────────────────────────

def calculate_item_costs(item):
    qty       = float(item.quantity or 0)
    item_type = item.item_type or 'labor_material'
    prod_base = item.prod_base if item.prod_base is not None else True

    if item_type == 'equipment':
        item.labor_hours     = 0
        item.labor_cost      = 0
        item.equipment_hours = 0
        item.material_cost   = qty * float(item.material_cost_per_unit or 0)
        item.equipment_cost  = qty * float(item.equipment_cost_per_unit or 0)
    else:
        item.material_cost = qty * float(item.material_cost_per_unit or 0)
        if prod_base:
            rate = float(item.production_rate or 0)
            item.labor_hours = (qty / rate) if rate > 0 else 0
            item.labor_cost  = item.labor_hours * float(item.labor_cost_per_hour or 0)
        else:
            item.labor_hours = 0
            item.labor_cost  = qty * float(item.labor_cost_per_unit or 0)
        item.equipment_hours = 0
        item.equipment_cost  = 0

    item.total_cost = (float(item.material_cost or 0) +
                       float(item.labor_cost or 0) +
                       float(item.equipment_cost or 0))

# ─────────────────────────────────────────
# HELPER: QUANTITY FORMULA CALCULATOR
# ─────────────────────────────────────────

def calculate_qty(formula, params, divisor=1, manual_qty=0):
    lf     = float(params.get('lf', 0))
    height = float(params.get('height', 0))
    depth  = float(params.get('depth', 0))
    width  = float(params.get('width', 0))
    sf     = lf * height if height else 0
    div    = float(divisor) if float(divisor) > 0 else 1
    return {
        'fixed':     float(manual_qty),
        'lf':        lf,
        'lf_x_2':    lf * 2,
        'sf':        sf,
        'sf_div':    sf / div,
        'depth':     lf * depth,
        'volume_cy': (lf * (width or 1) * depth) / 27 if depth else 0,
    }.get(formula, float(manual_qty))

# ─────────────────────────────────────────
# ASSEMBLY BUILDER ROUTES
# ─────────────────────────────────────────

@app.route('/project/<int:project_id>/assembly/builder')
@login_required
def assembly_builder(project_id):
    project = get_project_or_403(project_id)
    csi1_list = CSILevel1.query.order_by(CSILevel1.code).all()
    csi1_map  = {d.id: d for d in csi1_list}
    library_items = LibraryItem.query.filter_by(company_id=current_user.company_id).order_by(LibraryItem.description).all()
    library_data = [{
        'id': i.id, 'description': i.description,
        'csi_level_1_id': i.csi_level_1_id,
        'csi_code':  csi1_map[i.csi_level_1_id].code  if i.csi_level_1_id and i.csi_level_1_id in csi1_map else '',
        'csi_title': csi1_map[i.csi_level_1_id].title if i.csi_level_1_id and i.csi_level_1_id in csi1_map else '',
        'unit': i.unit or '', 'production_rate': float(i.production_rate or 1),
        'material_cost_per_unit': float(i.material_cost_per_unit or 0),
        'labor_cost_per_hour':    float(i.labor_cost_per_hour or 0),
        'equipment_cost_per_hour':float(i.equipment_cost_per_hour or 0),
        'notes': i.notes or ''
    } for i in library_items]

    template_data = None
    from_template_id = request.args.get('from_template', type=int)
    if from_template_id:
        # Verify the template belongs to the same company
        tmpl = (Assembly.query
                .join(Project, Assembly.project_id == Project.id)
                .filter(Assembly.id == from_template_id,
                        Assembly.is_template == True,
                        Project.company_id == current_user.company_id)
                .first())
        if tmpl:
            params = {}
            if tmpl.measurement_params:
                try:
                    params = json.loads(tmpl.measurement_params)
                except (ValueError, TypeError):
                    pass
            template_data = {
                'label': tmpl.assembly_label,
                'name':  tmpl.assembly_name,
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
@login_required
def save_assembly_builder(project_id):
    get_project_or_403(project_id)
    params_str = request.form.get('measurement_params', '{}')
    comp_str   = request.form.get('composition', '[]')
    try:
        params     = json.loads(params_str)
        comp_items = json.loads(comp_str)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid JSON data'})

    lf       = float(params.get('lf', 0))
    height   = float(params.get('height', 0))
    sf       = lf * height if height else lf
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
    db.session.flush()

    for i, comp in enumerate(comp_items):
        formula    = comp.get('formula', 'fixed')
        divisor    = float(comp.get('divisor', 1)) or 1
        manual_qty = float(comp.get('manual_qty', 0))
        qty        = calculate_qty(formula, params, divisor, manual_qty)
        mat_per    = float(comp.get('mat_cost', 0))
        lab_hr     = float(comp.get('labor_rate', 0))
        equ_hr     = float(comp.get('equip_rate', 0))
        prod_r     = float(comp.get('production_rate', 1)) or 1
        lab_hrs    = qty / prod_r if prod_r > 0 else 0
        equ_hrs    = lab_hrs
        mat_cost   = qty * mat_per
        lab_cost   = lab_hrs * lab_hr
        equ_cost   = equ_hrs * equ_hr
        total      = mat_cost + lab_cost + equ_cost

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
@login_required
def templates_browse():
    cid = current_user.company_id
    templates = (Assembly.query
                 .join(Project, Assembly.project_id == Project.id)
                 .filter(Assembly.is_template == True,
                         Project.company_id == cid)
                 .order_by(Assembly.assembly_name).all())
    projects = Project.query.filter_by(company_id=cid).order_by(Project.project_name).all()
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
            'csi_code':    csi1.code  if csi1 else '',
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
@login_required
def load_template(project_id, template_id):
    get_project_or_403(project_id)
    cid = current_user.company_id
    # Verify the template belongs to the same company
    tmpl = (Assembly.query
            .join(Project, Assembly.project_id == Project.id)
            .filter(Assembly.id == template_id,
                    Assembly.is_template == True,
                    Project.company_id == cid)
            .first_or_404())
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
@login_required
def library():
    cid = current_user.company_id
    items = LibraryItem.query.filter_by(company_id=cid).order_by(LibraryItem.description).all()
    csi1_list = CSILevel1.query.order_by(CSILevel1.code).all()
    csi2_list = CSILevel2.query.order_by(CSILevel2.code).all()
    csi1_map  = {d.id: d for d in csi1_list}
    csi2_map  = {s.id: s for s in csi2_list}
    csi2_data = [{'id': s.id, 'parent': s.csi_level_1_id, 'code': s.code, 'title': s.title}
                 for s in csi2_list]
    items_data = [{'id': i.id, 'description': i.description,
                   'csi_level_1_id': i.csi_level_1_id, 'csi_level_2_id': i.csi_level_2_id,
                   'unit': i.unit or '', 'production_rate': float(i.production_rate or 0),
                   'production_unit': i.production_unit or '',
                   'item_type': i.item_type or 'labor_material',
                   'prod_base': i.prod_base if i.prod_base is not None else True,
                   'material_cost_per_unit': float(i.material_cost_per_unit or 0),
                   'labor_cost_per_hour': float(i.labor_cost_per_hour or 0),
                   'labor_cost_per_unit': float(i.labor_cost_per_unit or 0),
                   'equipment_cost_per_hour': float(i.equipment_cost_per_hour or 0),
                   'equipment_cost_per_unit': float(i.equipment_cost_per_unit or 0),
                   'notes': i.notes or ''} for i in items]
    props = (GlobalProperty.query
             .filter_by(company_id=cid, category='trade')
             .order_by(GlobalProperty.name).all())
    trades_json = json.dumps([{'id': p.id, 'name': p.name} for p in props])
    return render_template('library.html', items=items, csi1_list=csi1_list,
                           csi2_json=json.dumps(csi2_data), csi1_map=csi1_map, csi2_map=csi2_map,
                           items_json=json.dumps(items_data), trades_json=trades_json)

def _apply_library_item_form(item, form):
    prod_base_val = form.get('prod_base', 'true').lower() in ('true', '1', 'on', 'yes')
    item.description             = form['description']
    item.csi_level_1_id          = form.get('csi_level_1_id') or None
    item.csi_level_2_id          = form.get('csi_level_2_id') or None
    item.unit                    = form.get('unit')
    item.item_type               = form.get('item_type', 'labor_material')
    item.prod_base               = prod_base_val
    item.production_rate         = form.get('production_rate') or None
    item.production_unit         = form.get('production_unit')
    item.material_cost_per_unit  = form.get('material_cost_per_unit') or None
    item.labor_cost_per_hour     = form.get('labor_cost_per_hour') or None
    item.labor_cost_per_unit     = form.get('labor_cost_per_unit') or None
    item.equipment_cost_per_hour = form.get('equipment_cost_per_hour') or None
    item.equipment_cost_per_unit = form.get('equipment_cost_per_unit') or None
    item.notes                   = form.get('notes')

@app.route('/library/item/new', methods=['POST'])
@login_required
def new_library_item():
    item = LibraryItem(company_id=current_user.company_id)
    _apply_library_item_form(item, request.form)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'item_id': item.id,
                    'description': item.description, 'unit': item.unit or '',
                    'item_type': item.item_type, 'prod_base': item.prod_base,
                    'production_rate': float(item.production_rate or 0),
                    'material_cost_per_unit': float(item.material_cost_per_unit or 0),
                    'labor_cost_per_hour': float(item.labor_cost_per_hour or 0),
                    'labor_cost_per_unit': float(item.labor_cost_per_unit or 0),
                    'equipment_cost_per_unit': float(item.equipment_cost_per_unit or 0)})

@app.route('/library/item/<int:item_id>/update', methods=['POST'])
@login_required
def update_library_item(item_id):
    item = get_library_item_or_403(item_id)
    _apply_library_item_form(item, request.form)
    item.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/library/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_library_item(item_id):
    item = get_library_item_or_403(item_id)
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
@login_required
def estimate_csv(project_id):
    project   = get_project_or_403(project_id)
    assemblies = Assembly.query.filter_by(project_id=project_id).order_by(Assembly.assembly_label).all()
    csi1_map   = {d.id: d for d in CSILevel1.query.all()}
    csi2_map   = {s.id: s for s in CSILevel2.query.all()}
    out = io.StringIO()
    w   = csv.writer(out)
    w.writerow(['Assembly', 'Assembly Name', 'CSI Division', 'CSI Section',
                'Description', 'Trade', 'Qty', 'Unit', 'Prod Rate (units/hr)', 'Labor Hrs',
                'Mat $/Unit', 'Material $', 'Labor $/Hr', 'Labor $',
                'Equip $/Hr', 'Equipment $', 'Total $', 'Notes'])
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
    pnum      = re.sub(r'[^\w-]', '', project.project_number or 'estimate')
    filename  = f"{safe_name}_{pnum}.csv"
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})

@app.route('/project/<int:project_id>/report/csi')
@login_required
def csi_report(project_id):
    project    = get_project_or_403(project_id)
    assemblies = Assembly.query.filter_by(project_id=project_id).order_by(Assembly.assembly_label).all()
    csi1_map   = {d.id: d for d in CSILevel1.query.order_by(CSILevel1.code).all()}
    csi2_map   = {s.id: s for s in CSILevel2.query.order_by(CSILevel2.code).all()}

    def subtotal(rows):
        return {
            'labor_hours':    sum(float(r['item'].labor_hours or 0) for r in rows),
            'material_cost':  sum(float(r['item'].material_cost or 0) for r in rows),
            'labor_cost':     sum(float(r['item'].labor_cost or 0) for r in rows),
            'equipment_cost': sum(float(r['item'].equipment_cost or 0) for r in rows),
            'total_cost':     sum(float(r['item'].total_cost or 0) for r in rows),
        }

    div_data      = {}
    uncategorized = []

    for asm in assemblies:
        for item in asm.line_items:
            row    = {'item': item, 'asm_label': asm.assembly_label, 'asm_name': asm.assembly_name}
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
    all_rows      = []
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
        divisions_out.append({'div': d['div'], 'sections': sections_out,
                               'total': div_total, 'color': color})

    all_rows.extend(uncategorized)
    grand_total = subtotal(all_rows)

    return render_template('csi_report.html', project=project,
                           divisions=divisions_out,
                           uncategorized=uncategorized,
                           uncategorized_total=subtotal(uncategorized),
                           grand_total=grand_total,
                           now=datetime.now(timezone.utc))

# ─────────────────────────────────────────
# BID PROPOSAL
# ─────────────────────────────────────────

@app.route('/project/<int:project_id>/proposal')
@login_required
def project_proposal(project_id):
    project  = get_project_or_403(project_id)
    company  = CompanyProfile.query.filter_by(company_id=current_user.company_id).first()
    props_map = {p.id: p.name for p in GlobalProperty.query.filter_by(company_id=current_user.company_id).all()}

    raw_assemblies = Assembly.query.filter_by(project_id=project_id).all()
    summary = {
        'total_material_cost': 0, 'total_labor_cost': 0, 'total_labor_hours': 0,
        'total_equipment_cost': 0, 'total_cost': 0
    }
    assembly_rows = []
    for asm in raw_assemblies:
        row = {'assembly': asm, 'material_cost': 0, 'labor_cost': 0,
               'labor_hours': 0, 'equipment_cost': 0, 'total_cost': 0, 'item_count': 0}
        for item in asm.line_items:
            row['item_count']    += 1
            row['material_cost'] += float(item.material_cost or 0)
            row['labor_cost']    += float(item.labor_cost or 0)
            row['labor_hours']   += float(item.labor_hours or 0)
            row['equipment_cost']+= float(item.equipment_cost or 0)
            row['total_cost']    += float(item.total_cost or 0)
        assembly_rows.append(row)
        for k in ('material_cost', 'labor_cost', 'labor_hours', 'equipment_cost'):
            summary['total_' + k] += row[k]
        summary['total_cost'] += row['total_cost']

    for item in LineItem.query.filter_by(project_id=project_id, assembly_id=None).all():
        summary['total_material_cost']  += float(item.material_cost or 0)
        summary['total_labor_cost']     += float(item.labor_cost or 0)
        summary['total_labor_hours']    += float(item.labor_hours or 0)
        summary['total_equipment_cost'] += float(item.equipment_cost or 0)
        summary['total_cost']           += float(item.total_cost or 0)

    csi1_map   = {d.id: d for d in CSILevel1.query.order_by(CSILevel1.code).all()}
    div_totals = {}
    for asm in raw_assemblies:
        csi1_id = asm.csi_level_1_id
        for item in asm.line_items:
            if csi1_id and csi1_id in csi1_map:
                if csi1_id not in div_totals:
                    div_totals[csi1_id] = {'div': csi1_map[csi1_id],
                                           'material_cost': 0, 'labor_cost': 0,
                                           'equipment_cost': 0, 'total_cost': 0}
                div_totals[csi1_id]['material_cost']  += float(item.material_cost or 0)
                div_totals[csi1_id]['labor_cost']     += float(item.labor_cost or 0)
                div_totals[csi1_id]['equipment_cost'] += float(item.equipment_cost or 0)
                div_totals[csi1_id]['total_cost']     += float(item.total_cost or 0)
    for item in LineItem.query.filter_by(project_id=project_id, assembly_id=None).all():
        csi1_id = item.csi_level_1_id
        if csi1_id and csi1_id in csi1_map:
            if csi1_id not in div_totals:
                div_totals[csi1_id] = {'div': csi1_map[csi1_id],
                                       'material_cost': 0, 'labor_cost': 0,
                                       'equipment_cost': 0, 'total_cost': 0}
            div_totals[csi1_id]['material_cost']  += float(item.material_cost or 0)
            div_totals[csi1_id]['labor_cost']     += float(item.labor_cost or 0)
            div_totals[csi1_id]['equipment_cost'] += float(item.equipment_cost or 0)
            div_totals[csi1_id]['total_cost']     += float(item.total_cost or 0)

    csi_divisions = sorted(div_totals.values(), key=lambda d: d['div'].code)

    return render_template('proposal.html',
                           project=project, company=company,
                           project_type_name=props_map.get(project.project_type_id, ''),
                           market_sector_name=props_map.get(project.market_sector_id, ''),
                           summary=summary, assembly_rows=assembly_rows,
                           csi_divisions=csi_divisions,
                           now=datetime.now(timezone.utc))

# ─────────────────────────────────────────
# PRODUCTION RATE STANDARDS
# ─────────────────────────────────────────

@app.route('/production-rates')
@login_required
def production_rates():
    standards = ProductionRateStandard.query.order_by(
        ProductionRateStandard.trade, ProductionRateStandard.description).all()
    csi1_list = CSILevel1.query.order_by(CSILevel1.code).all()
    csi2_list = CSILevel2.query.order_by(CSILevel2.code).all()
    csi1_map  = {d.id: d for d in csi1_list}
    csi2_map  = {s.id: s for s in csi2_list}
    csi2_data = [{'id': s.id, 'parent': s.csi_level_1_id, 'code': s.code, 'title': s.title}
                 for s in csi2_list]
    standards_data = [{'id': s.id, 'description': s.description, 'trade': s.trade or '',
                        'csi_level_1_id': s.csi_level_1_id, 'csi_level_2_id': s.csi_level_2_id,
                        'unit': s.unit or '',
                        'min_rate': float(s.min_rate or 0),
                        'typical_rate': float(s.typical_rate or 0),
                        'max_rate': float(s.max_rate or 0),
                        'source_notes': s.source_notes or ''} for s in standards]
    trades = [p.name for p in GlobalProperty.query.filter_by(
        company_id=current_user.company_id, category='trade').order_by(GlobalProperty.name).all()]
    return render_template('production_rates.html',
                           standards=standards, csi1_list=csi1_list,
                           csi2_json=json.dumps(csi2_data), csi1_map=csi1_map, csi2_map=csi2_map,
                           standards_json=json.dumps(standards_data),
                           trades=trades)

@app.route('/production-rates/new', methods=['POST'])
@login_required
def new_production_rate():
    s = ProductionRateStandard(
        trade=request.form.get('trade') or None,
        csi_level_1_id=request.form.get('csi_level_1_id') or None,
        csi_level_2_id=request.form.get('csi_level_2_id') or None,
        description=request.form['description'],
        unit=request.form.get('unit'),
        min_rate=request.form.get('min_rate') or None,
        typical_rate=request.form.get('typical_rate') or None,
        max_rate=request.form.get('max_rate') or None,
        source_notes=request.form.get('source_notes'),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'success': True, 'id': s.id})

@app.route('/production-rate/<int:std_id>/update', methods=['POST'])
@login_required
def update_production_rate(std_id):
    s = ProductionRateStandard.query.get_or_404(std_id)
    s.trade          = request.form.get('trade') or None
    s.csi_level_1_id = request.form.get('csi_level_1_id') or None
    s.csi_level_2_id = request.form.get('csi_level_2_id') or None
    s.description    = request.form['description']
    s.unit           = request.form.get('unit')
    s.min_rate       = request.form.get('min_rate') or None
    s.typical_rate   = request.form.get('typical_rate') or None
    s.max_rate       = request.form.get('max_rate') or None
    s.source_notes   = request.form.get('source_notes')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/production-rate/<int:std_id>/delete', methods=['POST'])
@login_required
def delete_production_rate(std_id):
    s = ProductionRateStandard.query.get_or_404(std_id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/production-rates/search')
@login_required
def search_production_rates():
    q     = request.args.get('q', '').lower()
    trade = request.args.get('trade', '')
    csi1  = request.args.get('csi1', '')
    query = ProductionRateStandard.query
    if trade:
        query = query.filter_by(trade=trade)
    if csi1:
        query = query.filter_by(csi_level_1_id=int(csi1))
    standards = query.order_by(ProductionRateStandard.trade, ProductionRateStandard.description).all()
    results = []
    for s in standards:
        if not q or q in s.description.lower() or (s.trade and q in s.trade.lower()):
            results.append({
                'id': s.id, 'description': s.description, 'trade': s.trade or '',
                'unit': s.unit or '',
                'typical_rate': float(s.typical_rate or 0),
                'min_rate': float(s.min_rate or 0),
                'max_rate': float(s.max_rate or 0),
            })
    return jsonify(results)

# ─────────────────────────────────────────
# PROJECT DATA API
# ─────────────────────────────────────────

@app.route('/project/<int:project_id>/data', methods=['GET'])
@login_required
def project_data(project_id):
    project = get_project_or_403(project_id)

    csi1_map = {d.id: f"{d.code} {d.title}" for d in CSILevel1.query.all()}
    csi2_map = {s.id: f"{s.code} {s.title}" for s in CSILevel2.query.all()}
    props_map = {p.id: p.name for p in GlobalProperty.query.filter_by(
        company_id=current_user.company_id).all()}

    # Build WBS assignment lookup: {line_item_id: {property_type: {id, name, code}}}
    wbs_props = (WBSProperty.query.filter_by(project_id=project_id)
                 .order_by(WBSProperty.display_order).all())
    wbs_value_map = {}
    for prop in wbs_props:
        for v in prop.values:
            wbs_value_map[v.id] = {'name': v.value_name, 'code': v.value_code}
    wbs_prop_map = {p.id: p.property_type for p in wbs_props}

    raw_assignments = LineItemWBS.query.filter(
        LineItemWBS.wbs_property_id.in_([p.id for p in wbs_props])
    ).all() if wbs_props else []
    # {line_item_id: {property_type: {value_id, value_name, value_code}}}
    li_wbs_map = {}
    for a in raw_assignments:
        ptype = wbs_prop_map.get(a.wbs_property_id, '')
        vinfo = wbs_value_map.get(a.wbs_value_id, {})
        li_wbs_map.setdefault(a.line_item_id, {})[ptype] = {
            'wbs_property_id': a.wbs_property_id,
            'wbs_value_id':    a.wbs_value_id,
            'value_name':      vinfo.get('name', ''),
            'value_code':      vinfo.get('code', ''),
        }

    total_material = total_labor = total_equipment = total_hours = total_cost = 0.0

    assemblies_out = []
    for asm in Assembly.query.filter_by(project_id=project_id).order_by(Assembly.assembly_label).all():
        items_out = []
        for it in LineItem.query.filter_by(assembly_id=asm.id).all():
            mat = float(it.material_cost or 0)
            lab = float(it.labor_cost or 0)
            equ = float(it.equipment_cost or 0)
            hrs = float(it.labor_hours or 0)
            tot = float(it.total_cost or 0)
            total_material  += mat
            total_labor     += lab
            total_equipment += equ
            total_hours     += hrs
            total_cost      += tot
            items_out.append({
                'id':                     it.id,
                'assembly_id':            it.assembly_id,
                'description':            it.description,
                'quantity':               float(it.quantity or 0),
                'unit':                   it.unit,
                'item_type':              it.item_type,
                'prod_base':              it.prod_base,
                'production_rate':        float(it.production_rate or 0),
                'production_unit':        it.production_unit,
                'material_cost_per_unit': float(it.material_cost_per_unit or 0),
                'labor_cost_per_hour':    float(it.labor_cost_per_hour or 0),
                'labor_cost_per_unit':    float(it.labor_cost_per_unit or 0),
                'equipment_cost_per_hour':float(it.equipment_cost_per_hour or 0),
                'equipment_cost_per_unit':float(it.equipment_cost_per_unit or 0),
                'material_cost':          mat,
                'labor_cost':             lab,
                'labor_hours':            hrs,
                'equipment_cost':         equ,
                'total_cost':             tot,
                'trade':                  it.trade,
                'notes':                  it.notes,
                'csi_division':           csi1_map.get(asm.csi_level_1_id, ''),
                'csi_section':            csi2_map.get(asm.csi_level_2_id, ''),
                'wbs':                    li_wbs_map.get(it.id, {}),
            })
        assemblies_out.append({
            'id':             asm.id,
            'assembly_label': asm.assembly_label,
            'assembly_name':  asm.assembly_name,
            'description':    asm.description,
            'quantity':       float(asm.quantity or 0),
            'unit':           asm.unit,
            'csi_level_1_id': asm.csi_level_1_id,
            'csi_level_1':    csi1_map.get(asm.csi_level_1_id, ''),
            'csi_level_2_id': asm.csi_level_2_id,
            'csi_level_2':    csi2_map.get(asm.csi_level_2_id, ''),
            'line_items':     items_out,
        })

    # Direct line items (no assembly)
    direct_items_out = []
    for it in LineItem.query.filter_by(project_id=project_id, assembly_id=None).all():
        mat = float(it.material_cost or 0)
        lab = float(it.labor_cost or 0)
        equ = float(it.equipment_cost or 0)
        hrs = float(it.labor_hours or 0)
        tot = float(it.total_cost or 0)
        total_material  += mat
        total_labor     += lab
        total_equipment += equ
        total_hours     += hrs
        total_cost      += tot
        direct_items_out.append({
            'id':                     it.id,
            'assembly_id':            None,
            'description':            it.description,
            'quantity':               float(it.quantity or 0),
            'unit':                   it.unit,
            'item_type':              it.item_type,
            'prod_base':              it.prod_base,
            'production_rate':        float(it.production_rate or 0),
            'production_unit':        it.production_unit,
            'material_cost_per_unit': float(it.material_cost_per_unit or 0),
            'labor_cost_per_hour':    float(it.labor_cost_per_hour or 0),
            'labor_cost_per_unit':    float(it.labor_cost_per_unit or 0),
            'equipment_cost_per_hour':float(it.equipment_cost_per_hour or 0),
            'equipment_cost_per_unit':float(it.equipment_cost_per_unit or 0),
            'material_cost':          mat,
            'labor_cost':             lab,
            'labor_hours':            hrs,
            'equipment_cost':         equ,
            'total_cost':             tot,
            'trade':                  it.trade,
            'notes':                  it.notes,
            'csi_division':           '',
            'csi_section':            '',
            'wbs':                    li_wbs_map.get(it.id, {}),
        })

    return jsonify({
        'project': {
            'id':             project.id,
            'project_name':   project.project_name,
            'project_number': project.project_number,
            'city':           project.city,
            'state':          project.state,
            'zip_code':       project.zip_code,
            'description':    project.description,
            'project_type':   props_map.get(project.project_type_id, ''),
            'market_sector':  props_map.get(project.market_sector_id, ''),
        },
        'assemblies':    assemblies_out,
        'direct_items':  direct_items_out,
        'totals': {
            'total_material':  total_material,
            'total_labor':     total_labor,
            'total_equipment': total_equipment,
            'total_hours':     total_hours,
            'total_cost':      total_cost,
        },
    })


# ─────────────────────────────────────────
# WBS ROUTES
# ─────────────────────────────────────────

@app.route('/project/<int:project_id>/wbs/initialize', methods=['POST'])
@login_required
def wbs_initialize(project_id):
    get_project_or_403(project_id)
    if WBSProperty.query.filter_by(project_id=project_id).count() == 0:
        _initialize_wbs(project_id)
    else:
        # Backfill location_2 / location_3 for projects created before they were added
        _backfill_wbs_locations(project_id)
    return jsonify({'success': True})


@app.route('/project/<int:project_id>/wbs', methods=['GET'])
@login_required
def wbs_get(project_id):
    get_project_or_403(project_id)
    props = (WBSProperty.query
             .filter_by(project_id=project_id)
             .order_by(WBSProperty.display_order)
             .all())
    result = []
    for prop in props:
        result.append({
            'id':            prop.id,
            'property_type': prop.property_type,
            'property_name': prop.property_name,
            'is_template':   prop.is_template,
            'is_custom':     prop.is_custom,
            'display_order': prop.display_order,
            'values': [{
                'id':           v.id,
                'value_name':   v.value_name,
                'value_code':   v.value_code,
                'parent_id':    v.parent_id,
                'display_order': v.display_order,
            } for v in prop.values],
        })
    return jsonify({'success': True, 'properties': result})


@app.route('/project/<int:project_id>/wbs/property', methods=['POST'])
@login_required
def wbs_upsert_property(project_id):
    get_project_or_403(project_id)
    data = request.get_json() or {}
    prop_type = data.get('property_type', '').strip()
    prop_name = data.get('property_name', '').strip()
    if not prop_type or not prop_name:
        return jsonify({'success': False, 'error': 'property_type and property_name required'}), 400

    prop = WBSProperty.query.filter_by(project_id=project_id, property_type=prop_type).first()
    if prop:
        prop.property_name = prop_name
    else:
        max_order = db.session.query(db.func.max(WBSProperty.display_order)).filter_by(
            project_id=project_id).scalar() or 0
        prop = WBSProperty(
            project_id=project_id, property_type=prop_type, property_name=prop_name,
            is_custom=True, display_order=max_order + 1
        )
        db.session.add(prop)
    db.session.commit()
    return jsonify({'success': True, 'id': prop.id})


@app.route('/project/<int:project_id>/wbs/value', methods=['POST'])
@login_required
def wbs_add_value(project_id):
    get_project_or_403(project_id)
    data = request.get_json() or {}
    prop_id    = data.get('wbs_property_id')
    value_name = (data.get('value_name') or '').strip()
    value_code = (data.get('value_code') or '').strip() or None
    parent_id  = data.get('parent_id') or None

    if not prop_id or not value_name:
        return jsonify({'success': False, 'error': 'wbs_property_id and value_name required'}), 400

    prop = WBSProperty.query.get_or_404(prop_id)
    if prop.project_id != project_id:
        abort(403)

    max_order = db.session.query(db.func.max(WBSValue.display_order)).filter_by(
        wbs_property_id=prop_id).scalar() or 0
    val = WBSValue(
        wbs_property_id=prop_id, value_name=value_name,
        value_code=value_code, parent_id=parent_id, display_order=max_order + 1
    )
    db.session.add(val)
    db.session.commit()
    return jsonify({'success': True, 'id': val.id})


@app.route('/project/<int:project_id>/wbs/value/reorder', methods=['POST'])
@login_required
def wbs_reorder_values(project_id):
    get_project_or_403(project_id)
    data = request.get_json() or {}
    for item in data.get('orders', []):
        val = db.session.query(WBSValue).join(WBSProperty).filter(
            WBSValue.id == item['id'],
            WBSProperty.project_id == project_id
        ).first()
        if val:
            val.display_order = item['display_order']
    db.session.commit()
    return jsonify({'success': True})


@app.route('/project/<int:project_id>/wbs/value/<int:value_id>', methods=['PUT'])
@login_required
def wbs_update_value(project_id, value_id):
    get_project_or_403(project_id)
    val = db.session.query(WBSValue).join(WBSProperty).filter(
        WBSValue.id == value_id,
        WBSProperty.project_id == project_id
    ).first_or_404()
    data = request.get_json() or {}
    if 'value_name' in data:
        name = (data['value_name'] or '').strip()
        if name:
            val.value_name = name
    if 'value_code' in data:
        val.value_code = (data['value_code'] or '').strip() or None
    db.session.commit()
    return jsonify({'success': True})


@app.route('/project/<int:project_id>/wbs/value/<int:value_id>', methods=['DELETE'])
@login_required
def wbs_delete_value(project_id, value_id):
    get_project_or_403(project_id)
    val = WBSValue.query.get_or_404(value_id)
    prop = WBSProperty.query.get_or_404(val.wbs_property_id)
    if prop.project_id != project_id:
        abort(403)
    # Remove any line item assignments for this value before deleting
    LineItemWBS.query.filter_by(wbs_value_id=value_id).delete()
    db.session.delete(val)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/line-item/<int:item_id>/wbs', methods=['POST'])
@login_required
def assign_lineitem_wbs(item_id):
    get_lineitem_or_403(item_id)
    data = request.get_json() or {}
    prop_id  = data.get('wbs_property_id')
    value_id = data.get('wbs_value_id')
    if not prop_id or not value_id:
        return jsonify({'success': False, 'error': 'wbs_property_id and wbs_value_id required'}), 400

    # Upsert — one value per property per line item
    assignment = LineItemWBS.query.filter_by(
        line_item_id=item_id, wbs_property_id=prop_id).first()
    if assignment:
        assignment.wbs_value_id = value_id
    else:
        assignment = LineItemWBS(
            line_item_id=item_id, wbs_property_id=prop_id, wbs_value_id=value_id
        )
        db.session.add(assignment)
    db.session.commit()
    return jsonify({'success': True, 'id': assignment.id})


@app.route('/project/<int:project_id>/wbs/summary', methods=['GET'])
@login_required
def wbs_summary(project_id):
    get_project_or_403(project_id)

    # Fetch all line items for the project
    all_items = (LineItem.query
                 .outerjoin(Assembly, LineItem.assembly_id == Assembly.id)
                 .filter(
                     db.or_(
                         Assembly.project_id == project_id,
                         db.and_(LineItem.project_id == project_id, LineItem.assembly_id == None)
                     )
                 ).all())

    item_ids = [i.id for i in all_items]

    # Build wbs assignment lookup: {line_item_id: {prop_id: value_id}}
    assignments = LineItemWBS.query.filter(LineItemWBS.line_item_id.in_(item_ids)).all() if item_ids else []
    assign_map = {}
    for a in assignments:
        assign_map.setdefault(a.line_item_id, {})[a.wbs_property_id] = a.wbs_value_id

    # Load WBS properties + values for this project
    props = (WBSProperty.query
             .filter_by(project_id=project_id)
             .order_by(WBSProperty.display_order)
             .all())
    value_map = {}
    for prop in props:
        for v in prop.values:
            value_map[v.id] = {'name': v.value_name, 'code': v.value_code}

    def item_totals(it):
        return {
            'material_cost':  float(it.material_cost or 0),
            'labor_cost':     float(it.labor_cost or 0),
            'equipment_cost': float(it.equipment_cost or 0),
            'labor_hours':    float(it.labor_hours or 0),
            'total_cost':     float(it.total_cost or 0),
        }

    result = []
    for prop in props:
        groups = {}   # value_id (or None) -> {meta, items[], subtotals}
        for it in all_items:
            vid = assign_map.get(it.id, {}).get(prop.id)
            key = vid  # None = unassigned
            if key not in groups:
                label = value_map[vid]['name'] if vid and vid in value_map else '(Unassigned)'
                code  = value_map[vid]['code']  if vid and vid in value_map else None
                groups[key] = {
                    'value_id':   vid,
                    'value_name': label,
                    'value_code': code,
                    'items':      [],
                    'subtotals':  {'material_cost': 0, 'labor_cost': 0,
                                   'equipment_cost': 0, 'labor_hours': 0, 'total_cost': 0},
                }
            t = item_totals(it)
            groups[key]['items'].append({'id': it.id, 'description': it.description, **t})
            for k in groups[key]['subtotals']:
                groups[key]['subtotals'][k] += t[k]

        result.append({
            'property_id':   prop.id,
            'property_type': prop.property_type,
            'property_name': prop.property_name,
            'groups':        list(groups.values()),
        })

    return jsonify({'success': True, 'wbs_summary': result})


# ─────────────────────────────────────────
# AI / CLAUDE ROUTES
# ─────────────────────────────────────────

@app.route('/ai/chat', methods=['POST'])
@login_required
@limiter.limit('20 per minute')
def ai_chat():
    data       = request.get_json()
    message    = data.get('message', '').strip()
    project_id = data.get('project_id')
    mode       = data.get('mode', 'chat')   # estimate | research | chat

    if not message:
        return jsonify({'success': False, 'error': 'message is required'}), 400

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return jsonify({'success': False, 'error': 'ANTHROPIC_API_KEY not configured'}), 500

    # ── Build system prompt ──────────────────────────────────────────────
    if mode == 'estimate' and project_id:
        project = get_project_or_403(project_id)

        # Gather CSI lookup maps
        csi1_map = {d.id: f"{d.code} {d.title}" for d in CSILevel1.query.all()}
        csi2_map = {s.id: f"{s.code} {s.title}" for s in CSILevel2.query.all()}

        # Build assembly + line-item context
        assemblies = Assembly.query.filter_by(project_id=project_id).order_by(Assembly.assembly_label).all()
        asm_blocks = []
        total_material = total_labor = total_equipment = total_hours = total_cost = 0.0

        for asm in assemblies:
            items = LineItem.query.filter_by(assembly_id=asm.id).all()
            item_rows = []
            for it in items:
                mat  = float(it.material_cost or 0)
                lab  = float(it.labor_cost or 0)
                equ  = float(it.equipment_cost or 0)
                hrs  = float(it.labor_hours or 0)
                tot  = float(it.total_cost or 0)
                total_material  += mat
                total_labor     += lab
                total_equipment += equ
                total_hours     += hrs
                total_cost      += tot
                item_rows.append(
                    f"  - [{it.id}] {it.description} | {float(it.quantity or 0)} {it.unit} "
                    f"| type={it.item_type} prod_base={it.prod_base} "
                    f"rate={float(it.production_rate or 0)} | "
                    f"mat=${mat:.2f} lab=${lab:.2f} equ=${equ:.2f} hrs={hrs:.1f} total=${tot:.2f}"
                )
            asm_blocks.append(
                f"Assembly [id={asm.id}] {asm.assembly_label}: {asm.assembly_name} "
                f"[CSI: {csi1_map.get(asm.csi_level_1_id, 'none')} / {csi2_map.get(asm.csi_level_2_id, 'none')}]\n"
                + ("\n".join(item_rows) if item_rows else "  (no line items)")
            )

        # Direct line items (no assembly)
        direct_items = LineItem.query.filter_by(project_id=project_id, assembly_id=None).all()
        if direct_items:
            direct_rows = []
            for it in direct_items:
                mat  = float(it.material_cost or 0)
                lab  = float(it.labor_cost or 0)
                equ  = float(it.equipment_cost or 0)
                hrs  = float(it.labor_hours or 0)
                tot  = float(it.total_cost or 0)
                total_material  += mat
                total_labor     += lab
                total_equipment += equ
                total_hours     += hrs
                total_cost      += tot
                direct_rows.append(
                    f"  - [{it.id}] {it.description} | {float(it.quantity or 0)} {it.unit} "
                    f"| total=${tot:.2f}"
                )
            asm_blocks.append("Direct Line Items (no assembly):\n" + "\n".join(direct_rows))

        # Production rate standards (global reference)
        standards = (ProductionRateStandard.query
                     .order_by(ProductionRateStandard.trade, ProductionRateStandard.description)
                     .limit(60).all())
        rates_text = "\n".join(
            f"  {s.trade or 'General'} | {s.description} | {s.unit} | "
            f"min={float(s.min_rate or 0)} typ={float(s.typical_rate or 0)} max={float(s.max_rate or 0)}"
            for s in standards
        )

        props_map = {p.id: p.name for p in GlobalProperty.query.filter_by(
            company_id=current_user.company_id).all()}

        system_prompt = f"""You are an expert construction cost estimator embedded in a project estimating tool.

PROJECT CONTEXT
---------------
Name:        {project.project_name}
Number:      {project.project_number or 'N/A'}
Location:    {project.city or ''} {project.state or ''} {project.zip_code or ''}
Type:        {props_map.get(project.project_type_id, 'N/A')}
Sector:      {props_map.get(project.market_sector_id, 'N/A')}
Description: {project.description or 'N/A'}

LIVE TOTALS
-----------
Material:  ${total_material:,.2f}
Labor:     ${total_labor:,.2f}  ({total_hours:,.1f} hrs)
Equipment: ${total_equipment:,.2f}
TOTAL:     ${total_cost:,.2f}

ASSEMBLIES & LINE ITEMS
------------------------
{chr(10).join(asm_blocks) if asm_blocks else '(none)'}

PRODUCTION RATE STANDARDS (reference)
--------------------------------------
{rates_text}

INSTRUCTIONS
------------
Answer the estimator's questions with specific, actionable advice based on the project data above.
Always explain your proposed change in plain text first. When the user asks you to make a change,
append EXACTLY ONE fenced JSON block at the end of your response. Never propose more than one action
per response. Only include a JSON block when the user explicitly asked you to add, change, update,
or delete something.

ACTION SCHEMAS
--------------

ADD new line items (create a new assembly if needed):
```json
{{
  "action": "add_line_items",
  "assembly_id": null,
  "new_assembly": {{
    "assembly_label": "A###",
    "assembly_name": "Assembly Name",
    "quantity": 0,
    "unit": "LS",
    "description": ""
  }},
  "line_items": [
    {{
      "description": "",
      "quantity": 0,
      "unit": "SF",
      "production_rate": 0,
      "production_unit": "SF/HR",
      "material_cost_per_unit": 0,
      "labor_cost_per_hour": 0,
      "equipment_cost_per_hour": 0,
      "notes": ""
    }}
  ]
}}
```

UPDATE a single line item (include only the fields being changed in "updates"):
```json
{{
  "action": "update_line_item",
  "line_item_id": 123,
  "updates": {{"labor_cost_per_hour": 85, "quantity": 6500}},
  "description": "plain English summary of what is being changed"
}}
```

UPDATE an assembly record (include only the fields being changed in "updates"):
```json
{{
  "action": "update_assembly",
  "assembly_id": 456,
  "updates": {{"quantity": 6500, "assembly_name": "New Name"}},
  "description": "plain English summary of what is being changed"
}}
```

DELETE a line item permanently:
```json
{{
  "action": "delete_line_item",
  "line_item_id": 123,
  "item_name": "name of item being deleted"
}}
```

BULK UPDATE multiple line items at once (useful for recalculate-all operations):
```json
{{
  "action": "bulk_update",
  "line_items": [
    {{"id": 1, "updates": {{"labor_cost_per_hour": 85}}}},
    {{"id": 2, "updates": {{"labor_cost_per_hour": 85}}}}
  ],
  "description": "plain English summary of the bulk change"
}}
```
"""

    elif mode == 'research':
        system_prompt = """You are a senior construction cost estimator with 20+ years of experience across commercial, residential, and civil projects. You have deep knowledge of CSI MasterFormat, RS Means pricing, labor productivity, material markets, and regional cost factors. Answer questions thoroughly and cite specific figures, ranges, and caveats where relevant."""

    else:  # chat / fallback
        system_prompt = """You are a knowledgeable construction industry assistant embedded in a project estimating tool. You help estimators with questions about materials, methods, costs, codes, and project management. Be concise and practical."""

    # ── Call Claude API ──────────────────────────────────────────────────
    try:
        client   = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=2048,
            system=system_prompt,
            messages=[{'role': 'user', 'content': message}],
        )
        reply_text = response.content[0].text
    except anthropic.AuthenticationError:
        return jsonify({'success': False, 'error': 'Invalid ANTHROPIC_API_KEY'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    # ── Extract write proposal if present ───────────────────────────────
    write_proposal = None
    fence_match = re.search(r'```json\s*([\s\S]*?)```', reply_text)
    if fence_match:
        try:
            write_proposal = json.loads(fence_match.group(1).strip())
            # Strip the proposal block from the displayed reply
            reply_text = reply_text[:fence_match.start()].rstrip()
        except (json.JSONDecodeError, ValueError):
            write_proposal = None

    return jsonify({'success': True, 'reply': reply_text,
                    'write_proposal': write_proposal, 'mode': mode})


@app.route('/ai/apply', methods=['POST'])
@login_required
def ai_apply():
    data       = request.get_json()
    proposal   = data.get('proposal', {})
    project_id = data.get('project_id')

    if not project_id or not proposal:
        return jsonify({'success': False, 'error': 'proposal and project_id are required'}), 400

    get_project_or_403(project_id)

    action = proposal.get('action', 'add_line_items')

    # ── update_line_item ─────────────────────────────────────────────────
    if action == 'update_line_item':
        item = get_lineitem_or_403(proposal.get('line_item_id'))
        updates = proposal.get('updates', {})
        allowed = {
            'description', 'quantity', 'unit', 'item_type', 'prod_base',
            'production_rate', 'production_unit', 'trade', 'notes',
            'material_cost_per_unit', 'labor_cost_per_hour',
            'labor_cost_per_unit', 'equipment_cost_per_hour',
            'equipment_cost_per_unit',
        }
        for field, value in updates.items():
            if field in allowed:
                setattr(item, field, value)
        calculate_item_costs(item)
        db.session.commit()
        return jsonify({'success': True, 'line_item_id': item.id})

    # ── update_assembly ──────────────────────────────────────────────────
    if action == 'update_assembly':
        assembly = get_assembly_or_403(proposal.get('assembly_id'))
        updates = proposal.get('updates', {})
        allowed = {
            'assembly_label', 'assembly_name', 'description',
            'quantity', 'unit', 'csi_level_1_id', 'csi_level_2_id',
        }
        for field, value in updates.items():
            if field in allowed:
                setattr(assembly, field, value)
        db.session.commit()
        return jsonify({'success': True, 'assembly_id': assembly.id})

    # ── delete_line_item ─────────────────────────────────────────────────
    if action == 'delete_line_item':
        item = get_lineitem_or_403(proposal.get('line_item_id'))
        item_id = item.id
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True, 'deleted_line_item_id': item_id})

    # ── bulk_update ──────────────────────────────────────────────────────
    if action == 'bulk_update':
        allowed = {
            'description', 'quantity', 'unit', 'item_type', 'prod_base',
            'production_rate', 'production_unit', 'trade', 'notes',
            'material_cost_per_unit', 'labor_cost_per_hour',
            'labor_cost_per_unit', 'equipment_cost_per_hour',
            'equipment_cost_per_unit',
        }
        updated_ids = []
        for entry in proposal.get('line_items', []):
            item = get_lineitem_or_403(entry.get('id'))
            for field, value in entry.get('updates', {}).items():
                if field in allowed:
                    setattr(item, field, value)
            calculate_item_costs(item)
            updated_ids.append(item.id)
        db.session.commit()
        return jsonify({'success': True, 'updated_ids': updated_ids})

    # ── add_line_items (default) ─────────────────────────────────────────
    assembly_id = proposal.get('assembly_id') or proposal.get('target_assembly_id')

    # If Claude returned a label (e.g. "A200") instead of a numeric ID, look it up
    if assembly_id and not str(assembly_id).lstrip('-').isdigit():
        matched = Assembly.query.filter_by(
            project_id=project_id,
            assembly_label=str(assembly_id)
        ).first()
        assembly_id = matched.id if matched else None

    if proposal.get('new_assembly'):
        na = proposal['new_assembly']
        assembly = Assembly(
            project_id=project_id,
            assembly_label=na.get('assembly_label') or na.get('label', 'AI'),
            assembly_name=na.get('assembly_name') or na.get('name', 'AI-Generated Assembly'),
            csi_level_1_id=na.get('csi_level_1_id') or None,
            csi_level_2_id=na.get('csi_level_2_id') or None,
            description=na.get('description') or None,
            quantity=na.get('quantity', 1) or 1,
            unit=na.get('unit', 'LS'),
        )
        db.session.add(assembly)
        db.session.flush()
        assembly_id = assembly.id
    elif assembly_id:
        get_assembly_or_403(assembly_id)

    if not assembly_id:
        return jsonify({'success': False, 'error': 'No assembly target specified'}), 400

    inserted = 0
    for li_data in proposal.get('line_items', []):
        prod_base = li_data.get('prod_base', True)
        if isinstance(prod_base, str):
            prod_base = prod_base.lower() not in ('false', '0', 'no')

        item = LineItem(
            assembly_id=assembly_id,
            project_id=project_id,
            description=li_data.get('description', 'AI-generated item'),
            quantity=float(li_data.get('quantity', 0) or 0),
            unit=li_data.get('unit', 'LS'),
            item_type=li_data.get('item_type', 'labor_material'),
            prod_base=prod_base,
            production_rate=float(li_data.get('production_rate', 0) or 0) or None,
            production_unit=li_data.get('production_unit') or None,
            material_cost_per_unit=float(li_data.get('material_cost_per_unit', 0) or 0),
            labor_cost_per_hour=float(li_data.get('labor_cost_per_hour', 0) or 0),
            labor_cost_per_unit=float(li_data.get('labor_cost_per_unit', 0) or 0),
            equipment_cost_per_hour=float(li_data.get('equipment_cost_per_hour', 0) or 0),
            equipment_cost_per_unit=float(li_data.get('equipment_cost_per_unit', 0) or 0),
            trade=li_data.get('trade') or None,
            notes=li_data.get('notes') or None,
        )
        calculate_item_costs(item)
        db.session.add(item)
        inserted += 1

    db.session.commit()
    return jsonify({'success': True, 'assembly_id': assembly_id, 'items_inserted': inserted})


@app.route('/ai/build-assembly', methods=['POST'])
@limiter.limit('20 per minute')
@login_required
def ai_build_assembly():
    data        = request.get_json()
    project_id  = data.get('project_id')
    description = (data.get('description') or '').strip()

    if not project_id or not description:
        return jsonify({'success': False, 'error': 'project_id and description are required'}), 400

    project = get_project_or_403(project_id)

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return jsonify({'success': False, 'error': 'ANTHROPIC_API_KEY not configured'}), 500

    # ── Gather context ────────────────────────────────────────────────────
    props_map  = {p.id: p.name for p in GlobalProperty.query.filter_by(
        company_id=current_user.company_id).all()}

    existing_labels = [
        a.assembly_label for a in
        Assembly.query.filter_by(project_id=project_id)
                      .order_by(Assembly.assembly_label).all()
    ]
    assembly_count  = len(existing_labels)
    next_number     = (assembly_count + 1) * 100
    next_label      = f"A{next_number}"

    standards = (ProductionRateStandard.query
                 .order_by(ProductionRateStandard.trade, ProductionRateStandard.description)
                 .all())
    rates_text = "\n".join(
        f"  {s.trade or 'General'} | {s.description} | {s.unit} | "
        f"min={float(s.min_rate or 0)} typ={float(s.typical_rate or 0)} max={float(s.max_rate or 0)}"
        for s in standards
    ) or "  (none on file)"

    # ── System prompt ─────────────────────────────────────────────────────
    system_prompt = f"""You are an expert construction cost estimator with 20+ years of experience.
Your task is to build a fully-costed assembly for the described scope of work.

PROJECT CONTEXT
---------------
Name:     {project.project_name}
Number:   {project.project_number or 'N/A'}
Location: {project.city or ''} {project.state or ''} {project.zip_code or ''}
Type:     {props_map.get(project.project_type_id, 'N/A')}
Sector:   {props_map.get(project.market_sector_id, 'N/A')}

EXISTING ASSEMBLY LABELS (already used — do NOT reuse these)
------------------------------------------------------------
{', '.join(existing_labels) if existing_labels else '(none yet)'}
Next available label: {next_label}

PRODUCTION RATE STANDARDS (use these where applicable)
-------------------------------------------------------
{rates_text}

INSTRUCTIONS
------------
- Return ONLY valid JSON. No markdown, no explanations, no text outside the JSON object.
- Include EVERY line item needed to fully execute the described scope — do not omit any component.
- Use realistic production rates and costs appropriate for the project location and type.
- Do not leave any numeric field as zero unless it is genuinely zero for that item type.
- For concrete work include: formwork, reinforcement, placement, finishing, curing, and any related items.
- For each line item set production_rate > 0 whenever crew output can be measured in units/hour.
- Use the production rates from the database above where available; supplement with expert knowledge where not.
- Assign the next available assembly label shown above.
- Set item_type to "labor_material" for most items, "equipment" for equipment-only items.
- Set prod_base to true when production_rate applies (labor hours = qty / rate), false for lump labor costs.

REQUIRED JSON FORMAT (return exactly this structure, nothing else):
{{
  "assembly": {{
    "assembly_label": "{next_label}",
    "assembly_name": "descriptive name",
    "description": "brief scope description",
    "quantity": 0,
    "unit": "SF"
  }},
  "line_items": [
    {{
      "description": "item description",
      "quantity": 0,
      "unit": "SF",
      "item_type": "labor_material",
      "prod_base": true,
      "production_rate": 0,
      "production_unit": "SF/HR",
      "material_cost_per_unit": 0,
      "labor_cost_per_hour": 0,
      "labor_cost_per_unit": 0,
      "equipment_cost_per_hour": 0,
      "equipment_cost_per_unit": 0,
      "trade": "trade name",
      "notes": "any relevant notes"
    }}
  ],
  "estimator_notes": "summary of assumptions, regional pricing adjustments, items to review"
}}"""

    # ── Call Claude ───────────────────────────────────────────────────────
    try:
        client   = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=4096,
            system=system_prompt,
            messages=[{'role': 'user', 'content': description}],
        )
        raw_text = response.content[0].text.strip()
    except anthropic.AuthenticationError:
        return jsonify({'success': False, 'error': 'Invalid ANTHROPIC_API_KEY'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    # ── Parse JSON from Claude ────────────────────────────────────────────
    # Strip any accidental markdown fences
    json_text = raw_text
    fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_text)
    if fence:
        json_text = fence.group(1).strip()

    try:
        result = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({'success': False,
                        'error': f'Claude returned invalid JSON: {str(e)}',
                        'raw': raw_text}), 500

    asm_data   = result.get('assembly', {})
    items_data = result.get('line_items', [])

    # ── Calculate costs for each line item ────────────────────────────────
    total_material = total_labor = total_equipment = total_hours = 0.0
    computed_items = []

    for li in items_data:
        qty       = float(li.get('quantity', 0) or 0)
        item_type = li.get('item_type', 'labor_material')
        prod_base = li.get('prod_base', True)
        if isinstance(prod_base, str):
            prod_base = prod_base.lower() not in ('false', '0', 'no')

        mat_rate  = float(li.get('material_cost_per_unit', 0) or 0)
        lbr_hr    = float(li.get('labor_cost_per_hour', 0) or 0)
        lbr_unit  = float(li.get('labor_cost_per_unit', 0) or 0)
        equ_hr    = float(li.get('equipment_cost_per_hour', 0) or 0)
        equ_unit  = float(li.get('equipment_cost_per_unit', 0) or 0)
        rate      = float(li.get('production_rate', 0) or 0)

        if item_type == 'equipment':
            labor_hours    = 0.0
            labor_cost     = 0.0
            material_cost  = qty * mat_rate
            equipment_cost = qty * equ_unit
        else:
            material_cost = qty * mat_rate
            if prod_base:
                labor_hours = (qty / rate) if rate > 0 else 0.0
                labor_cost  = labor_hours * lbr_hr
            else:
                labor_hours = 0.0
                labor_cost  = qty * lbr_unit
            equipment_cost = 0.0

        total_cost = material_cost + labor_cost + equipment_cost

        total_material  += material_cost
        total_labor     += labor_cost
        total_equipment += equipment_cost
        total_hours     += labor_hours

        computed_items.append({
            'description':            li.get('description', ''),
            'quantity':               qty,
            'unit':                   li.get('unit', 'LS'),
            'item_type':              item_type,
            'prod_base':              prod_base,
            'production_rate':        rate,
            'production_unit':        li.get('production_unit') or '',
            'material_cost_per_unit': mat_rate,
            'labor_cost_per_hour':    lbr_hr,
            'labor_cost_per_unit':    lbr_unit,
            'equipment_cost_per_hour': equ_hr,
            'equipment_cost_per_unit': equ_unit,
            'trade':                  li.get('trade') or '',
            'notes':                  li.get('notes') or '',
            # Calculated
            'labor_hours':    round(labor_hours, 2),
            'material_cost':  round(material_cost, 2),
            'labor_cost':     round(labor_cost, 2),
            'equipment_cost': round(equipment_cost, 2),
            'total_cost':     round(total_cost, 2),
        })

    grand_total = total_material + total_labor + total_equipment

    return jsonify({
        'success': True,
        'assembly': {
            'assembly_label': asm_data.get('assembly_label', next_label),
            'assembly_name':  asm_data.get('assembly_name', 'AI-Generated Assembly'),
            'description':    asm_data.get('description', ''),
            'quantity':       float(asm_data.get('quantity', 0) or 0),
            'unit':           asm_data.get('unit', 'LS'),
        },
        'line_items': computed_items,
        'totals': {
            'total_material':  round(total_material, 2),
            'total_labor':     round(total_labor, 2),
            'total_equipment': round(total_equipment, 2),
            'total_hours':     round(total_hours, 2),
            'grand_total':     round(grand_total, 2),
        },
        'estimator_notes': result.get('estimator_notes', ''),
    })


@app.route('/ai/scope-gap', methods=['POST'])
@limiter.limit('10 per minute')
@login_required
def ai_scope_gap():
    data       = request.get_json()
    project_id = data.get('project_id')

    if not project_id:
        return jsonify({'success': False, 'error': 'project_id is required'}), 400

    project = get_project_or_403(project_id)

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        return jsonify({'success': False, 'error': 'ANTHROPIC_API_KEY not configured'}), 500

    # ── CSI lookup maps ────────────────────────────────────────────────────
    csi1_map = {d.id: f"{d.code} {d.title}" for d in CSILevel1.query.all()}
    csi2_map = {s.id: f"{s.code} {s.title}" for s in CSILevel2.query.all()}

    # ── Project type / sector ──────────────────────────────────────────────
    props_map = {p.id: p.name for p in GlobalProperty.query.filter_by(
        company_id=current_user.company_id).all()}

    # ── Gather assemblies + line items, compute totals ─────────────────────
    assemblies = Assembly.query.filter_by(project_id=project_id).order_by(Assembly.assembly_label).all()
    asm_blocks = []
    total_material = total_labor = total_equipment = total_hours = total_cost = 0.0
    csi_divisions_present = set()

    for asm in assemblies:
        if asm.csi_level_1_id:
            csi_divisions_present.add(csi1_map.get(asm.csi_level_1_id, str(asm.csi_level_1_id)))

        items = LineItem.query.filter_by(assembly_id=asm.id).all()
        item_rows = []
        for it in items:
            mat = float(it.material_cost or 0)
            lab = float(it.labor_cost or 0)
            equ = float(it.equipment_cost or 0)
            hrs = float(it.labor_hours or 0)
            tot = float(it.total_cost or 0)
            total_material  += mat
            total_labor     += lab
            total_equipment += equ
            total_hours     += hrs
            total_cost      += tot
            item_rows.append(
                f"    - {it.description} | {float(it.quantity or 0)} {it.unit} "
                f"| trade={it.trade or 'N/A'} | mat=${mat:.2f} lab=${lab:.2f} equ=${equ:.2f} total=${tot:.2f}"
            )

        asm_blocks.append(
            f"  [{asm.assembly_label}] {asm.assembly_name}"
            f" [CSI: {csi1_map.get(asm.csi_level_1_id, 'none')} / {csi2_map.get(asm.csi_level_2_id, 'none')}]\n"
            + ("\n".join(item_rows) if item_rows else "    (no line items)")
        )

    # Direct line items (no assembly)
    direct_items = LineItem.query.filter_by(project_id=project_id, assembly_id=None).all()
    if direct_items:
        direct_rows = []
        for it in direct_items:
            mat = float(it.material_cost or 0)
            lab = float(it.labor_cost or 0)
            equ = float(it.equipment_cost or 0)
            tot = float(it.total_cost or 0)
            total_material  += mat
            total_labor     += lab
            total_equipment += equ
            total_cost      += tot
            direct_rows.append(
                f"    - {it.description} | {float(it.quantity or 0)} {it.unit} | total=${tot:.2f}"
            )
        asm_blocks.append("  [Direct Line Items — no assembly]\n" + "\n".join(direct_rows))

    # ── Production rate standards ──────────────────────────────────────────
    standards = (ProductionRateStandard.query
                 .order_by(ProductionRateStandard.trade, ProductionRateStandard.description)
                 .limit(80).all())
    rates_text = "\n".join(
        f"  {s.trade or 'General'} | {s.description} | {s.unit}"
        for s in standards
    ) or "  (none on file)"

    estimate_text = "\n\n".join(asm_blocks) if asm_blocks else "  (no assemblies or line items)"
    divisions_list = "\n".join(f"  - {d}" for d in sorted(csi_divisions_present)) or "  (none)"

    # ── System prompt ──────────────────────────────────────────────────────
    system_prompt = f"""You are a senior construction cost estimator with 25 years of experience reviewing bids and estimates before submission. You are conducting a formal peer review of the estimate below, exactly as you would prepare it for a pre-bid scope review meeting.

Your job is to identify gaps, omissions, and missing scope — not to reprice items. Be specific. Reference actual assembly names and line item descriptions from the estimate when calling out gaps.

PROJECT DETAILS
---------------
Name:        {project.project_name}
Number:      {project.project_number or 'N/A'}
Location:    {project.city or ''} {project.state or ''} {project.zip_code or ''}
Type:        {props_map.get(project.project_type_id, 'N/A')}
Sector:      {props_map.get(project.market_sector_id, 'N/A')}
Description: {project.description or 'N/A'}

LIVE ESTIMATE TOTALS
--------------------
Total Material:  ${total_material:,.2f}
Total Labor:     ${total_labor:,.2f}
Total Equipment: ${total_equipment:,.2f}
Total Hours:     {total_hours:,.1f}
Grand Total:     ${total_cost:,.2f}

CSI DIVISIONS PRESENT IN ESTIMATE
----------------------------------
{divisions_list}

FULL ESTIMATE (assemblies and line items)
-----------------------------------------
{estimate_text}

PRODUCTION RATE STANDARDS ON FILE
----------------------------------
{rates_text}

REVIEW INSTRUCTIONS
-------------------
Analyze this estimate at three levels and identify every meaningful gap:

LEVEL 1 — MISSING LINE ITEMS
Items that should exist within the current assemblies but are absent.
Examples: concrete assembly with no curing compound, no formwork, no rebar; drywall assembly with no corner bead, no fasteners; painting scope with no primer.

LEVEL 2 — MISSING ASSEMBLIES
Entire scopes of work that are absent given what is already in the estimate and the project type.
Examples: structural steel present but no metal deck, no shear studs, no steel erection equipment; site work present but no erosion control, no temporary fencing.

LEVEL 3 — MISSING CSI DIVISIONS
Entire CSI divisions that would typically be required for this project type and sector but have zero representation in the estimate.
Examples: no Division 01 General Conditions, no Division 10 Specialties, no Division 26 Electrical allowance, no Division 22 Plumbing.

For each gap assign a severity:
HIGH   — likely to cause a significant cost miss if submitted as-is
MEDIUM — should be resolved before bid day
LOW    — minor item or optional scope, flag for estimator awareness

Also note regional considerations for {project.city or 'the project location'}, {project.state or ''} — permits, prevailing wage, specific trade requirements, or weather-related scope that may be missing.

RESPONSE FORMAT
---------------
Return ONLY valid JSON. No markdown, no explanation, no text outside the JSON object. Your entire response must be parseable by json.loads().

{{
  "summary": "2-3 sentence overall assessment of the estimate completeness and readiness for bid",
  "completeness_score": 85,
  "gaps": [
    {{
      "level": "MISSING_LINE_ITEM",
      "severity": "HIGH",
      "assembly_name": "name of the related assembly, or null if not assembly-specific",
      "title": "short descriptive title of the gap",
      "description": "specific description of what is missing and why it matters for this project",
      "suggested_action": "concrete action the estimator should take",
      "estimated_cost_impact": "rough cost impact if known (e.g. '$5,000–$15,000' or 'minor')"
    }}
  ],
  "strengths": [
    "2 to 4 specific things the estimate does well"
  ],
  "review_notes": "any additional observations the estimator should consider before submitting this bid"
}}

Level values must be one of: MISSING_LINE_ITEM, MISSING_ASSEMBLY, MISSING_CSI_DIVISION
Severity values must be one of: HIGH, MEDIUM, LOW"""

    # ── Call Claude ────────────────────────────────────────────────────────
    try:
        client   = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=4096,
            system=system_prompt,
            messages=[{'role': 'user', 'content': 'Please review this estimate for scope gaps and missing items.'}],
        )
        raw_text = response.content[0].text.strip()
    except anthropic.AuthenticationError:
        return jsonify({'success': False, 'error': 'Invalid ANTHROPIC_API_KEY'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    # ── Parse JSON from Claude ─────────────────────────────────────────────
    json_text = raw_text
    fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_text)
    if fence:
        json_text = fence.group(1).strip()

    try:
        result = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({'success': False,
                        'error': f'Claude returned invalid JSON: {str(e)}',
                        'raw': raw_text}), 500

    # ── Sort gaps: HIGH → MEDIUM → LOW ────────────────────────────────────
    severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    gaps = result.get('gaps', [])
    gaps.sort(key=lambda g: severity_order.get(g.get('severity', 'LOW'), 2))
    result['gaps'] = gaps

    return jsonify({'success': True, **result})


# ─────────────────────────────────────────
# AI PRODUCTION RATE ASSISTANT
# ─────────────────────────────────────────

def _build_rates_text(standards):
    """Format a list of ProductionRateStandard rows into a compact text block."""
    if not standards:
        return "  (no matching records in database)"
    lines = []
    for s in standards:
        lines.append(
            f"  [{s.trade or 'General'}] {s.description} | unit={s.unit} | "
            f"min={float(s.min_rate or 0):.2f} typ={float(s.typical_rate or 0):.2f} "
            f"max={float(s.max_rate or 0):.2f} units/hr"
            + (f" | notes: {s.source_notes}" if s.source_notes else "")
        )
    return "\n".join(lines)


@app.route('/ai/production-rate', methods=['POST'])
@limiter.limit('20 per minute')
@login_required
def ai_production_rate():
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        return jsonify({'success': False, 'error': 'ANTHROPIC_API_KEY not configured'}), 500

    data           = request.get_json() or {}
    query          = (data.get('query') or '').strip()
    project_id     = data.get('project_id')
    trade_filter   = (data.get('trade') or '').strip()
    csi1_filter    = data.get('csi_level_1_id')

    if not query:
        return jsonify({'success': False, 'error': 'query is required'}), 400

    # ── Fuzzy-search production_rate_standards ────────────────────────────
    std_q = ProductionRateStandard.query
    if trade_filter:
        std_q = std_q.filter(ProductionRateStandard.trade.ilike(f'%{trade_filter}%'))
    if csi1_filter:
        std_q = std_q.filter_by(csi_level_1_id=int(csi1_filter))

    # Pull up to 20 rows whose description or trade contains any word in the query
    words = [w for w in re.split(r'\s+', query) if len(w) > 2]
    if words:
        from sqlalchemy import or_
        conditions = []
        for w in words[:6]:            # cap to avoid giant OR chains
            conditions.append(ProductionRateStandard.description.ilike(f'%{w}%'))
            conditions.append(ProductionRateStandard.trade.ilike(f'%{w}%'))
        std_q = std_q.filter(or_(*conditions))

    standards = std_q.order_by(ProductionRateStandard.trade,
                                ProductionRateStandard.description).limit(20).all()

    # ── Project location context ──────────────────────────────────────────
    location_context = ""
    if project_id:
        project = Project.query.filter_by(
            id=project_id, company_id=current_user.company_id).first()
        if project and (project.city or project.state):
            location_context = f"{project.city or ''}, {project.state or ''}".strip(', ')

    # ── Company trades (for labor rate context) ───────────────────────────
    trades = GlobalProperty.query.filter_by(
        company_id=current_user.company_id, category='trade').order_by(
        GlobalProperty.sort_order).all()
    trades_text = ", ".join(t.name for t in trades) if trades else "not specified"

    # ── Build system prompt ───────────────────────────────────────────────
    system_prompt = """You are an expert construction cost estimator and RS Means specialist with 25 years of field and estimating experience. You provide specific, actionable production rates and pricing data.

RULES:
- Always provide min, typical, and max ranges — never a single number without a range
- Rates are in UNITS PER HOUR (how many units one crew installs per hour)
- Labor rates are in USD per hour for the full crew (not per worker)
- Material costs are in USD per unit of the work item
- Factor in regional cost adjustments when a location is provided
- Reference the database records below when they are relevant; supplement with RS Means knowledge when not
- Explain what drives variation: crew size, access, substrate conditions, complexity, repetition
- Return ONLY valid JSON — no markdown fences, no text outside the JSON object

REQUIRED JSON FORMAT:
{
  "summary": "direct answer in 1-2 sentences",
  "rates": [
    {
      "description": "specific work item",
      "unit": "SF/LF/EA/CY etc",
      "min_rate": <number>,
      "typical_rate": <number>,
      "max_rate": <number>,
      "unit_label": "units per hour",
      "labor_rate_min": <number>,
      "labor_rate_typical": <number>,
      "labor_rate_max": <number>,
      "material_cost_min": <number>,
      "material_cost_typical": <number>,
      "material_cost_max": <number>,
      "source": "database" or "RS Means knowledge",
      "notes": "factors affecting this rate"
    }
  ],
  "regional_notes": "pricing notes specific to the project location, or empty string if no location",
  "recommendation": "what the estimator should use for this project and why"
}"""

    # ── User message ──────────────────────────────────────────────────────
    user_message_parts = [f"QUESTION: {query}"]
    if location_context:
        user_message_parts.append(f"PROJECT LOCATION: {location_context}")
    user_message_parts.append(f"COMPANY TRADES ON FILE: {trades_text}")
    user_message_parts.append(
        f"\nDATABASE PRODUCTION RATE RECORDS (use these when relevant):\n{_build_rates_text(standards)}"
    )
    user_message = "\n\n".join(user_message_parts)

    # ── Call Claude ───────────────────────────────────────────────────────
    try:
        client   = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=4096,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
        )
        raw_text = response.content[0].text.strip()
    except anthropic.AuthenticationError:
        return jsonify({'success': False, 'error': 'Invalid ANTHROPIC_API_KEY'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    # ── Parse JSON ────────────────────────────────────────────────────────
    json_text = raw_text
    fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_text)
    if fence:
        json_text = fence.group(1).strip()

    try:
        result = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({'success': False,
                        'error': f'Claude returned invalid JSON: {str(e)}',
                        'raw': raw_text}), 500

    return jsonify({'success': True, **result})


@app.route('/ai/validate-rate', methods=['POST'])
@limiter.limit('20 per minute')
@login_required
def ai_validate_rate():
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        return jsonify({'success': False, 'error': 'ANTHROPIC_API_KEY not configured'}), 500

    data        = request.get_json() or {}
    li_id       = data.get('line_item_id')
    project_id  = data.get('project_id')

    if not li_id:
        return jsonify({'success': False, 'error': 'line_item_id is required'}), 400

    # ── Fetch and authorise line item ─────────────────────────────────────
    item = get_lineitem_or_403(li_id)

    if item.production_rate is None:
        return jsonify({'success': False,
                        'error': 'Line item has no production rate to validate'}), 400

    current_rate = float(item.production_rate)

    # ── Fuzzy-match standards on description ─────────────────────────────
    words = [w for w in re.split(r'\s+', item.description) if len(w) > 2]
    standards = []
    if words:
        from sqlalchemy import or_
        conditions = []
        for w in words[:6]:
            conditions.append(ProductionRateStandard.description.ilike(f'%{w}%'))
            if item.trade:
                conditions.append(ProductionRateStandard.trade.ilike(f'%{item.trade}%'))
        standards = (ProductionRateStandard.query
                     .filter(or_(*conditions))
                     .order_by(ProductionRateStandard.trade, ProductionRateStandard.description)
                     .limit(10).all())

    # ── Project location ──────────────────────────────────────────────────
    location_context = ""
    if project_id:
        project = Project.query.filter_by(
            id=project_id, company_id=current_user.company_id).first()
        if project and (project.city or project.state):
            location_context = f"{project.city or ''}, {project.state or ''}".strip(', ')

    # ── System prompt ─────────────────────────────────────────────────────
    system_prompt = """You are an expert construction cost estimator reviewing a line item's production rate for reasonableness.

Rates are expressed as UNITS PER HOUR (how many units one crew installs per hour).
Compare the current rate against typical industry rates for the work type and location.
Return ONLY valid JSON — no markdown, no text outside the JSON.

REQUIRED JSON FORMAT:
{
  "is_reasonable": true or false,
  "current_rate": <number — the rate being reviewed>,
  "typical_range": {"min": <number>, "typical": <number>, "max": <number>},
  "assessment": "HIGH" or "LOW" or "REASONABLE",
  "explanation": "clear explanation of why this rate is or is not reasonable",
  "recommendation": "specific suggested rate or range to use instead, or confirmation to keep as-is"
}"""

    # ── User message ──────────────────────────────────────────────────────
    li_block = (
        f"LINE ITEM TO VALIDATE:\n"
        f"  Description: {item.description}\n"
        f"  Quantity: {float(item.quantity or 0)} {item.unit or ''}\n"
        f"  Production rate: {current_rate} {item.unit or 'units'}/hr\n"
        f"  Item type: {item.item_type or 'labor_material'}\n"
        f"  Trade: {item.trade or 'not specified'}\n"
    )
    if location_context:
        li_block += f"  Project location: {location_context}\n"

    db_block = f"\nDATABASE REFERENCE RATES:\n{_build_rates_text(standards)}"

    user_message = li_block + db_block

    # ── Call Claude ───────────────────────────────────────────────────────
    try:
        client   = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=1024,
            system=system_prompt,
            messages=[{'role': 'user', 'content': user_message}],
        )
        raw_text = response.content[0].text.strip()
    except anthropic.AuthenticationError:
        return jsonify({'success': False, 'error': 'Invalid ANTHROPIC_API_KEY'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    # ── Parse JSON ────────────────────────────────────────────────────────
    json_text = raw_text
    fence = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_text)
    if fence:
        json_text = fence.group(1).strip()

    try:
        result = json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as e:
        return jsonify({'success': False,
                        'error': f'Claude returned invalid JSON: {str(e)}',
                        'raw': raw_text}), 500

    return jsonify({'success': True, **result})


# ─────────────────────────────────────────
# STARTUP HELPERS
# ─────────────────────────────────────────

def _seed_company_properties(company_id):
    """Seed default global properties for a new company (called when admin creates a company)."""
    defaults = {
        'trade': ['Concrete', 'Drywall', 'Steel', 'Framing', 'Masonry',
                  'Electrical', 'Plumbing', 'Mechanical', 'Painting', 'Roofing'],
        'project_type': ['Ground Up', 'Interior Fit-Out', 'Renovation'],
        'market_sector': ['Retail', 'Multi-Family', 'Mixed-Use', 'Single Family',
                          'Higher-Ed', 'Healthcare', 'Office', 'Industrial'],
    }
    for category, names in defaults.items():
        existing = {p.name for p in GlobalProperty.query.filter_by(
            company_id=company_id, category=category).all()}
        for i, name in enumerate(names):
            if name not in existing:
                db.session.add(GlobalProperty(company_id=company_id,
                                              category=category, name=name, sort_order=i))

def _backfill_wbs_locations(project_id):
    """Normalize WBS for existing projects: rename area→location_1, fix display_orders,
    add missing location_2/3, delete bid_package."""
    props = {p.property_type: p for p in WBSProperty.query.filter_by(project_id=project_id).all()}

    # Rename 'area' → 'location_1'
    if 'area' in props and 'location_1' not in props:
        p = props.pop('area')
        p.property_type = 'location_1'
        p.property_name = 'Location 1'
        props['location_1'] = p

    # Add missing location_2 / location_3
    for prop_type, prop_name in [('location_2', 'Location 2'), ('location_3', 'Location 3')]:
        if prop_type not in props:
            new_prop = WBSProperty(
                project_id=project_id, property_type=prop_type, property_name=prop_name,
                is_template=True, display_order=99
            )
            db.session.add(new_prop)
            db.session.flush()
            props[prop_type] = new_prop

    # Fix display_orders so location_1/2/3 come first, then custom_1..4
    order_map = {'location_1': 1, 'location_2': 2, 'location_3': 3,
                 'custom_1': 5, 'custom_2': 6, 'custom_3': 7, 'custom_4': 8}
    for prop_type, order in order_map.items():
        if prop_type in props:
            props[prop_type].display_order = order

    # Delete bid_package and all its values
    if 'bid_package' in props:
        bp = props['bid_package']
        WBSValue.query.filter_by(wbs_property_id=bp.id).delete()
        db.session.delete(bp)

    db.session.commit()


def _initialize_wbs(project_id):
    """Seed default WBS properties and values for a new project."""
    # Location 1 – primary location breakdown (building / zone)
    loc1 = WBSProperty(
        project_id=project_id, property_type='location_1', property_name='Location 1',
        is_template=True, display_order=1
    )
    db.session.add(loc1)
    db.session.flush()
    for i, (name, code) in enumerate([
        ('Building A', 'BLDG-A'), ('Building B', 'BLDG-B'),
        ('Basement', 'BASE'), ('Ground Floor', 'GRD'), ('Upper Floors', 'UPR'),
        ('Roof', 'ROOF'), ('Site', 'SITE'),
    ]):
        db.session.add(WBSValue(
            wbs_property_id=loc1.id, value_name=name,
            value_code=code, display_order=i
        ))

    # Location 2 – secondary location (floor / wing)
    loc2 = WBSProperty(
        project_id=project_id, property_type='location_2', property_name='Location 2',
        is_template=True, display_order=2
    )
    db.session.add(loc2)

    # Location 3 – tertiary location (room / zone)
    loc3 = WBSProperty(
        project_id=project_id, property_type='location_3', property_name='Location 3',
        is_template=True, display_order=3
    )
    db.session.add(loc3)

    # Custom properties (no default values) — display_order 5-8
    for i in range(1, 5):
        db.session.add(WBSProperty(
            project_id=project_id, property_type=f'custom_{i}',
            property_name=f'Custom {i}', is_custom=True, display_order=i + 4
        ))

    db.session.commit()


def run_migrations():
    """Add new columns to existing tables without dropping data."""
    with app.app_context():
        stmts = [
            # Pre-auth columns (idempotent)
            "ALTER TABLE assemblies ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT FALSE",
            "ALTER TABLE assemblies ADD COLUMN IF NOT EXISTS measurement_params TEXT",
            "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS trade VARCHAR(100)",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS city VARCHAR(100)",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS state VARCHAR(50)",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS zip_code VARCHAR(20)",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type_id INTEGER",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS market_sector_id INTEGER",
            "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id)",
            "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS item_type VARCHAR(20) DEFAULT 'labor_material'",
            "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS prod_base BOOLEAN DEFAULT TRUE",
            "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS labor_cost_per_unit NUMERIC(10,2)",
            "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS equipment_cost_per_unit NUMERIC(10,2)",
            "ALTER TABLE line_items ALTER COLUMN assembly_id DROP NOT NULL",
            "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS csi_level_1_id INTEGER REFERENCES csi_level_1(id)",
            "ALTER TABLE line_items ADD COLUMN IF NOT EXISTS csi_level_2_id INTEGER REFERENCES csi_level_2(id)",
            "ALTER TABLE library_items ADD COLUMN IF NOT EXISTS item_type VARCHAR(20) DEFAULT 'labor_material'",
            "ALTER TABLE library_items ADD COLUMN IF NOT EXISTS prod_base BOOLEAN DEFAULT TRUE",
            "ALTER TABLE library_items ADD COLUMN IF NOT EXISTS labor_cost_per_unit NUMERIC(10,2)",
            "ALTER TABLE library_items ADD COLUMN IF NOT EXISTS equipment_cost_per_unit NUMERIC(10,2)",
            # Auth / multi-tenancy columns
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id)",
            "ALTER TABLE library_items ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id)",
            "ALTER TABLE global_properties ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id)",
            "ALTER TABLE company_profile ADD COLUMN IF NOT EXISTS company_id INTEGER REFERENCES companies(id)",
            # Password reset columns
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(100)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP",
            # Waitlist tables
            """CREATE TABLE IF NOT EXISTS waitlist_entries (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS waitlist_surveys (
                id SERIAL PRIMARY KEY,
                waitlist_entry_id INTEGER NOT NULL REFERENCES waitlist_entries(id),
                responses TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            # WBS tables (created by db.create_all; these are safety guards)
            """CREATE TABLE IF NOT EXISTS wbs_properties (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                property_type VARCHAR(50) NOT NULL,
                property_name VARCHAR(100) NOT NULL,
                is_template BOOLEAN DEFAULT false,
                is_custom BOOLEAN DEFAULT false,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS wbs_values (
                id SERIAL PRIMARY KEY,
                wbs_property_id INTEGER REFERENCES wbs_properties(id) ON DELETE CASCADE,
                value_name VARCHAR(100) NOT NULL,
                value_code VARCHAR(50),
                parent_id INTEGER REFERENCES wbs_values(id),
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS line_item_wbs (
                id SERIAL PRIMARY KEY,
                line_item_id INTEGER REFERENCES line_items(id) ON DELETE CASCADE,
                wbs_property_id INTEGER REFERENCES wbs_properties(id) ON DELETE CASCADE,
                wbs_value_id INTEGER REFERENCES wbs_values(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
        ]
        for sql in stmts:
            try:
                db.session.execute(db.text(sql))
                db.session.commit()
            except Exception:
                db.session.rollback()

def seed_production_rates():
    """Seed default production rate standards if table is empty."""
    with app.app_context():
        if ProductionRateStandard.query.count() > 0:
            return
        defaults = [
            ('Concrete',   'Concrete — Footings, continuous',          'LF',  15,  25,  40,  'Includes form, pour, strip'),
            ('Concrete',   'Concrete — Slab on grade, 4"',             'SF',  150, 250, 400, 'Machine-assisted placement'),
            ('Concrete',   'Concrete — Columns, square',               'LF',  8,   12,  20,  'Includes forming'),
            ('Masonry',    'Masonry — CMU block, 8"',                  'SF',  80,  120, 160, 'Running bond, mortar included'),
            ('Masonry',    'Masonry — Brick veneer',                   'SF',  60,  90,  130, 'Standard running bond'),
            ('Framing',    'Framing — Wood stud wall, 2x4 16"oc',     'SF',  200, 350, 500, 'Plate to plate, layout to sheathing'),
            ('Framing',    'Framing — Metal stud wall, 3-5/8"',       'SF',  175, 300, 450, 'Track + studs + blocking'),
            ('Framing',    'Framing — Floor joist system',             'SF',  100, 180, 280, 'Layout, cut, set, blocking'),
            ('Drywall',    'Drywall — Hang 5/8" GWB',                 'SF',  400, 600, 900, 'Flat ceilings reduce rate'),
            ('Drywall',    'Drywall — Tape, float, finish Level 4',    'SF',  350, 500, 700, 'Spray primer after'),
            ('Painting',   'Painting — Interior walls, 2-coat',        'SF',  300, 500, 800, 'Roller application'),
            ('Painting',   'Painting — Exterior siding',               'SF',  200, 350, 600, 'Brush + roller'),
            ('Roofing',    'Roofing — TPO single-ply membrane',        'SQ',  4,   6,   9,   'Mechanically fastened'),
            ('Roofing',    'Roofing — Asphalt shingle, 30yr',         'SQ',  6,   9,   14,  'Tear-off not included'),
            ('Electrical', 'Electrical — EMT conduit, 3/4"',           'LF',  30,  50,  80,  'Install only, material separate'),
            ('Electrical', 'Electrical — Receptacle outlet, rough-in', 'EA',  4,   6,   10,  'Box, wire, device'),
            ('Plumbing',   'Plumbing — Copper pipe, 3/4"',             'LF',  25,  40,  60,  'Solder joints'),
            ('Plumbing',   'Plumbing — PVC DWV, 3"',                  'LF',  30,  50,  75,  'Includes fittings'),
            ('Mechanical', 'HVAC — Flex duct, 8"',                     'LF',  40,  65,  100, 'Insulated'),
            ('Mechanical', 'HVAC — Sheet metal duct, rectangular',     'LB',  20,  35,  55,  'Fab + install'),
        ]
        for trade, desc, unit, min_r, typ_r, max_r, notes in defaults:
            db.session.add(ProductionRateStandard(
                trade=trade, description=desc, unit=unit,
                min_rate=min_r, typical_rate=typ_r, max_rate=max_r, source_notes=notes,
            ))
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    run_migrations()
    seed_production_rates()
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
