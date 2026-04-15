import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const COLORS = [
  '#e8c547','#e87b47','#47e8c5','#e847a3','#47a3e8',
  '#a3e847','#c547e8','#e84747','#47e847','#4747e8',
]

export default function ResumenMensual({ gastos }) {
  if (!gastos.length) return null

  // Total general
  const total = gastos.reduce((s, g) => s + Number(g.monto), 0)

  // Agrupar por categoría
  const porCategoria = gastos.reduce((acc, g) => {
    acc[g.categoria] = (acc[g.categoria] || 0) + Number(g.monto)
    return acc
  }, {})

  const data = Object.entries(porCategoria)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)

  const fmt = (n) => n.toLocaleString('es-AR', {
    style: 'currency', currency: 'ARS', maximumFractionDigits: 0
  })

  return (
    <div className="resumen-mensual">
      <div className="resumen-total">
        <span className="resumen-total-label">Total del mes</span>
        <span className="resumen-total-valor">{fmt(total)}</span>
      </div>

      <div className="resumen-chart">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={3}
              dataKey="value"
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v) => fmt(v)}
              contentStyle={{
                background: '#2a2a2a',
                border: '1px solid #e8c547',
                borderRadius: 8,
                color: '#f0f0f0'
              }}
              labelStyle={{ color: '#e8c547', fontWeight: 700 }}
              itemStyle={{ color: '#f0f0f0' }}
              wrapperStyle={{ color: '#f0f0f0' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="resumen-tabla">
        {data.map((item, i) => (
          <div key={item.name} className="resumen-row">
            <span className="resumen-dot" style={{ background: COLORS[i % COLORS.length] }} />
            <span className="resumen-cat">{item.name}</span>
            <span className="resumen-pct">{((item.value / total) * 100).toFixed(0)}%</span>
            <span className="resumen-val">{fmt(item.value)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
