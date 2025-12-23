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
    BREAK_DURATION: 20 * 1000,     // 20 seconds for break

    // MediaPipe FaceLandmarker eye indices
    LEFT_EYE: [362, 385, 387, 263, 373, 380],  // p1-p6 for left eye
    RIGHT_EYE: [33, 160, 158, 133, 153, 144],  // p1-p6 for right eye
    LEFT_IRIS: [468, 469, 470, 471, 472],
    RIGHT_IRIS: [473, 474, 475, 476, 477],

    // Health Analysis Thresholds
    FATIGUE_THRESHOLD_MILD: 0.8,   // 80% of initial blink rate
    FATIGUE_THRESHOLD_HIGH: 0.6,   // 60% of initial blink rate
    EYE_STRAIN_WEIGHTS: {
        blinkRate: 0.4,            // 40% weight for blink rate
        sessionDuration: 0.3,      // 30% weight for duration
        breakCompliance: 0.3       // 30% weight for taking breaks
    }
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
    breakTimerInterval: null,

    // Health Analysis (NEW)
    initialBlinkRate: null,      // First 2 minutes avg blink rate
    eyeStrainScore: 100,         // 0-100 (100 = healthy)
    fatigueLevel: 'low',         // low, medium, high
    breaksTaken: 0,
    breaksReminded: 0,
    earHistory: [],              // Last 100 EAR values for trend
    isOnBreak: false,
    breakCountdown: 0
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

        // Request notification permission for break reminders
        if ('Notification' in window && Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            console.log('Notification permission:', permission);
        }

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

    // Save session to history before resetting
    if (duration > 60) {
        saveSessionToHistory();
    }

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

    // Update health analysis every 30 seconds
    if (Math.floor(elapsedMinutes * 2) !== state._lastHealthUpdate) {
        state._lastHealthUpdate = Math.floor(elapsedMinutes * 2);
        calculateEyeStrainScore();
        detectFatigueLevel();
    }
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
    // Use the new overlay system
    showBreakOverlay();

    // Send browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification('👁️ Eye-Guard - Break Time!', {
            body: '⏰ 20-20-20 Rule: Look at something 20 feet away for 20 seconds.\n\nYour eyes will thank you!',
            icon: 'icons/icon-192x192.png',
            badge: 'icons/icon-72x72.png',
            tag: 'eye-break-reminder',
            requireInteraction: true,
            vibrate: [200, 100, 200]
        });

        notification.onclick = () => {
            window.focus();
            notification.close();
        };

        // Auto-close after 30 seconds
        setTimeout(() => notification.close(), 30000);
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

// ============ HEALTH ANALYSIS ============
function calculateEyeStrainScore() {
    if (!state.sessionStartTime) return 100;

    const elapsedMinutes = (Date.now() - state.sessionStartTime) / 60000;
    if (elapsedMinutes < 1) return 100;

    // Calculate current blink rate
    const currentBlinkRate = state.blinkCount / elapsedMinutes;

    // 1. Blink Rate Score (40%)
    let blinkScore = 100;
    if (currentBlinkRate < CONFIG.HEALTHY_BLINK_RATE_MIN) {
        blinkScore = Math.max(0, (currentBlinkRate / CONFIG.HEALTHY_BLINK_RATE_MIN) * 100);
    } else if (currentBlinkRate > CONFIG.HEALTHY_BLINK_RATE_MAX * 1.5) {
        blinkScore = 70; // Too high can indicate irritation
    }

    // 2. Session Duration Score (30%)
    let durationScore = 100;
    if (elapsedMinutes > 60) {
        durationScore = Math.max(30, 100 - (elapsedMinutes - 60) * 2);
    } else if (elapsedMinutes > 30) {
        durationScore = 100 - (elapsedMinutes - 30);
    }

    // 3. Break Compliance Score (30%)
    let breakScore = 100;
    if (state.breaksReminded > 0) {
        breakScore = Math.min(100, (state.breaksTaken / state.breaksReminded) * 100);
    }

    // Weighted average
    const totalScore = Math.round(
        blinkScore * CONFIG.EYE_STRAIN_WEIGHTS.blinkRate +
        durationScore * CONFIG.EYE_STRAIN_WEIGHTS.sessionDuration +
        breakScore * CONFIG.EYE_STRAIN_WEIGHTS.breakCompliance
    );

    state.eyeStrainScore = Math.max(0, Math.min(100, totalScore));
    updateHealthDisplay();
    return state.eyeStrainScore;
}

