import { useNavigate } from 'react-router-dom'

const METODO_ICON = {
  'Efectivo':    '💵',
  'Débito':      '💳',
  'Crédito':     '💳',
  'Transferencia': '📲',
}

export default function GastoCard({ gasto, onEliminar }) {
  const navigate = useNavigate()

  const fecha = gasto.fecha
    ? new Date(gasto.fecha + 'T00:00:00').toLocaleDateString('es-AR', {
        day: '2-digit', month: 'short'
      })
    : ''

  const monto = Number(gasto.monto).toLocaleString('es-AR', {
    style: 'currency', currency: 'ARS', maximumFractionDigits: 0
  })

  return (
    <div className="gasto-card">
      <div className="gasto-card-left">
        <span className="gasto-fecha">{fecha}</span>
        <span className="gasto-detalle">{gasto.detalle}</span>
        <span className="gasto-cat-badge">{gasto.categoria}</span>
      </div>
      <div className="gasto-card-right">
        <span className="gasto-monto">{monto}</span>
        <span className="gasto-metodo">
          {METODO_ICON[gasto.metodo_pago] || '💰'} {gasto.metodo_pago}
        </span>
        <div className="gasto-actions">
          <button
            className="btn-icon"
            onClick={() => navigate(`/editar/${gasto.id}`)}
            title="Editar"
          >✏️</button>
          <button
            className="btn-icon btn-delete"
            onClick={() => {
              if (confirm(`¿Eliminar "${gasto.detalle}"?`)) onEliminar(gasto.id)
            }}
            title="Eliminar"
          >🗑️</button>
        </div>
      </div>
    </div>
  )
}
