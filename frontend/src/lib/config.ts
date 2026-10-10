/** Runtime configuration from Vite env variables (see .env.example). */

const env = import.meta.env

function opt(value: string | undefined, fallback: string): string | null {
  if (value === 'off') return null
  return value && value.trim() ? value.trim() : fallback
}

export const config = {
  apiUrl: (env.VITE_API_URL && env.VITE_API_URL.trim()) || '/api/v1',
  /** Font glyphs for map labels. Default: OpenFreeMap (free, no key). */
  glyphsUrl: opt(env.VITE_GLYPHS_URL, 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf'),
  /** Modern reference vector tiles (OpenMapTiles schema). Default: OpenFreeMap. */
  modernTilesUrl: opt(env.VITE_MODERN_TILES_URL, 'https://tiles.openfreemap.org/planet'),
  /** Terrarium-encoded DEM for hillshade. Default: AWS Open Data Terrain Tiles. */
  terrainTilesUrl: opt(env.VITE_TERRAIN_TILES_URL, 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'),
  fontRegular: ['Noto Sans Regular'],
  fontBold: ['Noto Sans Bold'],
  fontItalic: ['Noto Sans Italic'],
}
