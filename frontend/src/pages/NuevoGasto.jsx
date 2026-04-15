import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useGastos } from '../hooks/useGastos.js'
import GastoForm from '../components/GastoForm.jsx'
import { getGastos } from '../api/gastos.js'

export default function NuevoGasto() {
  const navigate     = useNavigate()
  const { id }       = useParams()
  const isEdit       = Boolean(id)

  const { categorias, agregar, editar } = useGastos()
  const [gastoInicial, setGastoInicial] = useState(null)
  const [loadingEdit, setLoadingEdit]   = useState(isEdit)

  useEffect(() => {
    if (!isEdit) return
    getGastos().then(lista => {
      const g = lista.find(x => x.id === id)
      if (g) setGastoInicial(g)
    }).finally(() => setLoadingEdit(false))
  }, [id, isEdit])

  const handleSubmit = async (datos) => {
    if (isEdit) {
      await editar(id, datos)
    } else {
      await agregar(datos)
    }
    navigate('/')
  }

  if (loadingEdit) return (
    <div className="page">
      <div className="state-msg"><span className="spinner" /> Cargando…</div>
    </div>
  )

  return (
    <div className="page nuevo-page">
      <header className="page-header">
        <button className="btn-back" onClick={() => navigate(-1)}>← Volver</button>
        <h1 className="page-title">{isEdit ? '✏️ Editar gasto' : '➕ Nuevo gasto'}</h1>
      </header>

      <GastoForm
        categorias={categorias}
        gastoInicial={gastoInicial}
        onSubmit={handleSubmit}
        onCancel={() => navigate('/')}
      />
    </div>
  )
}
