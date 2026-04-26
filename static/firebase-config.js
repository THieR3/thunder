/**
 * Firebase Configuration for ElecPlan Frontend
 * Project: stone-a4d71
 * 
 * This file is loaded via module import in landing.html
 * and contains all necessary Firebase initialization code.
 */

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  GoogleAuthProvider,
  signInWithPopup,
  onAuthStateChanged,
  updateProfile,
  signOut,
} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js';
import {
  getFirestore,
  doc,
  setDoc,
  getDoc,
  updateDoc,
  deleteDoc,
  collection,
  query,
  where,
  getDocs,
  serverTimestamp,
  arrayUnion,
  arrayRemove,
} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js';
import {
  getStorage,
  ref,
  uploadBytes,
  downloadURL,
  deleteObject,
} from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-storage.js';

// ════════════════════════════════════════════════════════
// FIREBASE CONFIGURATION
// Project: stone-a4d71 (ElecPlan)
// ════════════════════════════════════════════════════════

export const firebaseConfig = {
  apiKey: 'AIzaSyAnuKRJpc8nzt30QM3OGBbRdxAJPllfom0',
  authDomain: 'stone-a4d71.firebaseapp.com',
  projectId: 'stone-a4d71',
  storageBucket: 'stone-a4d71.firebasestorage.app',
  messagingSenderId: '258565161026',
  appId: '1:258565161026:web:b428513f8fcb693d422ddb',
  measurementId: 'G-KHRCV7GTF0',
};

// ════════════════════════════════════════════════════════
// INITIALIZE FIREBASE SERVICES
// ════════════════════════════════════════════════════════

const fbApp = initializeApp(firebaseConfig);

export const auth = getAuth(fbApp);
export const db = getFirestore(fbApp);
export const storage = getStorage(fbApp);
export const googleProvider = new GoogleAuthProvider();

// Configure Google sign-in scopes
googleProvider.addScope('profile');
googleProvider.addScope('email');

// ════════════════════════════════════════════════════════
// AUTHENTICATION FUNCTIONS
// ════════════════════════════════════════════════════════

/**
 * Sign up with email/password
 */
export async function signUpWithEmail(email, password, displayName) {
  try {
    const credential = await createUserWithEmailAndPassword(auth, email, password);
    await updateProfile(credential.user, { displayName });
    await ensureUserProfile(credential.user, displayName);
    return credential.user;
  } catch (error) {
    throw error;
  }
}

/**
 * Sign in with email/password
 */
export async function signInWithEmail(email, password) {
  try {
    const credential = await signInWithEmailAndPassword(auth, email, password);
    return credential.user;
  } catch (error) {
    throw error;
  }
}

/**
 * Sign in with Google
 */
export async function signInWithGoogle() {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    await ensureUserProfile(result.user);
    return result.user;
  } catch (error) {
    throw error;
  }
}

/**
 * Send password reset email
 */
export async function resetPassword(email) {
  try {
    await sendPasswordResetEmail(auth, email);
  } catch (error) {
    throw error;
  }
}

/**
 * Sign out
 */
export async function signOutUser() {
  try {
    await signOut(auth);
  } catch (error) {
    throw error;
  }
}

/**
 * Get current user
 */
export function getCurrentUser() {
  return auth.currentUser;
}

/**
 * Listen to auth state changes
 */
export function onAuthChange(callback) {
  return onAuthStateChanged(auth, callback);
}

// ════════════════════════════════════════════════════════
// FIRESTORE FUNCTIONS
// ════════════════════════════════════════════════════════

/**
 * Ensure user profile exists in Firestore
 */
export async function ensureUserProfile(user, displayName = null) {
  try {
    const userRef = doc(db, 'users', user.uid);
    const userSnap = await getDoc(userRef);

    if (!userSnap.exists()) {
      await setDoc(userRef, {
        uid: user.uid,
        email: user.email,
        displayName: displayName || user.displayName || user.email.split('@')[0],
        photoURL: user.photoURL || null,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
        plan: 'free',
        projects: [],
        projectCount: 0,
      });
    }
  } catch (error) {
    console.error('Error ensuring user profile:', error);
    throw error;
  }
}

/**
 * Update user profile
 */
export async function updateUserProfile(uid, data) {
  try {
    const userRef = doc(db, 'users', uid);
    await updateDoc(userRef, {
      ...data,
      updatedAt: serverTimestamp(),
    });
  } catch (error) {
    console.error('Error updating user profile:', error);
    throw error;
  }
}

/**
 * Get user profile
 */
export async function getUserProfile(uid) {
  try {
    const userRef = doc(db, 'users', uid);
    const userSnap = await getDoc(userRef);
    return userSnap.exists() ? userSnap.data() : null;
  } catch (error) {
    console.error('Error getting user profile:', error);
    throw error;
  }
}

/**
 * Create a new project
 */
export async function createProject(uid, projectData) {
  try {
    const projectRef = doc(collection(db, 'users', uid, 'projects'));
    const projectId = projectRef.id;

    await setDoc(projectRef, {
      id: projectId,
      ...projectData,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
      owner: uid,
    });

    // Update user's project count
    const userRef = doc(db, 'users', uid);
    await updateDoc(userRef, {
      projectCount: (await getUserProfile(uid)).projectCount + 1,
      projects: arrayUnion(projectId),
    });

    return projectId;
  } catch (error) {
    console.error('Error creating project:', error);
    throw error;
  }
}

/**
 * Get user's projects
 */
