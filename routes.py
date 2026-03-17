# routes.py
# Add these routes to your existing app.py file

from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import psycopg2

# ============================================================================
# AUTHENTICATION DECORATOR
# ============================================================================

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# MARKETING / PUBLIC PAGES
# ============================================================================

@app.route('/')
def landing():
    """Landing page - marketing site"""
    return render_template('landing.html')


@app.route('/features')
def features():
    """Features page - detailed feature breakdown"""
    # For now, redirect to landing with #features anchor
    # Later you can create a dedicated features.html template
    return redirect('/#features')


@app.route('/pricing')
def pricing():
    """Pricing page - tier structure"""
    return render_template('pricing.html')


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        full_name = request.form.get('full_name')
        email = request.form.get('email').lower()
        password = request.form.get('password')
        
        # Validation
        if not all([company_name, full_name, email, password]):
            return render_template('signup.html', error='All fields are required')
        
        if len(password) < 8:
            return render_template('signup.html', error='Password must be at least 8 characters')
        
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Check if email already exists
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                cur.close()
                conn.close()
                return render_template('signup.html', error='Email already registered')
            
            # Create company first
            cur.execute("""
                INSERT INTO companies (company_name, created_at)
                VALUES (%s, NOW())
                RETURNING id
            """, (company_name,))
            company_id = cur.fetchone()[0]
            
            # Hash password and create user
            password_hash = generate_password_hash(password)
            cur.execute("""
                INSERT INTO users (company_id, email, password_hash, full_name, role, created_at)
                VALUES (%s, %s, %s, %s, 'owner', NOW())
                RETURNING id
            """, (company_id, email, password_hash, full_name))
            user_id = cur.fetchone()[0]
            
            conn.commit()
            cur.close()
            conn.close()
            
            # Log user in automatically
            session['user_id'] = user_id
            session['company_id'] = company_id
            session['user_name'] = full_name
            session['user_role'] = 'owner'
            
            flash('Account created successfully! Welcome to Zenbid.', 'success')
            return redirect('/app/dashboard')
            
        except Exception as e:
            print(f"Signup error: {e}")
            return render_template('signup.html', error='An error occurred. Please try again.')
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        if not email or not password:
            return render_template('login.html', error='Email and password are required')
        
        try:
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, company_id, password_hash, full_name, role, is_active
                FROM users
                WHERE email = %s
            """, (email,))
            user = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if not user:
                return render_template('login.html', error='Invalid email or password', email=email)
            
            user_id, company_id, password_hash, full_name, role, is_active = user
            
            if not is_active:
                return render_template('login.html', error='Account is inactive. Contact support.', email=email)
            
            if not check_password_hash(password_hash, password):
                return render_template('login.html', error='Invalid email or password', email=email)
            
            # Set session
            session['user_id'] = user_id
            session['company_id'] = company_id
            session['user_name'] = full_name
            session['user_role'] = role
            
            if remember:
                session.permanent = True  # Session lasts 31 days by default
            
            flash('Logged in successfully!', 'success')
            return redirect('/app/dashboard')
            
        except Exception as e:
            print(f"Login error: {e}")
            return render_template('login.html', error='An error occurred. Please try again.')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect('/')


@app.route('/forgot-password')
def forgot_password():
    """Password reset request (placeholder for now)"""
    # TODO: Implement password reset flow
    flash('Password reset functionality coming soon. Contact support for help.', 'info')
    return redirect('/login')


# ============================================================================
# APP ROUTES (Protected - Require Login)
# ============================================================================

@app.route('/app')
@app.route('/app/dashboard')
@login_required
def dashboard():
    """Main app dashboard - shows projects overview"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Get user's projects
        cur.execute("""
            SELECT 
                id, 
                project_name, 
                project_number, 
                location,
                created_at,
                updated_at
            FROM projects
            WHERE company_id = %s
            ORDER BY updated_at DESC
        """, (session['company_id'],))
        
        projects = cur.fetchall()
        
        # Get project stats
        cur.execute("""
            SELECT COUNT(*) FROM projects WHERE company_id = %s
        """, (session['company_id'],))
        project_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return render_template('app_dashboard.html', 
                             projects=projects,
                             project_count=project_count)
                             
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('app_dashboard.html', projects=[], project_count=0)


@app.route('/app/projects')
@login_required
def projects():
    """Projects list view"""
    return redirect('/app/dashboard')  # For now, same as dashboard


# ============================================================================
# PLACEHOLDER ROUTES (For footer links)
# ============================================================================

@app.route('/about')
def about():
    return "About page - Coming soon", 200

@app.route('/blog')
def blog():
    return "Blog - Coming soon", 200

@app.route('/careers')
def careers():
    return "Careers - Coming soon", 200

@app.route('/contact')
def contact():
    return "Contact page - Coming soon", 200

@app.route('/privacy')
def privacy():
    return "Privacy Policy - Coming soon", 200

@app.route('/terms')
def terms():
    return "Terms of Service - Coming soon", 200

@app.route('/security')
def security():
    return "Security - Coming soon", 200


# ============================================================================
# HELPER FUNCTION (if not already in app.py)
# ============================================================================

def get_db():
    """Get database connection"""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="estimator_db",
        user="postgres",
        password="your_password_here"  # UPDATE THIS
    )
