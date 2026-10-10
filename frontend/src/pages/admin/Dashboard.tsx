import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Badge, ErrorState, Loading } from '../../components/common/ui'
import { api } from '../../lib/api'
import { STATUS_LABELS, STATUS_TONES, useAdminMeta } from './adminApi'

export function Dashboard() {
  const meta = useAdminMeta()
  const stats = useQuery({ queryKey: ['admin-stats'], queryFn: () => api.get<Record<string, Record<string, number> | number>>('/admin/stats') })
  if (stats.isLoading) return <Loading />
  if (stats.isError) return <ErrorState error={stats.error} />
  const s = stats.data!
  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="wa-heading text-2xl">Visão geral do acervo</h1>
        <p className="text-[13px] text-steel-400">Registros criados no painel começam como rascunho; somente revisores publicam. Publicar exige ao menos uma fonte.</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Link to="/admin/importacoes" className="wa-panel rounded-md px-4 py-3">
          <p className="wa-label">Importações pendentes</p>
          <p className="wa-heading text-2xl">{String(s.imports_pending ?? 0)}</p>
        </Link>
        <Link to="/admin/revisao" className="wa-panel rounded-md px-4 py-3">
          <p className="wa-label">Em revisão</p>
          <p className="wa-heading text-2xl">
            {Object.values(s).reduce<number>((n, v) => n + (typeof v === 'object' ? (v.in_review ?? 0) : 0), 0)}
          </p>
        </Link>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {meta.data?.primary.map((key) => {
          const ent = meta.data!.entities.find((e) => e.key === key)!
          const v = s[key] as Record<string, number> | undefined
          return (
            <Link key={key} to={`/admin/e/${key}`} className="wa-panel rounded-md p-4 hover:border-brass-600">
              <p className="text-[14px] text-parchment">{ent.label_plural}</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {v && Object.entries(v).map(([st, n]) => (
                  <Badge key={st} tone={STATUS_TONES[st] ?? 'neutral'}>
                    {STATUS_LABELS[st] ?? st}: {n}
                  </Badge>
                ))}
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
