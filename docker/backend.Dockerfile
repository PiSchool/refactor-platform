# Refactor Platform — backend runtime.
# Heavy by design: it hosts the agent CLI, LSP servers, and the full Java
# build toolchain (4 JDKs + Maven + Gradle) that benchmark evaluation needs.
FROM ubuntu:22.04@sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl wget gnupg ca-certificates git unzip xz-utils procps \
      software-properties-common maven gradle \
 && rm -rf /var/lib/apt/lists/*

# ── JDKs 8/11/17/21 (Adoptium Temurin) ──────────────────────────────────────
RUN mkdir -p /etc/apt/keyrings \
 && wget -qO- https://packages.adoptium.net/artifactory/api/gpg/key/public \
      | gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg \
 && echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb jammy main" \
      > /etc/apt/sources.list.d/adoptium.list \
 && apt-get update && apt-get install -y --no-install-recommends \
      temurin-8-jdk temurin-11-jdk temurin-17-jdk temurin-21-jdk \
 && rm -rf /var/lib/apt/lists/*
ENV JDK_8_HOME=/usr/lib/jvm/temurin-8-jdk-amd64 \
    JDK_11_HOME=/usr/lib/jvm/temurin-11-jdk-amd64 \
    JDK_17_HOME=/usr/lib/jvm/temurin-17-jdk-amd64 \
    JDK_21_HOME=/usr/lib/jvm/temurin-21-jdk-amd64 \
    JAVA_HOME=/usr/lib/jvm/temurin-17-jdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# ── Python 3.12 + Node + agent CLIs ─────────────────────────────────────────
RUN add-apt-repository -y ppa:deadsnakes/ppa \
 && apt-get update && apt-get install -y --no-install-recommends \
      python3.12 python3.12-venv python3.12-dev \
 && rm -rf /var/lib/apt/lists/*
# Node from the official distribution, pinned and verified against its published
# checksum. The third-party apt repository used before was withdrawn when Node 20
# reached end of life; because its installer ran through a pipe, the failure was
# swallowed and the build fell back to the distribution's Node 12, which carries
# no npm. Verifying `node` and `npm` here fails the build at the cause instead.
ARG NODE_VERSION=24.18.0
ARG NODE_SHA256=55aa7153f9d88f28d765fcdad5ae6945b5c0f98a36881703817e4c450fa76742
RUN set -eu; \
    curl -fsSLo /tmp/node.tar.xz \
      "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz"; \
    echo "${NODE_SHA256}  /tmp/node.tar.xz" | sha256sum -c -; \
    tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 --no-same-owner \
      --exclude CHANGELOG.md --exclude LICENSE --exclude README.md; \
    rm /tmp/node.tar.xz; \
    node --version; npm --version

# Agent CLIs. Every shipped adapter's executable is installed here; an adapter
# declares the executable it drives, so one an operator adds later is reported
# as unavailable with its install command rather than failing inside a run.
RUN npm install -g --no-fund --no-audit \
      @github/copilot @openai/codex @anthropic-ai/claude-code opencode-ai \
 && npm cache clean --force

# Junie CLI. Its installer puts a launcher in $HOME/.local/bin and the runtime it
# launches in $HOME/.local/share/junie. Agent sessions run as an unprivileged
# user that cannot traverse root's home, so both are installed under /opt: the
# launcher goes on the system path and JUNIE_DATA tells it where the runtime is,
# whoever invokes it. JUNIE_SKIP_UPDATE_CHECK stops the binary replacing itself
# mid-study, which would make a run irreproducible. The installer is fetched to a
# file rather than piped into a shell, so a failed download fails this step
# instead of running an empty script. JUNIE_HOME, which holds per-session
# settings and credentials, is set by the adapter to a writable session
# directory.
ENV JUNIE_DATA=/opt/junie/.local/share/junie \
    JUNIE_SKIP_UPDATE_CHECK=1
RUN set -eu; \
    curl -fsSLo /tmp/junie-install.sh https://junie.jetbrains.com/install.sh; \
    HOME=/opt/junie bash /tmp/junie-install.sh; \
    rm /tmp/junie-install.sh; \
    mv /opt/junie/.local/bin/junie /usr/local/bin/junie; \
    chmod a+rx /usr/local/bin/junie; \
    chmod -R a+rX /opt/junie

# ── uv + server dependency layer (cached on lockfile) ───────────────────────
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH=/root/.local/bin:$PATH
WORKDIR /app/server
COPY server/pyproject.toml server/uv.lock ./
RUN uv sync --frozen --no-dev --extra postgres --python python3.12
# Python LSP into the same venv so `pylsp` lands on PATH.
RUN uv pip install python-lsp-server
# CodeBLEU for the swe benchmark's similarity metric. Pinned with its tree-sitter
# grammar: codebleu 0.7 builds the Java parser against these exact versions.
RUN uv pip install codebleu==0.7.0 tree-sitter==0.22.3 tree-sitter-java==0.21.0
ENV PATH=/app/server/.venv/bin:$PATH
# Java LSP: Eclipse JDT.LS snapshot ships a `bin/jdtls` launcher.
RUN mkdir -p /opt/jdtls \
 && curl -fsSL https://download.eclipse.org/jdtls/snapshots/jdt-language-server-latest.tar.gz \
      | tar xz -C /opt/jdtls \
 && ln -s /opt/jdtls/bin/jdtls /usr/local/bin/jdtls

# Aider, in its own tool environment: it pins litellm, scipy and a tree-sitter
# grammar pack, none of which belong in the server's dependency set. Pinned to
# the version its adapter was written against. Installed under /opt with the
# shim in /usr/local/bin, because agents run as an unprivileged user that cannot
# traverse root's home directory.
RUN UV_TOOL_DIR=/opt/uv-tools UV_TOOL_BIN_DIR=/usr/local/bin \
    uv tool install --python python3.12 aider-chat==0.86.2 \
 && chmod -R a+rX /opt/uv-tools \
 && rm -rf /root/.cache/uv

# ── App code + plugins ──────────────────────────────────────────────────────
COPY server /app/server
COPY plugins /app/plugins
COPY config.yaml /app/server/config.yaml

# Java test-suites assert on permission denial; root bypasses chmod and would
# fail them on an unmodified checkout. Builds are demoted to this user.
RUN useradd -m -u 1001 runner

# Agent sessions run as that user too, so every shipped adapter's CLI has to be
# usable by it and not only by root. The list comes from the manifests, so an
# adapter added later is gated without touching this step. The probe leaves
# 194 MB of first-run caches in that home; a session gets its own HOME, so
# nothing reads them and they are removed instead of shipped.
RUN set -eu; \
    for cli in $(sed -n 's/^binary:[[:space:]]*//p' /app/plugins/agents/*/plugin.yaml); do \
      printf '%s: ' "$cli"; \
      su runner -s /bin/sh -c "$cli --version" \
        || { echo "shipped agent CLI '$cli' is not usable by user runner"; exit 1; }; \
    done; \
    rm -rf /home/runner/.cache /root/.cache /root/.npm

# ── Build identity ──────────────────────────────────────────────────────────
# A rebuilt image is otherwise indistinguishable from the one it replaced, so it
# records what it was built from and /api/health reports it. Compose passes
# RP_BUILD_REV when the operator exports one; the fingerprint of the copied
# source is computed at runtime, so an unstamped build is still identifiable.
ARG RP_BUILD_REV=""
RUN printf 'revision=%s\nbuiltAt=%s\n' \
      "${RP_BUILD_REV}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /app/build-stamp

ENV RP_DATA_DIR=/data \
    RP_PLUGINS_DIR=/app/plugins \
    RP_BUILD_STAMP=/app/build-stamp \
    RP_BUILD_USER=runner \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONPATH=/app/server \
    PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
  CMD curl -fsS http://localhost:8000/api/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
