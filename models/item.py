from datetime import date, datetime, time
from typing import List, Optional

from sqlalchemy import CHAR
from sqlmodel import Field, Relationship, SQLModel

# ==========================================
# 1. TABLAS DE CATÁLOGOS
# ==========================================


class Rol(SQLModel, table=True):
    __tablename__: str = "rol"

    id: Optional[int] = Field(default=None, primary_key=True)
    rol: str = Field(sa_type=CHAR(50))

    # Relaciones
    usuarios: List["Usuarios"] = Relationship(back_populates="rol")


class Estado(SQLModel, table=True):
    __tablename__: str = "estado"

    id: Optional[int] = Field(default=None, primary_key=True)
    estado: str = Field(sa_type=CHAR(50))

    # Relaciones
    citas: List["Citas"] = Relationship(back_populates="estado")
    dias_libres: List["Dias_libres"] = Relationship(back_populates="estado")


class Especialidad(SQLModel, table=True):
    __tablename__: str = "especialidad"

    id: Optional[int] = Field(default=None, primary_key=True)
    especialidad: str = Field(sa_type=CHAR(100))

    # Relaciones
    medicos: List["Medicos"] = Relationship(back_populates="especialidad")
    citas: List["Citas"] = Relationship(back_populates="especialidad")


class GrupoSanguineo(SQLModel, table=True):
    __tablename__: str = "grupo_sanguineo"

    id: Optional[int] = Field(default=None, primary_key=True)
    grupo_sanguineo: str = Field(sa_type=CHAR(10))

    # Relaciones
    pacientes: List["Pacientes"] = Relationship(back_populates="grupo_sanguineo")


class Dias(SQLModel, table=True):
    __tablename__ = "dias"

    id: Optional[int] = Field(default=None, primary_key=True)
    dias: Optional[str] = Field(default=None, max_length=10)

    # Relaciones corregidas para hacer match con Horarios
    horarios: List["Horarios"] = Relationship(back_populates="dia")

class SystemSetting(SQLModel, table=True):
    __tablename__ = "systemsetting"

    id: Optional[int] = Field(default=None, primary_key=True)
    qr_descripcion: str

# ==========================================
# 2. TABLAS PRINCIPALES
# ==========================================


class Usuarios(SQLModel, table=True):
    __tablename__: str = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_completo: str = Field(sa_type=CHAR(150))
    cedula: int
    email: str = Field(sa_type=CHAR(100))
    contraseña: bytes  # Mapea directo a BYTEA

    rol_id: int = Field(foreign_key="rol.id")

    # Relaciones
    rol: Rol = Relationship(back_populates="usuarios")

    medicos: List["Medicos"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    pacientes: List["Pacientes"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    notificaciones: List["Notificaciones"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Horarios(SQLModel, table=True):
    __tablename__ = "horarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    dias_id: int = Field(foreign_key="dias.id")
    hora_de_entrada: time
    hora_de_salida: time
    medico_id: int = Field(foreign_key="medicos.id", ondelete="CASCADE", nullable=False)
    activo : bool

    medico: Optional["Medicos"] = Relationship(back_populates="horarios")
    dia: Optional[Dias] = Relationship(back_populates="horarios")

class Dias_libres(SQLModel, table=True):
    __tablename__ = "dias_libres"

    id: Optional[int] = Field(default=None, primary_key=True)
    medico_id: int = Field(foreign_key="medicos.id", ondelete="CASCADE", nullable=False)
    inicio: date
    final: date
    estado_id : int = Field(foreign_key="estado.id")

    medico: Optional["Medicos"] = Relationship(back_populates="dias_libres")
    estado: Optional[Estado] = Relationship(back_populates="dias_libres")


class Medicos(SQLModel, table=True):
  __tablename__ = "medicos"

  id: Optional[int] = Field(default=None, primary_key=True)

  usuarios_id: int = Field(
      foreign_key="usuarios.id", unique=True, nullable=False, ondelete="CASCADE"
  )

  especialidad_id: int = Field(foreign_key="especialidad.id", nullable=False)

  usuario: Optional[Usuarios] = Relationship(back_populates="medicos")
  especialidad: Optional[Especialidad] = Relationship(back_populates="medicos")
  horarios: List["Horarios"] = Relationship(
      back_populates="medico",
      sa_relationship_kwargs={"cascade": "all, delete-orphan"},
  )
  dias_libres: List["Dias_libres"] = Relationship(
      back_populates="medico",
      sa_relationship_kwargs={"cascade": "all, delete-orphan"},
  )
  citas: List["Citas"] = Relationship(back_populates="medico")


class Pacientes(SQLModel, table=True):
    __tablename__: str = "pacientes"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuarios_id: int = Field(foreign_key="usuarios.id")
    fecha_de_nacimiento: date
    direccion: str
    telefono_de_emergencia: int = Field(alias="telefono_de_emergencia")
    grupo_sanguineo_id: int = Field(foreign_key="grupo_sanguineo.id")

    # Relaciones
    usuario: Usuarios = Relationship(back_populates="pacientes")
    grupo_sanguineo: GrupoSanguineo = Relationship(back_populates="pacientes")
    citas: List["Citas"] = Relationship(back_populates="paciente")


class Citas(SQLModel, table=True):
    __tablename__: str = "citas"

    id: Optional[int] = Field(default=None, primary_key=True)
    pacientes_id: int = Field(foreign_key="pacientes.id")
    medicos_id: int = Field(foreign_key="medicos.id")
    fecha_de_encuentro: date
    hora_de_encuentro: time
    asunto: str = Field(sa_type=CHAR(255))
    enviado: date
    estado_id: int = Field(foreign_key="estado.id")
    especialidad_id: int = Field(foreign_key="especialidad.id")

    # Relaciones
    paciente: Pacientes = Relationship(back_populates="citas")
    medico: Medicos = Relationship(back_populates="citas")
    estado: Estado = Relationship(back_populates="citas")
    especialidad: Especialidad = Relationship(back_populates="citas")

class Notificaciones(SQLModel, table=True):
    __tablename__ = "notificaciones"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    usuario_id: int = Field(
      foreign_key="usuarios.id", index=True, nullable=False
  )
    titulo: str = Field(max_length=150, nullable=False)
    descripcion: str = Field(nullable=False)
    leida: bool = Field(default=False, nullable=False)
    fecha_de_creacion: datetime = Field(
      default_factory=datetime.utcnow, nullable=False
    )

    usuario: Optional[Usuarios] = Relationship(back_populates="notificaciones")
# ==========================================
# 3. TABLA INDEPENDIENTE
# ==========================================


class Admin(SQLModel, table=True):
    __tablename__: str = "admin"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario: str = Field(sa_type=CHAR(50))
    email: str = Field(sa_type=CHAR(100))
    contraseña: bytes
