from flask import Flask, jsonify
from flask_restful import Api

from config import Config
from extensions import db, migrate, bcrypt, jwt, cors
from models import TokenBlocklist
from resources.auth import Signup, Login, Me, Logout
from resources.tasks import TaskList, TaskDetail


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    api = Api(app)

    api.add_resource(Signup, "/signup")
    api.add_resource(Login, "/login")
    api.add_resource(Me, "/me")
    api.add_resource(Logout, "/logout")

    api.add_resource(TaskList, "/tasks")
    api.add_resource(TaskDetail, "/tasks/<int:task_id>")

    @app.get("/")
    def index():
        return {"message": "Productivity API is running"}, 200

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar() is not None

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"error": "Invalid token", "reason": reason}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({"error": "Authorization token is required", "reason": reason}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has been revoked"}), 401

    @app.errorhandler(404)
    def not_found(err):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(err):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5555, debug=True)
