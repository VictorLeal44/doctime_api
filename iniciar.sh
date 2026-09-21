sudo systemctl start postgresql

source ./venv/bin/activate
fastapi dev
# uvicorn app:app --host 0.0.0.0 --port 8000 --reload
# uvicorn main:app --reload
