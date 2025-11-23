This is a full-stack prototype of a modern NeoBank application, demonstrating a robust backend API built with FastAPI and an interactive frontend client using plain HTML/CSS/JavaScript. It focuses on integrating traditional banking functionalities with advanced, modern features like PIN authentication, Multi-Factor Voice Biometrics, and a powerful Generative AI-powered Conversational NLU engine for instant user interaction.

🛠️ Tech Stack
Backend: Python, FastAPI (Async API framework)

Database: SQLAlchemy (Async ORM)

Authentication: JWT, OAuth2 Password Bearer, Bcrypt for hashing.

AI/ML: Google Gemini 2.5 Flash for Natural Language Understanding (NLU), SpeechBrain for Automatic Speech Recognition (ASR) and Voice Biometrics.

Frontend: HTML, CSS, JavaScript (Vanilla JS for simplicity and performance).

✨ Features
User Management: Register and Login (JWT-based authentication).

Account/Transaction Management: View account balances and transaction history.

Secure Transfers: Initiate money transfers, secured by a mandatory Transaction PIN.

Multi-Factor Authentication (MFA):

PIN Management: Set and verify a transaction-specific PIN.

Voice Biometrics: Enroll and verify a user's voice for high-security actions.

Conversational AI Assistant:

Speech-to-Text (ASR): Converts spoken commands into text using SpeechBrain.

Intent Detection (NLU): Uses the Gemini 2.5 Flash API to detect banking intents (e.g., check_balance, transfer_money) and extract parameters (e.g., amount, recipient).

🚀 Installation & Setup
Clone the repository.

Set up the Python environment:

Bash

pip install fastapi uvicorn sqlalchemy python-jose[cryptography] passlib[bcrypt] pydantic aiofiles google-genai speechbrain torch numpy librosa soundfile
Note: Torch/SpeechBrain installation might require specific system dependencies.

Configure Environment Variables: Set the following in your environment or a .env file for the backend:

SECRET_KEY: A strong, random string for JWT signing.

ALGORITHM: JWT algorithm (e.g., HS256).

GEMINI_API_KEY: Your Google AI Studio API key.

VOICE_VERIFICATION_THRESHOLD: A float (e.g., 0.5) for voice verification.

Run the FastAPI Backend:

Bash

uvicorn backend.app:app --reload
The API will be available at http://127.0.0.1:8000.

Access the Frontend: Navigate to the frontend directory: cd frontend

Start the simple Python web server:

# This serves the files on port 8001
python -m http.server 8001




