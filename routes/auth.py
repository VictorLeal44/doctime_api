import email

from fastapi import APIRouter, Depends, HTTPException, status, Header
from psycopg2 import sql
from sqlalchemy.orm import selectinload
from sqlalchemy import true
from sqlmodel import Session, select, exists
from models.database import get_session
from models.item import Admin, Usuarios, Pacientes, Medicos
from security.security import *
from schemas.form import LoginForm, LoginFormAdmin, PacienteRead,MedicoSessionOut, SinginForm, HorarioOut

router = APIRouter()

@router.get("/user_exists")
def user_exists(x_setup_key: str = Header(alias="Key"), session: Session = Depends(get_session)):
    print(x_setup_key)
    if SECRET_KEY == x_setup_key:
        statement = select(exists().where(Admin.id != None))
        resultado = session.exec(statement).one()
        print(resultado)
        return {"exists": resultado}
    raise HTTPException(status_code=403, detail="Clave incorrecta")

@router.post("/login_user")
def login(data: LoginForm, session: Session = Depends(get_session)):
    try:
        print(data.Email,data.Contraseña)
        statement = select(Usuarios).where(Usuarios.email == data.Email)
        usuario = session.exec(statement).first()

        if not usuario:
            return {"mensaje": [], "mensaje": "Correo incorrecto"}

        # 2. Verificamos la contraseña
        if not verificar_contrasena(data.Contraseña, usuario.contraseña):
            return {'mensaje':'Contraseña incorrecta'}

        statement_paciente = select(Pacientes).where(Pacientes.usuarios_id == usuario.id)
        paciente = session.exec(statement_paciente).first()

        if paciente:
            paciente_data = PacienteRead(
                usuarioId=usuario.id,
                paciente_id=paciente.id,
                fecha_de_nacimiento=paciente.fecha_de_nacimiento,
                direccion=paciente.direccion,
                telefono_de_emergencia=paciente.telefono_de_emergencia,
                grupo_sanguineo_id=paciente.grupo_sanguineo_id,
                nombre_completo=usuario.nombre_completo,
                cedula=usuario.cedula,
                email=usuario.email,
                rol_id=usuario.rol_id,
            )
            return {"tipo": "paciente", "datos": [paciente_data], "mensaje": "realizado"}

        statement_medico = (
            select(Medicos)
            .where(Medicos.usuarios_id == usuario.id)
            .options(selectinload(Medicos.horarios))
        )
        medico = session.exec(statement_medico).first()
        print("este es el id de usuario y medico",usuario.id,medico.id)
        if medico:
            medico_data = MedicoSessionOut(
                usuarioId=usuario.id,
                medico_id=medico.id,
                nombre_completo=usuario.nombre_completo.strip(),
                cedula=str(usuario.cedula),
                email=usuario.email.strip(),
                rol_id=usuario.rol_id,
                medicoId=medico.id,
                especialidadId=medico.especialidad_id,
                horarios=[
                    HorarioOut(
                        id=h.id,
                        dias_id=h.dias_id,
                        hora_de_entrada=h.hora_de_entrada,
                        hora_de_salida=h.hora_de_salida,
                        activo=h.activo,
                    )
                    for h in medico.horarios
                ],
            )
            return {"tipo": "medico", "datos": [medico_data], "mensaje": "realizado"}

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no tiene un perfil de paciente ni de médico asociado."
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        session.rollback()
        print("--- ERROR EXACTO DE PYTHON ---")
        traceback.print_exc()  # Imprime la línea exacta del fallo en la consola de FastAPI
        print("------------------------------")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al iniciar sesión: {str(e)}"
        )

@router.post("/login_admin")
# Si es un formulario, usa Form() para cada campo
def login_admin(data : LoginFormAdmin, session: Session = Depends(get_session)):
    print(f"Login de: {data}")
    statement = select(Admin).where(Admin.usuario == data.usuario)
    usuario = session.exec(statement).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado")
    if not verificar_contrasena(data.contraseña, usuario.contraseña):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta"
        )
    return {"mensaje":"aceptado"}

@router.post("/signin_admin")
def signin_admin(data: SinginForm, session: Session = Depends(get_session)):
    try:
        # Generar hash en bytes (ejemplo con bcrypt)
        password_en_bytes = generar_hash_contrasena(data.contraseña)

        nuevo_admin = Admin(
            usuario=data.usuario,
            email=data.email,
            contraseña=password_en_bytes
        )

        session.add(nuevo_admin)
        session.commit()
        session.refresh(nuevo_admin)

        return {
            "mensaje": "aceptado",
        }

    except Exception as e:
        session.rollback()
        return {
            "mensaje": "rechazado",
        }

@router.post("/new_password_admin")
# Recibe el email para saber a quién actualizar
def new_password_admin(email: str, password: str, session: Session = Depends(get_session)):
    statement = select(Admin).where(Admin.email == email)
    admin_user = session.exec(statement).first()
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
    # Aquí iría la lógica de hashing y guardado
    return {"status": "actualizado"}
