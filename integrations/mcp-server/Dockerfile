# syntax=docker/dockerfile:1
#
# Build from the repository root, because the server ships the auditors and the
# reference library that live there:
#
#   docker build -f integrations/mcp-server/Dockerfile -t apple-native-engineer .
#   docker run --rm -p 3927:3927 apple-native-engineer
#   curl -s http://127.0.0.1:3927/health
#
# Two stages: dependencies are installed once with the lockfile, then the runtime
# image carries only node_modules, src, and the vendored Python tools.

FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY integrations/mcp-server/package.json integrations/mcp-server/package-lock.json ./
RUN npm ci --omit=dev


FROM node:22-bookworm-slim AS runtime

# Python is not optional: every auditor is a Python script, standard library only.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --create-home --uid 10001 mcp

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY integrations/mcp-server/package.json ./package.json
COPY integrations/mcp-server/src ./src

# The runtime knows this layout as `vendor/`: src/runner.js prefers the live
# repository when one exists and falls back to the staged copy otherwise.
COPY tools       ./vendor/tools
COPY data        ./vendor/data
COPY references  ./vendor/references
COPY checklists  ./vendor/checklists
COPY examples    ./vendor/examples
COPY commands    ./vendor/commands
COPY SKILL.md    ./vendor/SKILL.md
COPY README.md   ./vendor/README.md
COPY LICENSE     ./vendor/LICENSE

ENV NODE_ENV=production \
    APPLE_NATIVE_PYTHON=python3 \
    PYTHONUNBUFFERED=1

USER mcp
EXPOSE 3927

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:3927/health').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

ENTRYPOINT ["node", "src/index.js"]
# The container is only reachable through the published port, so the non-loopback
# bind is intentional here. Put an authenticating proxy in front of it if the port
# is exposed to anything but your own machine.
CMD ["--http", "--allow-remote", "--http-host", "0.0.0.0"]
