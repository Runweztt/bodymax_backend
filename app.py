from flask import Flask
from flask_cors import CORS

from routes.profile import bp as profile_bp
from routes.members import bp as members_bp
from routes.attendance import bp as attendance_bp
from routes.finance import bp as finance_bp
from routes.demo_data import bp as demo_data_bp
from routes.expiry import bp as expiry_bp
from routes.expenses import bp as expenses_bp
from routes.branches import bp as branches_bp


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(profile_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(demo_data_bp)
    app.register_blueprint(expiry_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(branches_bp)

    @app.get("/")
    def index():
        return {"message": "BodyMax Gym Backend API is Live!", "version": "1.0.0"}

    @app.get("/api/health")
    def health():
        return {"status": "ok backend is running smoothly"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
