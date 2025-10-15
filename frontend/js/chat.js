/**
 * PHC AI Assistant - Chat/Triage Interface
 * WITH COMPLETE TTS (TEXT-TO-SPEECH) FUNCTIONALITY + SMART CACHING
 */

const API_BASE = 'http://localhost:8000';

// =======================
// GLOBAL AUDIO + CACHE
// =======================
let currentAudio = null;
const ttsCache = {}; // 🧠 Cache: { text: audioUrl }

// =======================
// PAGE LOAD: Triage Page
// =======================
function loadTriagePage() {
    const html = `
        <div class="grid-2">
            <div class="form-card">
                <h3 style="margin-bottom: 20px;">AI Symptom Analysis</h3>
                <form id="triageForm">
                    <div class="form-group">
                        <label for="symptoms">Symptoms *</label>
                        <div style="position: relative;">
                            <textarea id="symptoms" required placeholder="Describe symptoms, use voice input, or ask about medicine stock..."></textarea>
                            <button type="button" id="voiceBtn" class="voice-btn" title="Voice Input" 
                                style="position: absolute; right: 8px; top: 8px; border: none; background: transparent; cursor: pointer; font-size: 20px;">
                                🎤
                            </button>
                        </div>
                        <small style="color: #6b7280; font-size: 12px;">
                            💡 Tip: Ask about stock! Try: "check malaria medicine"
                        </small>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="age">Age</label>
                            <input type="number" id="age" placeholder="Enter age">
                        </div>

                        <div class="form-group">
                            <label for="gender">Gender</label>
                            <select id="gender">
                                <option value="M">Male</option>
                                <option value="F">Female</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="language">Language</label>
                        <select id="language">
                            <option value="english">English</option>
                            <option value="hausa">Hausa</option>
                            <option value="yoruba">Yoruba</option>
                            <option value="igbo">Igbo</option>
                            <option value="pidgin">Pidgin</option>
                        </select>
                    </div>

                    <button type="submit" class="btn btn-primary">
                        Analyze Symptoms
                    </button>
                </form>
            </div>

            <div class="chart-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0;">Analysis Result</h3>
                    <button id="speakBtn" class="btn-icon" title="Read Result Aloud" 
                        style="display: none; border: none; background: var(--primary); color: white; padding: 8px 16px; 
                               border-radius: 6px; cursor: pointer; font-size: 20px;">
                        🔊
                    </button>
                </div>
                <div id="triage-result" style="padding: 20px; min-height: 300px; color: var(--gray); text-align: center;">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" 
                         style="margin: 40px auto; display: block; color: #d1d5db;">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    <p>Enter symptoms and click "Analyze"</p>
                </div>
            </div>
        </div>

        <div class="alert alert-warning mt-3">
            <strong>⚠️ Disclaimer:</strong> AI tool provides preliminary recommendations only. 
            Always consult healthcare professionals.
        </div>
    `;
    
    document.getElementById('content-area').innerHTML = html;

    document.getElementById('triageForm').addEventListener('submit', handleTriageSubmit);
    document.getElementById('voiceBtn').addEventListener('click', handleVoiceInput);
    document.getElementById('speakBtn').addEventListener('click', handleTextToSpeech);
}