function detectFatigueLevel() {
    const elapsedMinutes = (Date.now() - state.sessionStartTime) / 60000;
    if (elapsedMinutes < 2) return 'low';

    const currentBlinkRate = state.blinkCount / elapsedMinutes;

    // Set initial blink rate after 2 minutes
    if (!state.initialBlinkRate && elapsedMinutes >= 2) {
        state.initialBlinkRate = currentBlinkRate;
    }

    if (state.initialBlinkRate) {
        const ratio = currentBlinkRate / state.initialBlinkRate;
        if (ratio < CONFIG.FATIGUE_THRESHOLD_HIGH) {
            state.fatigueLevel = 'high';
        } else if (ratio < CONFIG.FATIGUE_THRESHOLD_MILD) {
            state.fatigueLevel = 'medium';
        } else {
            state.fatigueLevel = 'low';
        }
    }

    return state.fatigueLevel;
}

function updateHealthDisplay() {
    const scoreEl = document.getElementById('eyeStrainScore');
    const fatigueEl = document.getElementById('fatigueLevel');
    const meterFill = document.getElementById('strainMeterFill');

    if (scoreEl) {
        scoreEl.textContent = state.eyeStrainScore;
        scoreEl.className = 'health-score-value ' + getScoreClass(state.eyeStrainScore);
    }

    if (meterFill) {
        meterFill.style.width = `${state.eyeStrainScore}%`;
        meterFill.className = 'strain-meter-fill ' + getScoreClass(state.eyeStrainScore);
    }

    if (fatigueEl) {
        const fatigueIcons = { low: '😊', medium: '😐', high: '😫' };
        const fatigueLabels = { low: 'Low Fatigue', medium: 'Moderate Fatigue', high: 'High Fatigue' };
        fatigueEl.textContent = `${fatigueIcons[state.fatigueLevel]} ${fatigueLabels[state.fatigueLevel]}`;
        fatigueEl.className = 'fatigue-indicator fatigue-' + state.fatigueLevel;
    }
}

function getScoreClass(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'moderate';
    return 'poor';
}

