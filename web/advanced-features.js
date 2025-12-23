/**
 * Advanced Features for Eye-Guard
 * Settings, Dark Mode, Eye Exercises, Session History, Streaks, Sounds
 */

// ============ SETTINGS CONFIGURATION ============
const defaultSettings = {
    darkMode: false,
    breakInterval: 20, // minutes
    soundEnabled: true,
    autoStartTracking: false,
    showStreak: true,
    exerciseDuration: 20 // seconds
};

// Load settings from localStorage
function loadSettings() {
    const saved = localStorage.getItem('eyeguard-settings');
    return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
}

// Save settings to localStorage
function saveSettings(settings) {
    localStorage.setItem('eyeguard-settings', JSON.stringify(settings));
    applySettings(settings);
}

let currentSettings = loadSettings();

// ============ APPLY SETTINGS ============
function applySettings(settings) {
    // Dark Mode
    if (settings.darkMode) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }

    // Update break interval in config
    if (window.CONFIG) {
        window.CONFIG.BREAK_INTERVAL = settings.breakInterval * 60000;
    }
}

// ============ SESSION HISTORY ============
function getSessionHistory() {
    const history = localStorage.getItem('eyeguard-sessions');
    return history ? JSON.parse(history) : [];
}

function saveSession(session) {
    const history = getSessionHistory();
    history.push({
        date: new Date().toISOString(),
        duration: session.duration,
        blinks: session.blinks,
        blinkRate: session.blinkRate,
        healthScore: session.healthScore
    });
    // Keep only last 30 days
    const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
    const filtered = history.filter(s => new Date(s.date).getTime() > thirtyDaysAgo);
    localStorage.setItem('eyeguard-sessions', JSON.stringify(filtered));
    updateStreak();
}

// ============ DAILY STREAK ============
function getStreak() {
    const data = localStorage.getItem('eyeguard-streak');
    return data ? JSON.parse(data) : { count: 0, lastDate: null };
}

function updateStreak() {
    const streak = getStreak();
    const today = new Date().toDateString();
    const yesterday = new Date(Date.now() - 86400000).toDateString();

    if (streak.lastDate === today) {
        return streak.count; // Already tracked today
    } else if (streak.lastDate === yesterday) {
        streak.count++;
    } else if (streak.lastDate !== today) {
        streak.count = 1; // Reset streak
    }

    streak.lastDate = today;
    localStorage.setItem('eyeguard-streak', JSON.stringify(streak));
    updateStreakDisplay();
    return streak.count;
}

function updateStreakDisplay() {
    const streakElement = document.getElementById('streakDisplay');
    if (streakElement && currentSettings.showStreak) {
        const streak = getStreak();
        streakElement.textContent = `🔥 ${streak.count} day${streak.count !== 1 ? 's' : ''}`;
        streakElement.style.display = 'block';
    }
}

// ============ SOUND EFFECTS ============
const sounds = {
    blink: null,
    break: null,
    complete: null
};

function initSounds() {
    // Create audio context for generating sounds
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;

    sounds.context = new AudioContext();
}

function playSound(type) {
    if (!currentSettings.soundEnabled || !sounds.context) return;

    const ctx = sounds.context;
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    switch (type) {
        case 'blink':
            oscillator.frequency.value = 800;
            gainNode.gain.value = 0.05;
            oscillator.start();
            oscillator.stop(ctx.currentTime + 0.05);
            break;
        case 'break':
            oscillator.frequency.value = 440;
            gainNode.gain.value = 0.2;
            oscillator.start();
            setTimeout(() => oscillator.frequency.value = 550, 200);
            setTimeout(() => oscillator.frequency.value = 660, 400);
            oscillator.stop(ctx.currentTime + 0.6);
            break;
        case 'complete':
            oscillator.frequency.value = 523;
            gainNode.gain.value = 0.15;
            oscillator.start();
            setTimeout(() => oscillator.frequency.value = 659, 150);
            setTimeout(() => oscillator.frequency.value = 784, 300);
            oscillator.stop(ctx.currentTime + 0.5);
            break;
    }
}

// ============ EYE EXERCISES ============
const eyeExercises = [
    {
        name: 'Look Far Away',
        icon: '🏔️',
        instruction: 'Focus on something 20+ feet away',
        duration: 20
    },
    {
        name: 'Eye Rolling',
        icon: '🔄',
        instruction: 'Slowly roll your eyes clockwise, then counter-clockwise',
        duration: 15
    },
    {
        name: 'Palming',
        icon: '🙌',
        instruction: 'Cover your closed eyes with your palms. Breathe deeply.',
        duration: 30
    },
    {
        name: 'Near-Far Focus',
        icon: '👆',
        instruction: 'Focus on your thumb up close, then something far away. Repeat.',
        duration: 20
    },
    {
        name: 'Figure 8',
        icon: '♾️',
        instruction: 'Trace a large figure 8 with your eyes',
        duration: 15
    },
    {
        name: 'Blink Rapidly',
        icon: '😌',
        instruction: 'Blink quickly 20 times to refresh your eyes',
        duration: 10
    }
];

