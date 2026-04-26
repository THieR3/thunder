"""
Firebase Authentication Routes for Flask
Handles token verification and user management endpoints
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from typing import Optional, Dict, Any, Callable

from fb_admin import firebase_admin, create_user_profile


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ════════════════════════════════════════════════════════
# MIDDLEWARE: TOKEN VERIFICATION
# ════════════════════════════════════════════════════════


def require_auth(f: Callable) -> Callable:
    """
    Decorator to verify Firebase token from Authorization header.
    Usage: @require_auth
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not token:
            return jsonify({"error": "Missing authorization token"}), 401

        decoded_token = firebase_admin.verify_token(token)

        if not decoded_token:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.user_uid = decoded_token.get("uid")
        request.user_email = decoded_token.get("email")

        return f(*args, **kwargs)

    return decorated_function


# ════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ════════════════════════════════════════════════════════


@auth_bp.route("/verify-token", methods=["POST"])
def verify_token():
    """
    Verify Firebase token validity.

    Request body:
        {
            "token": "firebase_id_token"
        }

    Response:
        {
            "valid": true,
            "uid": "user_uid",
            "email": "user@example.com"
        }
    """
    try:
        data = request.get_json()
        token = data.get("token")

        if not token:
            return jsonify({"error": "Missing token"}), 400

        decoded_token = firebase_admin.verify_token(token)

        if not decoded_token:
            return jsonify({"valid": False}), 401

        return jsonify(
            {
                "valid": True,
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/user-profile", methods=["GET"])
@require_auth
def get_profile():
    """
    Get current user profile.
    Requires: Valid Firebase token in Authorization header

    Response:
        {
            "uid": "user_uid",
            "email": "user@example.com",
            "displayName": "User Name",
            "projectCount": 5,
            ...
        }
    """
    try:
        profile = firebase_admin.get_user_profile(request.user_uid)

        if not profile:
            return jsonify({"error": "User profile not found"}), 404

        return jsonify(profile)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/user-profile", methods=["PUT"])
@require_auth
def update_profile():
    """
    Update user profile.
    Requires: Valid Firebase token in Authorization header

    Request body:
        {
            "displayName": "New Name",
            "photoURL": "https://...",
            "plan": "pro"
        }

    Response:
        {"success": true, "message": "Profile updated"}
    """
    try:
        data = request.get_json()

        # Sanitize allowed fields
        allowed_fields = ["displayName", "photoURL", "plan"]
        update_data = {
            field: value for field, value in data.items() if field in allowed_fields
        }

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        success = firebase_admin.update_user_profile(request.user_uid, update_data)

        if not success:
            return jsonify({"error": "Failed to update profile"}), 500

        return jsonify({"success": True, "message": "Profile updated"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/create-user", methods=["POST"])
def create_user_endpoint():
    """
    Create new user (server-side).
    NOTE: Normally users create themselves via Firebase Auth in frontend.
    This is for admin purposes or special cases.

    Request body:
        {
            "email": "user@example.com",
            "password": "secure_password",
            "displayName": "User Name"
        }

    Response:
        {
            "success": true,
            "uid": "new_user_uid",
            "email": "user@example.com"
        }
    """
    try:
        data = request.get_json()

        email = data.get("email", "").strip()
        password = data.get("password", "")
        display_name = data.get("displayName", "")

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        user = firebase_admin.create_user(email, password, display_name)
        create_user_profile(user["uid"], user["email"], display_name)

        return jsonify({"success": True, "uid": user["uid"], "email": user["email"]})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/get-user/<uid>", methods=["GET"])
@require_auth
def get_user_endpoint(uid: str):
    """
    Get user info by UID (admin only).
    NOTE: User can only request their own info.

    Response:
        {
            "uid": "user_uid",
            "email": "user@example.com",
            "display_name": "User Name"
        }
    """
    try:
        # Users can only view their own profile
        if uid != request.user_uid:
            return jsonify({"error": "Unauthorized"}), 403

        user = firebase_admin.get_user(uid)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════
# EXPORT BLUEPRINT
# ════════════════════════════════════════════════════════


def init_auth_routes(app):
    """Register authentication routes with Flask app."""
    app.register_blueprint(auth_bp)
    print("✅ Auth routes registered")
