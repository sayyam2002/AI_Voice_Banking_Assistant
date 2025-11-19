// --- Globals ---
let userToken = null;
const API_BASE_URL = "http://127.0.0.1:8000";
let audioBlobs = [];
let dialogflowSessionId = null;
let pendingTransfer = null; // Store transfer details during verification

// --- Speech API Setup (For text recognition) ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
    alert("Your browser does not support Speech Recognition. Please use Chrome or Edge.");
}
const recognition = new SpeechRecognition();
recognition.continuous = false;
recognition.interimResults = false;
recognition.lang = 'en-US';

// --- DOM Elements ---
const loginContainer = document.getElementById("login-container");
const assistantContainer = document.getElementById("assistant-container");
const loginButton = document.getElementById("login-button");
const loginStatus = document.getElementById("login-status");
const speakButton = document.getElementById("speak-button");
const conversationLog = document.getElementById("conversation-log");

// Enrollment Elements
const enrollButton1 = document.getElementById("enroll-button-1");
const enrollButton2 = document.getElementById("enroll-button-2");
const enrollButton3 = document.getElementById("enroll-button-3");
const submitEnrollment = document.getElementById("submit-enrollment");
const enrollStatus = document.getElementById("enroll-status");

// --- WAV Recording Logic (The Fix) ---
let audioContext;
let mediaStreamSource;
let recorder;

async function initAudio() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        mediaStreamSource = audioContext.createMediaStreamSource(stream);
        console.log("Microphone initialized.");
    } catch (err) {
        console.error("Error accessing microphone:", err);
        enrollStatus.textContent = "Error: Could not access microphone.";
        enrollStatus.className = "status-message error";
    }
}

// Helper function to create a WAV file from raw audio data
function exportWAV(audioData, sampleRate) {
    const buffer = new ArrayBuffer(44 + audioData.length * 2);
    const view = new DataView(buffer);

    // Write WAV Header
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + audioData.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, audioData.length * 2, true);

    // Write PCM samples
    let offset = 44;
    for (let i = 0; i < audioData.length; i++) {
        let s = Math.max(-1, Math.min(1, audioData[i]));
        s = s < 0 ? s * 0x8000 : s * 0x7FFF;
        view.setInt16(offset, s, true);
        offset += 2;
    }

    return new Blob([view], { type: 'audio/wav' });
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

// --- 1. Login Logic ---
loginButton.addEventListener("click", async () => {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    
    loginStatus.textContent = "Logging in...";
    loginStatus.className = "status-message";
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });
        
        if (!response.ok) {
            try {
                const errorData = await response.json();
                throw new Error(errorData.detail); 
            } catch (e) {
                throw new Error("Login failed. Is the backend server running?");
            }
        }
        
        const data = await response.json();
        userToken = data.access_token;
        
        loginStatus.textContent = "Login successful!";
        loginStatus.className = "status-message success";
        
        // Initialize Audio Context on click (browser requirement)
        await initAudio();

        setTimeout(() => {
            loginContainer.style.display = "none";
            assistantContainer.style.display = "flex"; 
            speakResponse("Welcome back! How can I help you?");
        }, 800);

    } catch (error) {
        loginStatus.textContent = error.message; 
        loginStatus.className = "status-message error";
    }
});

// --- 2. Enrollment Logic ---
async function recordSample(sampleNumber) {
    if (!audioContext) await initAudio();
    if (audioContext.state === 'suspended') await audioContext.resume();

    const button = document.getElementById(`enroll-button-${sampleNumber}`);
    const nextButton = document.getElementById(`enroll-button-${sampleNumber + 1}`);
    
    button.innerHTML = '<i class="fa-solid fa-circle fa-beat"></i>';
    button.disabled = true;
    
    // Create a ScriptProcessorNode to capture audio
    const bufferSize = 4096;
    const recorderNode = audioContext.createScriptProcessor(bufferSize, 1, 1);
    const audioData = [];

    recorderNode.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        for (let i = 0; i < inputData.length; i++) {
            audioData.push(inputData[i]);
        }
    };

    mediaStreamSource.connect(recorderNode);
    recorderNode.connect(audioContext.destination);

    // Stop after 3 seconds
    setTimeout(() => {
        mediaStreamSource.disconnect(recorderNode);
        recorderNode.disconnect(audioContext.destination);
        
        // Convert to WAV blob
        const wavBlob = exportWAV(audioData, audioContext.sampleRate);
        audioBlobs.push(wavBlob);

        button.innerHTML = '<i class="fa-solid fa-check"></i>';
        button.style.background = "#dcfce7";
        button.style.color = "#166534";
        enrollStatus.textContent = `Sample ${sampleNumber} captured.`;
        
        if (nextButton) {
            nextButton.disabled = false;
        } else {
            submitEnrollment.style.display = "block";
        }
    }, 3000);
}

