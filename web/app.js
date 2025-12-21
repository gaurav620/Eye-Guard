/**
 * Eyeguard PWA - Eye Tracking Application
 * Real-time blink detection using MediaPipe FaceLandmarker
 */

// Import MediaPipe Vision using ES modules
import { FaceLandmarker, FilesetResolver } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.8/+esm';

// ============ CONFIG ============
const CONFIG = {
    EAR_THRESHOLD: 0.21,           // Eye Aspect Ratio threshold for blink
    BLINK_CONSEC_FRAMES: 2,        // Consecutive frames for blink detection
    HEALTHY_BLINK_RATE_MIN: 15,    // Healthy range: 15-20 blinks/min
    HEALTHY_BLINK_RATE_MAX: 20,
    BREAK_INTERVAL: 20 * 60 * 1000, // 20 minutes for 20-20-20 rule

    // MediaPipe FaceLandmarker eye indices
    LEFT_EYE: [362, 385, 387, 263, 373, 380],  // p1-p6 for left eye
    RIGHT_EYE: [33, 160, 158, 133, 153, 144],  // p1-p6 for right eye
    LEFT_IRIS: [468, 469, 470, 471, 472],
    RIGHT_IRIS: [473, 474, 475, 476, 477]
};

// ============ STATE ============
let state = {
    isTracking: false,
    stream: null,
    faceLandmarker: null,
    animationFrameId: null,
    videoReady: false,

    // Session data
    sessionStartTime: null,
    blinkCount: 0,
    blinkRateHistory: [],

    // Blink detection
    prevEyeState: 'open',
    closedFrameCount: 0,

    // Break timer
    lastBreakTime: null,
    breakTimerInterval: null
};

// ============ DOM ELEMENTS ============
const elements = {};

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    initElements();
    initEventListeners();
    initPWA();
    console.log('Eyeguard PWA initialized');
});

function initElements() {
    elements.startCameraBtn = document.getElementById('startCameraBtn');
    elements.stopCameraBtn = document.getElementById('stopCameraBtn');
    elements.landingSection = document.getElementById('landingSection');
    elements.trackingSection = document.getElementById('trackingSection');
    elements.videoElement = document.getElementById('videoElement');
    elements.canvasOverlay = document.getElementById('canvasOverlay');
    elements.loadingOverlay = document.getElementById('loadingOverlay');
    elements.sessionTime = document.getElementById('sessionTime');
    elements.blinkCount = document.getElementById('blinkCount');
    elements.blinkRate = document.getElementById('blinkRate');
    elements.blinkRateProgress = document.getElementById('blinkRateProgress');
    elements.earValue = document.getElementById('earValue');
    elements.healthStatus = document.getElementById('healthStatus');
    elements.breakTimer = document.getElementById('breakTimer');
    elements.toast = document.getElementById('toast');
    elements.toastIcon = document.getElementById('toastIcon');
    elements.toastMessage = document.getElementById('toastMessage');
    elements.installBtn = document.getElementById('installBtn');
    elements.installBanner = document.getElementById('installBanner');
    elements.installBannerBtn = document.getElementById('installBannerBtn');
}

function initEventListeners() {
    if (elements.startCameraBtn) {
        elements.startCameraBtn.addEventListener('click', startTracking);
    }
    if (elements.stopCameraBtn) {
        elements.stopCameraBtn.addEventListener('click', stopTracking);
    }
    if (elements.installBtn) {
        elements.installBtn.addEventListener('click', installPWA);
    }
    if (elements.installBannerBtn) {
        elements.installBannerBtn.addEventListener('click', installPWA);
    }
}

// ============ PWA INSTALLATION ============
let deferredPrompt = null;

function initPWA() {
    // Register service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js')
            .then((registration) => {
                console.log('ServiceWorker registered:', registration.scope);
            })
            .catch((error) => {
                console.error('ServiceWorker registration failed:', error);
            });
    }

    // Listen for install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;

        // Show install button
        if (elements.installBtn) {
            elements.installBtn.style.display = 'block';
        }

        // Show install banner after 10 seconds
        setTimeout(() => {
            if (deferredPrompt && elements.installBanner) {
                elements.installBanner.classList.add('show');
            }
        }, 10000);
    });

    // Handle app installed
    window.addEventListener('appinstalled', () => {
        deferredPrompt = null;
        if (elements.installBtn) elements.installBtn.style.display = 'none';
        if (elements.installBanner) elements.installBanner.classList.remove('show');
        showToast('✅ App installed successfully!', 'success');
    });
}