// ============ ENHANCED BREAK SYSTEM ============
function showBreakOverlay() {
    state.isOnBreak = true;
    state.breakCountdown = CONFIG.BREAK_DURATION / 1000;
    state.breaksReminded++;

    // Create break overlay if not exists
    let overlay = document.getElementById('breakOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'breakOverlay';
        overlay.className = 'break-overlay';
        overlay.innerHTML = `
            <div class="break-content">
                <div class="break-icon">👀</div>
                <h2>Time for an Eye Break!</h2>
                <p>Look at something 20 feet away</p>
                <div class="break-countdown" id="breakCountdownDisplay">20</div>
                <p class="break-subtitle">seconds remaining</p>
                <button class="btn btn-secondary" onclick="skipBreak()">Skip Break</button>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    overlay.classList.add('show');

    // Start countdown
    const countdownEl = document.getElementById('breakCountdownDisplay');
    const countdownInterval = setInterval(() => {
        state.breakCountdown--;
        if (countdownEl) countdownEl.textContent = state.breakCountdown;

        if (state.breakCountdown <= 0) {
            clearInterval(countdownInterval);
            completeBreak();
        }
    }, 1000);

    // Store interval for potential skip
    overlay.dataset.intervalId = countdownInterval;
}

function completeBreak() {
    state.isOnBreak = false;
    state.breaksTaken++;
    state.lastBreakTime = Date.now();

    const overlay = document.getElementById('breakOverlay');
    if (overlay) {
        overlay.classList.remove('show');
    }

    showToast('✅ Great job taking a break! Your eyes thank you.', 'success');
    calculateEyeStrainScore();
}

// Global function for skip button
window.skipBreak = function () {
    const overlay = document.getElementById('breakOverlay');
    if (overlay) {
        const intervalId = overlay.dataset.intervalId;
        if (intervalId) clearInterval(parseInt(intervalId));
        overlay.classList.remove('show');
    }
    state.isOnBreak = false;
    state.lastBreakTime = Date.now();
    showToast('Break skipped. Remember to rest your eyes!', 'warning');
};

// ============ EMAIL REPORT ============
function generateHealthReport() {
    const duration = state.sessionStartTime
        ? Math.floor((Date.now() - state.sessionStartTime) / 1000)
        : 0;
    const avgRate = duration > 0
        ? (state.blinkCount / (duration / 60)).toFixed(1)
        : 0;

    const report = {
        date: new Date().toLocaleDateString(),
        time: new Date().toLocaleTimeString(),
        sessionDuration: formatTime(duration),
        totalBlinks: state.blinkCount,
        avgBlinkRate: avgRate,
        eyeStrainScore: state.eyeStrainScore,
        fatigueLevel: state.fatigueLevel,
        breaksTaken: state.breaksTaken,
        breaksReminded: state.breaksReminded,
        recommendations: getHealthRecommendations()
    };

    return report;
}

function getHealthRecommendations() {
    const recommendations = [];

    const elapsedMinutes = state.sessionStartTime
        ? (Date.now() - state.sessionStartTime) / 60000
        : 0;
    const blinkRate = elapsedMinutes > 0 ? state.blinkCount / elapsedMinutes : 0;

    if (blinkRate < CONFIG.HEALTHY_BLINK_RATE_MIN) {
        recommendations.push('⚠️ Your blink rate is below normal. Try to blink more consciously.');
    }
    if (elapsedMinutes > 60) {
        recommendations.push('⏰ Long screen session detected. Consider taking longer breaks.');
    }
    if (state.fatigueLevel === 'high') {
        recommendations.push('😫 High fatigue detected. Rest your eyes for 10-15 minutes.');
    }
    if (state.breaksTaken < state.breaksReminded) {
        recommendations.push('🔔 You missed some eye breaks. Following the 20-20-20 rule helps prevent strain.');
    }
    if (recommendations.length === 0) {
        recommendations.push('✅ Great job! Your eye health looks good. Keep following healthy habits!');
    }

    return recommendations;
}

function sendEmailReport() {
    const report = generateHealthReport();

    const subject = `Eyeguard Health Report - ${report.date}`;
    const body = `
🏥 EYEGUARD EYE HEALTH REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Date: ${report.date}
🕐 Time: ${report.time}

📊 SESSION SUMMARY
━━━━━━━━━━━━━━━━━━
⏱️ Duration: ${report.sessionDuration}
👁️ Total Blinks: ${report.totalBlinks}
📈 Avg Blink Rate: ${report.avgBlinkRate}/min
🎯 Eye Strain Score: ${report.eyeStrainScore}/100
😊 Fatigue Level: ${report.fatigueLevel}
☕ Breaks Taken: ${report.breaksTaken}/${report.breaksReminded}

💡 RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━
${report.recommendations.join('\n')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated by Eyeguard - Your Eye Health Monitor
    `.trim();

    // Open email client with pre-filled content
    const mailtoLink = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.open(mailtoLink, '_blank');

    showToast('📧 Email report ready! Check your email app.', 'success');
}

// Global function for email button
window.sendEmailReport = sendEmailReport;

// ============ SAVE SESSION DATA ============
function saveSessionToHistory() {
    const report = generateHealthReport();
    const history = JSON.parse(localStorage.getItem('eyeguard_sessions') || '[]');

    history.push({
        ...report,
        timestamp: Date.now()
    });

    // Keep last 30 sessions
    if (history.length > 30) {
        history.shift();
    }

    localStorage.setItem('eyeguard_sessions', JSON.stringify(history));
}

