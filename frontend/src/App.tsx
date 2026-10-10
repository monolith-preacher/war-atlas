import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Loading } from './components/common/ui'
import { AboutPage } from './pages/AboutPage'
import { ExplorerPage } from './pages/ExplorerPage'

const AdminApp = lazy(() => import('./pages/admin/AdminApp'))

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ExplorerPage />} />
      <Route path="/sobre" element={<AboutPage />} />
      <Route
        path="/admin/*"
        element={
          <Suspense fallback={<Loading />}>
            <AdminApp />
          </Suspense>
        }
      />
      <Route path="*" element={<div className="p-10 text-center text-parchment">Página não encontrada.</div>} />
    </Routes>
  )
}
