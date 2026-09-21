# from site import USER_BASE
from sys import exception

# from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from models.database import get_session
from models.item import *
from security.security import *
from schemas.form import *

from datetime import time, date, timedelta

router = APIRouter()


@router.get("/users/rol")
def get_all_users(rol=str,tamano_lote= int, session: Session = Depends(get_session)):
    offset_actual = 0
    resultados = []

    if rol == "medicos":
        # 1. Tu consulta original adaptada para traer los datos básicos de usuario y médico
        statement = (
            select(
                Usuarios.id,
                Usuarios.nombre_completo,
                Usuarios.cedula,
                Usuarios.email,
                Medicos.id.label("medico_id"),  # Alias para evitar confusiones con Usuarios.id
                Medicos.especialidad_id
            )
            .join(Medicos, Usuarios.id == Medicos.usuarios_id)
            .offset(offset_actual)
            .limit(tamano_lote)
        )

        filas = session.exec(statement).all()

        if not filas:
            raise HTTPException(
                status_code=404,
                detail="No existe en la base de datos.",
            )

        datos = []
        for row in filas:
            stmt_horarios = (
                select(
                    Dias.dias.label("dia_semana"),
                    Horarios.hora_de_entrada,
                    Horarios.hora_de_salida,
                    Horarios.activo,
                )
                .join(Dias, Dias.id == Horarios.dias_id)
                .where(Horarios.medico_id == row.medico_id)
                .order_by(Horarios.dias_id)
                .limit(7)
            )
            horarios_db = session.exec(stmt_horarios).all()

            horarios_list = [
                {
                    "dia_semana": str(h.dia_semana),
                    "hora_de_entrada": h.hora_de_entrada,
                    "hora_de_salida": h.hora_de_salida,
                    "activo": h.activo,
                }
                for h in horarios_db
            ]

            # 3. Construimos el diccionario exactamente como lo pide tu frontend
            datos.append({
                "id": row.id,
                "Nombre": row.nombre_completo,
                "Cedula": row.cedula,
                "Email": row.email,
                "medico_id": row.medico_id,
                "Especialidad": row.especialidad_id,
                "horarios": horarios_list,
            })

        return {"datos": datos}

    elif rol == "pacientes":
        statement = (
            select(
                Usuarios.id,
                Usuarios.nombre_completo,
                Usuarios.cedula,
                Usuarios.email,
                Pacientes.fecha_de_nacimiento,
                Pacientes.telefono_de_emergencia,
                Pacientes.direccion,
                Pacientes.grupo_sanguineo_id,
            )
            .join(Pacientes, Usuarios.id == Pacientes.usuarios_id)
            .offset(offset_actual)
            .limit(tamano_lote)
        )

        resultados = session.exec(statement).all()

        if not resultados:
            raise HTTPException(
                status_code=404,
                detail="No existe en la base de datos.",
            )

        # Convertimos cada tupla en un diccionario limpio y serializable
        pacientes_db = [
            {
                "id": row.id,
                "Nombre": row.nombre_completo,
                "Cedula": row.cedula,
                "Email": row.email,
                "Fecha_de_nacimiento": row.fecha_de_nacimiento,
                "Telefono": row.telefono_de_emergencia,
                "Direccion": row.direccion,
                "Tipo_de_sangre": row.grupo_sanguineo_id,
            }
            for row in resultados
        ]

        return {"datos": pacientes_db}

