import { useState, useEffect } from 'react'

const METODOS_PAGO = ['Efectivo', 'Débito', 'Crédito', 'Transferencia']

const EMPTY_FORM = {
  monto:       '',
  detalle:     '',
  categoria:   '',
  metodo_pago: 'Efectivo',
  fecha:       new Date().toISOString().split('T')[0],
  notas:       '',
}

export default function GastoForm({ categorias, gastoInicial, onSubmit, onCancel }) {
  const [form,    setForm]    = useState(EMPTY_FORM)
  const [saving,  setSaving]  = useState(false)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    if (gastoInicial) {
      setForm({
        monto:       gastoInicial.monto      || '',
        detalle:     gastoInicial.detalle    || '',
        categoria:   gastoInicial.categoria  || '',
        metodo_pago: gastoInicial.metodo_pago || 'Efectivo',
        fecha:       gastoInicial.fecha      || EMPTY_FORM.fecha,
        notas:       gastoInicial.notas      || '',
      })
    }
  }, [gastoInicial])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async () => {
    if (!form.monto || !form.detalle || !form.categoria) {
      setError('Completá monto, detalle y categoría.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await onSubmit({ ...form, monto: Number(String(form.monto).replace(',', '.')) })
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="gasto-form">
      {error && <div className="form-error">⚠️ {error}</div>}

      <div className="form-group">
        <label>Monto $</label>
        <input
          type="number"
          inputMode="decimal"
          placeholder="0"
          value={form.monto}
          onChange={e => set('monto', e.target.value)}
          className="input-monto"
        />
      </div>

      <div className="form-group">
        <label>Detalle</label>
        <input
          type="text"
          placeholder="Descripción del gasto"
          value={form.detalle}
          onChange={e => set('detalle', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Categoría</label>
        <div className="cat-grid">
          {categorias.map(c => (
            <button
              key={c.nombre}
              type="button"
              className={`cat-btn ${form.categoria === c.nombre ? 'selected' : ''}`}
              onClick={() => set('categoria', c.nombre)}
            >
              <span>{c.icono}</span>
              <span>{c.nombre}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Método de pago</label>
        <div className="metodo-btns">
          {METODOS_PAGO.map(m => (
            <button
              key={m}
              type="button"
              className={`metodo-btn ${form.metodo_pago === m ? 'selected' : ''}`}
              onClick={() => set('metodo_pago', m)}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Fecha</label>
        <input
          type="date"
          value={form.fecha}
          onChange={e => set('fecha', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Notas (opcional)</label>
        <input
          type="text"
          placeholder="Notas adicionales"
          value={form.notas}
          onChange={e => set('notas', e.target.value)}
        />
      </div>

      <div className="form-actions">
        <button className="btn-secondary" onClick={onCancel} disabled={saving}>
          Cancelar
        </button>
        <button className="btn-primary" onClick={handleSubmit} disabled={saving}>
          {saving ? 'Guardando…' : gastoInicial ? 'Guardar cambios' : 'Registrar gasto'}
        </button>
      </div>
    </div>
  )
}
