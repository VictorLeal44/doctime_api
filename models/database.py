import os
from typing import Union
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine

# 1. Leer la variable de entorno de Render, con respaldo por si estás probando local
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/postgres")

# 2. Render a veces provee la URL con 'postgres://', SQLAlchemy requiere 'postgresql://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
