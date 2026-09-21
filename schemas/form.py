from pydantic import BaseModel
from typing import Optional
from datetime import date, time
from typing import List, Optional

class CitaCreate(BaseModel):
    pacientes_id: int
    asunto: str
    especialidad_id: int


# 1. Esquema para recibir los datos del Horario
class HorarioCreate(BaseModel):
    dias_id: int
    hora_de_entrada: time
    hora_de_salida: time
    medico_id: int

# 2. Esquema para recibir la relación con el Médico (y su horario)
class MedicoCreateNested(BaseModel):
    especialidad_id: int
    #horario: HorarioCreate  # Se puede enviar el horario directamente al crear el médico


# 3. Esquema Principal de Registro
class UsuarioMedicoCreate(BaseModel):
    nombre_completo: str
    cedula: int
    email: str
    contraseña: str
    rol_id : int
    medico: Optional[MedicoCreateNested] = None

class UsuarioMedicoEdit(BaseModel):
    nombre_completo: str
    cedula: int
    email: str
    medico: Optional[MedicoCreateNested] = None

class PacienteCreateNested(BaseModel):
    fecha_de_nacimiento: date
    telefono: str
    direccion: str
    tipo_de_sangre: int

class UsuarioPacienteCreate(BaseModel):
    nombre_completo : str
    cedula: int
    email: str
    contraseña: str

    paciente: Optional[PacienteCreateNested] = None


class UsuarioPacienteEdit(BaseModel):
    nombre_completo : str
    cedula: int
    email: str

    paciente: Optional[PacienteCreateNested] = None

class LoginForm(BaseModel):
    Email : str
    Contraseña : str

class LoginFormAdmin(BaseModel):
    usuario : str
    contraseña : str

class SinginForm(BaseModel):
    usuario: str
    email: str
    contraseña: str

class PacienteRead(BaseModel):
    # Datos del Paciente (excluyendo usuarios_id repetido)
    usuarioId: int
    paciente_id: int
    fecha_de_nacimiento: date
    direccion: str
    telefono_de_emergencia: int
    grupo_sanguineo_id: int

    # Datos del Usuario (excluyendo contraseña)
    nombre_completo: str
    cedula: int
    email: str
    rol_id: int

class HorarioOut(BaseModel):
    id: int
    dias_id: int
    hora_de_entrada: time
    hora_de_salida: time
    activo : bool

    # class Config:
    #     from_attributes = True

class MedicoSessionOut(BaseModel):
    # Datos de tabla usuarios
    usuarioId: int
    medico_id: int
    nombre_completo: str
    cedula: str
    email: str
    rol_id: int

    # Datos de tabla medicos
    medicoId: int
    especialidadId: int
    horarios: List[HorarioOut]

    class Config:
        from_attributes = True

class AceptCita(BaseModel):
    id : int
    fecha : date
    hora : time
    medico_id : int

class CitaRecordResponse(BaseModel):
    id: Optional[int] = None
    Paciente: str
    Paciente_id: int
    Asunto: str
    Especialidad_id: Optional[int] = None

class MedicoResponse(BaseModel):
    id: int
    medico_name: str
    especialidad_id: int

class Horario(BaseModel):
    dias_id: int
    hora_de_entrada: time
    hora_de_salida: time
    activo: bool

class HorarioUpdate(BaseModel):
    horario_list: List[Horario]

class dias_libres(BaseModel):
    medico_id: int
    inicio: date
    final: date

class NotificacionesCreated(BaseModel):
    usuarios_id: int
    titulo: str
    descripcion: str