enrollButton1.addEventListener("click", () => recordSample(1));
enrollButton2.addEventListener("click", () => recordSample(2));
enrollButton3.addEventListener("click", () => recordSample(3));

submitEnrollment.addEventListener("click", async () => {
    if (audioBlobs.length !== 3) {
        enrollStatus.textContent = "Please record all 3 samples.";
        return;
    }
    
    enrollStatus.textContent = "Uploading...";
    enrollStatus.className = "status-message";
    
    const formData = new FormData();
    formData.append("file1", audioBlobs[0], "sample1.wav");
    formData.append("file2", audioBlobs[1], "sample2.wav");
    formData.append("file3", audioBlobs[2], "sample3.wav");
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/enroll-voice`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${userToken}` },
            body: formData,
        });
        
        if (!response.ok) throw new Error("Enrollment failed.");
        
        const data = await response.json();
        enrollStatus.textContent = "Voice ID Enabled";
        enrollStatus.className = "status-message success";
        
        setTimeout(() => {
            document.getElementById("enrollment-section").style.display = "none";
            speakResponse("Voice enrollment complete. Your account is now secured.");
        }, 1500);

    } catch (error) {
        console.error(error);
        enrollStatus.textContent = "Error: " + error.message;
        enrollStatus.className = "status-message error";
    }
});

// --- 3. Voice Input (Speech-to-Text) ---
speakButton.addEventListener("mousedown", () => {
    speakButton.classList.add("listening");
    recognition.start();
});

speakButton.addEventListener("mouseup", () => {
    speakButton.classList.remove("listening");
    recognition.stop();
});

recognition.onresult = (event) => {
    const spokenText = event.results[0][0].transcript;
    addLog("user", spokenText);
    processVoiceCommand(spokenText);
};

recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    speakButton.classList.remove("listening");
};

// --- 4. Command Processing ---
async function processVoiceCommand(text) {
    try {
        const response = await fetch(`${API_BASE_URL}/detect-intent`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text }),
        });
        
        if (!response.ok) throw new Error("Connection to brain failed.");
        
        const nluData = await response.json();
        const intent = nluData.intent;
        const params = nluData.parameters;
        
        console.log("NLU Intent:", intent, "Params:", params);

        switch (intent) {
            case "check_balance":
                await handleGetBalance();
                break;
            case "get_history":
                await handleGetHistory();
                break;
            case "greet":
            case "goodbye":
                speakResponse(nluData.response_text);
                break;
            case "transfer_funds":
                if (params.amount && params.person) {
                    await initiateTransferFlow(params.person, params.amount);
                } else {
                    speakResponse(nluData.response_text);
                }
                break;
            default:
                speakResponse(nluData.response_text || "I didn't quite catch that.");
        }

    } catch (error) {
        console.error("Error:", error);
        speakResponse("Sorry, I'm having trouble connecting to my brain.");
    }
}

// --- 5. API Handlers ---

async function handleGetBalance() {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/balance`, {
            headers: { "Authorization": `Bearer ${userToken}` }
        });
        const data = await response.json();
        const firstAccount = data[0];
        speakResponse(`Your ${firstAccount.account_type} account has $${firstAccount.balance}.`);
    } catch (error) {
        speakResponse("Sorry, I couldn't get your balance.");
    }
}

async function handleGetHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/history`, {
            headers: { "Authorization": `Bearer ${userToken}` }
        });
        const data = await response.json();
        const lastTransaction = data[0];
        speakResponse(`Last transaction was $${lastTransaction.amount} at ${lastTransaction.description}.`);
    } catch (error) {
        speakResponse("Sorry, couldn't load history.");
    }
}

