# INTEGRATION GUIDE: Adding Marketing Site to Estimator AgentX

This guide walks you through integrating the new marketing site with your existing Flask app.

---

## What You're Getting

### **New Marketing Pages** (Public - No Login Required)
- **Landing Page** (`/`) - Hero, features, CTA
- **Pricing Page** (`/pricing`) - Tier structure
- **Signup Page** (`/signup`) - Account creation
- **Login Page** (`/login`) - User authentication

### **Updated App Interface** (Protected - Login Required)
- **App Dashboard** (`/app/dashboard`) - Refined dark mode color scheme
- **Sidebar Navigation** - Consistent branding
- **Better Typography** - Optimized for long work sessions

### **New Color System**
- **Marketing pages:** Clean white backgrounds with blue/coral accents
- **App pages:** Soft dark mode (`#0F1419` background instead of harsh `#1a1a2e`)
- **Consistent brand colors:** `#2D5BFF` (blue) + `#FF6B35` (coral)

---

## Files to Copy

Copy these files from `/mnt/user-data/outputs/` to your project directory:

### **Templates** → `C:\Users\Tknig\Dropbox\Estimator Agent\templates\`

```
base.html              ← Marketing site base template
landing.html           ← Landing page
pricing.html           ← Pricing page
signup.html            ← Signup page
login.html             ← Login page
app_base.html          ← App interface base template (REPLACES your old one)
app_dashboard.html     ← New dashboard (updated colors)
```

### **Routes** → Merge into `app.py`

```
routes.py              ← Contains all new routes (see integration steps below)
```

---

## Step-by-Step Integration

### **STEP 1: Backup Your Current Files**

In VS Code terminal:
```bash
cd "C:\Users\Tknig\Dropbox\Estimator Agent"
mkdir backup
copy app.py backup\app.py
copy -r templates backup\templates
```

### **STEP 2: Install Required Packages** (if not already installed)

```bash
pip install Flask
pip install psycopg2
pip install Flask-Login
pip install Werkzeug
```

### **STEP 3: Update Your `app.py`**

Open `app.py` in VS Code. Add this at the top if it's not there:

```python
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import psycopg2
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-in-production'  # CHANGE THIS
app.permanent_session_lifetime = timedelta(days=31)  # Session lasts 31 days if "remember me" checked
```

### **STEP 4: Add Database Helper Function**

Add this function to `app.py` (if not already there):

```python
def get_db():
    """Get database connection"""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="estimator_db",
        user="postgres",
        password="your_password_here"  # UPDATE THIS WITH YOUR ACTUAL PASSWORD
    )
```

### **STEP 5: Add the Login Decorator**

Add this decorator function to `app.py`:

```python
def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
```

### **STEP 6: Copy All Routes from `routes.py`**

Open the `routes.py` file I created. Copy ALL the route functions and paste them into your `app.py` file, AFTER the helper functions but BEFORE the `if __name__ == '__main__':` line.

Routes you're adding:
- `/` (landing)
- `/pricing` (pricing page)
- `/signup` (registration)
- `/login` (authentication)
- `/logout` (logout)
- `/app/dashboard` (main app dashboard)
- Plus placeholder routes for `/about`, `/blog`, etc.

### **STEP 7: Update Your Existing Routes**

**Find your existing project routes** (like `/project/<id>`) and add `@login_required` decorator above them:

```python
@app.route('/project/<int:project_id>')
@login_required  # ← ADD THIS LINE
def project_detail(project_id):
    # Your existing code...
```

Do this for ALL routes that should require login (basically everything except `/`, `/pricing`, `/signup`, `/login`).

### **STEP 8: Update Templates to Use New Base**

**For app pages** (dashboard, project detail, etc.), change the extends line at the top:

```jinja2
{# OLD: #}
{% extends "base.html" %}

{# NEW: #}
{% extends "app_base.html" %}
```

**For marketing pages** (landing, pricing, signup, login), they already extend the right base.

### **STEP 9: Add Flash Message Support**

In your `app_base.html` template, add this right after the `<div class="app-content">` line:

