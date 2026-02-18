from flask import Flask
from flask_cors import CORS

from routes.profile import bp as profile_bp
from routes.members import bp as members_bp
from routes.attendance import bp as attendance_bp
from routes.finance import bp as finance_bp
from routes.demo_data import bp as demo_data_bp


def create_app():
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:5173"])

    app.register_blueprint(profile_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(demo_data_bp)

    @app.get("/api/health")
    def health():
        return {"status": "ok backend is running smoothly"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
