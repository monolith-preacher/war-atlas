# --- build ---
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG VITE_API_URL=/api/v1
ARG VITE_GLYPHS_URL=
ARG VITE_MODERN_TILES_URL=
ARG VITE_TERRAIN_TILES_URL=
ENV VITE_API_URL=$VITE_API_URL VITE_GLYPHS_URL=$VITE_GLYPHS_URL VITE_MODERN_TILES_URL=$VITE_MODERN_TILES_URL VITE_TERRAIN_TILES_URL=$VITE_TERRAIN_TILES_URL
RUN npm run build

# --- serve ---
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
