import { useState, useMemo } from 'react'
import { useGastos } from '../hooks/useGastos.js'
import ResumenMensual from '../components/ResumenMensual.jsx'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from 'recharts'

function mesActual() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function mesMenos(mes, n) {
  const [anio, m] = mes.split('-').map(Number)
  const d = new Date(anio, m - 1 - n)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function labelMesCorto(mes) {
  const [anio, m] = mes.split('-')
  return new Date(Number(anio), Number(m) - 1).toLocaleDateString('es-AR', { month: 'short' })
}

export default function Estadisticas() {
  const [mes, setMes] = useState(mesActual())
  const { gastos, loading } = useGastos({ mes })

  // Para el gráfico de barras, cargamos los últimos 6 meses
  const meses = Array.from({ length: 6 }, (_, i) => mesMenos(mesActual(), 5 - i))

  // Datos de barras: usamos los gastos del mes actual simplificados
  // En producción esto requeriría múltiples fetches; aquí mostramos el mes seleccionado
  const barData = useMemo(() => {
    if (!gastos.length) return []
    // Agrupar por día del mes
    const porDia = gastos.reduce((acc, g) => {
      const dia = g.fecha ? g.fecha.split('-')[2] : '??'
      acc[dia] = (acc[dia] || 0) + Number(g.monto)
      return acc
    }, {})
    return Object.entries(porDia)
      .map(([dia, total]) => ({ dia: `${parseInt(dia)}`, total }))
      .sort((a, b) => Number(a.dia) - Number(b.dia))
  }, [gastos])

  const fmt = (n) => n >= 1000
    ? `$${(n / 1000).toFixed(0)}k`
    : `$${n}`

  return (
    <div className="page stats-page">
      <header className="page-header">
        <h1 className="page-title">📊 Estadísticas</h1>

        <div className="mes-tabs">
          {meses.map(m => (
            <button
              key={m}
              className={`mes-tab ${m === mes ? 'active' : ''}`}
              onClick={() => setMes(m)}
            >
              {labelMesCorto(m)}
            </button>
          ))}
        </div>
      </header>

      {loading ? (
        <div className="state-msg"><span className="spinner" /> Cargando…</div>
      ) : (
        <>
          <ResumenMensual gastos={gastos} />

          {barData.length > 0 && (
            <div className="chart-section">
              <h2 className="section-title">Gastos por día</h2>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                  <XAxis dataKey="dia" tick={{ fill: '#888', fontSize: 11 }} />
                  <YAxis tickFormatter={fmt} tick={{ fill: '#888', fontSize: 11 }} width={40} />
                  <Tooltip
                    cursor={false}
                    formatter={(v) => v.toLocaleString('es-AR', {
                      style: 'currency', currency: 'ARS', maximumFractionDigits: 0
                    })}
                    contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: 8 }}
                    labelStyle={{ color: '#e8c547' }}
                    itemStyle={{ color: '#f0f0f0' }}
                  />
                  <Bar dataKey="total" fill="#e8c547" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Ranking de métodos de pago */}
          {gastos.length > 0 && (
            <div className="chart-section">
              <h2 className="section-title">Por método de pago</h2>
              {(() => {
                const porMetodo = gastos.reduce((acc, g) => {
                  const m = g.metodo_pago || 'Efectivo'
                  acc[m] = (acc[m] || 0) + Number(g.monto)
                  return acc
                }, {})
                const total = gastos.reduce((s, g) => s + Number(g.monto), 0)
                return Object.entries(porMetodo)
                  .sort((a, b) => b[1] - a[1])
                  .map(([metodo, val]) => (
                    <div key={metodo} className="metodo-row">
                      <span className="metodo-nombre">{metodo}</span>
                      <div className="metodo-bar-wrap">
                        <div
                          className="metodo-bar-fill"
                          style={{ width: `${(val / total) * 100}%` }}
                        />
                      </div>
                      <span className="metodo-val">
                        {val.toLocaleString('es-AR', {
                          style: 'currency', currency: 'ARS', maximumFractionDigits: 0
                        })}
                      </span>
                    </div>
                  ))
              })()}
            </div>
          )}
        </>
      )}
    </div>
  )
}
