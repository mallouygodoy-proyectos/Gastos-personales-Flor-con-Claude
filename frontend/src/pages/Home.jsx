import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGastos } from '../hooks/useGastos.js'
import GastosList from '../components/GastosList.jsx'

function mesActual() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function labelMes(mes) {
  const [anio, m] = mes.split('-')
  return new Date(Number(anio), Number(m) - 1).toLocaleDateString('es-AR', {
    month: 'long', year: 'numeric'
  })
}

function mesMenos(mes, n) {
  const [anio, m] = mes.split('-').map(Number)
  const d = new Date(anio, m - 1 - n)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

export default function Home() {
  const navigate  = useNavigate()
  const [mes, setMes] = useState(mesActual())
  const [catFiltro, setCatFiltro] = useState('')

  const { gastos, categorias, loading, error, eliminar } = useGastos({ mes })

  const gastosFiltrados = useMemo(() =>
    catFiltro ? gastos.filter(g => g.categoria === catFiltro) : gastos
  , [gastos, catFiltro])

  const totalMes = gastos.reduce((s, g) => s + Number(g.monto), 0)

  const meses = Array.from({ length: 6 }, (_, i) => mesMenos(mesActual(), i))

  return (
    <div className="page home-page">
      <header className="page-header">
        <div className="header-top">
          <h1 className="page-title">💸 Gastos</h1>
          <span className="header-total">
            {totalMes.toLocaleString('es-AR', {
              style: 'currency', currency: 'ARS', maximumFractionDigits: 0
            })}
          </span>
        </div>

        {/* Selector de mes */}
        <div className="mes-tabs">
          {meses.map(m => (
            <button
              key={m}
              className={`mes-tab ${m === mes ? 'active' : ''}`}
              onClick={() => setMes(m)}
            >
              {labelMes(m)}
            </button>
          ))}
        </div>

        {/* Filtro categoría */}
        {categorias.length > 0 && (
          <div className="cat-filter-row">
            <button
              className={`cat-filter-btn ${!catFiltro ? 'active' : ''}`}
              onClick={() => setCatFiltro('')}
            >
              Todas
            </button>
            {categorias.map(c => (
              <button
                key={c.nombre}
                className={`cat-filter-btn ${catFiltro === c.nombre ? 'active' : ''}`}
                onClick={() => setCatFiltro(c.nombre)}
              >
                {c.icono} {c.nombre}
              </button>
            ))}
          </div>
        )}
      </header>

      <GastosList
        gastos={gastosFiltrados}
        loading={loading}
        error={error}
        onEliminar={eliminar}
      />

      <button className="fab" onClick={() => navigate('/nuevo')} title="Nuevo gasto">
        +
      </button>
    </div>
  )
}