async function installPWA() {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
        console.log('PWA installed');
    }

    deferredPrompt = null;
    if (elements.installBanner) elements.installBanner.classList.remove('show');
}

// ============ CAMERA & TRACKING ============
async function startTracking() {
    console.log('Starting eye tracking...');

    try {
        // Show tracking section
        elements.landingSection.classList.add('hidden');
        elements.trackingSection.classList.remove('hidden');
        elements.loadingOverlay.classList.remove('hidden');

        // Get camera stream
        console.log('Requesting camera access...');
        state.stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'user',
                width: { ideal: 640 },
                height: { ideal: 480 }
            }
        });
        console.log('Camera access granted');

        elements.videoElement.srcObject = state.stream;

        // Wait for video to be ready
        await new Promise((resolve, reject) => {
            elements.videoElement.onloadedmetadata = () => {
                console.log('Video metadata loaded');
                resolve();
            };
            elements.videoElement.onerror = (e) => {
                reject(new Error('Video error: ' + e.message));
            };
            setTimeout(() => reject(new Error('Video load timeout')), 10000);
        });

        await elements.videoElement.play();
        console.log('Video playing');
        state.videoReady = true;

        // Setup canvas
        const { videoWidth, videoHeight } = elements.videoElement;
        elements.canvasOverlay.width = videoWidth || 640;
        elements.canvasOverlay.height = videoHeight || 480;
        console.log(`Canvas size: ${elements.canvasOverlay.width}x${elements.canvasOverlay.height}`);

        // Initialize FaceLandmarker
        console.log('Initializing FaceLandmarker...');
        await initFaceLandmarker();
        console.log('FaceLandmarker ready');

        // Hide loading overlay
        elements.loadingOverlay.classList.add('hidden');

        // Start session
        state.isTracking = true;
        state.sessionStartTime = Date.now();
        state.blinkCount = 0;
        state.lastBreakTime = Date.now();

        // Start timers
        startSessionTimer();
        startBreakTimer();

        // Start detection loop
        detectFrame();

        showToast('👁️ Eye tracking started!', 'success');

    } catch (error) {
        console.error('Error starting camera:', error);
        showToast('❌ Error: ' + error.message, 'error');

        // Reset the UI
        elements.landingSection.classList.remove('hidden');
        elements.trackingSection.classList.add('hidden');

        // Clean up stream if it exists
        if (state.stream) {
            state.stream.getTracks().forEach(track => track.stop());
            state.stream = null;
        }
    }
}

async function initFaceLandmarker() {
    console.log('Loading WASM files...');
    const filesetResolver = await FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.8/wasm'
    );

    console.log('Creating FaceLandmarker...');
    state.faceLandmarker = await FaceLandmarker.createFromOptions(filesetResolver, {
        baseOptions: {
            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
            delegate: 'GPU'
        },
        runningMode: 'VIDEO',
        numFaces: 1,
        minFaceDetectionConfidence: 0.5,
        minFacePresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
        outputFaceBlendshapes: false,
        outputFacialTransformationMatrixes: false
    });

    console.log('FaceLandmarker initialized successfully');
}

function stopTracking() {
    console.log('Stopping eye tracking...');
    state.isTracking = false;
    state.videoReady = false;

    // Stop video stream
    if (state.stream) {
        state.stream.getTracks().forEach(track => track.stop());
        state.stream = null;
    }

    // Cancel animation frame
    if (state.animationFrameId) {
        cancelAnimationFrame(state.animationFrameId);
        state.animationFrameId = null;
    }

    // Stop timers
    if (state.breakTimerInterval) {
        clearInterval(state.breakTimerInterval);
        state.breakTimerInterval = null;
    }

    // Close FaceLandmarker
    if (state.faceLandmarker) {
        try {
            state.faceLandmarker.close();
        } catch (e) {
            console.warn('Error closing FaceLandmarker:', e);
        }
        state.faceLandmarker = null;
    }

    // Calculate session stats
    const duration = state.sessionStartTime
        ? Math.floor((Date.now() - state.sessionStartTime) / 1000)
        : 0;
    const avgRate = duration > 0
        ? (state.blinkCount / (duration / 60)).toFixed(1)
        : 0;

    // Show summary if we had a session
    if (duration > 0) {
        showToast(`Session: ${formatTime(duration)} | ${state.blinkCount} blinks | ${avgRate}/min`, 'success');
    }

    // Reset UI
    elements.landingSection.classList.remove('hidden');
    elements.trackingSection.classList.add('hidden');

    // Reset state
    state.sessionStartTime = null;
    state.blinkCount = 0;
    state.prevEyeState = 'open';
    state.closedFrameCount = 0;
}

