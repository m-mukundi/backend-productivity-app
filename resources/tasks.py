from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from extensions import db
from models import Task
from schemas import TaskCreateSchema, TaskUpdateSchema

task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()

DEFAULT_PER_PAGE = 10
MAX_PER_PAGE = 100


def _current_user_id():
    return int(get_jwt_identity())


def _get_owned_task_or_error(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return None, ({"error": "Task not found"}, 404)
    if task.user_id != _current_user_id():
        return None, ({"error": "You do not have access to this task"}, 403)
    return task, None


class TaskList(Resource):
    @jwt_required()
    def get(self):
        try:
            page = max(int(request.args.get("page", 1)), 1)
            per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
        except (TypeError, ValueError):
            return {"error": "page and per_page must be integers"}, 400

        per_page = max(1, min(per_page, MAX_PER_PAGE))

        status = request.args.get("status")
        query = Task.query.filter_by(user_id=_current_user_id())
        if status:
            query = query.filter_by(status=status)
        query = query.order_by(Task.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "tasks": [task.to_dict() for task in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }, 200

    @jwt_required()
    def post(self):
        json_data = request.get_json(silent=True) or {}
        try:
            data = task_create_schema.load(json_data)
        except ValidationError as err:
            return {"errors": err.messages}, 422

        task = Task(
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            user_id=_current_user_id(),
        )
        db.session.add(task)
        db.session.commit()

        return {"task": task.to_dict()}, 201


class TaskDetail(Resource):
    @jwt_required()
    def get(self, task_id):
        task, error = _get_owned_task_or_error(task_id)
        if error:
            return error
        return {"task": task.to_dict()}, 200

    @jwt_required()
    def patch(self, task_id):
        task, error = _get_owned_task_or_error(task_id)
        if error:
            return error

        json_data = request.get_json(silent=True) or {}
        try:
            data = task_update_schema.load(json_data, partial=True)
        except ValidationError as err:
            return {"errors": err.messages}, 422

        for field in ("title", "description", "status"):
            if field in data:
                setattr(task, field, data[field])

        db.session.commit()
        return {"task": task.to_dict()}, 200

    @jwt_required()
    def delete(self, task_id):
        task, error = _get_owned_task_or_error(task_id)
        if error:
            return error

        db.session.delete(task)
        db.session.commit()
        return {}, 204
