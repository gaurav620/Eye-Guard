/**
 * AI Chat Assistant for Eye-Guard
 * Provides eye health guidance and app usage help
 * Features: Local knowledge base, text-to-speech, speech-to-text
 */

// ============ KNOWLEDGE BASE ============
const knowledgeBase = {
    // Eye Health Topics
    '20-20-20': {
        keywords: ['20-20-20', '20 20 20', 'twenty twenty twenty', '20 rule', 'break rule'],
        response: `👁️ **The 20-20-20 Rule**

Every **20 minutes**, look at something **20 feet away** for **20 seconds**.

**Why it works:**
• Relaxes eye muscles
• Reduces digital eye strain
• Prevents fatigue buildup

💡 **Tip:** Eye-Guard automatically reminds you every 20 minutes!`
    },

    'blink_rate': {
        keywords: ['blink', 'blinking', 'blink rate', 'how often', 'blink count'],
        response: `👁️ **Healthy Blink Rate**

Normal: **15-20 blinks per minute**
When using screens: Often drops to **3-5 blinks/min**!

**Why blinking matters:**
• Keeps eyes moist
• Clears debris
• Prevents dry eyes

⚠️ If your blink rate is low, try to consciously blink more often!`
    },

    'eye_strain': {
        keywords: ['eye strain', 'tired eyes', 'strain', 'fatigue', 'sore eyes', 'burning'],
        response: `😣 **Eye Strain Relief**

**Symptoms:** Tired, dry, burning eyes; headaches

**Prevention Tips:**
1. Follow the 20-20-20 rule
2. Blink more often
3. Adjust screen brightness
4. Keep screen 20-26 inches away
5. Use proper lighting

🎯 Eye-Guard tracks your health score - keep it above 70!`
    },

    'screen_distance': {
        keywords: ['distance', 'how far', 'screen position', 'monitor', 'sit'],
        response: `📏 **Optimal Screen Distance**

• **Desktop:** 20-26 inches (arm's length)
• **Laptop:** Same, or slightly closer
• **Phone:** 12-16 inches

**Screen Position:**
• Top of screen at eye level
• Slight downward gaze (10-20°)
• Avoid looking up at screens!`
    },

    'dry_eyes': {
        keywords: ['dry eyes', 'dry', 'moisture', 'tears', 'lubricant'],
        response: `💧 **Dry Eye Prevention**

**Causes:** Low blink rate, air conditioning, heating

**Solutions:**
1. Blink consciously every few seconds
2. Use a humidifier
3. Take regular breaks
4. Consider eye drops (consult doctor)
5. Stay hydrated!

Eye-Guard monitors your blink rate to help prevent dry eyes.`
    },

    'blue_light': {
        keywords: ['blue light', 'night mode', 'blue filter', 'screen light'],
        response: `🔵 **Blue Light & Eye Health**

**Blue light from screens can:**
• Cause eye strain
• Affect sleep patterns
• Lead to digital fatigue

**Protection:**
1. Use night mode/blue light filter
2. Reduce screen time before bed
3. Take regular breaks
4. Adjust screen brightness`
    },

    // App Usage Topics
    'how_to_start': {
        keywords: ['how to use', 'start', 'begin', 'get started', 'tutorial', 'help me'],
        response: `🚀 **Getting Started with Eye-Guard**

1. **Click "Start Eye Tracking"** on the home screen
2. **Allow camera access** when prompted
3. **Face the camera** - AI will detect your eyes
4. **Watch your stats** - blinks, rate, health score
5. **Take breaks** when reminded (20-20-20 rule)

📧 You can also email yourself a health report!`
    },

    'features': {
        keywords: ['features', 'what can', 'capabilities', 'what does', 'functions'],
        response: `✨ **Eye-Guard Features**

👁️ **Blink Detection** - Real-time AI tracking
📊 **Health Stats** - Score, rate, session time
⏰ **Break Reminders** - 20-20-20 rule alerts
😊 **Fatigue Monitor** - Tracks eye tiredness
📧 **Email Reports** - Send health summary
📱 **Works Offline** - Install as PWA

Ask me about any feature for more details!`
    },

    'health_score': {
        keywords: ['health score', 'score', 'points', 'rating', 'how is score'],
        response: `🎯 **Eye Health Score Explained**

**Score Range:** 0-100

• **80-100:** 🟢 Excellent - Great eye care!
• **60-79:** 🟡 Good - Room for improvement
• **40-59:** 🟠 Fair - Take more breaks
• **0-39:** 🔴 Poor - Rest your eyes!

**Based on:**
• Blink rate (40%)
• Session duration (30%)
• Break compliance (30%)`
    },

    'email_report': {
        keywords: ['email', 'report', 'send report', 'summary', 'export'],
        response: `📧 **Email Health Report**

Click the **"Send Report via Email"** button during a tracking session to:

• Get a summary of your session
• See your blink statistics
• Receive personalized recommendations
• Keep records of your eye health

Great for sharing with eye doctors!`
    },

    // Greetings & Generic
    'greeting': {
        keywords: ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening'],
        response: `👋 Hello! I'm your Eye Health Assistant!

I can help you with:
• 👁️ Eye health tips
• 📊 Understanding your stats
• 🎯 Using Eye-Guard features
• ⏰ Break reminders

What would you like to know?`
    },

    'thanks': {
        keywords: ['thank', 'thanks', 'appreciate', 'helpful'],
        response: `😊 You're welcome! Taking care of your eyes is important.

Remember:
• Follow the 20-20-20 rule
• Keep blinking regularly
• Take breaks when reminded

Stay healthy! 👁️✨`
    }
};

