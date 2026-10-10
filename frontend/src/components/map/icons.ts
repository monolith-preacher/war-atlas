/** Map symbols drawn on canvas at runtime (no external sprite needed). */
import type { Map as MLMap } from 'maplibre-gl'

const SIZE = 64

function make(draw: (c: CanvasRenderingContext2D, s: number) => void) {
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = SIZE
  const ctx = canvas.getContext('2d')!
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  draw(ctx, SIZE)
  const img = ctx.getImageData(0, 0, SIZE, SIZE)
  return { width: SIZE, height: SIZE, data: new Uint8Array(img.data.buffer) }
}

function swords(c: CanvasRenderingContext2D, s: number, fill: string, stroke: string) {
  c.beginPath()
  c.arc(s / 2, s / 2, s * 0.4, 0, Math.PI * 2)
  c.fillStyle = fill
  c.fill()
  c.lineWidth = 3
  c.strokeStyle = stroke
  c.stroke()
  c.lineWidth = 4.5
  c.strokeStyle = '#f6efe0'
  c.beginPath()
  c.moveTo(s * 0.32, s * 0.32)
  c.lineTo(s * 0.68, s * 0.68)
  c.moveTo(s * 0.68, s * 0.32)
  c.lineTo(s * 0.32, s * 0.68)
  c.stroke()
  c.lineWidth = 3
  c.beginPath()
  c.moveTo(s * 0.27, s * 0.42)
  c.lineTo(s * 0.42, s * 0.27)
  c.moveTo(s * 0.58, s * 0.27)
  c.lineTo(s * 0.73, s * 0.42)
  c.stroke()
}

export function registerIcons(map: MLMap) {
  const icons: Record<string, [ReturnType<typeof make>, boolean]> = {
    'battle-active': [make((c, s) => swords(c, s, '#8e2f25', '#f08a72')), false],
    'battle-past': [make((c, s) => swords(c, s, '#3a3f44', '#8a939b')), false],
    event: [
      make((c, s) => {
        c.beginPath()
        c.moveTo(s / 2, s * 0.12)
        c.lineTo(s * 0.88, s / 2)
        c.lineTo(s / 2, s * 0.88)
        c.lineTo(s * 0.12, s / 2)
        c.closePath()
        c.fillStyle = '#d8b25a'
        c.fill()
        c.lineWidth = 3
        c.strokeStyle = '#2a2414'
        c.stroke()
      }),
      false,
    ],
    objective: [
      make((c, s) => {
        c.strokeStyle = '#e8c96a'
        c.lineWidth = 4
        for (const r of [0.36, 0.2]) {
          c.beginPath()
          c.arc(s / 2, s / 2, s * r, 0, Math.PI * 2)
          c.stroke()
        }
        c.fillStyle = '#e8c96a'
        c.beginPath()
        c.arc(s / 2, s / 2, s * 0.06, 0, Math.PI * 2)
        c.fill()
      }),
      false,
    ],
    fortification: [
      make((c, s) => {
        c.fillStyle = '#2b2a26'
        c.strokeStyle = '#c9b48a'
        c.lineWidth = 3.5
        c.beginPath()
        const y = s * 0.3
        c.moveTo(s * 0.18, s * 0.82)
        c.lineTo(s * 0.18, y)
        for (let i = 0; i < 4; i++) {
          const x = s * (0.18 + i * 0.16)
          c.lineTo(x + s * 0.08, y)
          c.lineTo(x + s * 0.08, y - s * 0.1)
          c.lineTo(x + s * 0.16, y - s * 0.1)
          c.lineTo(x + s * 0.16, y)
        }
        c.lineTo(s * 0.82, s * 0.82)
        c.closePath()
        c.fill()
        c.stroke()
      }),
      false,
    ],
    airfield: [
      make((c, s) => {
        c.fillStyle = '#1f2a36'
        c.strokeStyle = '#9fb7d6'
        c.lineWidth = 3
        c.beginPath()
        c.arc(s / 2, s / 2, s * 0.38, 0, Math.PI * 2)
        c.fill()
        c.stroke()
        c.lineWidth = 5
        c.beginPath()
        c.moveTo(s / 2, s * 0.22)
        c.lineTo(s / 2, s * 0.78)
        c.moveTo(s * 0.24, s * 0.48)
        c.lineTo(s * 0.76, s * 0.48)
        c.moveTo(s * 0.38, s * 0.72)
        c.lineTo(s * 0.62, s * 0.72)
        c.stroke()
      }),
      false,
    ],
    naval: [
      make((c, s) => {
        c.fillStyle = '#18252f'
        c.strokeStyle = '#7fa6c4'
        c.lineWidth = 3
        c.beginPath()
        c.arc(s / 2, s / 2, s * 0.38, 0, Math.PI * 2)
        c.fill()
        c.stroke()
        c.lineWidth = 4
        c.beginPath()
        c.moveTo(s / 2, s * 0.24)
        c.lineTo(s / 2, s * 0.74)
        c.moveTo(s * 0.36, s * 0.34)
        c.lineTo(s * 0.64, s * 0.34)
        c.moveTo(s * 0.28, s * 0.56)
        c.quadraticCurveTo(s / 2, s * 0.86, s * 0.72, s * 0.56)
        c.stroke()
      }),
      false,
    ],
    // NATO-style frame (white, SDF-tinted by side)
    unit: [
      make((c, s) => {
        c.strokeStyle = '#fff'
        c.lineWidth = 5
        c.strokeRect(s * 0.12, s * 0.26, s * 0.76, s * 0.48)
        c.beginPath()
        c.moveTo(s * 0.12, s * 0.26)
        c.lineTo(s * 0.88, s * 0.74)
        c.moveTo(s * 0.88, s * 0.26)
        c.lineTo(s * 0.12, s * 0.74)
        c.stroke()
      }),
      true,
    ],
    arrowhead: [
      make((c, s) => {
        c.fillStyle = '#fff'
        c.beginPath()
        c.moveTo(s / 2, s * 0.08)
        c.lineTo(s * 0.86, s * 0.86)
        c.lineTo(s / 2, s * 0.66)
        c.lineTo(s * 0.14, s * 0.86)
        c.closePath()
        c.fill()
      }),
      true,
    ],
  }
  for (const [name, [img, sdf]] of Object.entries(icons)) {
    if (!map.hasImage(name)) map.addImage(name, img, { pixelRatio: 2, sdf })
  }
}

/** Arrowheads for axis lines: a point at the last vertex rotated along the final segment. */
export function arrowheadsFor(fc: GeoJSON.FeatureCollection): GeoJSON.FeatureCollection {
  const out: GeoJSON.Feature[] = []
  for (const f of fc.features) {
    const layer = f.properties?.layer
    if ((layer !== 'advance_axis' && layer !== 'withdrawal_axis') || f.geometry.type !== 'LineString') continue
    const coords = f.geometry.coordinates
    if (coords.length < 2) continue
    const [x1, y1] = coords[coords.length - 2]
    const [x2, y2] = coords[coords.length - 1]
    const lat = ((y1 + y2) / 2) * (Math.PI / 180)
    const bearing = (Math.atan2((x2 - x1) * Math.cos(lat), y2 - y1) * 180) / Math.PI
    out.push({ type: 'Feature', geometry: { type: 'Point', coordinates: [x2, y2] }, properties: { ...f.properties, bearing } })
  }
  return { type: 'FeatureCollection', features: out }
}
