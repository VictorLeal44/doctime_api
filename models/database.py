import os
from typing import Union

from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine

# Obtiene la URL de la variable de entorno (por defecto usa localhost para desarrollo)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/postgres")

# Corrección obligatoria: SQLAlchemy / SQLModel requiere 'postgresql://' en lugar de 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
