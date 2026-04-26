"""
Firestore Project Management Routes
Handles CRUD operations for user projects
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Optional, Dict, Any

from fb_admin import (
    firebase_admin,
    create_project,
    get_user_projects,
    get_project,
    update_project,
    delete_project,
    add_project_file,
)
from auth_routes import require_auth


projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


# ════════════════════════════════════════════════════════
# PROJECT ENDPOINTS
# ════════════════════════════════════════════════════════


@projects_bp.route("", methods=["GET"])
@require_auth
def list_projects():
    """
    Get all projects for current user.

    Response:
        [
            {
                "id": "project_id",
                "name": "Project Name",
                "description": "...",
                "layout": {...},
                "createdAt": "2024-01-15T...",
                "updatedAt": "2024-01-15T..."
            }
        ]
    """
    try:
        projects = firebase_admin.get_user_projects(request.user_uid)
        return jsonify(projects)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projects_bp.route("", methods=["POST"])
@require_auth
def create_project_endpoint():
    """
    Create new project.

    Request body:
        {
            "name": "My Project",
            "description": "Project description",
            "layout": [],
            "settings": {}
        }

    Response:
        {
            "success": true,
            "id": "project_id",
            "message": "Project created"
        }
    """
    try:
        data = request.get_json()

        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "Project name required"}), 400

        description = data.get("description", "")
        layout = data.get("layout", [])
        settings = data.get("settings", {})

        project_data = {
            "name": name,
            "description": description,
            "layout": layout,
            "settings": settings,
            "rooms": [],
            "files": [],
        }

        project_id = firebase_admin.create_project(request.user_uid, project_data)

        if not project_id:
            return jsonify({"error": "Failed to create project"}), 500

        return jsonify({"success": True, "id": project_id, "message": "Project created"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projects_bp.route("/<project_id>", methods=["GET"])
@require_auth
def get_project_endpoint(project_id: str):
    """
    Get single project by ID.

    Response:
        {
            "id": "project_id",
            "name": "Project Name",
            "layout": {...},
            ...
        }
    """
    try:
        project = firebase_admin.get_project(request.user_uid, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        return jsonify(project)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projects_bp.route("/<project_id>", methods=["PUT"])
@require_auth
def update_project_endpoint(project_id: str):
    """
    Update project.

    Request body:
        {
            "name": "New Name",
            "description": "...",
            "layout": [],
            "rooms": []
        }

    Response:
        {"success": true, "message": "Project updated"}
    """
    try:
        project = firebase_admin.get_project(request.user_uid, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        data = request.get_json()

        # Sanitize allowed fields
        allowed_fields = ["name", "description", "layout", "rooms", "settings"]
        update_data = {
            field: value for field, value in data.items() if field in allowed_fields
        }

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        success = firebase_admin.update_project(request.user_uid, project_id, update_data)

        if not success:
            return jsonify({"error": "Failed to update project"}), 500

        return jsonify({"success": True, "message": "Project updated"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projects_bp.route("/<project_id>", methods=["DELETE"])
@require_auth
def delete_project_endpoint(project_id: str):
    """
    Delete project.

    Response:
        {"success": true, "message": "Project deleted"}
    """
    try:
        project = firebase_admin.get_project(request.user_uid, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        success = firebase_admin.delete_project(request.user_uid, project_id)

        if not success:
            return jsonify({"error": "Failed to delete project"}), 500

        return jsonify({"success": True, "message": "Project deleted"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projects_bp.route("/<project_id>/rooms", methods=["POST"])
@require_auth
def add_room(project_id: str):
    """
    Add room to project.

    Request body:
        {
            "name": "Living Room",
            "type": "salon",
            "x_pct": 5.0,
            "y_pct": 5.0,
            "w_pct": 38.0,
            "h_pct": 44.0
        }

    Response:
        {"success": true, "message": "Room added"}
    """
    try:
        project = firebase_admin.get_project(request.user_uid, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        data = request.get_json()
        rooms = project.get("rooms", [])

        room = {
            "id": f"room_{len(rooms)}",
            "name": data.get("name", ""),
            "type": data.get("type", "salon"),
            "x_pct": float(data.get("x_pct", 0)),
            "y_pct": float(data.get("y_pct", 0)),
            "w_pct": float(data.get("w_pct", 20)),
            "h_pct": float(data.get("h_pct", 20)),
            "devices": [],
            "protections": [],
        }

        rooms.append(room)
        success = firebase_admin.update_project(
            request.user_uid, project_id, {"rooms": rooms}
        )

        if not success:
            return jsonify({"error": "Failed to add room"}), 500

        return jsonify({"success": True, "message": "Room added"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projects_bp.route("/<project_id>/rooms/<room_id>", methods=["DELETE"])
@require_auth
def delete_room(project_id: str, room_id: str):
    """
    Delete room from project.

    Response:
        {"success": true, "message": "Room deleted"}
    """
    try:
        project = firebase_admin.get_project(request.user_uid, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        rooms = project.get("rooms", [])
        rooms = [r for r in rooms if r.get("id") != room_id]

        success = firebase_admin.update_project(
            request.user_uid, project_id, {"rooms": rooms}
        )

        if not success:
            return jsonify({"error": "Failed to delete room"}), 500

        return jsonify({"success": True, "message": "Room deleted"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@projects_bp.route("/<project_id>/export", methods=["GET"])
@require_auth
def export_project(project_id: str):
    """
    Export project as JSON.

    Query params:
        ?format=json|csv

    Response:
        Project data in requested format
    """
    try:
        project = firebase_admin.get_project(request.user_uid, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        export_format = request.args.get("format", "json")

        if export_format == "csv":
            # TODO: Implement CSV export
            return jsonify({"error": "CSV export not yet implemented"}), 501
        else:
            return jsonify(project)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# EXPORT BLUEPRINT
# ════════════════════════════════════════════════════════


def init_projects_routes(app):
    """Register projects routes with Flask app."""
    app.register_blueprint(projects_bp)
    print("✅ Projects routes registered")
