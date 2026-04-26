# Firebase Quick Start — Next Steps

**Your Firebase Project:** `stone-a4d71`

## ⚡ Essential Setup (5 minutes)

### 1. Download Service Account Key

1. Open [Firebase Console](https://console.firebase.google.com/project/stone-a4d71)
2. Click ⚙️ **Settings** (top-left menu)
3. Go to **Service Accounts** tab
4. Click **Generate New Private Key** (big blue button, bottom-right)
5. Save the downloaded JSON file as:
   ```
   d:\TLP_builder\tlp.1\serviceAccountKey.json
   ```

### 2. Install Dependencies

```bash

pip install -r requirements.txt
```

This installs:
- `firebase-admin` (Python backend)
- `google-cloud-firestore` (Database)
- `google-cloud-storage` (File storage)

### 3. Update app.py

Add this to your `app.py` at the top:

```python
# Firebase imports (add after existing imports)
from firebase_admin import firebase_admin
from auth_routes import init_auth_routes
from projects_routes import init_projects_routes
from storage_routes import init_storage_routes

# After creating Flask app, add:
firebase_admin.initialize("serviceAccountKey.json")

# Before app.run(), add:
init_auth_routes(app)
init_projects_routes(app)
init_storage_routes(app)
```

### 4. Update landing.html

Replace the Firebase config section (lines 276-282) with:

```html
<script type="module">
  import * as Firebase from './firebase-config.js';
  
  // Firebase is now ready to use!
  // Sign up example:
  async function signUpExample() {
    try {
      const user = await Firebase.signUpWithEmail(
        'user@example.com',
        'password123',
        'User Name'
      );
      console.log('User created:', user.uid);
    } catch (error) {
      console.error('Error:', Firebase.getErrorMessage(error.code));
    }
  }
</script>
```

### 5. Configure Firebase Console

In [Firebase Console](https://console.firebase.google.com/project/stone-a4d71):

1. **Authentication:**
   - Go to **Authentication** → **Sign-in method**
   - Enable: ✅ **Email/Password**
   - Enable: ✅ **Google**
   - Save

2. **Firestore:**
   - Go to **Firestore Database**
   - Click **Create Database**
   - Select **Start in test mode** (or production with rules below)
   - Choose region: `europe-west1` or closest to you
   - Create

3. **Firestore Security Rules:**
   - Go to **Firestore** → **Rules** tab
   - Replace with this:
   ```firestore
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /users/{userId} {
         allow read, write: if request.auth.uid == userId;
       }
       match /users/{userId}/projects/{projectId} {
         allow read, write, delete: if request.auth.uid == userId;
       }
     }
   }
   ```
   - Publish

4. **Storage:**
   - Go to **Storage** → **Rules** tab
   - Replace with this:
   ```
   rules_version = '2';
   service firebase.storage {
     match /b/{bucket}/o {
       match /users/{userId}/projects/{projectId}/{allPaths=**} {
         allow read, write: if request.auth.uid == userId;
       }
     }
   }
   ```
   - Publish

## 📁 New Files Created

- ✅ `static/firebase-config.js` — Frontend SDK wrapper
- ✅ `firebase_admin.py` — Backend Admin SDK
- ✅ `auth_routes.py` — Authentication endpoints
- ✅ `projects_routes.py` — Project management endpoints
- ✅ `storage_routes.py` — File upload/download endpoints
- ✅ `FIREBASE_SETUP.md` — Complete documentation
- ✅ `requirements.txt` — Updated with Firebase packages

## 🧪 Quick Test

### Frontend
```javascript
// In browser console at https://localhost:5000
import * as Firebase from './firebase-config.js';
await Firebase.signUpWithEmail('test@example.com', 'password', 'Test');
```

### Backend
```bash
curl -X POST http://localhost:5000/api/auth/verify-token \
  -H "Content-Type: application/json" \
  -d '{"token":"your_firebase_token_here"}'
```

## 🔗 Key Endpoints Ready to Use

```
POST   /api/auth/verify-token           → Verify Firebase token
GET    /api/auth/user-profile           → Get user profile
PUT    /api/auth/user-profile           → Update profile
GET    /api/projects                    → List projects
POST   /api/projects                    → Create project
GET    /api/projects/{id}               → Get project
PUT    /api/projects/{id}               → Update project
DELETE /api/projects/{id}               → Delete project
POST   /api/storage/upload              → Upload file
GET    /api/storage/list/{projectId}    → List files
DELETE /api/storage/delete/{id}/{file}  → Delete file
```

## 📞 Need Help?

See `FIREBASE_SETUP.md` for:
- Complete API reference
- Database structure
- Integration examples
- Troubleshooting guide

---

**Everything is ready!** Just download the service account key and run your app.
