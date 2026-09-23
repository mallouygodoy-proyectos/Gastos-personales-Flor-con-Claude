import os
import json
import re
import urllib.request as _urllib
from datetime import datetime, date
from typing import Optional

import httpx
import jwt
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIG ---
SHEET_ID        = os.getenv("SHEET_ID_GASTOS")
TOKEN_TG        = os.getenv("TOKEN_TELEGRAM_GASTOS")
USUARIOS_TG     = os.getenv("USUARIOS_PERMITIDOS", "").split(",")
SCOPES          = ["https://www.googleapis.com/auth/spreadsheets"]
RANGE_GASTOS    = "GASTOS!A:H"
RANGE_CATS      = "CATEGORIAS!A:C"
RANGE_ESTADO    = "ESTADO!A:F"


# --- SERVICE ACCOUNT JWT ---
def get_access_token() -> str:
    creds = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    now = int(datetime.utcnow().timestamp())
    payload = {
        "iss": creds["client_email"],
        "sub": creds["client_email"],
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
        "scope": " ".join(SCOPES),
    }
    token = jwt.encode(payload, creds["private_key"], algorithm="RS256")
    import urllib.parse
    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": token
    }).encode()
    req = _urllib.Request(
        "https://oauth2.googleapis.com/token", data=data, method="POST"
    )
    with _urllib.urlopen(req) as r:
        return json.loads(r.read())["access_token"]


async def sheets_get(range_: str) -> list:
    token = get_access_token()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{range_}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json().get("values", [])


async def sheets_append(range_: str, values: list) -> dict:
    token = get_access_token()
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
           f"/values/{range_}:append?valueInputOption=USER_ENTERED")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            url, headers={"Authorization": f"Bearer {token}"},
            json={"values": values}
        )
        r.raise_for_status()
        return r.json()


async def sheets_update(range_: str, values: list) -> dict:
    token = get_access_token()
    url = (f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
           f"/values/{range_}?valueInputOption=USER_ENTERED")
    async with httpx.AsyncClient() as client:
        r = await client.put(
            url, headers={"Authorization": f"Bearer {token}"},
            json={"values": values}
        )
        r.raise_for_status()
        return r.json()


# --- ESTADO PERSISTENTE EN SHEETS ---
async def guardar_estado(chat_id: int, datos: dict):
    """Guarda o actualiza el estado pendiente de un chat en la hoja ESTADO."""
    rows = await sheets_get(RANGE_ESTADO)
    chat_str = str(chat_id)
    valor = json.dumps(datos)
    # Buscar si ya existe una fila para este chat_id
    for i, row in enumerate(rows):
        if row and row[0] == chat_str:
            fila_num = i + 1
            await sheets_update(f"ESTADO!A{fila_num}:B{fila_num}", [[chat_str, valor]])
            return
    # Si no existe, agregar nueva fila
    await sheets_append(RANGE_ESTADO, [[chat_str, valor]])


async def leer_estado(chat_id: int) -> Optional[dict]:
    """Lee el estado pendiente de un chat desde la hoja ESTADO."""
    rows = await sheets_get(RANGE_ESTADO)
    chat_str = str(chat_id)
    for row in rows:
        if row and row[0] == chat_str and len(row) > 1 and row[1]:
            try:
                return json.loads(row[1])
            except Exception:
                return None
    return None


async def borrar_estado(chat_id: int):
    """Borra el estado pendiente de un chat en la hoja ESTADO."""
    rows = await sheets_get(RANGE_ESTADO)
    chat_str = str(chat_id)
    for i, row in enumerate(rows):
        if row and row[0] == chat_str:
            fila_num = i + 1
            await sheets_update(f"ESTADO!A{fila_num}:B{fila_num}", [["", ""]])
            return


# --- MODELOS ---
class Gasto(BaseModel):
    monto:       float
    detalle:     str
    categoria:   str
    usuario:     Optional[str] = "Flor"
    metodo_pago: Optional[str] = "Efectivo"
    fecha:       Optional[str] = None
    notas:       Optional[str] = ""


class GastoUpdate(BaseModel):
    monto:       Optional[float] = None
    detalle:     Optional[str]   = None
    categoria:   Optional[str]   = None
    metodo_pago: Optional[str]   = None
    notas:       Optional[str]   = None


# --- HELPERS ---
def generar_id() -> str:
    return f"G{datetime.now().strftime('%Y%m%d%H%M%S')}"


def row_to_dict(row: list) -> dict:
    keys = ["id", "fecha", "monto", "detalle", "categoria", "usuario", "metodo_pago", "notas"]
    padded = row + [""] * (len(keys) - len(row))
    return dict(zip(keys, padded))


# --- ENDPOINTS REST ---
@app.get("/api/gastos")
async def get_gastos(mes: Optional[str] = None, categoria: Optional[str] = None):
    rows = await sheets_get(RANGE_GASTOS)
    if not rows or len(rows) < 2:
        return []
    data = [row_to_dict(r) for r in rows[1:] if r]
    if mes:
        data = [g for g in data if str(g["fecha"]).startswith(mes)]
    if categoria:
        data = [g for g in data if g["categoria"] == categoria]
    return data


@app.post("/api/gastos", status_code=201)
async def post_gasto(gasto: Gasto):
    nuevo_id = generar_id()
    fecha    = gasto.fecha or date.today().isoformat()
    fila = [[nuevo_id, fecha, gasto.monto, gasto.detalle,
             gasto.categoria, gasto.usuario, gasto.metodo_pago, gasto.notas]]
    await sheets_append(RANGE_GASTOS, fila)
    return {"id": nuevo_id, "status": "ok"}


