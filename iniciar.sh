sudo systemctl start postgresql

source ./venv/bin/activate
fastapi dev
# uvicorn app:app --host https://doctime-api-2vo5.onrender.com --port 8000 --reload
# uvicorn main:app --reload
