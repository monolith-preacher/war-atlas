import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { useAuth } from '../../store/auth'

export interface FieldMeta {
  name: string
  label: string
  type: 'text' | 'textarea' | 'date' | 'enum' | 'ref' | 'int' | 'float' | 'bool' | 'geometry' | 'json'
  required: boolean
  options: string[] | null
  ref: string | null
  geometry_type: string | null
}

export interface EntityMeta {
  key: string
  label: string
  label_plural: string
  primary: boolean
  has_status: boolean
  title_fields: string[]
  fields: FieldMeta[]
}

export interface AdminMeta {
  entities: EntityMeta[]
  primary: string[]
  user: { email: string; role: string }
}

export const STATUS_LABELS: Record<string, string> = { draft: 'Rascunho', in_review: 'Em revisão', published: 'Publicado', archived: 'Arquivado' }
export const STATUS_TONES: Record<string, string> = { draft: 'neutral', in_review: 'warn', published: 'ok', archived: 'info' }

export function useAdminMeta() {
  const token = useAuth((s) => s.token)
  return useQuery({ queryKey: ['admin-meta', token], queryFn: () => api.get<AdminMeta>('/admin/meta'), enabled: !!token, staleTime: Infinity })
}

export function useEntityMeta(key: string | undefined) {
  const meta = useAdminMeta()
  return { ...meta, entity: meta.data?.entities.find((e) => e.key === key) }
}

export const isReviewer = (role?: string) => role === 'reviewer' || role === 'admin'