export async function getUserProjects(uid) {
  try {
    const projectsRef = collection(db, 'users', uid, 'projects');
    const q = query(projectsRef);
    const querySnapshot = await getDocs(q);
    return querySnapshot.docs.map((d) => d.data());
  } catch (error) {
    console.error('Error getting projects:', error);
    throw error;
  }
}

/**
 * Get single project
 */
export async function getProject(uid, projectId) {
  try {
    const projectRef = doc(db, 'users', uid, 'projects', projectId);
    const projectSnap = await getDoc(projectRef);
    return projectSnap.exists() ? projectSnap.data() : null;
  } catch (error) {
    console.error('Error getting project:', error);
    throw error;
  }
}

/**
 * Update project
 */
export async function updateProject(uid, projectId, data) {
  try {
    const projectRef = doc(db, 'users', uid, 'projects', projectId);
    await updateDoc(projectRef, {
      ...data,
      updatedAt: serverTimestamp(),
    });
  } catch (error) {
    console.error('Error updating project:', error);
    throw error;
  }
}

/**
 * Delete project
 */
export async function deleteProject(uid, projectId) {
  try {
    const projectRef = doc(db, 'users', uid, 'projects', projectId);
    await deleteDoc(projectRef);

    // Update user's project list
    const userRef = doc(db, 'users', uid);
    await updateDoc(userRef, {
      projects: arrayRemove(projectId),
      projectCount: (await getUserProfile(uid)).projectCount - 1,
    });
  } catch (error) {
    console.error('Error deleting project:', error);
    throw error;
  }
}

/**
 * Save project drawing/layout
 */
export async function saveProjectLayout(uid, projectId, layout) {
  try {
    const projectRef = doc(db, 'users', uid, 'projects', projectId);
    await updateDoc(projectRef, {
      layout: layout,
      updatedAt: serverTimestamp(),
    });
  } catch (error) {
    console.error('Error saving layout:', error);
    throw error;
  }
}

// ════════════════════════════════════════════════════════
// STORAGE FUNCTIONS
// ════════════════════════════════════════════════════════

/**
 * Upload project file (image/PDF)
 * @param {string} uid - User ID
 * @param {string} projectId - Project ID
 * @param {File} file - File to upload
 * @param {string} fileType - 'image', 'pdf', or 'export'
 * @returns {Promise<string>} Download URL
 */
export async function uploadProjectFile(uid, projectId, file, fileType = 'image') {
  try {
    const timestamp = Date.now();
    const fileExtension = file.name.split('.').pop();
    const fileName = `${fileType}-${timestamp}.${fileExtension}`;

    const storageRef = ref(storage, `users/${uid}/projects/${projectId}/${fileName}`);
    const snapshot = await uploadBytes(storageRef, file);
    const downloadUrl = await downloadURL(snapshot.ref);

    // Save file metadata to Firestore
    const projectRef = doc(db, 'users', uid, 'projects', projectId);
    await updateDoc(projectRef, {
      files: arrayUnion({
        name: file.name,
        type: fileType,
        size: file.size,
        url: downloadUrl,
        uploadedAt: serverTimestamp(),
      }),
    });

    return downloadUrl;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
}

/**
 * Delete project file from storage
 */
export async function deleteProjectFile(uid, projectId, fileName) {
  try {
    const fileRef = ref(storage, `users/${uid}/projects/${projectId}/${fileName}`);
    await deleteObject(fileRef);

    // Remove from Firestore
    const projectRef = doc(db, 'users', uid, 'projects', projectId);
    const projectSnap = await getDoc(projectRef);
    const files = projectSnap.data().files || [];
    const updatedFiles = files.filter((f) => f.name !== fileName);

    await updateDoc(projectRef, { files: updatedFiles });
  } catch (error) {
    console.error('Error deleting file:', error);
    throw error;
  }
}

// ════════════════════════════════════════════════════════
// ERROR HANDLING
// ════════════════════════════════════════════════════════

/**
 * Firebase error message localization (French)
 */
export function getErrorMessage(errorCode) {
  const errorMessages = {
    'auth/user-not-found': 'Aucun compte avec cet email.',
    'auth/wrong-password': 'Mot de passe incorrect.',
    'auth/email-already-in-use': 'Cet email est déjà utilisé.',
    'auth/weak-password': 'Le mot de passe doit contenir au moins 6 caractères.',
    'auth/invalid-email': 'Adresse email invalide.',
    'auth/too-many-requests': 'Trop de tentatives. Réessayez dans quelques minutes.',
    'auth/popup-closed-by-user': 'Connexion annulée.',
    'auth/network-request-failed': 'Erreur réseau. Vérifiez votre connexion.',
    'auth/invalid-api-key': 'Configuration Firebase incorrecte. Vérifiez vos clés.',
    'auth/operation-not-allowed': 'Cette méthode de connexion n\'est pas activée.',
  };
  return (
    errorMessages[errorCode] || 'Une erreur est survenue. Réessayez plus tard.'
  );
}

// ════════════════════════════════════════════════════════
// EXPORT ALL FIREBASE INSTANCES
// ════════════════════════════════════════════════════════

export default {
  firebaseConfig,
  auth,
  db,
  storage,
  googleProvider,
  signUpWithEmail,
  signInWithEmail,
  signInWithGoogle,
  resetPassword,
  signOutUser,
  getCurrentUser,
  onAuthChange,
  ensureUserProfile,
  updateUserProfile,
  getUserProfile,
  createProject,
  getUserProjects,
  getProject,
  updateProject,
  deleteProject,
  saveProjectLayout,
  uploadProjectFile,
  deleteProjectFile,
  getErrorMessage,
};
