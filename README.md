# Gastos Personales

App PWA de registro de gastos personales con Google Sheets como base de datos,
interfaz React instalable en Android y bot de Telegram para carga rápida.

## Stack

- **Backend**: FastAPI (Python) en Vercel serverless
- **Frontend**: React + Vite como PWA instalable
- **DB**: Google Sheets via Service Account
- **Bot**: python-telegram-bot v20

## Estructura

```
/
├── api/
│   └── index.py          ← FastAPI: endpoints REST + webhook Telegram
├── frontend/
│   ├── public/
│   │   └── manifest.json ← PWA manifest
│   └── src/
│       ├── api/
│       │   └── gastos.js       ← funciones fetch al backend
│       ├── components/
│       │   ├── GastoCard.jsx
│       │   ├── GastosList.jsx
│       │   ├── GastoForm.jsx
│       │   └── ResumenMensual.jsx
│       ├── hooks/
│       │   └── useGastos.js
│       ├── pages/
│       │   ├── Home.jsx
│       │   ├── NuevoGasto.jsx
│       │   └── Estadisticas.jsx
│       ├── styles/
│       │   └── index.css
│       ├── App.jsx
│       └── main.jsx
├── requirements.txt
└── vercel.json
```

## Setup Google Sheets

1. Crear spreadsheet con dos hojas:

**Hoja GASTOS** — headers en fila 1:
`ID | FECHA | MONTO | DETALLE | CATEGORIA | USUARIO | METODO_PAGO | NOTAS`

**Hoja CATEGORIAS** — headers en fila 1:
`NOMBRE | ICONO | COLOR`

Ejemplo de categorías:
```
Supermercado | 🛒 | #4CAF50
Salidas      | 🍽️ | #FF5722
Transporte   | 🚌 | #2196F3
Hogar        | 🏠 | #9C27B0
Salud        | 💊 | #F44336
Otros        | 💰 | #888888
```

2. Crear Service Account en Google Cloud Console:
   - IAM & Admin → Service Accounts → Create
   - Descargar JSON de credenciales
   - Compartir el Spreadsheet con el email de la service account (editor)

## Variables de entorno en Vercel

```
SHEET_ID_GASTOS=<ID del spreadsheet>
GOOGLE_SERVICE_ACCOUNT_JSON=<contenido completo del JSON de la service account>
TOKEN_TELEGRAM_GASTOS=<token del bot de Telegram>
USUARIOS_PERMITIDOS=tu_usuario_telegram,otro_usuario
```

## Setup Bot Telegram

1. Crear bot con @BotFather → obtener TOKEN
2. Hacer deploy en Vercel
3. Registrar webhook:
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<tu-app>.vercel.app/webhook/telegram"
```

Uso del bot:
```
5000 cena           → registra $5000 en la categoría que elijas
5000 cena 15/04     → con fecha específica
```

## Setup Frontend

```bash
cd frontend
npm install
npm run dev       # desarrollo (proxy a localhost:8000)
npm run build     # genera dist/ para Vercel
```

**Instalar en Android:**
1. Abrir la URL de la app en Chrome
2. Menú → "Agregar a pantalla de inicio"
3. Queda instalada como app nativa

## Deploy en Vercel

```bash
# Desde la raíz del repo
vercel deploy
```

Vercel detecta automáticamente el `vercel.json` y buildea tanto el backend Python como el frontend estático.

## Endpoints API

| Método | Path | Descripción |
|--------|------|-------------|
| GET    | /api/gastos?mes=2026-04 | Listar gastos (filtro opcional por mes/categoría) |
| POST   | /api/gastos | Crear gasto |
| PATCH  | /api/gastos/:id | Editar gasto |
| DELETE | /api/gastos/:id | Eliminar gasto |
| GET    | /api/categorias | Listar categorías |
| POST   | /webhook/telegram | Webhook del bot |
