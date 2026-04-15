const BASE = import.meta.env.VITE_API_URL || ''

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Gastos ──────────────────────────────────────────────
export function getGastos({ mes, categoria } = {}) {
  const params = new URLSearchParams()
  if (mes)       params.set('mes', mes)
  if (categoria) params.set('categoria', categoria)
  const qs = params.toString()
  return apiFetch(`/api/gastos${qs ? `?${qs}` : ''}`)
}

export function postGasto(gasto) {
  return apiFetch('/api/gastos', {
    method: 'POST',
    body: JSON.stringify(gasto),
  })
}

export function patchGasto(id, cambios) {
  return apiFetch(`/api/gastos/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(cambios),
  })
}

export function deleteGasto(id) {
  return apiFetch(`/api/gastos/${id}`, { method: 'DELETE' })
}

// ── Categorías ──────────────────────────────────────────
export function getCategorias() {
  return apiFetch('/api/categorias')
}