function getRandomExercise() {
    return eyeExercises[Math.floor(Math.random() * eyeExercises.length)];
}

// ============ CREATE SETTINGS UI ============
function createSettingsUI() {
    const settingsContainer = document.createElement('div');
    settingsContainer.id = 'settingsPanel';
    settingsContainer.className = 'settings-panel';
    settingsContainer.innerHTML = `
        <div class="settings-backdrop" onclick="toggleSettings()"></div>
        <div class="settings-content">
            <div class="settings-header">
                <h3>⚙️ Settings</h3>
                <button class="settings-close" onclick="toggleSettings()">✕</button>
            </div>
            <div class="settings-body">
                <!-- Dark Mode -->
                <div class="settings-item">
                    <div class="settings-item-info">
                        <span class="settings-item-icon">🌙</span>
                        <div>
                            <div class="settings-item-title">Dark Mode</div>
                            <div class="settings-item-desc">Reduce eye strain at night</div>
                        </div>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="darkModeToggle" onchange="updateSetting('darkMode', this.checked)">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                
                <!-- Sound Effects -->
                <div class="settings-item">
                    <div class="settings-item-info">
                        <span class="settings-item-icon">🔔</span>
                        <div>
                            <div class="settings-item-title">Sound Effects</div>
                            <div class="settings-item-desc">Audio feedback for actions</div>
                        </div>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="soundToggle" onchange="updateSetting('soundEnabled', this.checked)">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                
                <!-- Show Streak -->
                <div class="settings-item">
                    <div class="settings-item-info">
                        <span class="settings-item-icon">🔥</span>
                        <div>
                            <div class="settings-item-title">Show Streak</div>
                            <div class="settings-item-desc">Display daily tracking streak</div>
                        </div>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="streakToggle" onchange="updateSetting('showStreak', this.checked)">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                
                <!-- Break Interval -->
                <div class="settings-item">
                    <div class="settings-item-info">
                        <span class="settings-item-icon">⏰</span>
                        <div>
                            <div class="settings-item-title">Break Interval</div>
                            <div class="settings-item-desc">Minutes between break reminders</div>
                        </div>
                    </div>
                    <select id="breakIntervalSelect" class="settings-select" onchange="updateSetting('breakInterval', parseInt(this.value))">
                        <option value="10">10 min</option>
                        <option value="15">15 min</option>
                        <option value="20">20 min</option>
                        <option value="30">30 min</option>
                        <option value="45">45 min</option>
                        <option value="60">60 min</option>
                    </select>
                </div>
                
                <!-- Session History -->
                <div class="settings-section">
                    <h4>📊 Session History</h4>
                    <div id="sessionHistoryList" class="session-history-list">
                        <!-- Populated by JS -->
                    </div>
                </div>
                
                <!-- Eye Exercises -->
                <div class="settings-section">
                    <h4>👁️ Eye Exercises</h4>
                    <button class="btn btn-exercise" onclick="startExercise()">
                        🧘 Start Random Exercise
                    </button>
                </div>
                
                <!-- Tips -->
                <div class="settings-section tips-section">
                    <h4>💡 Eye Care Tips</h4>
                    <div class="tip-card" id="tipCard">
                        <div class="tip-icon">💡</div>
                        <div class="tip-text">Keep your screen brightness similar to your surroundings to reduce eye strain.</div>
                    </div>
                    <button class="btn btn-tip" onclick="showRandomTip()">Next Tip</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(settingsContainer);

    // Add settings button to header
    addSettingsButton();

    // Add streak display
    addStreakDisplay();

    // Load initial settings into UI
    loadSettingsUI();

    // Populate session history
    populateSessionHistory();
}

function addSettingsButton() {
    const headerActions = document.querySelector('.header-actions');
    if (headerActions) {
        const settingsBtn = document.createElement('button');
        settingsBtn.className = 'header-btn settings-btn';
        settingsBtn.id = 'settingsBtn';
        settingsBtn.innerHTML = '⚙️';
        settingsBtn.onclick = toggleSettings;
        settingsBtn.title = 'Settings';
        headerActions.insertBefore(settingsBtn, headerActions.firstChild);
    }
}

function addStreakDisplay() {
    const headerActions = document.querySelector('.header-actions');
    if (headerActions) {
        const streakDisplay = document.createElement('span');
        streakDisplay.className = 'streak-display';
        streakDisplay.id = 'streakDisplay';
        streakDisplay.style.display = 'none';
        headerActions.insertBefore(streakDisplay, headerActions.firstChild);
        updateStreakDisplay();
    }
}

function loadSettingsUI() {
    document.getElementById('darkModeToggle').checked = currentSettings.darkMode;
    document.getElementById('soundToggle').checked = currentSettings.soundEnabled;
    document.getElementById('streakToggle').checked = currentSettings.showStreak;
    document.getElementById('breakIntervalSelect').value = currentSettings.breakInterval;
}

function toggleSettings() {
    const panel = document.getElementById('settingsPanel');
    panel.classList.toggle('open');
}

function updateSetting(key, value) {
    currentSettings[key] = value;
    saveSettings(currentSettings);

    if (key === 'showStreak') {
        updateStreakDisplay();
    }
}

function populateSessionHistory() {
    const list = document.getElementById('sessionHistoryList');
    const sessions = getSessionHistory();

    if (sessions.length === 0) {
        list.innerHTML = '<div class="no-sessions">No sessions yet. Start tracking!</div>';
        return;
    }

    // Show last 5 sessions
    const recent = sessions.slice(-5).reverse();
    list.innerHTML = recent.map(session => {
        const date = new Date(session.date);
        const formattedDate = date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        const mins = Math.floor(session.duration / 60);
        return `
            <div class="session-item">
                <div class="session-date">${formattedDate}</div>
                <div class="session-stats">
                    <span>⏱️ ${mins}m</span>
                    <span>👁️ ${session.blinks} blinks</span>
                    <span>💯 ${session.healthScore || '-'}</span>
                </div>
            </div>
        `;
    }).join('');
}

// ============ EYE CARE TIPS ============
const eyeCareTips = [
    "Keep your screen brightness similar to your surroundings to reduce eye strain.",
    "Position your screen 20-26 inches (arm's length) from your eyes.",
    "The top of your screen should be at or slightly below eye level.",
    "Blink more often! We blink 66% less when looking at screens.",
    "Use artificial tears if your eyes feel dry.",
    "Take a 5-10 minute break every hour for longer sessions.",
    "Adjust your room lighting to reduce glare on your screen.",
    "Consider using blue light filtering glasses or screen settings.",
    "Stay hydrated - drink water throughout the day for healthier eyes.",
    "Get enough sleep - tired eyes are more prone to strain.",
    "If you wear contacts, give your eyes a break with glasses sometimes.",
    "Green plants in your workspace can help reduce eye fatigue."
];

let lastTipIndex = -1;

function showRandomTip() {
    let index;
    do {
        index = Math.floor(Math.random() * eyeCareTips.length);
    } while (index === lastTipIndex);

    lastTipIndex = index;
    const tipCard = document.getElementById('tipCard');
    tipCard.querySelector('.tip-text').textContent = eyeCareTips[index];
    tipCard.classList.add('tip-animate');
    setTimeout(() => tipCard.classList.remove('tip-animate'), 300);
}

// ============ EXERCISE MODAL ============
function startExercise() {
    const exercise = getRandomExercise();
    toggleSettings(); // Close settings

    const modal = document.createElement('div');
    modal.className = 'exercise-modal';
    modal.id = 'exerciseModal';
    modal.innerHTML = `
        <div class="exercise-content">
            <div class="exercise-icon">${exercise.icon}</div>
            <h2 class="exercise-name">${exercise.name}</h2>
            <p class="exercise-instruction">${exercise.instruction}</p>
            <div class="exercise-timer" id="exerciseTimer">${exercise.duration}</div>
            <p class="exercise-label">seconds remaining</p>
            <button class="btn btn-secondary" onclick="closeExercise()">Skip</button>
        </div>
    `;

    document.body.appendChild(modal);
    setTimeout(() => modal.classList.add('open'), 10);

    let remaining = exercise.duration;
    const timer = setInterval(() => {
        remaining--;
        document.getElementById('exerciseTimer').textContent = remaining;

        if (remaining <= 0) {
            clearInterval(timer);
            playSound('complete');
            closeExercise();
            showToast('🎉 Great job! Exercise complete!', 'success');
        }
    }, 1000);

    modal.dataset.timerId = timer;
}

function closeExercise() {
    const modal = document.getElementById('exerciseModal');
    if (modal) {
        clearInterval(parseInt(modal.dataset.timerId));
        modal.classList.remove('open');
        setTimeout(() => modal.remove(), 300);
    }
}

// ============ SHOWTOAST HELPER ============
function showToast(message, type) {
    // Use existing toast if available, otherwise create one
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        toast.innerHTML = '<span id="toastIcon"></span><span id="toastMessage"></span>';
        document.body.appendChild(toast);
    }

    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    document.getElementById('toastIcon').textContent = icons[type] || 'ℹ️';
    document.getElementById('toastMessage').textContent = message;

    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    // Apply saved settings
    applySettings(currentSettings);

    // Create settings UI
    createSettingsUI();

    // Initialize sounds
    initSounds();

    // Show streak if enabled
    if (currentSettings.showStreak) {
        updateStreakDisplay();
    }

    console.log('Advanced features initialized');
});

// ============ GLOBAL EXPORTS ============
window.toggleSettings = toggleSettings;
window.updateSetting = updateSetting;
window.startExercise = startExercise;
window.closeExercise = closeExercise;
window.showRandomTip = showRandomTip;
window.playSound = playSound;
window.saveSession = saveSession;
window.currentSettings = currentSettings;