// =======================
// INVENTORY QUERY HANDLER
// =======================
async function handleInventoryQuery(message) {
    const lowerMessage = message.toLowerCase();
    const inventoryKeywords = [
        'stock', 'inventory', 'medicine', 'drug', 'available', 'supply', 
        'reorder', 'order', 'do we have', 'check', 'how much', 'how many'
    ];

    const isInventoryQuery = inventoryKeywords.some(k => lowerMessage.includes(k));
    if (!isInventoryQuery) return null;

    try {
        console.log('🔍 Detected inventory query');
        const response = await fetch(`${API_BASE}/api/inventory/predict-stockouts`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        const critical = data.predictions.filter(p => p.alert_level === 'CRITICAL');
        const warning = data.predictions.filter(p => p.alert_level === 'WARNING');

        const med = extractMedicineName(lowerMessage);
        if (med) {
            const match = data.predictions.find(p => p.item_name.toLowerCase().includes(med));
            if (match) return formatSpecificMedicineResponse(match);
            return `❓ Could not find "${med}" in inventory.`;
        }

        if (!critical.length && !warning.length) return formatAllGoodResponse(data.summary);
        return formatStockAlertsResponse(critical, warning, data.summary);
    } catch (err) {
        console.error('❌ Inventory query error:', err);
        return `⚠️ Could not check inventory.`;
    }
}

function extractMedicineName(message) {
    const meds = ['paracetamol', 'malaria', 'act', 'coartem', 'amoxicillin', 'augmentin',
                  'metronidazole', 'ciprofloxacin', 'ors', 'zinc', 'vitamin', 'folic acid', 'iron'];
    return meds.find(m => message.includes(m)) || null;
}

// =======================
// TRIAGE SUBMIT HANDLER
// =======================
async function handleTriageSubmit(e) {
    e.preventDefault();

    const symptoms = document.getElementById('symptoms').value.trim();
    const age = document.getElementById('age').value;
    const gender = document.getElementById('gender').value;
    const language = document.getElementById('language').value;
    const resultDiv = document.getElementById('triage-result');
    const speakBtn = document.getElementById('speakBtn');

    speakBtn.style.display = 'none';
    resultDiv.innerHTML = `<div class="loading" style="padding: 40px;">
        <div class="spinner" style="margin: 0 auto 16px; width: 40px; height: 40px; border: 4px solid #e5e7eb;
        border-top-color: var(--primary); border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <p style="color: #6b7280;">Analyzing...</p></div>`;

    const invRes = await handleInventoryQuery(symptoms);
    if (invRes) {
        resultDiv.innerHTML = `<div style="padding: 20px;">
            <h4 style="margin: 0 0 16px 0; color: var(--primary);">📦 Inventory Status</h4>
            ${invRes}
        </div>`;
        speakBtn.style.display = 'block';
        speakBtn.dataset.text = extractPlainText(invRes);
        speakBtn.dataset.language = language;
        return;
    }

    try {
        const data = await apiCall('/api/triage/analyze', {
            method: 'POST',
            body: JSON.stringify({ symptoms, patient_info: { age: parseInt(age) || null, gender }, language })
        });
        displayTriageResult(data, language);
    } catch (error) {
        console.error('Triage error:', error);
        resultDiv.innerHTML = `<div class="alert alert-error" style="margin: 20px;">
            ❌ Failed to analyze. Please try again.</div>`;
    }
}

// =======================
// DISPLAY TRIAGE RESULT
// =======================
function displayTriageResult(data, language) {
    const colors = { Critical: 'red', Urgent: 'yellow', Routine: 'green' };
    const color = colors[data.urgency_level] || 'blue';
    const html = `
        <div style="padding: 20px;">
            <div style="background: #dbeafe; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <p style="font-size: 12px; color: #1e40af;">Likely Diagnosis</p>
                <p style="font-size: 20px; font-weight: 700;">${data.likely_diagnosis || 'Not determined'}</p>
            </div>
            <div style="background: ${color === 'red' ? '#fee2e2' : color === 'yellow' ? '#fef3c7' : '#d1fae5'};
                        padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                <p style="font-size: 12px;">Urgency Level</p>
                <p style="font-size: 20px; font-weight: 700;">${data.urgency_level || 'Routine'}</p>
            </div>
            <p><strong>Recommended Action:</strong> ${data.recommended_action || 'Consult healthcare worker'}</p>
        </div>`;
    document.getElementById('triage-result').innerHTML = html;

    const speakBtn = document.getElementById('speakBtn');
    speakBtn.style.display = 'block';
    speakBtn.dataset.text = `Diagnosis: ${data.likely_diagnosis}. Urgency: ${data.urgency_level}. ${data.recommended_action}`;
    speakBtn.dataset.language = language;
}

// =======================
// TEXT-TO-SPEECH (TTS) with SMART CACHE
// =======================
async function handleTextToSpeech() {
    const speakBtn = document.getElementById('speakBtn');
    const text = speakBtn.dataset.text;
    const language = speakBtn.dataset.language || 'english';
    if (!text) return alert('No text to read');

    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
        speakBtn.textContent = '🔊';
        return;
    }

    try {
        const plainText = extractPlainText(text).trim();
        speakBtn.textContent = '⏳';
        speakBtn.disabled = true;

        // 🧠 Check cache first
        if (ttsCache[plainText]) {
            console.log('🎧 Playing from TTS cache');
            await playAudio(ttsCache[plainText], speakBtn);
            return;
        }

        console.log('🗣️ Generating new TTS...');
        const formData = new FormData();
        formData.append('text', plainText);
        formData.append('language', language);

        const response = await fetch(`${API_BASE}/api/audio/text-to-speech`, { method: 'POST', body: formData });
        if (!response.ok) throw new Error(`TTS error: ${response.status}`);

        const blob = await response.blob();
        const audioUrl = URL.createObjectURL(blob);
        ttsCache[plainText] = audioUrl; // 🧠 Cache result

        await playAudio(audioUrl, speakBtn);
    } catch (err) {
        console.error('❌ TTS error:', err);
        alert('Text-to-speech failed.');
    } finally {
        speakBtn.textContent = '🔊';
        speakBtn.disabled = false;
    }
}

// Helper: Play Audio
async function playAudio(audioUrl, speakBtn) {
    try {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }
        currentAudio = new Audio(audioUrl);
        currentAudio.onended = () => {
            speakBtn.textContent = '🔊';
            speakBtn.disabled = false;
            currentAudio = null;
        };
        await currentAudio.play();
        speakBtn.textContent = '⏸️';
        console.log('✅ Playing audio');
    } catch (err) {
        console.error('Audio play error:', err);
        speakBtn.textContent = '🔊';
    }
}

// =======================
// VOICE INPUT (STT)
// =======================
let mediaRecorder;
let audioChunks = [];

async function handleVoiceInput() {
    const voiceBtn = document.getElementById('voiceBtn');
    const language = document.getElementById('language').value;
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
            mediaRecorder.onstop = async () => {
                const blob = new Blob(audioChunks, { type: 'audio/wav' });
                await transcribeAudio(blob, language);
            };

            mediaRecorder.start();
            voiceBtn.textContent = '⏹️';
            voiceBtn.style.background = '#ef4444';
        } catch (err) {
            alert('Microphone access denied');
        }
    } else {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(t => t.stop());
        voiceBtn.textContent = '🎤';
        voiceBtn.style.background = '';
    }
}

async function transcribeAudio(blob, language) {
    try {
        const formData = new FormData();
        formData.append('audio', blob, 'recording.wav');
        formData.append('language', language);

        const res = await fetch(`${API_BASE}/api/audio/transcribe`, { method: 'POST', body: formData });
        const data = await res.json();

        if (data.success) document.getElementById('symptoms').value = data.text;
        else alert('Transcription failed');
    } catch (err) {
        console.error('❌ Transcription error:', err);
        alert('Failed to transcribe');
    }
}

// =======================
// UTILITIES
// =======================
async function apiCall(endpoint, options = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
}

function extractPlainText(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent || div.innerText || '';
}

console.log('✅ Chat.js loaded with TTS cache + STT support');
