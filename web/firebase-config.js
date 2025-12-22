/**
 * Firebase Configuration for Eye-Guard
 * Authentication setup with Email/Password
 */

// Firebase SDK imports (using CDN modules)
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { getAuth } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCbtTZtuBA6nsMYCgNfdpWGBkRtmtbbiv0",
    authDomain: "eye-guard-e7569.firebaseapp.com",
    projectId: "eye-guard-e7569",
    storageBucket: "eye-guard-e7569.firebasestorage.app",
    messagingSenderId: "934426131518",
    appId: "1:934426131518:web:34784655148eb68aef256f",
    measurementId: "G-4GBXE4NKBS"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Export for use in other modules
export { app, auth };
