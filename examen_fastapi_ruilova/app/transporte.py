from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.datos import RUTAS
from app.esquemas import Ruta, RutaActualizar, RutaCrear

router = APIRouter(prefix="/rutas", tags=["rutas"])


def obtener_ruta(codigo: str) -> dict:
    for ruta in RUTAS:
        if ruta["codigo"] == codigo.upper():
            return ruta
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No existe la ruta con el codigo '{codigo}'",
    )


RutaEncontrada = Annotated[dict, Depends(obtener_ruta)]



@router.get("", response_model=list[Ruta])
def listar_rutas(zona: Annotated[int | None, Query(ge=1, le=8)] = None,nocturna: bool = False,) -> list[dict]:
    resultado = RUTAS
    if zona is not None:
        resultado = [m for m in resultado if m["zona"] == zona]
    if nocturna:
        resultado = [m for m in resultado if m["nocturna"]]
    return resultado


@router.post("", response_model=Ruta, status_code=status.HTTP_201_CREATED)
def crear_ruta(nueva: RutaCrear) -> dict:
    if any(m["codigo"] == nueva.codigo for m in RUTAS):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La ruta '{nueva.codigo}' ya existe",
        )
    RUTAS.append(nueva.model_dump())
    return RUTAS[-1]



@router.get("/ingresos")
def ingresos_diarios(frecuencias: Annotated[int, Query(ge=1, le=20)], zona: Annotated[int | None, Query(ge=1, le=8)]=None) -> dict:
    seleccion = [m for m in RUTAS if zona is None or m["zona"] == zona]
    if not seleccion:
        raise HTTPException(404, f"No hay rutas en la zona {zona}")

    ingreso_diario = 0
    total_tarifa_sin_recargo = 0
    valor_m = 0
    promedio = 0
    for m in seleccion:
        valor_m = m["tarifa"]
        promedio += valor_m * frecuencias
        if m["nocturna"]:
            valor_m *= 1.20
        ingreso_diario += valor_m * frecuencias
        total_tarifa_sin_recargo += valor_m

    con_recargo = sum(1 for m in seleccion if m["nocturna"]) * frecuencias

    return {
        "rutas": len(seleccion),
        "frecuencias": frecuencias,
        "tarifa_promedio": round(promedio / len(seleccion*frecuencias), 2),
        "ingreso_diario": round(ingreso_diario, 2),
        "rutas_con_recargo" : con_recargo,
        "porcentaje_nocturnas": round(con_recargo * 100 / len(seleccion*frecuencias), 1),
    }



@router.get("/asignadas")
def rutas_asignadas(asignadas: Annotated[list[str] | None, Query()] = None) -> dict:
    if not RUTAS:
        raise HTTPException(404, "No hay rutas en la zona")
    codigos = {c.upper() for c in (asignadas or [])}
    total_rutas = 0
    pendiente_mas_cara = None
    mayor_actual = 0
    total_asignadas = 0
    tarifa_pendientes = 0
    for ruta in RUTAS:
        if ruta['tarifa'] > mayor_actual and ruta['codigo'] not in codigos:
            mayor_actual = ruta['tarifa']
            pendiente_mas_cara = ruta['codigo']
        total_rutas = len(RUTAS)
        if ruta["codigo"] in codigos:
            total_asignadas += 1
        if ruta["codigo"] not in codigos:
            tarifa_pendientes += ruta['tarifa']
    return {"total": total_rutas ,
        "asignadas": total_asignadas,
        "pendientes": total_rutas - total_asignadas,
        "porcentaje_cobertura": round((total_asignadas/total_rutas)*100,1),
        "tarifa_pendiente_total": tarifa_pendientes,
        "pendiente_mas_cara" : pendiente_mas_cara,}


@router.get("/{codigo}", response_model=Ruta)
def ver_ruta(ruta: RutaEncontrada) -> dict:
    return ruta


@router.put("/{codigo}", response_model=Ruta)
def actualizar_ruta(cambios: RutaActualizar, ruta: RutaEncontrada) -> dict:
    ruta.update(cambios.model_dump(exclude_unset=True))
    return ruta


@router.delete("/{codigo}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ruta(ruta: RutaEncontrada) -> None:
    RUTAS.remove(ruta)
