import { useState, useEffect, useCallback } from 'react'
import { getGastos, getCategorias, postGasto, patchGasto, deleteGasto } from '../api/gastos.js'

export function useGastos(filtros = {}) {
  const [gastos,     setGastos]     = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState(null)

  const cargar = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [g, c] = await Promise.all([
        getGastos(filtros),
        getCategorias(),
      ])
      // filtramos filas "eliminadas" que quedaron vacías en Sheets
      setGastos(g.filter(x => x.id && x.detalle !== 'ELIMINADO'))
      setCategorias(c)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros.mes, filtros.categoria])

  useEffect(() => { cargar() }, [cargar])

  const agregar = async (gasto) => {
    await postGasto(gasto)
    await cargar()
  }

  const editar = async (id, cambios) => {
    await patchGasto(id, cambios)
    await cargar()
  }

  const eliminar = async (id) => {
    await deleteGasto(id)
    await cargar()
  }

  return { gastos, categorias, loading, error, cargar, agregar, editar, eliminar }
}