// Default response when no match found
const defaultResponse = `I'm here to help with eye health and using Eye-Guard! 

Try asking about:
• "What is the 20-20-20 rule?"
• "How do I start eye tracking?"
• "What's a healthy blink rate?"
• "How is my health score calculated?"

Or click one of the quick action buttons below!`;

// ============ STATE ============
let isOpen = false;
let isRecording = false;
let isSpeaking = false;
let speechSynthesis = window.speechSynthesis;
let speechRecognition = null;

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    createChatUI();
    initSpeechRecognition();
    console.log('AI Chat Assistant initialized');
});

// ============ CREATE UI ============
function createChatUI() {
    // Create container
    const container = document.createElement('div');
    container.id = 'aiChatContainer';
    container.innerHTML = `
        <!-- Floating Chat Button -->
        <button class="ai-chat-button" id="aiChatButton" aria-label="Open AI Chat">
            <span class="ai-chat-button-icon">🤖</span>
        </button>
        
        <!-- Chat Window -->
        <div class="ai-chat-window" id="aiChatWindow">
            <div class="ai-chat-header">
                <div class="ai-chat-avatar">🤖</div>
                <div class="ai-chat-title-group">
                    <h3 class="ai-chat-title">Eye Health Assistant</h3>
                    <p class="ai-chat-subtitle">Ask me about eye care & app usage</p>
                </div>
                <button class="ai-chat-close" id="aiChatClose" aria-label="Close chat">✕</button>
            </div>
            
            <div class="ai-chat-messages" id="aiChatMessages">
                <!-- Messages will be added here -->
            </div>
            
            <div class="ai-chat-quick-actions" id="aiQuickActions">
                <button class="ai-chat-quick-btn" data-query="What is the 20-20-20 rule?">20-20-20 Rule</button>
                <button class="ai-chat-quick-btn" data-query="How do I start eye tracking?">How to Start</button>
                <button class="ai-chat-quick-btn" data-query="What's a healthy blink rate?">Blink Rate</button>
                <button class="ai-chat-quick-btn" data-query="How is my health score calculated?">Health Score</button>
            </div>
            
            <div class="ai-chat-input-area">
                <button class="ai-chat-voice-btn" id="aiVoiceBtn" aria-label="Voice input">🎤</button>
                <input type="text" class="ai-chat-input" id="aiChatInput" 
                       placeholder="Ask about eye health..." 
                       autocomplete="off">
                <button class="ai-chat-send-btn" id="aiSendBtn" aria-label="Send message">➤</button>
            </div>
        </div>
    `;

    document.body.appendChild(container);

    // Initialize event listeners
    initChatListeners();

    // Show welcome message after a delay
    setTimeout(() => {
        addMessage('ai', `👋 Hi! I'm your Eye Health Assistant. 

I can help you understand:
• Eye care best practices
• How to use Eye-Guard
• Your health stats

Ask me anything or use the quick buttons below!`);
    }, 500);
}

// ============ EVENT LISTENERS ============
function initChatListeners() {
    const chatButton = document.getElementById('aiChatButton');
    const chatWindow = document.getElementById('aiChatWindow');
    const closeBtn = document.getElementById('aiChatClose');
    const input = document.getElementById('aiChatInput');
    const sendBtn = document.getElementById('aiSendBtn');
    const voiceBtn = document.getElementById('aiVoiceBtn');
    const quickActions = document.getElementById('aiQuickActions');

    // Toggle chat
    chatButton.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    // Send message
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Voice input
    voiceBtn.addEventListener('click', toggleVoiceInput);

    // Quick actions
    quickActions.addEventListener('click', (e) => {
        if (e.target.classList.contains('ai-chat-quick-btn')) {
            const query = e.target.dataset.query;
            input.value = query;
            sendMessage();
        }
    });
}

