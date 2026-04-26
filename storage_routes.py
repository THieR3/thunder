"""
Firebase Storage File Management Routes
Handles file uploads and downloads for projects
"""

import os
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from typing import Optional, Tuple
import tempfile

from fb_admin import firebase_admin
from auth_routes import require_auth


storage_bp = Blueprint("storage", __name__, url_prefix="/api/storage")

# Configuration
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "json"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def allowed_file(filename: str) -> bool:
    """Check if file type is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_type(filename: str) -> str:
    """Determine file type from extension."""
    ext = filename.rsplit(".", 1)[1].lower()
    if ext in {"png", "jpg", "jpeg", "gif"}:
        return "image"
    elif ext == "pdf":
        return "pdf"
    elif ext == "json":
        return "export"
    return "file"


# ════════════════════════════════════════════════════════
# FILE UPLOAD ENDPOINTS
# ════════════════════════════════════════════════════════


@storage_bp.route("/upload", methods=["POST"])
@require_auth
def upload_file():
    """
    Upload file to Firebase Storage.

    Form data:
        file: File to upload
        projectId: Project ID

    Response:
        {
            "success": true,
            "url": "https://storage.googleapis.com/...",
            "fileName": "uploaded_file.png",
            "fileType": "image",
            "size": 1024
        }
    """
    try:
        # Check file presence
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        if "projectId" not in request.form:
            return jsonify({"error": "Project ID required"}), 400

        file = request.files["file"]
        project_id = request.form.get("projectId")

        # Validate file
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return (
                jsonify(
                    {
                        "error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
                    }
                ),
                400,
            )

        if file.content_length > MAX_FILE_SIZE:
            return jsonify({"error": f"File too large. Max: {MAX_FILE_SIZE / 1024 / 1024}MB"}), 400

        # Verify project exists
        project = firebase_admin.get_project(request.user_uid, project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file.save(temp_file.name)
        temp_file.close()

        try:
            # Upload to Firebase Storage
            file_type = get_file_type(file.filename)
            download_url = firebase_admin.upload_project_file(
                request.user_uid, project_id, temp_file.name, file_type
            )

            if not download_url:
                return jsonify({"error": "Upload failed"}), 500

            # Add file metadata to project
            file_info = {
                "name": secure_filename(file.filename),
                "type": file_type,
                "size": file.content_length,
                "url": download_url,
                "uploadedAt": firebase_admin.firestore.SERVER_TIMESTAMP,
            }

            firebase_admin.add_project_file(request.user_uid, project_id, file_info)

            return jsonify(
                {
                    "success": True,
                    "url": download_url,
                    "fileName": file.filename,
                    "fileType": file_type,
                    "size": file.content_length,
                }
            )

        finally:
            # Clean up temp file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@storage_bp.route("/download/<project_id>/<file_name>", methods=["GET"])
@require_auth
def download_file(project_id: str, file_name: str):
    """
    Download file from Firebase Storage.

    Query params:
        ?type=image|pdf|export

    Response:
        File binary content
    """
    try:
        # Verify project exists
        project = firebase_admin.get_project(request.user_uid, project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        file_type = request.args.get("type", "image")
        file_name = secure_filename(file_name)

        # Download from Firebase Storage
        file_content = firebase_admin.download_project_file(
            request.user_uid, project_id, file_name, file_type
        )

        if not file_content:
            return jsonify({"error": "File not found"}), 404

        return send_file(
            io.BytesIO(file_content),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=file_name,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@storage_bp.route("/delete/<project_id>/<file_name>", methods=["DELETE"])
@require_auth
def delete_file(project_id: str, file_name: str):
    """
    Delete file from Firebase Storage.

    Query params:
        ?type=image|pdf|export

    Response:
        {"success": true, "message": "File deleted"}
    """
    try:
        # Verify project exists
        project = firebase_admin.get_project(request.user_uid, project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        file_type = request.args.get("type", "image")
        file_name = secure_filename(file_name)

        # Delete from Firebase Storage
        success = firebase_admin.delete_storage_file(
            request.user_uid, project_id, file_name, file_type
        )

        if not success:
            return jsonify({"error": "Failed to delete file"}), 500

        # Remove from project metadata
        files = project.get("files", [])
        files = [f for f in files if f.get("name") != file_name]
        firebase_admin.update_project(request.user_uid, project_id, {"files": files})

        return jsonify({"success": True, "message": "File deleted"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@storage_bp.route("/list/<project_id>", methods=["GET"])
@require_auth
def list_project_files(project_id: str):
    """
    List all files in project.

    Response:
        [
            {
                "name": "plan.png",
                "type": "image",
                "size": 1024,
                "url": "https://storage.googleapis.com/...",
                "uploadedAt": "2024-01-15T..."
            }
        ]
    """
    try:
        project = firebase_admin.get_project(request.user_uid, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        files = project.get("files", [])
        return jsonify(files)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# BULK OPERATIONS
# ════════════════════════════════════════════════════════


@storage_bp.route("/cleanup/<project_id>", methods=["POST"])
@require_auth
def cleanup_old_files(project_id: str):
    """
    Delete all files older than specified days.

    Query params:
        ?days=30

    Response:
        {
            "success": true,
            "deletedCount": 5,
            "message": "Cleaned up 5 old files"
        }
    """
    try:
        days = int(request.args.get("days", 30))
        project = firebase_admin.get_project(request.user_uid, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        # TODO: Implement cleanup logic based on uploadedAt timestamp

        return jsonify(
            {"success": True, "deletedCount": 0, "message": "Cleanup completed"}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# EXPORT BLUEPRINT
# ════════════════════════════════════════════════════════

import io


def init_storage_routes(app):
    """Register storage routes with Flask app."""
    app.register_blueprint(storage_bp)
    print("✅ Storage routes registered")