// ============ DETECTION LOOP ============
function detectFrame() {
    if (!state.isTracking || !state.faceLandmarker || !state.videoReady) {
        console.log('Detection stopped: tracking=' + state.isTracking + ', landmarker=' + !!state.faceLandmarker + ', videoReady=' + state.videoReady);
        return;
    }

    try {
        const video = elements.videoElement;
        const canvas = elements.canvasOverlay;
        const ctx = canvas.getContext('2d');

        // Make sure video is playing and has data
        if (video.readyState < 2) {
            state.animationFrameId = requestAnimationFrame(detectFrame);
            return;
        }

        // Run detection
        const startTime = performance.now();
        const results = state.faceLandmarker.detectForVideo(video, startTime);

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (results && results.faceLandmarks && results.faceLandmarks.length > 0) {
            const landmarks = results.faceLandmarks[0];

            // Calculate EAR
            const leftEAR = calculateEAR(landmarks, CONFIG.LEFT_EYE);
            const rightEAR = calculateEAR(landmarks, CONFIG.RIGHT_EYE);
            const avgEAR = (leftEAR + rightEAR) / 2;

            // Update EAR display
            if (elements.earValue) {
                elements.earValue.textContent = avgEAR.toFixed(3);
            }

            // Detect blink
            detectBlink(avgEAR);

            // Draw eye landmarks
            drawEyeLandmarks(ctx, landmarks, canvas.width, canvas.height);
        }

        // Continue loop
        state.animationFrameId = requestAnimationFrame(detectFrame);

    } catch (error) {
        console.error('Detection error:', error);
        state.animationFrameId = requestAnimationFrame(detectFrame);
    }
}

// ============ EAR CALCULATION ============
function calculateEAR(landmarks, eyeIndices) {
    try {
        const p1 = landmarks[eyeIndices[0]];
        const p2 = landmarks[eyeIndices[1]];
        const p3 = landmarks[eyeIndices[2]];
        const p4 = landmarks[eyeIndices[3]];
        const p5 = landmarks[eyeIndices[4]];
        const p6 = landmarks[eyeIndices[5]];

        const vertical1 = distance(p2, p6);
        const vertical2 = distance(p3, p5);
        const horizontal = distance(p1, p4);

        if (horizontal === 0) return 0.3;
        return (vertical1 + vertical2) / (2 * horizontal);
    } catch (e) {
        return 0.3;
    }
}

function distance(p1, p2) {
    if (!p1 || !p2) return 0;
    return Math.sqrt(
        Math.pow(p2.x - p1.x, 2) +
        Math.pow(p2.y - p1.y, 2) +
        Math.pow((p2.z || 0) - (p1.z || 0), 2)
    );
}

// ============ BLINK DETECTION ============
function detectBlink(ear) {
    const isClosed = ear < CONFIG.EAR_THRESHOLD;

    if (isClosed) {
        state.closedFrameCount++;
    } else {
        if (state.prevEyeState === 'closed' && state.closedFrameCount >= CONFIG.BLINK_CONSEC_FRAMES) {
            state.blinkCount++;
            if (elements.blinkCount) {
                elements.blinkCount.textContent = state.blinkCount;
            }

            const blinkCard = elements.blinkCount?.closest('.stat-card');
            if (blinkCard) {
                blinkCard.classList.add('blink-detected');
                setTimeout(() => blinkCard.classList.remove('blink-detected'), 500);
            }

            updateBlinkRate();
        }
        state.closedFrameCount = 0;
    }

    state.prevEyeState = isClosed ? 'closed' : 'open';
}

