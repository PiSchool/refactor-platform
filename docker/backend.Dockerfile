# Refactor Platform — backend runtime.
# Heavy by design: it hosts the agent CLI, LSP servers, and the full Java
# build toolchain (4 JDKs + Maven + Gradle) that benchmark evaluation needs.
FROM ubuntu:22.04
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

# ── Python 3.12 + Node 20 + Copilot CLI ─────────────────────────────────────
RUN add-apt-repository -y ppa:deadsnakes/ppa \
 && apt-get update && apt-get install -y --no-install-recommends \
      python3.12 python3.12-venv python3.12-dev \
 && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @github/copilot \
 && rm -rf /var/lib/apt/lists/*

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

# ── App code + plugins ──────────────────────────────────────────────────────
COPY server /app/server
COPY plugins /app/plugins
COPY config.yaml /app/server/config.yaml

# Java test-suites assert on permission denial; root bypasses chmod and would
# fail them on an unmodified checkout. Builds are demoted to this user.
RUN useradd -m -u 1001 runner

ENV RP_DATA_DIR=/data \
    RP_PLUGINS_DIR=/app/plugins \
    RP_BUILD_USER=runner \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONPATH=/app/server \
    PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
  CMD curl -fsS http://localhost:8000/api/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
