from fastapi import FastAPI

from routes.auth import router as auth_router
from routes.citas import router as citas_router
from routes.users import router as users_router

app = FastAPI()

app.include_router(citas_router, prefix="/v1", tags=["citas"])
app.include_router(users_router, prefix="/v1", tags=["users"])
app.include_router(auth_router, prefix="/v1", tags=["auth"])
