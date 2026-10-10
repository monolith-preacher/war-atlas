import { ClipboardCheck, Database, FileClock, LayoutDashboard, LogOut, Map, ShieldAlert, Upload } from 'lucide-react'
import { useState } from 'react'
import { Link, NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { ErrorState, Loading } from '../../components/common/ui'
import { Logo } from '../../components/layout/Header'
import { api, ApiError } from '../../lib/api'
import { useAuth } from '../../store/auth'
import { useAdminMeta } from './adminApi'
import { Dashboard } from './Dashboard'
import { EntityForm } from './EntityForm'
import { EntityList } from './EntityList'
import { ImportsPage, IntegrityPage, ReviewQueue, RevisionsPage } from './Workflow'

function LoginPage() {
  const setSession = useAuth((s) => s.setSession)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const r = await api.login(email, password)
      setSession(r.access_token, r.user)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Falha ao entrar.')
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="wa-grid-bg flex h-full items-center justify-center p-4">
      <form onSubmit={submit} className="wa-panel w-full max-w-sm space-y-4 rounded-lg p-6">
        <Logo />
        <div>
          <h1 className="wa-heading text-xl">Painel administrativo</h1>
          <p className="text-[12.5px] text-steel-400">Acesso restrito a editores e revisores. A exploração pública não requer login.</p>
        </div>
        <label className="block space-y-1">
          <span className="wa-label">E-mail</span>
          <input className="wa-input" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="block space-y-1">
          <span className="wa-label">Senha</span>
          <input className="wa-input" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <p className="text-[12.5px] text-alert" role="alert">{error}</p>}
        <button className="wa-btn wa-btn-primary w-full justify-center" disabled={busy}>
          {busy ? 'Entrando…' : 'Entrar'}
        </button>
        <Link to="/" className="wa-link block text-center text-[12px]">
          ← Voltar ao mapa
        </Link>
      </form>
    </div>
  )
}

export default function AdminApp() {
  const token = useAuth((s) => s.token)
  const user = useAuth((s) => s.user)
  const logout = useAuth((s) => s.logout)
  const meta = useAdminMeta()
  const navigate = useNavigate()
  if (!token) return <LoginPage />
  if (meta.isLoading) return <Loading label="Carregando painel…" />
  if (meta.isError) return <ErrorState error={meta.error} onRetry={() => meta.refetch()} />
  const entities = meta.data!.entities
  const primary = meta.data!.primary.map((k) => entities.find((e) => e.key === k)!).filter(Boolean)
  const relations = entities.filter((e) => !e.primary)
  const navCls = ({ isActive }: { isActive: boolean }) => `flex items-center gap-2 rounded px-2 py-1 text-[12.5px] ${isActive ? 'bg-ink-700 text-brass-300' : 'text-steel-300 hover:bg-ink-800 hover:text-parchment'}`
  return (
    <div className="flex h-full flex-col">
      <header className="wa-panel flex items-center gap-4 border-x-0 border-t-0 px-4 py-2">
        <Logo />
        <span className="wa-chip border-brass-600 text-brass-300">Administração</span>
        <div className="ml-auto flex items-center gap-3 text-[12px] text-steel-400">
          <span>
            {user?.email} · <b className="text-steel-200">{user?.role}</b>
          </span>
          <Link to="/" className="wa-btn">
            <Map size={14} /> Mapa
          </Link>
          <button className="wa-btn" onClick={() => { logout(); navigate('/admin') }}>
            <LogOut size={14} /> Sair
          </button>
        </div>
      </header>
      <div className="flex min-h-0 flex-1">
        <nav className="w-60 shrink-0 space-y-4 overflow-y-auto border-r border-ink-700 bg-ink-900 p-3">
          <div className="space-y-0.5">
            <NavLink end to="/admin" className={navCls}><LayoutDashboard size={14} /> Visão geral</NavLink>
            <NavLink to="/admin/revisao" className={navCls}><ClipboardCheck size={14} /> Fila de revisão</NavLink>
            <NavLink to="/admin/importacoes" className={navCls}><Upload size={14} /> Importações</NavLink>
            <NavLink to="/admin/integridade" className={navCls}><ShieldAlert size={14} /> Integridade</NavLink>
            <NavLink to="/admin/historico" className={navCls}><FileClock size={14} /> Histórico de alterações</NavLink>
          </div>
          <div>
            <p className="wa-label mb-1 px-2">Registros principais</p>
            {primary.map((e) => (
              <NavLink key={e.key} to={`/admin/e/${e.key}`} className={navCls}>
                <Database size={13} /> {e.label_plural}
              </NavLink>
            ))}
          </div>
          <details>
            <summary className="wa-label cursor-pointer px-2">Relações e apoio ({relations.length})</summary>
            <div className="mt-1">
              {relations.map((e) => (
                <NavLink key={e.key} to={`/admin/e/${e.key}`} className={navCls}>
                  {e.label_plural}
                </NavLink>
              ))}
            </div>
          </details>
        </nav>
        <main className="min-w-0 flex-1 overflow-y-auto">
          <Routes>
            <Route index element={<Dashboard />} />
            <Route path="revisao" element={<ReviewQueue />} />
            <Route path="importacoes" element={<ImportsPage />} />
            <Route path="integridade" element={<IntegrityPage />} />
            <Route path="historico" element={<RevisionsPage />} />
            <Route path="e/:entity" element={<EntityList />} />
            <Route path="e/:entity/novo" element={<EntityForm />} />
            <Route path="e/:entity/:id" element={<EntityForm />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
