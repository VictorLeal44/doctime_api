from fastapi import APIRouter, Depends, HTTPException

from models.database import get_session
from sqlmodel import Session, select, col, exists
from sqlalchemy import func,extract
from sqlalchemy.orm import joinedload
from typing import List

from models.item import Citas, Pacientes, Medicos, Usuarios, Estado, SystemSetting,Notificaciones
from schemas.form import *

from datetime import date
import calendar

router = APIRouter()


@router.get("/")
def get_all_appointments(tamano_lote: int = 10, session: Session = Depends(get_session)):
    try:
        # Precargamos explícitamente las relaciones para evitar errores de Lazy Loading
        statement = (
            select(Citas)
            .options(
                joinedload(Citas.paciente).joinedload(Pacientes.usuario),
                joinedload(Citas.medico).joinedload(Medicos.usuario),
                joinedload(Citas.estado)
            )
            .where(Citas.estado_id != 1)
            .offset(0)
            .limit(tamano_lote)
        )

        resultants = session.exec(statement).all()

        datos_formateados = [
            {
                "id": cita.id,
                "Paciente": (
                    cita.paciente.usuario.nombre_completo.strip()
                    if (cita.paciente and cita.paciente.usuario)
                    else "Sin Paciente"
                ),
                # Corrección: Validamos cita.medico y cita.medico.usuario
                "Medico": (
                    cita.medico.usuario.nombre_completo.strip()
                    if (cita.medico and cita.medico.usuario)
                    else "Sin medico"
                ),
                "Fecha_de_encuentro": str(cita.fecha_de_encuentro) if cita.fecha_de_encuentro else "",
                "Hora_de_encuentro": str(cita.hora_de_encuentro) if cita.hora_de_encuentro else "",
                "Asunto": cita.asunto.strip() if cita.asunto else "",
                "Enviado": str(cita.enviado) if cita.enviado else "",
                "Estado": cita.estado.estado.strip() if cita.estado else "Desconocido",
                "Especialidad_id": cita.especialidad_id
            }
            for cita in resultants
        ]

        return {"datos": datos_formateados}

    except Exception as e:
        print(f"Falló el endpoint get_all_appointments: {e}")
        session.rollback()
        raise HTTPException(
            detail="Error al obtener las citas"
        )

@router.get("/appointment_id")
def get_appointment_by_id(id: int, session: Session = Depends(get_session)):
    try:
        resultants = session.get(Citas, id)
        return {'mensaje':'funcionó',
            'datos':resultants}
    except Exception as e:
        print("simplemente falló", e)
        Session.rollback()
        return {"mensaje": "Fallido"}

@router.get("/get_requests_appointment")
def get_requests_appointment( session = Depends(get_session)):
    try:
        statement = (
                select(
                    Citas.id.label("id"),
                    Usuarios.nombre_completo.label("Paciente"),
                    Pacientes.id.label("Paciente_id"),
                    Citas.asunto.label("Asunto"),
                    Citas.especialidad_id.label("Especialidad_id")
                )
                .join(Pacientes, Citas.pacientes_id == Pacientes.id)
                .join(Usuarios, Pacientes.usuarios_id == Usuarios.id)
                .where(Citas.estado_id == 1)
            )

        results = session.exec(statement).all()

        statement_medicos = (
        select(
            Medicos.id.label("id"),
            Usuarios.nombre_completo.label("medico_name"),
            Medicos.especialidad_id.label("especialidad_id")
        )
        .join(Usuarios, Medicos.usuarios_id == Usuarios.id)
    )
        medicos_data = session.exec(statement_medicos).all()
        print(medicos_data)

        return {'mensaje':'funcionó',
            'datos':[
                CitaRecordResponse(
                    id=row.id,
                    Paciente=row.Paciente.strip(),
                    Paciente_id=row.Paciente_id,
                    Asunto=row.Asunto,
                    Especialidad_id=row.Especialidad_id
                )
                for row in results
            ],
            'medicos':[MedicoResponse(
            id=row.id,
            medico_name=row.medico_name.strip() if isinstance(row.medico_name, str) else row.medico_name,
            especialidad_id=row.especialidad_id
        )
        for row in medicos_data
                ]
            }

    except Exception as e:
        print("simplemente falló", e)
        Session.rollback()
        return {"mensaje": "Fallido"}

