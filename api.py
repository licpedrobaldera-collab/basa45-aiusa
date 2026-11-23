# basa45-AIUSA - API PARA CELULAR - Baldera Santos & Asociados
# Funciona en Android y iPhone - Sin instalar nada en el celular
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import io, re
from datetime import datetime
import pytz

app = FastAPI(title="basa45-AIUSA API CELULAR", version="10-10 FULL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Memoria en vivo - Autoguardado
DB = {"asistencias": [], "casos": [], "hallazgos": []}

def limpiar_texto(x):
    try:
        if pd.isna(x): return ""
        return str(x).strip()
    except: return ""
def limpiar_numero(x):
    try:
        if pd.isna(x) or str(x).strip()=="": return 0.0
        s=re.sub(r"[^0-9.\-]", "", str(x).replace(",",""))
        return float(s) if s not in ["","-","."] else 0.0
    except: return 0.0

def validar_cedula_rd(ced):
    s=str(ced).replace("-","").replace(" ","").strip()
    if len(s)!=11: return False
    m=[7,9,10,5,8,4,2,1,6]; tot=0
    try:
        for i in range(9): tot+=int(s[i])*m[i]
        return (10-(tot%10))%10==int(s[10])
    except: return False

class Asistencia(BaseModel):
    pais: str = "República Dominicana"
    entidad: str = "INFOTEP"
    nombre: str
    cedula: str
    tipo: str = "Entrada"
    venta: float = 0.0

class Caso(BaseModel):
    pais: str = "República Dominicana"
    entidad: str = "INFOTEP"
    proyecto: str = "Auditoria"
    desde: str = "2015-01"
    hasta: str = "2026-11"

@app.get("/")
def inicio():
    return {
        "sistema": "basa45-AIUSA API CELULAR 10-10",
        "autor": "Lic. Pedro Baldera - Baldera Santos & Asociados",
        "estado": "EN LINEA ✅",
        "marco": "NOBACI + NIA/ISA + NICSP + NIF/NIIF + INTOSAI",
        "como_usar": "Abra /docs en su celular para probar",
        "endpoints": ["/asistencia", "/caso", "/auditar", "/matriz", "/historico", "/docs"]
    }

@app.post("/asistencia")
def registrar_asistencia(data: Asistencia):
    # Guarda al instante
    zona = pytz.timezone("America/Santo_Domingo")
    now = datetime.now(zona)
    reg = {
        "fecha": now.strftime("%Y-%m-%d"),
        "hora": now.strftime("%H:%M:%S"),
        "pais": data.pais,
        "entidad": data.entidad,
        "nombre": limpiar_texto(data.nombre),
        "cedula": limpiar_texto(data.cedula),
        "tipo": data.tipo,
        "venta": data.venta
    }
    DB["asistencias"].append(reg)
    return {"ok": True, "mensaje": f"✅ Guardado al instante: {reg['nombre']} - {reg['tipo']} - {reg['hora']}", "registro": reg, "total_asistencias": len(DB["asistencias"])}

@app.post("/caso")
def crear_caso(data: Caso):
    caso = {"pais": data.pais, "entidad": data.entidad, "proyecto": data.proyecto, "desde": data.desde, "hasta": data.hasta, "estado": "Activo"}
    DB["casos"].append(caso)
    return {"ok": True, "mensaje": f"✅ Caso creado: {data.proyecto}", "caso": caso}

@app.get("/historico")
def ver_historico():
    return {"casos": DB["casos"], "asistencias": DB["asistencias"], "hallazgos": DB["hallazgos"], "total_casos": len(DB["casos"])}

@app.post("/auditar")
async def auditar(file: UploadFile = File(...), pais: str = Form("República Dominicana")):
    # Limpieza IA - Cero Error
    try:
        contenido = await file.read()
        if file.filename.endswith(".csv"):
            try: df = pd.read_csv(io.BytesIO(contenido), dtype=str, keep_default_na=False)
            except: df = pd.read_csv(io.BytesIO(contenido), dtype=str, keep_default_na=False, encoding="latin1")
        else:
            df = pd.read_excel(io.BytesIO(contenido), dtype=str, keep_default_na=False)
        df = df.dropna(how="all")
        df.columns = [limpiar_texto(c).upper() if limpiar_texto(c) else f"COL_{i}" for i,c in enumerate(df.columns)]
        df = df[df.apply(lambda r: any(limpiar_texto(x)!="" for x in r), axis=1)]

        col_id = next((c for c in df.columns if any(k in c for k in ["CED","ID","COD"])), df.columns[0])
        col_nom = next((c for c in df.columns if "NOM" in c), df.columns[1] if len(df.columns)>1 else df.columns[0])
        col_suel = next((c for c in df.columns if any(k in c for k in ["SUEL","BRUTO","SALARIO"])), None)
        col_asist = next((c for c in df.columns if "ASIST" in c), None)

        hallazgos = []; total = 0.0; vistos = {}
        for idx, row in df.iterrows():
            idv = limpiar_texto(row.get(col_id,"")); nom = limpiar_texto(row.get(col_nom,""))
            sueldo = limpiar_numero(row.get(col_suel,0)) if col_suel else 0.0
            dias = int(limpiar_numero(row.get(col_asist,0))) if col_asist else 0
            total += sueldo
            if idv and pais=="República Dominicana" and not validar_cedula_rd(idv):
                hallazgos.append({"ID":"H-CEDULA","NOBACI":"Ambiente de Control","NIA":"NIA 500","Condicion":f"ID inválido: {nom} ({idv})","Criterio":"Ley 41-08 + NOBACI","Causa":"ID incorrecto","Efecto":"Riesgo identidad","Riesgo":"ALTO","Evidencia":f"Fila {idx+2}","Recomendacion":"Validar con JCE","Monto":0})
            if idv and idv in vistos:
                hallazgos.append({"ID":"H-DUP","NOBACI":"Actividades de Control","NIA":"NIA 240 Fraude","Condicion":f"Duplicado: {nom} cobra 2 veces","Criterio":"NIA 240","Causa":"Falta depuración","Efecto":f"Duplicado {sueldo:,.0f}","Riesgo":"CRITICO","Evidencia":f"Fila {idx+2}","Recomendacion":"Depurar y recuperar","Monto":sueldo})
            if idv: vistos[idv]=1
            tiene_asist = any(a["cedula"]==idv or a["nombre"]==nom for a in DB["asistencias"])
            if sueldo>0 and dias==0 and not tiene_asist:
                hallazgos.append({"ID":"H-FANTASMA","NOBACI":"Valoración de Riesgo","NIA":"NIA 240 Fraude","Condicion":f"Posible FANTASMA: {nom} cobra {sueldo:,.0f} con 0 días asistencia","Criterio":"Ley 41-08 + NIA 240","Causa":"Cobra sin asistir","Efecto":f"Pago sin soporte {sueldo:,.0f}","Riesgo":"CRITICO","Evidencia":f"Fila {idx+2} + Asistencias","Recomendacion":"Suspender pago y verificar","Monto":sueldo})
        DB["hallazgos"] = hallazgos
        return {
            "ok": True,
            "pais": pais,
            "total_nomina_real": total,
            "filas_limpias": len(df),
            "hallazgos_reales": len(hallazgos),
            "hallazgos": hallazgos,
            "opinion": "CON SALVEDADES" if hallazgos else "SIN SALVEDADES",
            "marco": "NOBACI + NIA 200,240,315,500,530,700 + NICSP + INTOSAI"
        }
    except Exception as e:
        return {"ok": False, "error_controlado": str(e), "mensaje": "No se detuvo, revise que sea Excel/CSV real"}

@app.get("/matriz")
def matriz():
    return {"matriz_hallazgos": DB["hallazgos"], "total": len(DB["hallazgos"]), "descargar": "Use /historico para ver todo"}

@app.delete("/historico/borrar")
def borrar_historico():
    DB["asistencias"]=[]; DB["casos"]=[]; DB["hallazgos"]=[]
    return {"ok": True, "mensaje": "🗑️ Histórico borrado"}