# Dev server entrypoint — avoids the routes_takeoff circular import when running app.py as __main__
from app import app, run_migrations, seed_production_rates

if __name__ == '__main__':
    with app.app_context():
        from app import db
        db.create_all()
    run_migrations()
    seed_production_rates()
    app.run(port=5000, debug=False, use_reloader=False)