@router.get("/appointment_user")
def get_appointment_by_user(id: int, session: Session = Depends(get_session)):
    try:
        statement = (
            select(
                Citas.id.label("cita_id"),
                Usuarios.nombre_completo.label("nombre_medico"),
                Citas.fecha_de_encuentro,
                Citas.hora_de_encuentro,
                Citas.asunto,
                Estado.estado.label("nombre_estado")
            )
            .join(Medicos, Citas.medicos_id == Medicos.id, isouter=True)
            .join(Usuarios, Medicos.usuarios_id == Usuarios.id, isouter=True)
            .join(Estado, Citas.estado_id == Estado.id, isouter=True)
            .where(Citas.pacientes_id == id)
        )

        resultados = session.exec(statement).mappings().all()

        return {
            "mensaje": "éxito",
            "datos": resultados
        }
    except Exception as e:
        print("Error en consulta:", e)
        session.rollback()
        return {"mensaje": "Fallido", "error": str(e)}

@router.get("/appointment_medic")
def get_appointment_by_medic(id: int, session: Session = Depends(get_session)):
    try:
        statement = (
            select(
                Citas.id.label("cita_id"),
                Usuarios.nombre_completo.label("nombre_paciente"),
                Citas.fecha_de_encuentro,
                Citas.hora_de_encuentro,
                Citas.asunto,
                Estado.estado.label("nombre_estado")
            )
            .join(Pacientes, Citas.pacientes_id == Pacientes.id, isouter=True)
            .join(Usuarios, Pacientes.usuarios_id == Usuarios.id, isouter=True)
            .join(Estado, Citas.estado_id == Estado.id, isouter=True)
            .where(Citas.medicos_id == id)
        )

        resultados = session.exec(statement).mappings().all()

        return {
            "mensaje": "éxito",
            "datos": resultados
        }
    except Exception as e:
        print("Error en consulta:", e)
        session.rollback()
        return {"mensaje": "Fallido", "error": str(e)}

@router.post("/")
def create_appointment(data: CitaCreate, session=Depends(get_session)):
    try:
        statement = select(exists().where(Citas.estado_id == 2 and data.pacientes_id))
        resultado = session.exec(statement).one()
        print('este es el resultado: ',resultado)
        if not resultado:
            new_appointment = Citas(
                pacientes_id=data.pacientes_id,
                asunto=data.asunto,
                especialidad_id=data.especialidad_id,
                estado_id=1
            )
            session.add(new_appointment)

            #Session.rollback()
            session.commit()
            return {"mensaje": "Su cita fue enviada con éxito"}
        print("ya posee cita")
        return {"mensaje": "Ya posees una cita"}
    except Exception as e:
        print("simplemente falló", e)
        Session.rollback()
        return {"mensaje": "Fallido"}

@router.get("/dashboard_appointment")
def dashboard_appointment(type: str ,year:int,session = Depends(get_session)):
    try:
        dashboard = []
        calendario = []
        contenedor = []

        for mes in range(12):
            _, ultimo_dia = calendar.monthrange(year, mes+1)
            inicio_del_mes = date(year,mes+1,1)
            final_del_mes = date(year,mes+1,ultimo_dia)


            # statement = select(func.count(Citas.id)).where(
            # col(Citas.fecha_de_encuentro) >= inicio_del_mes,
            # col(Citas.fecha_de_encuentro) <= final_del_mes
            # )
            # citas_del_mes = session.exec(statement).one()
            # result.append(citas_del_mes)

            statement_calendario = select(func.extract('day',Citas.fecha_de_encuentro)).where(
            col(Citas.fecha_de_encuentro) >= inicio_del_mes,
            col(Citas.fecha_de_encuentro) <= final_del_mes
            )

            resultado = session.exec(statement_calendario).all()
            if resultado:
                dashboard.append(len(resultado))
            #     calendario.append({
            #     'dot': {
            #     'color': 'purple',
            #     'fillMode': 'solid',
            #     'contentClass': 'italic',
            #     },
            #     'popover': {
            #         'label': 'Cita de emergencia',
            #         },
            #     'dates': new Date(year, month, 12),
            # })
                ordenados = sorted(resultado)
                valor_actual = ordenados[0]

                for i in ordenados:
                    contador = ordenados.count(i)
                    calendario.append([i,mes,year,contador]) # dia mes y cantidad de citas

                print("resultados : ---------------",calendario)
            else:
                dashboard.append(0)
        return {"dashboard":dashboard,
                "calendario":calendario}
    except Exception as e:
        Session.rollback()
        return {"mensaje": "Fallido"}

@router.get("/category_data")
def category_data(session: Session = Depends(get_session)):
    try:
        statements = [select(func.count(Pacientes.id)),
                      select(func.count(Medicos.id)),
                      select(func.count(Citas.id)).where(Citas.estado_id == 2),
                      select(func.count(Citas.id)).where(Citas.estado_id == 3)]
        datas = []
        for i in statements:
            resultado = session.exec(i).one()
            datas.append(resultado)
        return {"datos" : datas }
    except Exception as e:
        print("simplemente falló", e)
        Session.rollback()
        return {"mensaje": "Fallido"}

