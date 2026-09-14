from flask import request
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User, TokenBlocklist
from schemas import RegisterSchema, LoginSchema, flatten_errors

register_schema = RegisterSchema()
login_schema = LoginSchema()


class Signup(Resource):
    def post(self):
        json_data = request.get_json(silent=True) or {}
        try:
            data = register_schema.load(json_data)
        except ValidationError as err:
            return {"errors": flatten_errors(err.messages)}, 422

        if data["password"] != data["password_confirmation"]:
            return {"errors": ["Password and password confirmation do not match"]}, 422

        if User.query.filter_by(username=data["username"]).first():
            return {"errors": ["Username is already taken"]}, 409

        user = User(username=data["username"])
        user.password = data["password"]

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username is already taken"]}, 409

        access_token = create_access_token(identity=str(user.id))
        return {"token": access_token, "user": user.to_dict()}, 201


class Login(Resource):
    def post(self):
        json_data = request.get_json(silent=True) or {}
        try:
            data = login_schema.load(json_data)
        except ValidationError as err:
            return {"errors": flatten_errors(err.messages)}, 422

        user = User.query.filter_by(username=data["username"]).first()
        if user is None or not user.check_password(data["password"]):
            return {"errors": ["Invalid username or password"]}, 401

        access_token = create_access_token(identity=str(user.id))
        return {"token": access_token, "user": user.to_dict()}, 200


class Me(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get(int(get_jwt_identity()))
        if user is None:
            return {"errors": ["User not found"]}, 404
        return user.to_dict(), 200


class Logout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        db.session.add(TokenBlocklist(jti=jti))
        db.session.commit()
        return {"message": "Successfully logged out"}, 200