# @router.get("/get_medico/{especialidad_id}/{fecha}/{hora}")
@router.get("/get_medico")
def get_medico(especialidad_id: int, fecha: date, hora: time, session: Session = Depends(get_session)):
    try:
        # 1. Cálculo de día de la semana y rango de tiempo en memoria
        dt_inicio = datetime.combine(fecha, hora)
        dt_salida = dt_inicio + timedelta(minutes=30)
        hora_salida = dt_salida.time()
        dia_semana = fecha.weekday() + 1  # Lunes=1 ... Domingo=7

        # 2. ÚNICA CONSULTA: Seleccionamos los campos específicos que necesitas
        statement = (
            select(
                Medicos.id.label("medico_id"),
                Usuarios.nombre_completo.label("nombre_medico"),
                Horarios.id.label("horario_id"),
            )
            .join(Medicos, Horarios.medico_id == Medicos.id)
            .join(Usuarios, Medicos.usuarios_id == Usuarios.id)  # Join hacia usuarios
            .outerjoin(
                Citas,
                (Citas.medicos_id == Medicos.id) &
                (Citas.fecha_de_encuentro == fecha) &
                (Citas.hora_de_encuentro == hora)
            )
            .where(
                Medicos.especialidad_id == especialidad_id,
                Horarios.dias_id == dia_semana,
                Horarios.activo == True,
                Horarios.hora_de_entrada <= hora,
                Horarios.hora_de_salida >= hora_salida,
                Citas.id == None
            )
        )

        resultados = session.exec(statement).all()

        if not resultados:
            raise HTTPException(
                status_code=404,
                detail="No hay horarios ni médicos disponibles para la especialidad, fecha y hora solicitadas."
            )

        # 3. Formateamos la respuesta JSON de forma limpia
        datos_respuesta = [
            {
                "medico_id": fila.medico_id,
                "nombre_medico": fila.nombre_medico.strip() if isinstance(fila.nombre_medico, str) else fila.nombre_medico,
            }
            for fila in resultados
        ]

        return {
            'mensaje': 'funcionó',
            'datos': datos_respuesta,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("Error en get_medico:", e)
        session.rollback()
        return {"mensaje": "Fallido", "error": str(e)}


@router.post("/users/medicos")
def create_user_medicos(new_data: UsuarioMedicoCreate, session: Session = Depends(get_session)):
    try:
        # 1. Hashear contraseña y convertir a bytes (según tu modelo)
        # bytes_password = hash_password(datos.contraseña)
        password_en_bytes = generar_hash_contrasena(new_data.contraseña)
        # 2. Crear instancia de Usuario
        nuevo_usuario = Usuarios(
            nombre_completo=new_data.nombre_completo,
            cedula=new_data.cedula,
            email=new_data.email,
            contraseña=password_en_bytes,
            rol_id=new_data.rol_id
        )
        session.add(nuevo_usuario)
        session.flush()  # 'flush' genera el ID de nuevo_usuario sin hacer commit aún

        # 3. Si vienen datos de médico, creamos el Horario y el Médico
        if new_data.medico:
            # nuevo_horario = Horarios(
            #     dias_id=new_data.medico.horario.dias_id,
            #     hora_de_entrada=new_data.medico.horario.hora_de_entrada,
            #     hora_de_salida=new_data.medico.horario.hora_de_salida,
            #     turnos_id=new_data.medico.horario.turnos_id
            # )
            # session.add(nuevo_horario)
            # session.flush()  # Genera el ID de nuevo_horario

            nuevo_medico = Medicos(
                usuarios_id=nuevo_usuario.id,
                especialidad_id=new_data.medico.especialidad_id,
            )
            session.add(nuevo_medico)
            session.flush()
            print(nuevo_medico.id, '--------------------')


        for dia in range(7):
            nuevo_horario = Horarios(
                dias_id = dia+1,
                hora_de_entrada = time(0,0),
                hora_de_salida = time(0,0),
                medico_id = nuevo_medico.id,
                activo = False)

            session.add(nuevo_horario)

        # 4. Confirmar todos los cambios en la base de datos de un solo golpe
        session.commit()
        session.refresh(nuevo_usuario)

        return {"mensaje": "Médico registrado exitosamente", "id": nuevo_usuario.id}

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar el usuario: {str(e)}"
        )

@router.post("/users/paciente") #/v1/users/paciente
def create_user_paciente(new_data: UsuarioPacienteCreate, session: Session = Depends(get_session)):
    print(new_data)
    try:
        # bytes_password = hash_password(datos.contraseña)
        password_en_bytes = generar_hash_contrasena(new_data.contraseña)
        # 2. Crear instancia de Usuario
        nuevo_usuario = Usuarios(
            nombre_completo=new_data.nombre_completo,
            cedula=new_data.cedula,
            email=new_data.email,
            contraseña=password_en_bytes,
            rol_id= 1
        )
        session.add(nuevo_usuario)
        session.flush()  # 'flush' genera el ID de nuevo_usuario sin hacer commit aún

        # 3. Si vienen datos de médico, creamos el Horario y el Médico
        if new_data.paciente:

            nuevo_paciente = Pacientes(
                usuarios_id=nuevo_usuario.id,
                fecha_de_nacimiento = new_data.paciente.fecha_de_nacimiento,
                telefono_de_emergencia =new_data.paciente.telefono,
                direccion =new_data.paciente.direccion,
                grupo_sanguineo_id =new_data.paciente.tipo_de_sangre

            )
            session.add(nuevo_paciente)

        # 4. Confirmar todos los cambios en la base de datos de un solo golpe
        session.commit()
        session.refresh(nuevo_usuario)

        return {"mensaje": "Paciente registrado exitosamente", "id": nuevo_usuario.id}

    except Exception as e:
        session.rollback()  # Si algo falla, deshace todos los registros
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar el usuario: {str(e)}"
        )

@router.post("/users")
def create_user(user_data: Usuarios, session: Session = Depends(get_session)):
    try:
        statement = select(Usuarios).where(
            (Usuarios.cedula == str(user_data.cedula))
            | (Usuarios.email == user_data.email)
        )
        usuario_existente = session.exec(statement).first()

        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cédula o el correo electrónico ya se encuentran registrados.",
            )
        password_en_bytes = generar_hash_contrasena(user_data.contraseña)
        user_data.contraseña = password_en_bytes
        # print(user_data)
        session.add(user_data)
        session.rollback()
        # session.commit()
        return {"mensaje": "exitoso"}
    except Exception as e:
        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}

