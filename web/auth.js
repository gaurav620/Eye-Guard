/**
 * Eye-Guard Authentication Module
 * Handles Sign Up, Sign In, Password Reset, and Session Management
 */

import { auth } from './firebase-config.js';
import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut as firebaseSignOut,
    sendPasswordResetEmail,
    sendEmailVerification,
    onAuthStateChanged,
    updateProfile
} from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';

// ============ SIGN UP ============
/**
 * Create a new user account with email and password
 * @param {string} email - User's email address
 * @param {string} password - User's password (min 6 characters)
 * @param {string} displayName - User's display name (optional)
 * @returns {Promise<Object>} - Result with success status and user data or error
 */
export async function signUp(email, password, displayName = '') {
    try {
        // Create the user account
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        // Set display name if provided
        if (displayName) {
            await updateProfile(user, { displayName });
        }

        // Send email verification
        await sendEmailVerification(user);

        return {
            success: true,
            user: {
                uid: user.uid,
                email: user.email,
                displayName: user.displayName || email.split('@')[0],
                emailVerified: user.emailVerified
            },
            message: 'Account created! Please check your email to verify your account.'
        };
    } catch (error) {
        return {
            success: false,
            error: getErrorMessage(error.code)
        };
    }
}

// ============ SIGN IN ============
/**
 * Sign in an existing user with email and password
 * @param {string} email - User's email address
 * @param {string} password - User's password
 * @returns {Promise<Object>} - Result with success status and user data or error
 */
export async function signIn(email, password) {
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;

        return {
            success: true,
            user: {
                uid: user.uid,
                email: user.email,
                displayName: user.displayName || email.split('@')[0],
                emailVerified: user.emailVerified
            },
            message: 'Login successful!'
        };
    } catch (error) {
        return {
            success: false,
            error: getErrorMessage(error.code)
        };
    }
}

// ============ SIGN OUT ============
/**
 * Sign out the current user
 * @returns {Promise<Object>} - Result with success status
 */
export async function signOut() {
    try {
        await firebaseSignOut(auth);
        return {
            success: true,
            message: 'Logged out successfully!'
        };
    } catch (error) {
        return {
            success: false,
            error: getErrorMessage(error.code)
        };
    }
}

// ============ PASSWORD RESET ============
/**
 * Send a password reset email to the user
 * @param {string} email - User's email address
 * @returns {Promise<Object>} - Result with success status
 */
export async function resetPassword(email) {
    try {
        await sendPasswordResetEmail(auth, email);
        return {
            success: true,
            message: 'Password reset email sent! Check your inbox.'
        };
    } catch (error) {
        return {
            success: false,
            error: getErrorMessage(error.code)
        };
    }
}

// ============ RESEND VERIFICATION ============
/**
 * Resend verification email to current user
 * @returns {Promise<Object>} - Result with success status
 */
export async function resendVerificationEmail() {
    try {
        const user = auth.currentUser;
        if (user) {
            await sendEmailVerification(user);
            return {
                success: true,
                message: 'Verification email sent!'
            };
        }
        return {
            success: false,
            error: 'No user logged in'
        };
    } catch (error) {
        return {
            success: false,
            error: getErrorMessage(error.code)
        };
    }
}

// ============ AUTH STATE OBSERVER ============
/**
 * Listen for authentication state changes
 * @param {Function} callback - Function to call when auth state changes
 * @returns {Function} - Unsubscribe function
 */
export function onAuthChange(callback) {
    return onAuthStateChanged(auth, (user) => {
        if (user) {
            callback({
                isLoggedIn: true,
                user: {
                    uid: user.uid,
                    email: user.email,
                    displayName: user.displayName || user.email.split('@')[0],
                    emailVerified: user.emailVerified
                }
            });
        } else {
            callback({
                isLoggedIn: false,
                user: null
            });
        }
    });
}

// ============ GET CURRENT USER ============
/**
 * Get the currently logged in user
 * @returns {Object|null} - Current user data or null
 */
export function getCurrentUser() {
    const user = auth.currentUser;
    if (user) {
        return {
            uid: user.uid,
            email: user.email,
            displayName: user.displayName || user.email.split('@')[0],
            emailVerified: user.emailVerified
        };
    }
    return null;
}

// ============ CHECK AUTH STATUS ============
/**
 * Check if user is logged in (for page protection)
 * @returns {Promise<boolean>} - True if user is logged in
 */
export function checkAuth() {
    return new Promise((resolve) => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            unsubscribe();
            resolve(!!user);
        });
    });
}

// ============ ERROR MESSAGES ============
/**
 * Convert Firebase error codes to user-friendly messages
 * @param {string} errorCode - Firebase error code
 * @returns {string} - User-friendly error message
 */
function getErrorMessage(errorCode) {
    const errorMessages = {
        'auth/email-already-in-use': 'This email is already registered. Try signing in instead.',
        'auth/invalid-email': 'Please enter a valid email address.',
        'auth/operation-not-allowed': 'Email/password sign-in is not enabled.',
        'auth/weak-password': 'Password should be at least 6 characters.',
        'auth/user-disabled': 'This account has been disabled.',
        'auth/user-not-found': 'No account found with this email.',
        'auth/wrong-password': 'Incorrect password. Please try again.',
        'auth/invalid-credential': 'Invalid email or password.',
        'auth/too-many-requests': 'Too many attempts. Please try again later.',
        'auth/network-request-failed': 'Network error. Check your connection.',
        'auth/popup-closed-by-user': 'Sign-in popup was closed.',
        'auth/requires-recent-login': 'Please log in again to complete this action.'
    };

    return errorMessages[errorCode] || 'An error occurred. Please try again.';
}
