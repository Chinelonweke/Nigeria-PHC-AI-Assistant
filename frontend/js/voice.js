// Voice input functionality (placeholder for future implementation)

let recognition = null;
let isListening = false;

// Initialize Speech Recognition (if supported)
function initVoiceInput() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            const symptomsField = document.getElementById('symptoms');
            if (symptomsField) {
                symptomsField.value += (symptomsField.value ? ' ' : '') + transcript;
            }
            isListening = false;
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            isListening = false;
        };
        
        recognition.onend = function() {
            isListening = false;
        };
    }
}

// Start voice input
function startVoiceInput() {
    if (recognition && !isListening) {
        recognition.start();
        isListening = true;
    } else {
        alert('Speech recognition is not supported in your browser.');
    }
}

// Stop voice input
function stopVoiceInput() {
    if (recognition && isListening) {
        recognition.stop();
        isListening = false;
    }
}

// Initialize on load
if (window.location.pathname.includes('dashboard.html')) {
    initVoiceInput();
}