@router.put("/update_users/medic/{medico_id}")
def update_user_medic(
    medico_id: int, datos_nuevos: UsuarioMedicoEdit, session: Session = Depends(get_session)
):
    try:
        statement = select(Usuarios).where(Usuarios.id == medico_id)
        usuario = session.exec(statement).first()
        if usuario is None:
            print("no existe en la base de datos.")
            raise HTTPException(
                status_code=404,
                detail="no existe en la base de datos.",
            )
        usuario.nombre_completo = datos_nuevos.nombre_completo
        usuario.cedula = datos_nuevos.cedula
        usuario.email = datos_nuevos.email

        session.add(usuario)
        #Session.rollback()
        session.commit()

        statement_medico = select(Medicos).where(Medicos.usuarios_id == medico_id)
        medico = session.exec(statement_medico).first()
        if medico is None:
            print("no existe en la base de datos.")
            raise HTTPException(
                status_code=404,
                detail="no existe en la base de datos.",
            )
        medico.especialidad_id = datos_nuevos.medico.especialidad_id

        session.add(medico)
        #Session.rollback()
        session.commit()
        return {"mensaje": "exitoso"}
    except Exception as e:
        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}


@router.put("/update_users/patient/{paciente_id}")
def update_user_patient(paciente_id: int,datos_nuevos: UsuarioPacienteEdit, session: Session = Depends(get_session)):
    try:
        statement = select(Usuarios).where(Usuarios.id == paciente_id)
        usuario = session.exec(statement).first()
        if usuario is None:
            print("el usuario no existe en la base de datos.")
            raise HTTPException(
                status_code=404,
                detail="no existe en la base de datos.",
            )
        usuario.nombre_completo = datos_nuevos.nombre_completo
        usuario.cedula = datos_nuevos.cedula
        usuario.email = datos_nuevos.email

        session.add(usuario)
        #Session.rollback()
        session.commit()

        statement_paciente = select(Pacientes).where(Pacientes.usuarios_id == paciente_id)
        paciente = session.exec(statement_paciente).first()
        if paciente is None:
            print("el paciente no existe en la base de datos.")
            raise HTTPException(
                status_code=404,
                detail="no existe en la base de datos.",
            )
        paciente.fecha_de_nacimiento = datos_nuevos.paciente.fecha_de_nacimiento
        paciente.telefono_de_emergencia = datos_nuevos.paciente.telefono
        paciente.direccion = datos_nuevos.paciente.direccion
        paciente.grupo_sanguineo_id = datos_nuevos.paciente.tipo_de_sangre

        session.add(paciente)
        #Session.rollback()
        session.commit()
        return {"mensaje": "exitoso"}
    except Exception as e:
        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}


@router.delete("/{user_id}/delete_user")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    try:
        usuario = session.get(Usuarios, user_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Médico no encontrado")

        session.delete(usuario)
        #session.rollback()

        session.commit()

        return {"mensaje": "exitoso",}

    except Exception as e:
        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}

@router.put("/{user_id}/update_horario")
def update_horario(user_id: int,value : HorarioUpdate, session: Session = Depends(get_session)):
    try:
        # dias_list = {'Lunes':1,'Martes':2,'Miércoles':3,'Jueves':4,'Viernes':5,'Sábado':6,'Domingo':7}
        print(HorarioUpdate)
        for item in value.horario_list:
            statement = select(Horarios).where(
                Horarios.medico_id == user_id,
                Horarios.dias_id == item.dias_id,
                # Horarios.medico_id == user_id
            )
            datos_horario = session.exec(statement).first()

            if datos_horario:
                datos_horario.hora_de_entrada = item.hora_de_entrada
                datos_horario.hora_de_salida = item.hora_de_salida
                datos_horario.activo = item.activo
                session.add(datos_horario)
            session.commit()

        return {"mensaje": "exitoso"}

        return {"mensaje": "exitoso"}

    except Exception as e:
        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}

@router.post("/request_time_off")
def request_time_off(value : dias_libres, session: Session = Depends(get_session)):
    try:
        print(value)
        solicitud = Dias_libres(
            medico_id = value.medico_id,
            inicio = value.inicio,
            final = value.final,
            estado_id = 1)
        session.add(solicitud)
        session.commit()

        return {"mensaje": "exitoso"}

    except Exception as e:
        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}

@router.patch("/time_off/{id}/{type}")
def time_off(id : int,type : int , session: Session = Depends(get_session)):
    try:
        statement = select(Dias_libres).where(Dias_libres.id == id)
        dia_libre = session.exec(statement).first()
        if dia_libre is None:
            raise HTTPException(
                status_code=404,
                detail=f"La petición con ID {id} no existe en la base de datos.",
            )
        dia_libre.estado_id = type
        session.add(dia_libre)
        session.commit()

        return {"mensaje": "exitoso"}

    except Exception as e:
        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}