async function handleGetLoanInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/loans/info`);
        const data = await response.json();
        const personalLoan = data.find(loan => loan.loan_type === 'personal');
        speakResponse(`Personal loans are at ${personalLoan.interest_rate} percent interest.`);
    } catch (error) {
        speakResponse("Couldn't load loan info.");
    }
}

// --- 6. SECURE TRANSFER FLOW (NEW) ---

async function initiateTransferFlow(recipient, amount) {
    // Store transfer details
    pendingTransfer = { recipient, amount };
    
    speakResponse(`You want to send ${amount} to ${recipient}. For security, please say your 4-digit PIN.`);
    
    // Start listening for PIN
    setTimeout(() => {
        recognition.start();
    }, 3000);
}

// Listen for PIN during transfer
recognition.onresult = async (event) => {
    const spokenText = event.results[0][0].transcript;
    addLog("user", spokenText);
    
    // If we're waiting for a PIN
    if (pendingTransfer && !pendingTransfer.pinVerified) {
        // Extract digits from speech (e.g., "one two three four" or "1234")
        const pin = extractPIN(spokenText);
        
        if (pin) {
            await verifyPINAndVoice(pin);
        } else {
            processVoiceCommand(spokenText);
        }
    } else {
        processVoiceCommand(spokenText);
    }
};

function extractPIN(text) {
    // Remove spaces and extract only digits
    const digitWords = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'
    };
    
    let pin = '';
    const words = text.toLowerCase().split(' ');
    
    for (let word of words) {
        if (digitWords[word]) {
            pin += digitWords[word];
        } else if (/^\d$/.test(word)) {
            pin += word;
        }
    }
    
    // Check if we got exactly 4 digits
    if (pin.length === 4) {
        return pin;
    }
    
    // Try direct extraction from text
    const directMatch = text.match(/\b\d{4}\b/);
    return directMatch ? directMatch[0] : null;
}

async function verifyPINAndVoice(pin) {
    try {
        // Step 1: Verify PIN
        speakResponse("Verifying your PIN...");
        
        const pinResponse = await fetch(`${API_BASE_URL}/auth/verify-pin`, {
            method: "POST",
            headers: { 
                "Authorization": `Bearer ${userToken}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ pin })
        });
        
        if (!pinResponse.ok) {
            throw new Error("Invalid PIN. Transfer cancelled.");
        }
        
        pendingTransfer.pinVerified = true;
        pendingTransfer.pin = pin;
        
        // Step 2: Request voice verification
        speakResponse("PIN correct. Now please say: My voice is my password.");
        
        // Wait and then start recording for voice verification
        setTimeout(async () => {
            await recordVoiceVerification();
        }, 3000);
        
    } catch (error) {
        speakResponse(error.message || "Security verification failed. Transfer cancelled.");
        pendingTransfer = null;
    }
}

async function recordVoiceVerification() {
    if (!audioContext) await initAudio();
    if (audioContext.state === 'suspended') await audioContext.resume();
    
    speakResponse("Recording now...");
    
    const bufferSize = 4096;
    const recorderNode = audioContext.createScriptProcessor(bufferSize, 1, 1);
    const audioData = [];

    recorderNode.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        for (let i = 0; i < inputData.length; i++) {
            audioData.push(inputData[i]);
        }
    };

    mediaStreamSource.connect(recorderNode);
    recorderNode.connect(audioContext.destination);

    // Stop after 3 seconds
    setTimeout(async () => {
        mediaStreamSource.disconnect(recorderNode);
        recorderNode.disconnect(audioContext.destination);
        
        const wavBlob = exportWAV(audioData, audioContext.sampleRate);
        
        // Verify voice
        await verifyVoiceAndCompleteTransfer(wavBlob);
        
    }, 3000);
}

async function verifyVoiceAndCompleteTransfer(voiceBlob) {
    try {
        speakResponse("Verifying your voice...");
        
        const formData = new FormData();
        formData.append("file", voiceBlob, "verify.wav");
        
        const voiceResponse = await fetch(`${API_BASE_URL}/auth/verify-voice`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${userToken}` },
            body: formData
        });
        
        if (!voiceResponse.ok) {
            throw new Error("Voice verification failed. Transfer cancelled for your security.");
        }
        
        // Both verifications passed - complete the transfer
        await executeTransfer();
        
    } catch (error) {
        speakResponse(error.message || "Voice verification failed. Transfer cancelled.");
        pendingTransfer = null;
    }
}

async function executeTransfer() {
    try {
        speakResponse("Processing transfer...");
        
        const response = await fetch(`${API_BASE_URL}/transfer`, {
            method: "POST",
            headers: { 
                "Authorization": `Bearer ${userToken}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                recipient: pendingTransfer.recipient,
                amount: parseFloat(pendingTransfer.amount),
                currency: "USD",
                pin: pendingTransfer.pin
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Transfer failed");
        }
        
        const data = await response.json();
        speakResponse(`Success! Transferred ${pendingTransfer.amount} to ${pendingTransfer.recipient}. Your new balance is ${data.new_balance} dollars.`);
        
        // Clear pending transfer
        pendingTransfer = null;
        
    } catch (error) {
        speakResponse(error.message || "Sorry, the transfer failed.");
        pendingTransfer = null;
    }
}

// --- 7. Utilities ---
function speakResponse(text) {
    addLog("bot", text);
    const utterance = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utterance);
}

function addLog(sender, text) {
    const logItem = document.createElement("div");
    logItem.classList.add("log-item", sender);
    logItem.textContent = text;
    conversationLog.appendChild(logItem);
    conversationLog.scrollTop = conversationLog.scrollHeight;
}