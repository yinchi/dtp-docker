FROM oven/bun:latest as builder

WORKDIR /build
# Ensure node_modules/, dist/ are in .Dockerignore
COPY . .
RUN bun install
RUN bun run build

FROM joseluisq/static-web-server:2-alpine
COPY --from=builder /build/dist /var/public
