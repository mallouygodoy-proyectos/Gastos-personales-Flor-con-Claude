import os
import json
import re
import asyncio
from datetime import datetime, date
from typing import Optional

import httpx
import jwt
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, ConversationHandler,
    MessageHandler, CommandHandler, filters, ContextTypes
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod: reemplazá con tu dominio Vercel
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
    import urllib.request, urllib.parse
    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": token
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=data, method="POST"
    )
    with urllib.request.urlopen(req) as r:
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
            # Marcamos como eliminado sobreescribiendo con vacíos
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
ESPERANDO_CATEGORIA = 1

CATEGORIAS_TECLADO = [
    ["Supermercado", "Salidas", "Almuerzos"],
    ["Transporte",   "Educación", "Remis"],
    ["Servicios",    "Viajes",    "Hogar"],
    ["Regalos",      "Mascota",   "Préstamos"],
    ["Gimnasio",     "Deporte",   "Insumos"],
    ["Alquiler",     "Salud",     "Alfarería"],
    ["Farmacia",     "Cuidado personal", "Deuda"],
    ["Indumentaria", "Kiosco",    "Otros"],
]


def parsear_fecha(texto: str):
    match = re.search(r'(\d{1,2}/\d{1,2}(/\d{2,4})?)', texto)
    if match:
        fecha_str = match.group(1)
        partes = fecha_str.split("/")
        dia = int(partes[0])
        mes = int(partes[1])
        anio = int(partes[2]) if len(partes) > 2 else datetime.now().year
        if anio < 100:
            anio += 2000
        return datetime(anio, mes, dia).date().isoformat(), fecha_str
    return None, None


async def inicio_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.message.from_user.username
    if usuario not in USUARIOS_TG:
        return ConversationHandler.END

    texto  = update.message.text.strip()
    partes = texto.split(" ")

    if len(partes) < 2:
        await update.message.reply_text("Enviame el gasto así: '5000 cena' o '5000 cena 15/01'")
        return ConversationHandler.END

    try:
        monto = float(partes[0].replace(".", "").replace(",", "."))
        fecha_iso, fecha_legible = parsear_fecha(texto)
        detalle = texto.replace(partes[0], "", 1).strip()
        if fecha_legible:
            detalle = detalle.replace(fecha_legible, "").strip()

        context.user_data["gasto"] = {
            "monto":        monto,
            "detalle":      detalle if detalle else "-",
            "fecha":        fecha_iso,
            "usuario":      update.message.from_user.first_name,
            "metodo_pago":  "Efectivo",
        }

        markup = ReplyKeyboardMarkup(CATEGORIAS_TECLADO, one_time_keyboard=True, resize_keyboard=True)
        txt_fecha = f" del {fecha_legible}" if fecha_legible else " de hoy"
        await update.message.reply_text(
            f"¿Categoría para ${monto}{txt_fecha} — '{detalle}'?",
            reply_markup=markup
        )
        return ESPERANDO_CATEGORIA

    except ValueError:
        await update.message.reply_text("❌ El primer valor debe ser el monto.")
        return ConversationHandler.END


async def finalizar_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categoria = update.message.text
    datos = context.user_data.get("gasto")
    if not datos:
        await update.message.reply_text("Hubo un error, empezá de nuevo.")
        return ConversationHandler.END

    datos["categoria"] = categoria
    nuevo_id = generar_id()
    fecha    = datos.get("fecha") or date.today().isoformat()
    fila = [[nuevo_id, fecha, datos["monto"], datos["detalle"],
             datos["categoria"], datos["usuario"], datos["metodo_pago"], ""]]
    try:
        await sheets_append(RANGE_GASTOS, fila)
        await update.message.reply_text(
            f"✅ Registrado: ${datos['monto']} en {categoria}",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error al guardar: {e}")
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelado.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


tg_app = ApplicationBuilder().token(TOKEN_TG).build() if TOKEN_TG else None

if tg_app:
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & (~filters.COMMAND), inicio_gasto)],
        states={ESPERANDO_CATEGORIA: [MessageHandler(filters.TEXT & (~filters.COMMAND), finalizar_registro)]},
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )
    tg_app.add_handler(conv_handler)


@app.post("/webhook/telegram")
async def webhook_telegram(request: Request):
    if not tg_app:
        raise HTTPException(500, "Bot no configurado")
    body = await request.json()
    update = Update.de_json(body, tg_app.bot)

    async def _run():
        if not tg_app.running:
            await tg_app.initialize()
        await tg_app.process_update(update)
        await tg_app.shutdown()

    asyncio.run(_run())
    return {"ok": True}
