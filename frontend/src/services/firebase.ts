import { initializeApp } from "firebase/app";
import {
  createUserWithEmailAndPassword,
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  type User,
} from "firebase/auth";
import { ref } from "vue";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const user = ref<User | null>(auth.currentUser);
const authReady = ref(false);

onAuthStateChanged(auth, (nextUser) => {
  user.value = nextUser;
  authReady.value = true;
});

async function login(email: string, password: string) {
  return signInWithEmailAndPassword(auth, email, password);
}

async function loginWithGoogle() {
  const provider = new GoogleAuthProvider();
  return signInWithPopup(auth, provider);
}

async function register(email: string, password: string) {
  return createUserWithEmailAndPassword(auth, email, password);
}

async function logout() {
  return signOut(auth);
}

async function getIdToken() {
  if (!auth.currentUser) {
    return null;
  }
  return auth.currentUser.getIdToken();
}

export { auth, user, authReady, login, loginWithGoogle, register, logout, getIdToken };