@router.patch("/appointment/accept")
def accept_appointment(values: AceptCita, session=Depends(get_session)):
    try:
        statement = select(Citas).where(Citas.id == values.id)
        cita = session.exec(statement).first()
        if cita is None:
            print(f"La cita con ID {values.id} no existe en la base de datos.")
            raise HTTPException(
                status_code=404,
                detail=f"La cita con ID {values.id} no existe en la base de datos.",
            )
        cita.estado_id = 2
        cita.medicos_id = values.medico_id
        cita.fecha_de_encuentro = values.fecha
        cita.hora_de_encuentro = values.hora

        session.add(cita)
        session.commit()
        # Session.commit()
        return {"mensaje": "exitoso"}
    except Exception as e:
        print(values)

        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}

@router.patch("/{appointment_id}/reject")
def reject_appointment(appointment_id: int, session=Depends(get_session)):
    try:
        statement = select(Citas).where(Citas.id == appointment_id)
        cita = session.exec(statement).first()
        if cita is None:
            print(f"La cita con ID {appointment_id} no existe en la base de datos.")
            raise HTTPException(
                status_code=404,
                detail=f"La cita con ID {appointment_id} no existe en la base de datos.",
            )

        cita.estado_id = 4

        session.add(cita)
        # session.rollback()
        session.commit()
        return {"mensaje": "exitoso"}
    except Exception as e:
        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}


@router.patch("/{pacientes_id}/{value}/complete")
def complete_appointment(pacientes_id: int,value: str, session=Depends(get_session)):
    try:
        # qr = session.get(SystemSetting)
        statement = select(SystemSetting.qr_descripcion)
        qr = session.exec(statement).first()
        print(qr)
        if qr != value:
            return {"mensaje": "rechazado"}

        statement_cita = select(Citas).where(Citas.pacientes_id == pacientes_id).where(Citas.estado_id == 2)
        cita = session.exec(statement_cita).first()
        if cita is None:
            print(f"La cita con ID {pacientes_id} no existe en la base de datos.")
            raise HTTPException(
                status_code=404,
                detail=f"La cita con ID {pacientes_id} no existe en la base de datos.",
            )

        cita.estado_id = 3
        session.add(cita)
        session.commit()
        # Session.commit()
        return {"mensaje": "exitoso"}

    except Exception as e:
        print("simplemente falló", e)
        session.rollback()
        return {"mensaje": "Fallido"}


@router.delete("/delete/appointment")
def delete_appointment(id: int, session=Depends(get_session)):
    try:
        cita = session.get(Citas, id)

        if not cita:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        session.delete(cita)
        session.commit()

        return {"mensaje": "exitoso"}
    except Exception as e:
        session.rollback()
        return {"mensaje": f"Fallido: {str(e)}"}


@router.get("/qr")
def qr(session=Depends(get_session)):
    try:
        statement = select(SystemSetting.qr_descripcion)
        qr_actual = session.exec(statement).first()

        if not qr_actual:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        return {"mensaje": "exitoso",
                'datos': qr_actual}
    except Exception as e:
        session.rollback()
        return {"mensaje": f"Fallido: {str(e)}"}

@router.patch("/qr_update/{nuevo_qr}")
def qr_update(nuevo_qr : str ,session=Depends(get_session)):
    try:
        statement = select(SystemSetting)
        qr_actual = session.exec(statement).first()

        if not qr_actual:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

        qr_actual.qr_descripcion = nuevo_qr
        session.commit()

        return {"mensaje": "exitoso"}
    except Exception as e:
        session.rollback()
        return {"mensaje": f"Fallido: {str(e)}"}

@router.post("/new_notification")
def new_notification(value : NotificacionesCreated ,session=Depends(get_session)):
    try:
        nueva_notificacion = Notificaciones(
            usuario_id = value.usuarios_id,
            titulo = value.titulo,
            descripcion = value.descripcion,
            leida = False)

        session.add(nueva_notificacion)
        session.commit()

        return {"mensaje": "exitoso"}
    except Exception as e:
        session.rollback()
        return {"mensaje": f"Fallido: {str(e)}"}

@router.get("/view_notification/{id}")
def view_notification(id: int ,session=Depends(get_session)):
    try:
        statement = select(Notificaciones).where(Notificaciones.usuario_id == id)
        datos = session.exec(statement).all()
        return {"mensaje": "exitoso",
                "datos": datos}
    except Exception as e:
        session.rollback()
        return {"mensaje": f"Fallido: {str(e)}"}
