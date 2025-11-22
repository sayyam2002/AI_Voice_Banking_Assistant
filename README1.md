Backend initialization:
in terminal
cd backend
py -3.10 -m venv venv-rasa
venv-rasa\scripts\activate
python.exe -m pip install --upgrade pip
pip install fastapi "uvicorn[standard]" pydantic pydantic-settings httpx
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu
pip install speechbrain --no-deps
pip install hyperpyyaml sentencepiece
pip install huggingface_hub==0.14.1 --no-deps
pip install python-multipart
pip install sqlalchemy asyncpg 'pydantic[email]' passlib 'python-jose[cryptography]' packaging
pip install joblib scipy tqdm>=4.42.1
Then, 
pip freeze > requirements.txt

cd..
uvicorn backend.app:app --reload --port 8000

Database
install postgres 18.1
after installing at the last step there will be something called stack builder check that box.
in stack builder, categories->Add-ons->pgAgent
then click next
open pgAdmin
and connect to database instance
then create database called neobank

and thats it