// ============ STATS UPDATES ============
function updateBlinkRate() {
    if (!state.sessionStartTime) return;

    const elapsedMinutes = (Date.now() - state.sessionStartTime) / 60000;
    if (elapsedMinutes < 0.1) return;

    const rate = state.blinkCount / elapsedMinutes;
    if (elements.blinkRate) {
        elements.blinkRate.textContent = rate.toFixed(1);
    }

    const percentage = Math.min(100, (rate / CONFIG.HEALTHY_BLINK_RATE_MAX) * 100);
    if (elements.blinkRateProgress) {
        elements.blinkRateProgress.style.width = `${percentage}%`;
    }

    updateHealthStatus(rate);
}

function updateHealthStatus(rate) {
    const status = elements.healthStatus;
    if (!status) return;

    if (rate >= CONFIG.HEALTHY_BLINK_RATE_MIN && rate <= CONFIG.HEALTHY_BLINK_RATE_MAX) {
        status.className = 'health-status healthy';
        status.textContent = '✅ Eyes Healthy';
    } else if (rate < CONFIG.HEALTHY_BLINK_RATE_MIN) {
        status.className = 'health-status warning';
        status.textContent = '⚠️ Blink More Often!';
    } else {
        status.className = 'health-status danger';
        status.textContent = '⚠️ High Blink Rate';
    }
}

function startSessionTimer() {
    const updateTimer = () => {
        if (!state.sessionStartTime || !state.isTracking) return;

        const elapsed = Math.floor((Date.now() - state.sessionStartTime) / 1000);
        if (elements.sessionTime) {
            elements.sessionTime.textContent = formatTime(elapsed);
        }

        updateBlinkRate();
        requestAnimationFrame(updateTimer);
    };

    updateTimer();
}

function startBreakTimer() {
    state.breakTimerInterval = setInterval(() => {
        if (!state.lastBreakTime || !state.isTracking) return;

        const elapsed = Date.now() - state.lastBreakTime;
        const remaining = Math.max(0, CONFIG.BREAK_INTERVAL - elapsed);

        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        if (elements.breakTimer) {
            elements.breakTimer.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }

        if (remaining === 0) {
            showBreakReminder();
            state.lastBreakTime = Date.now();
        }
    }, 1000);
}

function showBreakReminder() {
    showToast('⏰ Time for a break! Look 20ft away for 20 seconds', 'warning');

    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Eyeguard - Break Time!', {
            body: 'Look at something 20 feet away for 20 seconds',
            icon: 'icons/icon-192x192.png'
        });
    }
}

// ============ DRAWING ============
function drawEyeLandmarks(ctx, landmarks, width, height) {
    ctx.fillStyle = '#10b981';
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;

    drawEye(ctx, landmarks, CONFIG.LEFT_EYE, width, height);
    drawEye(ctx, landmarks, CONFIG.RIGHT_EYE, width, height);
    drawIris(ctx, landmarks, CONFIG.LEFT_IRIS, width, height);
    drawIris(ctx, landmarks, CONFIG.RIGHT_IRIS, width, height);
}

function drawEye(ctx, landmarks, indices, width, height) {
    ctx.beginPath();

    indices.forEach((idx, i) => {
        if (idx >= landmarks.length) return;
        const x = landmarks[idx].x * width;
        const y = landmarks[idx].y * height;

        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }

        ctx.fillRect(x - 2, y - 2, 4, 4);
    });

    ctx.closePath();
    ctx.stroke();
}

function drawIris(ctx, landmarks, indices, width, height) {
    if (!indices || indices.length === 0) return;

    ctx.fillStyle = '#3b82f6';

    let centerX = 0, centerY = 0;
    let count = 0;
    indices.forEach(idx => {
        if (idx < landmarks.length) {
            centerX += landmarks[idx].x * width;
            centerY += landmarks[idx].y * height;
            count++;
        }
    });

    if (count === 0) return;
    centerX /= count;
    centerY /= count;

    ctx.beginPath();
    ctx.arc(centerX, centerY, 4, 0, 2 * Math.PI);
    ctx.fill();
}

// ============ UTILITIES ============
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function showToast(message, type = 'info') {
    if (!elements.toast || !elements.toastIcon || !elements.toastMessage) return;

    const icons = {
        success: '✅',
        warning: '⚠️',
        error: '❌',
        info: 'ℹ️'
    };

    elements.toastIcon.textContent = icons[type] || icons.info;
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast ${type} show`;

    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 4000);
}
