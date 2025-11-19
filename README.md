# AI_Voice_Banking_Assistant
This is an AI Voice Assistant for Banking Application
AI Voice Assistant for Financial Operations

This is a proof-of-concept for an AI-powered Voice Banking Assistant, built for the "AI Voice Assistant for Financial Operations" challenge.

It allows users to perform mock financial operations using natural language voice commands. The project focuses on privacy and control by using the open-source Rasa NLU for all intent processing, ensuring no user conversation data is sent to third-party cloud services.

Project Architecture

This project runs as three separate, communicating services:

Frontend (The "Face"): A simple HTML/CSS/JS web page (./frontend) that runs in the browser. It handles capturing the user's voice (Speech-to-Text) and speaking the assistant's responses (Text-to-Speech).

Backend (The "Conductor"): A FastAPI server (main.py) that acts as a secure proxy. It handles user login, manages banking logic (like checking balances), and communicates with the NLU "brain."

NLU (The "Brain"): A Rasa NLU server (./rasa_agent) that receives text from the backend, determines the user's intent (e.g., check_balance), and sends that structured intent back to the backend.

Prerequisites

Python 3.10 or Python 3.11.
(This project is NOT compatible with Python 3.12 or newer due to Rasa/TensorFlow dependencies).

A Python virtual environment.

A web browser that supports the Web Speech API (Google Chrome or Microsoft Edge are recommended).

Installation

Clone the repository (or ensure you have all the files in the AGENT folder).

Create and activate your virtual environment:
(From the AGENT directory)

# Make sure you are using Python 3.10 or 3.11
py -3.10 -m venv venv-rasa

# Activate the environment
.\venv-rasa\Scripts\activate


Install all required packages:

# This installs Rasa, FastAPI, Uvicorn, and httpx
pip install rasa fastapi "uvicorn[standard]" pydantic httpx


Train the NLU model:
This is a one-time setup step.

# Navigate into the rasa_agent folder
cd rasa_agent

# Train the NLU model
rasa train nlu

# Go back to the main project folder
cd ..


How to Run

You must run all three services simultaneously in three separate terminals.

➡️ Terminal 1: Start the "Brain" (Rasa NLU Server)

Open your first terminal.

Activate the virtual environment: .\venv-rasa\Scripts\activate

Navigate to the rasa_agent directory: cd rasa_agent

Start the Rasa server:

rasa run -m models --enable-api


Leave this terminal running. It will serve the NLU model on http://localhost:5005.

➡️ Terminal 2: Start the "Backend" (FastAPI Server)

Open a new terminal.

Navigate to the AGENT directory.

Activate the virtual environment: .\venv-rasa\Scripts\activate

Start the FastAPI server:

uvicorn main:app --reload


Leave this terminal running. It will serve the API on http://localhost:8000.

➡️ Terminal 3: Start the "Frontend" (Web Server)

Open a third terminal.

Navigate to the frontend directory: cd frontend

Start the simple Python web server:

# This serves the files on port 8001
python -m http.server 8001


Leave this terminal running.

How to Use

Open your web browser (Chrome or Edge) and go to: http://localhost:8001

Your browser will ask for microphone permission. Click Allow.

Log in using the mock credentials:

Username: user123

Password: password123

Click and hold the "Hold to Speak" button.

Try saying one of the following commands:

"What is my balance?"

"Show me my cash."

"What's my transaction history?"

"I want to send money." (The bot will ask follow-up questions).

"Send 50 dollars to Jane."

Project Structure

AGENT/
├── .gitignore              # Ignores venv and model files
├── main.py                 # (Terminal 2) The FastAPI Backend
├── README.md               # This file
├── frontend/               # (Terminal 3) The Webpage
│   ├── index.html
│   ├── script.js
│   └── style.css
├── rasa_agent/             # (Terminal 1) The NLU "Brain"
│   ├── config.yml          # Rasa: How to train
│   ├── domain.yml          # Rasa: List of intents/entities
│   ├── data/
│   │   └── nlu.yml         # Rasa: Training examples
│   └── models/
│       └── nlu-....tar.gz  # The trained model
└── venv-rasa/                # Python virtual environment (ignored by Git)