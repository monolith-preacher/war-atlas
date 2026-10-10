import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  user: { email: string; role: string } | null
  setSession: (token: string, user: { email: string; role: string }) => void
  logout: () => void
}

/** Admin session. Stored in sessionStorage (cleared when the browser tab closes). */
export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setSession: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'waratlas-auth', storage: { getItem: (k) => JSON.parse(sessionStorage.getItem(k) || 'null'), setItem: (k, v) => sessionStorage.setItem(k, JSON.stringify(v)), removeItem: (k) => sessionStorage.removeItem(k) } },
  ),
)
