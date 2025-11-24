🚀 NeoBank – AI-Powered Modern Banking System

This project is a full-stack prototype of a modern NeoBank application, combining a secure backend built with FastAPI and an interactive frontend using HTML/CSS/JavaScript.
It integrates traditional banking features with next-generation AI capabilities, including:

🔐 Transaction PIN authentication

🔊 Multi-Factor Voice Biometrics

🤖 Generative AI–powered Conversational Banking Assistant

🛠️ Tech Stack
Backend

Python 3.10

FastAPI (Async API Framework)

SQLAlchemy (Async ORM)

Authentication: JWT, OAuth2 Password Bearer

Bcrypt for password hashing

SpeechBrain for Speaker Verification & Speech-to-Text

Google Gemini 2.5 Flash for NLU / intent detection

Torch, Librosa, Soundfile for audio processing

Frontend

HTML

CSS

JavaScript (Vanilla JS for lightweight performance)

✨ Features
🔑 User Authentication

Register

Login

JWT-secured sessions

Password hashing with Bcrypt

💳 Account & Transaction Management

View account balance

View full transaction history

Transfer funds

🔐 Security

Transaction PIN (Set + Verify)

Multi-Factor Authentication

PIN Verification

Voice Biometrics Authentication

Voice Enrollment

Voice Verification

🤖 AI Conversational Assistant

Speech-to-Text (ASR) using SpeechBrain

Intent Recognition (NLU) using Gemini Flash

Supports commands like:

“Check my balance”

“Send ₹500 to Amit”

“Show my last 5 transactions”

🚀 Installation & Setup
1️⃣ Clone the Repository
git clone -b sayyam-3 https://github.com/sayyam2002/AI_Voice_Banking_Assistant/edit/sayyam-3
cd AI_Voice_Banking_Assistant

2️⃣ Backend Setup
Create Virtual Environment
cd backend
py -3.10 -m venv venv
venv\Scripts\activate

Install Dependencies
python -m pip install --upgrade pip

pip install fastapi "uvicorn[standard]" pydantic pydantic-settings httpx
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu
pip install speechbrain --no-deps
pip install hyperpyyaml sentencepiece
pip install huggingface_hub==0.14.1 --no-deps
pip install python-multipart
pip install sqlalchemy asyncpg "pydantic[email]" passlib "python-jose[cryptography]" packaging
pip install joblib scipy "tqdm>=4.42.1"
pip install bcrypt
pip install google-generativeai
pip install librosa
pip install soundfile
pip install asgiref

Freeze requirements
pip freeze > requirements.txt

3️⃣ Environment Variables

Create a .env file inside /backend:

SECRET_KEY=your-strong-secret-key
ALGORITHM=HS256
DATABASE_URL=postgresql+asyncpg://postgres:YOURPASSWORD@localhost:5432/neobank
GEMINI_API_KEY=your-gemini-api-key
VOICE_VERIFICATION_THRESHOLD=0.5

4️⃣ Database Setup (PostgreSQL)

Install PostgreSQL 18.1

At final step, check Stack Builder

Inside Stack Builder:

Categories → Add-ons → pgAgent

Open pgAdmin → Connect to server

Create database:

neobank

5️⃣ Start Backend
uvicorn backend.app:app --reload --port 8000


Backend API will run at:

📍 http://127.0.0.1:8000

🎨 Frontend Setup
Start Frontend Server
cd frontend
python -m http.server 8001


Frontend will be live at:
http://127.0.0.1:8001


