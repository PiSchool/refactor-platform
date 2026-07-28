# Refactor Platform — Next.js dashboard (standalone output).
FROM node:24-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS build
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
# Build identity, served by /rp-build. The fingerprint covers the dashboard
# source, so a rebuild that changed nothing reports the same value and an
# operator can tell a replaced bundle from the one it replaced.
ARG RP_BUILD_REV=""
RUN printf 'revision=%s\nbuiltAt=%s\nfingerprint=%s\n' \
      "${RP_BUILD_REV}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(node scripts/build-fingerprint.mjs)" \
      > build-stamp
# API origin is baked into the rewrite table at build time (Next resolves
# rewrites() during build). Compose passes the backend service URL.
ARG PLATFORM_API_ORIGIN=http://backend:8000
ENV PLATFORM_API_ORIGIN=$PLATFORM_API_ORIGIN NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:24-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS run
WORKDIR /app/web
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=build /app/web/.next/standalone ./
COPY --from=build /app/web/.next/static ./.next/static
# Next's standalone bundle excludes public/; without this the brand assets 404.
COPY --from=build /app/web/public ./public
COPY --from=build /app/web/build-stamp ./build-stamp
EXPOSE 3000
CMD ["node", "server.js"]
