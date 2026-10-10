/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_GLYPHS_URL?: string
  readonly VITE_MODERN_TILES_URL?: string
  readonly VITE_TERRAIN_TILES_URL?: string
}
interface ImportMeta {
  readonly env: ImportMetaEnv
}