// ============ TOGGLE CHAT ============
function toggleChat() {
    const chatButton = document.getElementById('aiChatButton');
    const chatWindow = document.getElementById('aiChatWindow');

    isOpen = !isOpen;

    if (isOpen) {
        chatWindow.classList.add('open');
        chatButton.classList.add('active');
        chatButton.querySelector('.ai-chat-button-icon').textContent = '✕';
        document.getElementById('aiChatInput').focus();
    } else {
        chatWindow.classList.remove('open');
        chatButton.classList.remove('active');
        chatButton.querySelector('.ai-chat-button-icon').textContent = '🤖';
        stopSpeaking();
    }
}

// ============ SEND MESSAGE ============
function sendMessage() {
    const input = document.getElementById('aiChatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addMessage('user', message);
    input.value = '';

    // Show typing indicator
    showTyping();

    // Generate response after delay
    setTimeout(() => {
        hideTyping();
        const response = generateResponse(message);
        addMessage('ai', response);
    }, 600 + Math.random() * 400);
}

// ============ ADD MESSAGE ============
function addMessage(type, text) {
    const messagesContainer = document.getElementById('aiChatMessages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-chat-message ${type}`;

    const avatar = type === 'ai' ? '🤖' : '👤';

    // Format text with markdown-like styling
    const formattedText = formatMessage(text);

    messageDiv.innerHTML = `
        <div class="ai-chat-message-avatar">${avatar}</div>
        <div class="ai-chat-message-content">
            <div class="ai-chat-message-bubble">
                ${formattedText}
                ${type === 'ai' ? '<button class="ai-chat-speak-btn" onclick="speakMessage(this)" aria-label="Read aloud">🔊</button>' : ''}
            </div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ============ FORMAT MESSAGE ============
function formatMessage(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/• /g, '&bull; ');
}

// ============ TYPING INDICATOR ============
function showTyping() {
    const messagesContainer = document.getElementById('aiChatMessages');

    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-chat-message ai';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="ai-chat-message-avatar">🤖</div>
        <div class="ai-chat-typing">
            <div class="ai-chat-typing-dot"></div>
            <div class="ai-chat-typing-dot"></div>
            <div class="ai-chat-typing-dot"></div>
        </div>
    `;

    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTyping() {
    const typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
}

// ============ GENERATE RESPONSE ============
function generateResponse(query) {
    const lowerQuery = query.toLowerCase();

    // Find best matching topic
    let bestMatch = null;
    let bestScore = 0;

    for (const [topic, data] of Object.entries(knowledgeBase)) {
        for (const keyword of data.keywords) {
            if (lowerQuery.includes(keyword.toLowerCase())) {
                const score = keyword.length;
                if (score > bestScore) {
                    bestScore = score;
                    bestMatch = data.response;
                }
            }
        }
    }

    return bestMatch || defaultResponse;
}

// ============ TEXT-TO-SPEECH ============
function speakMessage(button) {
    const bubble = button.parentElement;
    const text = bubble.textContent.replace('🔊', '').trim();

    if (isSpeaking) {
        stopSpeaking();
        return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;

    utterance.onstart = () => {
        isSpeaking = true;
        button.classList.add('speaking');
        button.textContent = '⏸️';
    };

    utterance.onend = () => {
        isSpeaking = false;
        button.classList.remove('speaking');
        button.textContent = '🔊';
    };

    speechSynthesis.speak(utterance);
}

function stopSpeaking() {
    speechSynthesis.cancel();
    isSpeaking = false;
    document.querySelectorAll('.ai-chat-speak-btn').forEach(btn => {
        btn.classList.remove('speaking');
        btn.textContent = '🔊';
    });
}

// ============ SPEECH-TO-TEXT ============
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        speechRecognition = new SpeechRecognition();
        speechRecognition.continuous = false;
        speechRecognition.interimResults = false;
        speechRecognition.lang = 'en-US';

        speechRecognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById('aiChatInput').value = transcript;
            stopRecording();
            sendMessage();
        };

        speechRecognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            stopRecording();
        };

        speechRecognition.onend = () => {
            stopRecording();
        };
    } else {
        // Hide voice button if not supported
        setTimeout(() => {
            const voiceBtn = document.getElementById('aiVoiceBtn');
            if (voiceBtn) voiceBtn.style.display = 'none';
        }, 100);
    }
}

function toggleVoiceInput() {
    if (!speechRecognition) return;

    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

function startRecording() {
    if (!speechRecognition) return;

    try {
        speechRecognition.start();
        isRecording = true;
        document.getElementById('aiVoiceBtn').classList.add('recording');
        document.getElementById('aiChatInput').placeholder = 'Listening...';
    } catch (e) {
        console.error('Error starting speech recognition:', e);
    }
}

function stopRecording() {
    if (!speechRecognition) return;

    try {
        speechRecognition.stop();
    } catch (e) {
        // Ignore
    }
    isRecording = false;
    document.getElementById('aiVoiceBtn').classList.remove('recording');
    document.getElementById('aiChatInput').placeholder = 'Ask about eye health...';
}

// Global function for speak buttons
window.speakMessage = speakMessage;
