# ==============================================================================
# Multi-stage Dockerfile: Frontend Build & Nginx Production Runtime
# ==============================================================================

# Stage 1: Build React Application
FROM node:22-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci --silent || npm install --silent

COPY frontend/ ./
RUN npm run build

# Stage 2: Nginx Runtime
FROM nginx:1.27-alpine

# Install curl for container health check
RUN apk add --no-cache curl

# Copy custom Nginx configuration
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