@app.patch("/api/gastos/{gasto_id}")
async def patch_gasto(gasto_id: str, cambios: GastoUpdate):
    rows = await sheets_get(RANGE_GASTOS)
    for i, row in enumerate(rows):
        if row and row[0] == gasto_id:
            fila_num = i + 1
            d = row_to_dict(row)
            if cambios.monto       is not None: d["monto"]       = cambios.monto
            if cambios.detalle     is not None: d["detalle"]     = cambios.detalle
            if cambios.categoria   is not None: d["categoria"]   = cambios.categoria
            if cambios.metodo_pago is not None: d["metodo_pago"] = cambios.metodo_pago
            if cambios.notas       is not None: d["notas"]       = cambios.notas
            rng = f"GASTOS!A{fila_num}:H{fila_num}"
            await sheets_update(rng, [[
                d["id"], d["fecha"], d["monto"], d["detalle"],
                d["categoria"], d["usuario"], d["metodo_pago"], d["notas"]
            ]])
            return {"status": "updated"}
    raise HTTPException(404, "Gasto no encontrado")


@app.delete("/api/gastos/{gasto_id}")
async def delete_gasto(gasto_id: str):
    rows = await sheets_get(RANGE_GASTOS)
    for i, row in enumerate(rows):
        if row and row[0] == gasto_id:
            fila_num = i + 1
            rng = f"GASTOS!A{fila_num}:H{fila_num}"
            await sheets_update(rng, [["", "", "", "ELIMINADO", "", "", "", ""]])
            return {"status": "deleted"}
    raise HTTPException(404, "Gasto no encontrado")


@app.get("/api/categorias")
async def get_categorias():
    rows = await sheets_get(RANGE_CATS)
    if not rows or len(rows) < 2:
        return []
    return [{"nombre": r[0], "icono": r[1] if len(r) > 1 else "💰",
             "color": r[2] if len(r) > 2 else "#888"} for r in rows[1:] if r]


# --- BOT TELEGRAM ---
CATEGORIAS_TECLADO = [
    ["Supermercado", "Salidas",       "Transporte"],
    ["Hogar",        "Belleza",        "Mascota"],
    ["Viajes",       "Salud",          "Regalos"],
    ["Actividad fisica", "Indumentaria", "Otros"],
]


def tg_send(chat_id: int, text: str, keyboard=None):
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = json.dumps({
            "keyboard": keyboard,
            "one_time_keyboard": True,
            "resize_keyboard": True
        })
    else:
        payload["reply_markup"] = json.dumps({"remove_keyboard": True})
    data = json.dumps(payload).encode()
    req = _urllib.Request(
        f"https://api.telegram.org/bot{TOKEN_TG}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with _urllib.urlopen(req) as r:
        return json.loads(r.read())


def parsear_fecha(texto: str):
    match = re.search(r'(\d{1,2}/\d{1,2}(/\d{2,4})?)', texto)
    if match:
        fecha_str = match.group(1)
        partes = fecha_str.split("/")
        dia  = int(partes[0])
        mes  = int(partes[1])
        anio = int(partes[2]) if len(partes) > 2 else datetime.now().year
        if anio < 100:
            anio += 2000
        return datetime(anio, mes, dia).date().isoformat(), fecha_str
    return None, None


# Lista de categorías válidas para distinguirlas de nuevos gastos
CATEGORIAS_VALIDAS = {cat for fila in CATEGORIAS_TECLADO for cat in fila}


@app.post("/webhook/telegram")
async def webhook_telegram(request: Request):
    body = await request.json()
    message = body.get("message", {})
    if not message:
        return {"ok": True}

    chat_id  = message["chat"]["id"]
    username = message.get("from", {}).get("username", "")
    text     = message.get("text", "").strip()

    if username not in USUARIOS_TG:
        return {"ok": True}

    # Verificar si hay un gasto pendiente esperando categoría en Sheets
    datos = await leer_estado(chat_id)

    if datos and text in CATEGORIAS_VALIDAS:
        # El usuario eligió categoría → registrar el gasto
        await borrar_estado(chat_id)
        datos["categoria"] = text
        nuevo_id = generar_id()
        fecha    = datos.get("fecha") or date.today().isoformat()
        fila = [[nuevo_id, fecha, datos["monto"], datos["detalle"],
                 datos["categoria"], datos["usuario"], "Efectivo", ""]]
        try:
            await sheets_append(RANGE_GASTOS, fila)
            tg_send(chat_id, f"✅ ${int(datos['monto'])} en {text} registrado!")
        except Exception as e:
            tg_send(chat_id, f"❌ Error al guardar: {e}")
        return {"ok": True}

    # Parsear nuevo gasto
    partes = text.split(" ")
    try:
        monto = float(partes[0].replace(".", "").replace(",", "."))
    except (ValueError, IndexError):
        tg_send(chat_id, "Enviame el gasto así:\n'5000 cena' o '5000 cena 15/04'")
        return {"ok": True}

    fecha_iso, fecha_legible = parsear_fecha(text)
    detalle = text.replace(partes[0], "", 1).strip()
    if fecha_legible:
        detalle = detalle.replace(fecha_legible, "").strip()

    detalle_corto = detalle[:25] + "…" if len(detalle) > 25 else detalle

    estado = {
        "monto":   monto,
        "detalle": detalle if detalle else "-",
        "fecha":   fecha_iso,
        "usuario": message.get("from", {}).get("first_name", "Flor"),
    }

    try:
        await guardar_estado(chat_id, estado)
    except Exception as e:
        tg_send(chat_id, f"❌ Error interno: {e}")
        return {"ok": True}

    txt_fecha = f" {fecha_legible}" if fecha_legible else ""
    tg_send(
        chat_id,
        f"${int(monto)}{txt_fecha} — {detalle_corto}\n¿Categoría?",
        keyboard=CATEGORIAS_TECLADO
    )
    return {"ok": True}
