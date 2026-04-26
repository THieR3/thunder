"""
Firebase Admin SDK Configuration for Python Backend
Project: stone-a4d71

This module initializes Firebase Admin SDK for server-side operations.
Requires: Firebase service account key JSON file

To get your service account key:
1. Go to https://console.firebase.google.com/project/stone-a4d71
2. Settings (⚙️) → Project Settings → Service Accounts
3. Click "Generate New Private Key"
4. Save as 'serviceAccountKey.json' in this directory
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from typing import Optional, Dict, List, Any


class FirebaseAdmin:
    """Initialize and manage Firebase Admin SDK connections."""

    _db = None
    _auth = None
    _storage_bucket = None
    _app = None

    @classmethod
    def initialize(cls, credentials_path: str = None):
        """
        Initialize Firebase Admin SDK.

        Args:
            credentials_path: Path to your Firebase service account key JSON file

        Raises:
            FileNotFoundError: If credentials file not found
            ValueError: If Firebase app already initialized
        """
        # Priority for credentials path:
        # 1. explicit `credentials_path` argument
        # 2. environment `GOOGLE_APPLICATION_CREDENTIALS`
        # 3. environment `FIREBASE_CREDENTIALS`
        # 4. fallback to Application Default Credentials (ADC)
        creds_path = credentials_path or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or os.environ.get('FIREBASE_CREDENTIALS')

        try:
            if creds_path:
                if not os.path.exists(creds_path):
                    raise FileNotFoundError(
                        f"Firebase credentials file not found: {creds_path}\n"
                        f"Download from: https://console.firebase.google.com/project/stone-a4d71"
                        f"/settings/serviceaccounts/adminsdk"
                    )
                cred = credentials.Certificate(creds_path)
                cls._app = firebase_admin.initialize_app(
                    cred,
                    {
                        "storageBucket": "stone-a4d71.firebasestorage.app",
                    },
                )
            else:
                # Try Application Default Credentials
                adc = credentials.ApplicationDefault()
                cls._app = firebase_admin.initialize_app(
                    adc,
                    {
                        "storageBucket": "stone-a4d71.firebasestorage.app",
                    },
                )
            cls._db = firestore.client()
            cls._auth = auth
            cls._storage_bucket = storage.bucket()
            print("✅ Firebase Admin SDK initialized successfully")
        except Exception as e:
            raise ValueError(f"Failed to initialize Firebase Admin: {str(e)}")

    @classmethod
    def get_db(cls):
        """Get Firestore database client."""
        if cls._db is None:
            raise RuntimeError("Firebase not initialized. Call initialize() first.")
        return cls._db

    @classmethod
    def get_auth(cls):
        """Get Firebase Auth service."""
        if cls._auth is None:
            raise RuntimeError("Firebase not initialized. Call initialize() first.")
        return cls._auth

    @classmethod
    def get_storage(cls):
        """Get Firebase Storage bucket."""
        if cls._storage_bucket is None:
            raise RuntimeError("Firebase not initialized. Call initialize() first.")
        return cls._storage_bucket


# ════════════════════════════════════════════════════════
# AUTHENTICATION FUNCTIONS
# ════════════════════════════════════════════════════════


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Firebase ID token from frontend.

    Args:
        token: Firebase ID token from client

    Returns:
        Decoded token claims if valid, None otherwise
    """
    try:
        decoded_token = FirebaseAdmin.get_auth().verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {str(e)}")
        return None


def create_user(email: str, password: str, display_name: str = "") -> Dict[str, str]:
    """
    Create a new Firebase user.

    Args:
        email: User email
        password: User password (min 6 chars)
        display_name: Optional display name

    Returns:
        User UID and email
    """
    try:
        user = FirebaseAdmin.get_auth().create_user(
            email=email,
            password=password,
            display_name=display_name or email.split("@")[0],
        )
        return {"uid": user.uid, "email": user.email}
    except Exception as e:
        raise ValueError(f"Error creating user: {str(e)}")


def get_user(uid: str) -> Optional[Dict[str, Any]]:
    """Get user by UID."""
    try:
        user = FirebaseAdmin.get_auth().get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "email_verified": user.email_verified,
        }
    except Exception as e:
        print(f"Error getting user: {str(e)}")
        return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    try:
        user = FirebaseAdmin.get_auth().get_user_by_email(email)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
        }
    except Exception as e:
        print(f"Error getting user by email: {str(e)}")
        return None


def delete_user(uid: str) -> bool:
    """Delete a user and their profile."""
    try:
        FirebaseAdmin.get_auth().delete_user(uid)
        # Also delete Firestore profile
        FirebaseAdmin.get_db().collection("users").document(uid).delete()
        return True
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        return False


# ════════════════════════════════════════════════════════
# FIRESTORE FUNCTIONS
# ════════════════════════════════════════════════════════


def create_user_profile(uid: str, email: str, display_name: str = "") -> bool:
    """Create user profile in Firestore."""
    try:
        FirebaseAdmin.get_db().collection("users").document(uid).set(
            {
                "uid": uid,
                "email": email,
                "displayName": display_name or email.split("@")[0],
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
                "plan": "free",
                "projects": [],
                "projectCount": 0,
            }
        )
        return True
    except Exception as e:
        print(f"Error creating user profile: {str(e)}")
        return False


