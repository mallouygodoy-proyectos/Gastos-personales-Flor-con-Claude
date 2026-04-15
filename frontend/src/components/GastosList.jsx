import GastoCard from './GastoCard.jsx'

export default function GastosList({ gastos, loading, error, onEliminar }) {
  if (loading) return (
    <div className="state-msg">
      <span className="spinner" />
      Cargando gastos…
    </div>
  )
  if (error)   return <div className="state-msg error">⚠️ {error}</div>
  if (!gastos.length) return (
    <div className="state-msg empty">
      <span>🍃</span>
      <p>No hay gastos registrados</p>
    </div>
  )

  // Agrupar por fecha
  const grupos = gastos.reduce((acc, g) => {
    const key = g.fecha || 'Sin fecha'
    if (!acc[key]) acc[key] = []
    acc[key].push(g)
    return acc
  }, {})

  const fechasOrdenadas = Object.keys(grupos).sort((a, b) => b.localeCompare(a))

  return (
    <div className="gastos-list">
      {fechasOrdenadas.map(fecha => (
        <div key={fecha} className="gastos-grupo">
          <div className="grupo-header">
            {fecha !== 'Sin fecha'
              ? new Date(fecha + 'T00:00:00').toLocaleDateString('es-AR', {
                  weekday: 'long', day: 'numeric', month: 'long'
                })
              : 'Sin fecha'}
            <span className="grupo-total">
              {grupos[fecha]
                .reduce((s, g) => s + Number(g.monto), 0)
                .toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })}
            </span>
          </div>
          {grupos[fecha].map(g => (
            <GastoCard key={g.id} gasto={g} onEliminar={onEliminar} />
          ))}
        </div>
      ))}
    </div>
  )
}
