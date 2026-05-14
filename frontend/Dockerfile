FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --prefer-offline

COPY . .
# Minimal config.json so vite.config.js falls through to env vars during build.
# In production nginx handles /api routing, so no backend URL needs to be embedded.
RUN echo '{"backendUrl":"","backendPort":""}' > src/config.json
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
