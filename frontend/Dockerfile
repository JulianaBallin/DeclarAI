# ============================================================
# DeclarAI - Frontend Dockerfile
# Multi-stage: Node.js (build) + Nginx (serve)
# ============================================================

# Estágio 1: build do React
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --silent

COPY . .

# URL da API injetada em tempo de build; pode ser sobrescrita no docker-compose
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ============================================================
# Estágio 2: servidor Nginx para os arquivos estáticos
# ============================================================
FROM nginx:1.27-alpine

LABEL description="Frontend React do DeclarAI"

# Config Nginx com suporte a SPA (react-router)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia o build gerado no estágio anterior
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
