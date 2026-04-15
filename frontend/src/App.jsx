import { Routes, Route, NavLink } from 'react-router-dom'
import Home          from './pages/Home.jsx'
import NuevoGasto    from './pages/NuevoGasto.jsx'
import Estadisticas  from './pages/Estadisticas.jsx'

const NAV_ITEMS = [
  { to: '/',             label: 'Gastos',  icon: '💸' },
  { to: '/estadisticas', label: 'Resumen', icon: '📊' },
]

export default function App() {
  return (
    <div className="app-shell">
      <main className="app-main">
        <Routes>
          <Route path="/"              element={<Home />} />
          <Route path="/nuevo"         element={<NuevoGasto />} />
          <Route path="/editar/:id"    element={<NuevoGasto />} />
          <Route path="/estadisticas"  element={<Estadisticas />} />
        </Routes>
      </main>

      <nav className="bottom-nav">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
