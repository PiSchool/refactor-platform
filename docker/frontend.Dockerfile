# Refactor Platform — Next.js dashboard (standalone output).
FROM node:20-slim AS build
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
# API origin is baked into the rewrite table at build time (Next resolves
# rewrites() during build). Compose passes the backend service URL.
ARG PLATFORM_API_ORIGIN=http://backend:8000
ENV PLATFORM_API_ORIGIN=$PLATFORM_API_ORIGIN NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-slim AS run
WORKDIR /app/web
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000
COPY --from=build /app/web/.next/standalone ./
COPY --from=build /app/web/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
