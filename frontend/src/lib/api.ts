import { config } from './config'
import { useAuth } from '../store/auth'

export interface ApiErrorBody {
  code: string
  message: string
  details?: unknown
}

export class ApiError extends Error {
  status: number
  code: string
  details?: unknown
  constructor(status: number, body: ApiErrorBody) {
    super(body.message)
    this.status = status
    this.code = body.code
    this.details = body.details
  }
}

type Params = Record<string, string | number | boolean | null | undefined>

function buildUrl(path: string, params?: Params): string {
  const url = `${config.apiUrl}${path}`
  if (!params) return url
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') qs.set(k, String(v))
  }
  const s = qs.toString()
  return s ? `${url}?${s}` : url
}

async function request<T>(method: string, path: string, opts: { params?: Params; body?: unknown; form?: URLSearchParams; signal?: AbortSignal } = {}): Promise<T> {
  const headers: Record<string, string> = {}
  const token = useAuth.getState().token
  if (token) headers.Authorization = `Bearer ${token}`
  let body: BodyInit | undefined
  if (opts.form) {
    body = opts.form
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
  } else if (opts.body !== undefined) {
    body = JSON.stringify(opts.body)
    headers['Content-Type'] = 'application/json'
  }
  let res: Response
  try {
    res = await fetch(buildUrl(path, opts.params), { method, headers, body, signal: opts.signal })
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw e
    throw new ApiError(0, { code: 'network_error', message: 'Não foi possível conectar à API. Verifique se o backend está em execução.' })
  }
  if (res.status === 401 && token) useAuth.getState().logout()
  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) {
    const err = (data && data.error) || { code: 'http_error', message: `Erro ${res.status}` }
    throw new ApiError(res.status, err)
  }
  return data as T
}

export const api = {
  get: <T>(path: string, params?: Params, signal?: AbortSignal) => request<T>('GET', path, { params, signal }),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, { body }),
  patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, { body }),
  del: <T>(path: string) => request<T>('DELETE', path),
  login: (email: string, password: string) =>
    request<{ access_token: string; user: { email: string; role: string } }>('POST', '/auth/login', {
      form: new URLSearchParams({ username: email, password }),
    }),
}
