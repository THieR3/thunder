# Firebase Configuration Guide — ElecPlan (tlp.1)

Complete Firebase integration setup for both frontend and backend of your ElecPlan project.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Frontend Setup](#frontend-setup)
3. [Backend Setup](#backend-setup)
4. [Database Structure](#database-structure)
5. [API Endpoints](#api-endpoints)
6. [Integration with app.py](#integration-with-apppy)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Your Firebase Project Details

```
Project Name: stone-a4d71
Web API Key: AIzaSyAnuKRJpc8nzt30QM3OGBbRdxAJPllfom0
Auth Domain: stone-a4d71.firebaseapp.com
Project ID: stone-a4d71
Storage Bucket: stone-a4d71.firebasestorage.app
```

### Step 1: Download Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com/project/stone-a4d71)
2. Navigate: **⚙️ Settings** → **Service Accounts** tab
3. Click **Generate New Private Key**
4. Save as `serviceAccountKey.json` in `/tlp.1/` directory

### Step 2: Install Backend Dependencies

```bash
cd d:\TLP_builder\tlp.1
pip install -r requirements.txt
```

### Step 3: Update app.py

See [Integration with app.py](#integration-with-apppy) section below.

---

## 🎨 Frontend Setup

### File: `static/firebase-config.js`

This module provides all frontend Firebase functions:

```html
<!-- In your HTML file (landing.html) -->
<script type="module">
  import * as Firebase from './firebase-config.js';

  // Sign up
  try {
    const user = await Firebase.signUpWithEmail('user@example.com', 'password', 'Full Name');
    console.log('User created:', user.uid);
  } catch (error) {
    console.error('Signup failed:', Firebase.getErrorMessage(error.code));
  }

  // Sign in
  try {
    const user = await Firebase.signInWithEmail('user@example.com', 'password');
    console.log('Signed in:', user.email);
  } catch (error) {
    console.error('Login failed:', Firebase.getErrorMessage(error.code));
  }

  // Create project
  try {
    const projectId = await Firebase.createProject(Firebase.getCurrentUser().uid, {
      name: 'My ElecPlan Project',
      description: 'NFC 15-100 electrical plan',
      layout: [],
    });
    console.log('Project created:', projectId);
  } catch (error) {
    console.error('Failed to create project:', error);
  }

  // Upload file
  try {
    const file = document.getElementById('fileInput').files[0];
    const url = await Firebase.uploadProjectFile(
      Firebase.getCurrentUser().uid,
      projectId,
      file,
      'image'
    );
    console.log('File uploaded to:', url);
  } catch (error) {
    console.error('Upload failed:', error);
  }
</script>
```

### Available Frontend Functions

```javascript
// Authentication
signUpWithEmail(email, password, displayName)
signInWithEmail(email, password)
signInWithGoogle()
resetPassword(email)
signOutUser()
getCurrentUser()
onAuthChange(callback)

// User Profile
ensureUserProfile(user, displayName)
updateUserProfile(uid, data)
getUserProfile(uid)

// Projects
createProject(uid, projectData)
getUserProjects(uid)
getProject(uid, projectId)
updateProject(uid, projectId, data)
deleteProject(uid, projectId)
saveProjectLayout(uid, projectId, layout)

// Storage
uploadProjectFile(uid, projectId, file, fileType)
deleteProjectFile(uid, projectId, fileName)

// Utilities
getErrorMessage(errorCode)
```

---

## 🔧 Backend Setup

### File: `firebase_admin.py`

Core Firebase Admin SDK wrapper. Auto-initializes on import.

```python
from firebase_admin import (
    firebase_admin,
    verify_token,
    create_user,
    get_user,
    get_user_profile,
    update_user_profile,
    create_project,
    get_user_projects,
    get_project,
    update_project,
    delete_project,
    upload_project_file,
    download_project_file,
    delete_storage_file,
)

# Verify token from frontend
decoded_token = firebase_admin.verify_token(token)
if decoded_token:
    uid = decoded_token['uid']
    email = decoded_token['email']

# Create user (server-side)
user = firebase_admin.create_user('user@example.com', 'password', 'Full Name')

# Get user projects
projects = firebase_admin.get_user_projects(uid)
for project in projects:
    print(f"Project: {project['name']}")

# Upload file
url = firebase_admin.upload_project_file(uid, project_id, '/path/to/file.png', 'image')
```

### Files: `auth_routes.py`, `projects_routes.py`, `storage_routes.py`

Pre-built Flask blueprints with complete endpoints. See [API Endpoints](#api-endpoints).

---

## 📊 Database Structure

Firestore collections are organized as follows:

```
users/
├── {uid}/
│   ├── uid
│   ├── email
│   ├── displayName
│   ├── photoURL
│   ├── createdAt
│   ├── updatedAt
│   ├── plan (free|pro|enterprise)
│   ├── projectCount
│   └── projects/ (subcollection)
│       └── {projectId}/
│           ├── id
│           ├── name
│           ├── description
│           ├── layout
│           ├── rooms[]
│           ├── settings
│           ├── files[] (metadata)
│           ├── createdAt
│           ├── updatedAt
│           └── owner (uid)
```

### Firestore Security Rules

Add these rules to your Firestore (Console → Firestore → Rules):

```firestore
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only read/write their own profile
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId;
    }

    // Users can only access their own projects
    match /users/{userId}/projects/{projectId} {
      allow read, write, delete: if request.auth.uid == userId;
    }
  }
}
```

---

## 🔌 API Endpoints

### Authentication Endpoints

#### Verify Token
```
POST /api/auth/verify-token
Body: { "token": "firebase_id_token" }
Response: { "valid": true, "uid": "...", "email": "..." }
```

#### Get User Profile
```
GET /api/auth/user-profile
Headers: Authorization: Bearer {token}
Response: { "uid": "...", "email": "...", "displayName": "...", ... }
```

#### Update User Profile
```
PUT /api/auth/user-profile
Headers: Authorization: Bearer {token}
Body: { "displayName": "New Name", "plan": "pro" }
Response: { "success": true, "message": "Profile updated" }
```

#### Create User (Server-side)
```
POST /api/auth/create-user
Body: { "email": "...", "password": "...", "displayName": "..." }
Response: { "success": true, "uid": "...", "email": "..." }
```

### Projects Endpoints

#### List Projects
```
GET /api/projects
Headers: Authorization: Bearer {token}
Response: [{ "id": "...", "name": "...", ... }]
```

#### Create Project
```
POST /api/projects
Headers: Authorization: Bearer {token}
Body: { "name": "Project Name", "description": "...", "layout": [] }
Response: { "success": true, "id": "project_id" }
```

#### Get Project
```
GET /api/projects/{projectId}
Headers: Authorization: Bearer {token}
Response: { "id": "...", "name": "...", "layout": [...], ... }
```

#### Update Project
```
PUT /api/projects/{projectId}
Headers: Authorization: Bearer {token}
Body: { "name": "New Name", "layout": [...] }
Response: { "success": true, "message": "Project updated" }
```

#### Delete Project
```
DELETE /api/projects/{projectId}
Headers: Authorization: Bearer {token}
Response: { "success": true, "message": "Project deleted" }
```

#### Add Room
```
POST /api/projects/{projectId}/rooms
Headers: Authorization: Bearer {token}
Body: {
  "name": "Living Room",
  "type": "salon",
  "x_pct": 5.0,
  "y_pct": 5.0,
  "w_pct": 38.0,
  "h_pct": 44.0
}
Response: { "success": true, "message": "Room added" }
```

#### Delete Room
```
DELETE /api/projects/{projectId}/rooms/{roomId}
Headers: Authorization: Bearer {token}
Response: { "success": true, "message": "Room deleted" }
```

### Storage Endpoints

#### Upload File
```
POST /api/storage/upload
Headers: Authorization: Bearer {token}
Form Data:
  - file: (binary file)
  - projectId: "project_id"
Response: {
  "success": true,
  "url": "https://storage.googleapis.com/...",
  "fileName": "...",
  "fileType": "image|pdf|export",
  "size": 1024
}
```

#### Download File
```
GET /api/storage/download/{projectId}/{fileName}?type=image|pdf|export
Headers: Authorization: Bearer {token}
Response: (binary file download)
```

#### Delete File
```
DELETE /api/storage/delete/{projectId}/{fileName}?type=image|pdf|export
Headers: Authorization: Bearer {token}
Response: { "success": true, "message": "File deleted" }
```

#### List Project Files
```
GET /api/storage/list/{projectId}
Headers: Authorization: Bearer {token}
Response: [
  {
    "name": "plan.png",
    "type": "image",
    "size": 1024,
    "url": "https://...",
    "uploadedAt": "2024-01-15T..."
  }
]
```

---

## 🔗 Integration with app.py

### Updated app.py with Firebase

```python
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# Import Firebase modules
from firebase_admin import firebase_admin
from auth_routes import init_auth_routes
from projects_routes import init_projects_routes
from storage_routes import init_storage_routes

# Initialize Flask
app = Flask(__name__, static_folder='static')
CORS(app)
os.makedirs('static/uploads', exist_ok=True)

# Initialize Firebase Admin SDK
# Make sure serviceAccountKey.json is in the same directory
firebase_admin.initialize("serviceAccountKey.json")

# Register Firebase routes
init_auth_routes(app)
init_projects_routes(app)
init_storage_routes(app)

# Your existing routes...
@app.route('/')
def index():
    return send_from_directory('static', 'landing.html')

@app.route('/app')
def app_page():
    # Protected: Check for valid token
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    decoded_token = firebase_admin.verify_token(token)
    
    if not decoded_token:
        return jsonify({"error": "Unauthorized"}), 401
    
    return send_from_directory('static', 'index.html')

# Your other existing routes...

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### Full Integration Example

```python
# In app.py, add this endpoint to process uploads with Firebase
from werkzeug.utils import secure_filename

@app.route('/api/analyze-plan', methods=['POST'])
def analyze_plan():
    """
    Analyze electrical plan and save to project
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    decoded_token = firebase_admin.verify_token(token)
    
    if not decoded_token:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    project_id = request.form.get('projectId')
    
    # Your existing analysis logic...
    rooms = analyze_image(file.stream)
    
    # Save to project
    project = firebase_admin.get_project(decoded_token['uid'], project_id)
    project['rooms'] = rooms
    firebase_admin.update_project(decoded_token['uid'], project_id, {
        'rooms': rooms,
        'analysis_date': firebase_admin.firestore.SERVER_TIMESTAMP
    })
    
    # Save file to storage
    temp_path = f"temp_{decoded_token['uid']}_{project_id}.png"
    file.save(temp_path)
    
    try:
        url = firebase_admin.upload_project_file(
            decoded_token['uid'],
            project_id,
            temp_path,
            'image'
        )
        return jsonify({
            "success": True,
            "rooms": rooms,
            "url": url
        })
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

---

## 🧪 Testing

### Test Frontend Authentication

```javascript
// In browser console
import * as Firebase from './firebase-config.js';

// Test sign up
const user = await Firebase.signUpWithEmail('test@example.com', 'testpass123', 'Test User');
console.log('Created user:', user.uid);

// Test sign in
const signedInUser = await Firebase.signInWithEmail('test@example.com', 'testpass123');
console.log('Signed in:', signedInUser.email);

// Test project creation
const projectId = await Firebase.createProject(user.uid, {
  name: 'Test Project',
  description: 'Testing Firebase integration'
});
console.log('Created project:', projectId);
```

### Test Backend Authentication

```python
import requests

# Get token from frontend or create test user
token = "firebase_id_token_here"

# Verify token
response = requests.post(
    'http://localhost:5000/api/auth/verify-token',
    json={'token': token}
)
print(response.json())

# Get user profile
response = requests.get(
    'http://localhost:5000/api/auth/user-profile',
    headers={'Authorization': f'Bearer {token}'}
)
print(response.json())

# Create project
response = requests.post(
    'http://localhost:5000/api/projects',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'name': 'Backend Test Project',
        'description': 'Created via API test'
    }
)
print(response.json())
```

---

## 🆘 Troubleshooting

### Firebase Admin SDK Not Found

```
FileNotFoundError: Firebase credentials file not found: serviceAccountKey.json
```

**Solution:** Download your service account key from Firebase Console and save it as `serviceAccountKey.json` in `/tlp.1/` directory.

### Token Verification Failed

```
Invalid or expired token
```

**Solution:**
- Token may have expired (refresh on frontend)
- Token format incorrect (should be `Bearer {token}`)
- Firebase app not properly initialized

### CORS Errors in Frontend

```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solution:** Already configured with `flask-cors>=4.0.0`. If still failing, check that `CORS(app)` is called in app.py.

### Storage Upload Fails

```
Error uploading file: Insufficient permissions
```

**Solution:** Check Firebase Storage security rules. Default rule should allow authenticated users:

```firestore
match /users/{userId}/projects/{projectId}/{allPaths=**} {
  allow read, write: if request.auth.uid == userId;
}
```

### Firestore Write Fails

```
Error creating project: PERMISSION_DENIED: Missing or insufficient permissions
```

**Solution:** Update Firestore security rules (see [Database Structure](#database-structure) section).

---

## 📚 Additional Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Firebase Admin SDK (Python)](https://firebase.google.com/docs/database/admin/start)
- [Firebase Authentication](https://firebase.google.com/docs/auth)
- [Cloud Firestore](https://firebase.google.com/docs/firestore)
- [Cloud Storage](https://firebase.google.com/docs/storage)

---

## ✅ Checklist

- [ ] Service account key downloaded and saved as `serviceAccountKey.json`
- [ ] `requirements.txt` installed (`pip install -r requirements.txt`)
- [ ] `firebase-config.js` script added to HTML
- [ ] Firebase routes registered in `app.py`
- [ ] Firestore security rules updated
- [ ] Firebase Console enables Email/Password and Google authentication
- [ ] CORS configured in Flask
- [ ] Frontend can sign up/login
- [ ] Backend API endpoints returning 200 status
- [ ] Projects can be created and retrieved
- [ ] Files can be uploaded to storage

---

**Last Updated:** April 22, 2026
**Firebase Project:** stone-a4d71
