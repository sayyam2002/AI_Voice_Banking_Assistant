// --- Globals ---
let userToken = null; // Stores the mock auth token
const API_BASE_URL = "http://127.0.0.1:8000"; // Our FastAPI backend

// --- Speech API Setup ---
// Check for browser support
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
    alert("Your browser does not support Speech Recognition. Please use Chrome or Edge.");
}
const recognition = new SpeechRecognition();
recognition.continuous = false; // Stop listening after one phrase
recognition.interimResults = false; // Get final results only
recognition.lang = 'en-US';

// --- DOM Elements ---
const loginContainer = document.getElementById("login-container");
const assistantContainer = document.getElementById("assistant-container");
const loginButton = document.getElementById("login-button");
const loginStatus = document.getElementById("login-status");
const speakButton = document.getElementById("speak-button");
const conversationLog = document.getElementById("conversation-log");

// --- 1. Login Logic ---
loginButton.addEventListener("click", async () => {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    
    loginStatus.textContent = "Logging in...";
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });
        
        // This is the new, improved part
        if (!response.ok) {
            // Get the REAL error message from the FastAPI server
            const errorData = await response.json();
            // The server sends {"detail": "Incorrect username or password"}
            throw new Error(errorData.detail); 
        }
        
        const data = await response.json();
        userToken = data.access_token; // Save the token
        
        // Hide login, show assistant
        loginStatus.textContent = "Login successful!";
        loginStatus.className = "status-message success";
        setTimeout(() => {
            loginContainer.style.display = "none";
            assistantContainer.style.display = "block";
            speakResponse("Welcome back! How can I help you?");
        }, 1000);

    } catch (error) {
        // This will now display the REAL server error
        loginStatus.textContent = error.message; 
        loginStatus.className = "status-message error";
    }
});

// --- 2. Voice Input (Speech-to-Text) ---
speakButton.addEventListener("mousedown", () => {
    speakButton.textContent = "Listening...";
    speakButton.classList.add("listening");
    recognition.start();
});

speakButton.addEventListener("mouseup", () => {
    speakButton.textContent = "Hold to Speak";
    speakButton.classList.remove("listening");
    recognition.stop();
});

// Handle the result from speech recognition
recognition.onresult = (event) => {
    const spokenText = event.results[0][0].transcript;
    addLog("user", spokenText);
    processVoiceCommand(spokenText);
};

recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    speakButton.textContent = "Hold to Speak";
    speakButton.classList.remove("listening");
};

// --- 3. Command Processing (The "Brain") ---
async function processVoiceCommand(text) {
    // This is a *very* simple NLU (Natural Language Understanding).
    // In the next phase, we will replace this with a real AI service.
    
    text = text.toLowerCase();
    
    if (text.includes("balance") || text.includes("how much money")) {
        await handleGetBalance();
    } else if (text.includes("history") || text.includes("transactions")) {
        await handleGetHistory();
    } else if (text.includes("loan") || text.includes("interest rate")) {
        await handleGetLoanInfo();
    } else if (text.includes("transfer") || text.includes("send money")) {
        // We'll add this later, as it's more complex (needs recipient, amount)
        speakResponse("Sorry, transfers are not fully implemented in this demo.");
    } else {
        speakResponse("I'm not sure I understood that. Can you try again?");
    }
}

// --- 4. API Handlers ---
// These functions call your FastAPI backend

async function handleGetBalance() {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/balance`, {
            headers: { "Authorization": `Bearer ${userToken}` }
        });
        const data = await response.json();
        
        // Format the API response into a natural sentence
        const firstAccount = data[0];
        const responseText = `Your ${firstAccount.account_type} account has a balance of $${firstAccount.balance}.`;
        speakResponse(responseText);

    } catch (error) {
        console.error("Error getting balance:", error);
        speakResponse("Sorry, I had trouble retrieving your balance.");
    }
}

async function handleGetHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/history`, {
            headers: { "Authorization": `Bearer ${userToken}` }
        });
        const data = await response.json();
        
        // Get the most recent transaction
        const lastTransaction = data[0];
        const responseText = `Your last transaction was for $${lastTransaction.amount} at ${lastTransaction.description}.`;
        speakResponse(responseText);

    } catch (error) {
        console.error("Error getting history:", error);
        speakResponse("Sorry, I had trouble retrieving your transaction history.");
    }
}

async function handleGetLoanInfo() {
    // This endpoint is public, no auth needed
    try {
        const response = await fetch(`${API_BASE_URL}/loans/info`);
        const data = await response.json();
        
        const personalLoan = data.find(loan => loan.loan_type === 'personal');
        const responseText = `We offer several products. For example, our personal loan has an interest rate of ${personalLoan.interest_rate} percent.`;
        speakResponse(responseText);

    } catch (error) {
        console.error("Error getting loan info:", error);
        speakResponse("Sorry, I had trouble getting loan information.");
    }
}


// --- 5. Voice Output (Text-to-Speech) ---
function speakResponse(text) {
    addLog("bot", text);
    
    const utterance = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utterance);
}

// --- 6. Utility ---
function addLog(sender, text) {
    const logItem = document.createElement("div");
    logItem.classList.add("log-item", sender);
    logItem.textContent = text;
    conversationLog.appendChild(logItem);
    // Scroll to bottom
    conversationLog.scrollTop = conversationLog.scrollHeight;
}