```html
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    {% for category, message in messages %}
      <div class="alert alert-{{ category }}" style="margin-bottom: 1.5rem;">
        {{ message }}
      </div>
    {% endfor %}
  {% endif %}
{% endwith %}
```

And add this CSS to `app_base.html` in the `<style>` block:

```css
.alert {
    padding: 0.875rem 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    font-size: 0.875rem;
}

.alert-error {
    background: var(--error-bg);
    border: 1px solid var(--error);
    color: var(--error);
}

.alert-success {
    background: var(--success-bg);
    border: 1px solid var(--success);
    color: var(--success);
}

.alert-info {
    background: var(--info-bg);
    border: 1px solid var(--info);
    color: var(--info);
}
```

### **STEP 10: Update Database Schema** (if needed)

Make sure your `users` table has these fields:

```sql
-- Run this in PostgreSQL if you need to add missing columns:

ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user';
```

### **STEP 11: Test the Flow**

1. **Start your Flask app:**
   ```bash
   python app.py
   ```

2. **Visit `localhost:5000`** - You should see the NEW landing page (white background, blue/coral colors)

3. **Click "Sign Up"** - Create a test account

4. **After signup** - You should be redirected to `/app/dashboard` (dark mode, refined colors)

5. **Log out** - Click the user menu in the sidebar footer

6. **Log back in** - Visit `/login` and sign in with your test account

---

## Troubleshooting

### **Issue: "Template not found" error**
- Make sure all `.html` files are in `templates/` folder
- Check file names match exactly (case-sensitive)

### **Issue: "Session not found" or login doesn't work**
- Make sure you set `app.secret_key` in `app.py`
- Restart the Flask server after adding the secret key

### **Issue: Database connection error**
- Update the `password` in `get_db()` function
- Make sure PostgreSQL is running

### **Issue: Colors look wrong**
- Make sure you copied the ENTIRE `app_base.html` file
- Clear your browser cache (Ctrl + Shift + R)

### **Issue: Signup creates user but doesn't log in**
- Check that the session variables are being set correctly in the `/signup` route
- Make sure `session['user_id']` is being set

---

## Next Steps After Integration

1. **Update the AI panel** on your existing project pages to match the new color scheme
2. **Create a features page** (`/features`) with detailed feature breakdown
3. **Add actual stats** to the dashboard (currently placeholder numbers)
4. **Implement password reset** (currently just a placeholder)
5. **Add OAuth** (Google/Microsoft login buttons are placeholders for now)

---

## Quick Reference: New Color Variables

Use these in any new templates or CSS:

```css
/* Marketing (Light Mode) */
--primary-brand: #2D5BFF;        /* Main blue */
--accent-coral: #FF6B35;         /* Accent coral */
--marketing-bg: #FFFFFF;         /* White background */

/* App (Dark Mode) */
--app-bg: #0F1419;               /* Soft black background (easier on eyes) */
--app-card: #1A1F26;             /* Card/panel color */
--app-input: #252B33;            /* Input field background */
--text-primary: #E8EAED;         /* Soft white text */
--text-secondary: #9CA3AF;       /* Gray text */

/* States */
--success: #10B981;              /* Green */
--warning: #F59E0B;              /* Amber */
--error: #EF4444;                /* Red */
```

---

## File Checklist

Before testing, verify these files exist:

- [ ] `templates/base.html` (marketing base)
- [ ] `templates/landing.html` (landing page)
- [ ] `templates/pricing.html` (pricing page)
- [ ] `templates/signup.html` (signup page)
- [ ] `templates/login.html` (login page)
- [ ] `templates/app_base.html` (app base)
- [ ] `templates/app_dashboard.html` (dashboard)
- [ ] `app.py` updated with new routes
- [ ] Database password updated in `get_db()`
- [ ] `app.secret_key` set

---

## Questions?

If something doesn't work:
1. Check the terminal for error messages
2. Make sure PostgreSQL is running
3. Verify all files are copied correctly
4. Check that the database password is correct

Need me to generate any specific pieces? Let me know!