def get_user_profile(uid: str) -> Optional[Dict[str, Any]]:
    """Get user profile from Firestore."""
    try:
        doc = FirebaseAdmin.get_db().collection("users").document(uid).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return None


def update_user_profile(uid: str, data: Dict[str, Any]) -> bool:
    """Update user profile in Firestore."""
    try:
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        FirebaseAdmin.get_db().collection("users").document(uid).update(data)
        return True
    except Exception as e:
        print(f"Error updating user profile: {str(e)}")
        return False


def create_project(uid: str, project_data: Dict[str, Any]) -> Optional[str]:
    """
    Create a new project for user.

    Returns:
        Project ID if successful, None otherwise
    """
    try:
        project_data["createdAt"] = firestore.SERVER_TIMESTAMP
        project_data["updatedAt"] = firestore.SERVER_TIMESTAMP
        project_data["owner"] = uid

        ref = FirebaseAdmin.get_db().collection("users").document(uid).collection(
            "projects"
        ).add(project_data)

        project_id = ref[1].id
        return project_id
    except Exception as e:
        print(f"Error creating project: {str(e)}")
        return None


def get_user_projects(uid: str) -> List[Dict[str, Any]]:
    """Get all projects for a user."""
    try:
        docs = (
            FirebaseAdmin.get_db()
            .collection("users")
            .document(uid)
            .collection("projects")
            .stream()
        )
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Error getting projects: {str(e)}")
        return []


def get_project(uid: str, project_id: str) -> Optional[Dict[str, Any]]:
    """Get single project."""
    try:
        doc = (
            FirebaseAdmin.get_db()
            .collection("users")
            .document(uid)
            .collection("projects")
            .document(project_id)
            .get()
        )
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"Error getting project: {str(e)}")
        return None


def update_project(uid: str, project_id: str, data: Dict[str, Any]) -> bool:
    """Update project."""
    try:
        data["updatedAt"] = firestore.SERVER_TIMESTAMP
        FirebaseAdmin.get_db().collection("users").document(uid).collection(
            "projects"
        ).document(project_id).update(data)
        return True
    except Exception as e:
        print(f"Error updating project: {str(e)}")
        return False


def delete_project(uid: str, project_id: str) -> bool:
    """Delete project."""
    try:
        FirebaseAdmin.get_db().collection("users").document(uid).collection(
            "projects"
        ).document(project_id).delete()
        return True
    except Exception as e:
        print(f"Error deleting project: {str(e)}")
        return False


def add_project_file(uid: str, project_id: str, file_info: Dict[str, Any]) -> bool:
    """Add file metadata to project."""
    try:
        FirebaseAdmin.get_db().collection("users").document(uid).collection(
            "projects"
        ).document(project_id).update(
            {"files": firestore.ArrayUnion([file_info])}
        )
        return True
    except Exception as e:
        print(f"Error adding file: {str(e)}")
        return False


# ════════════════════════════════════════════════════════
# STORAGE FUNCTIONS
# ════════════════════════════════════════════════════════


def upload_project_file(
    uid: str, project_id: str, file_path: str, file_type: str = "image"
) -> Optional[str]:
    """
    Upload file to Firebase Storage.

    Args:
        uid: User ID
        project_id: Project ID
        file_path: Path to local file
        file_type: Type of file (image, pdf, export)

    Returns:
        Public download URL if successful, None otherwise
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        storage_path = f"users/{uid}/projects/{project_id}/{file_type}/{file_name}"

        blob = FirebaseAdmin.get_storage().blob(storage_path)
        blob.upload_from_filename(file_path)
        blob.make_public()

        return blob.public_url
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return None


def download_project_file(
    uid: str, project_id: str, file_name: str, file_type: str = "image"
) -> Optional[bytes]:
    """Download file from Firebase Storage."""
    try:
        storage_path = f"users/{uid}/projects/{project_id}/{file_type}/{file_name}"
        blob = FirebaseAdmin.get_storage().blob(storage_path)

        if not blob.exists():
            return None

        return blob.download_as_bytes()
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return None


def delete_storage_file(
    uid: str, project_id: str, file_name: str, file_type: str = "image"
) -> bool:
    """Delete file from Firebase Storage."""
    try:
        storage_path = f"users/{uid}/projects/{project_id}/{file_type}/{file_name}"
        blob = FirebaseAdmin.get_storage().blob(storage_path)
        blob.delete()
        return True
    except Exception as e:
        print(f"Error deleting file: {str(e)}")
        return False


# ════════════════════════════════════════════════════════
# MODULE INITIALIZATION
# ════════════════════════════════════════════════════════

def init_firebase(credentials_path: str = None):
    """Initialize Firebase Admin SDK when module is imported."""
    try:
        if not firebase_admin._apps:
            FirebaseAdmin.initialize(credentials_path)
    except Exception as e:
        print(f"⚠️  Firebase initialization warning: {str(e)}")
        print(f"Firebase will not be available until initialized manually.")


# Try to auto-initialize on module import
init_firebase()
