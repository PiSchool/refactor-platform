#!/bin/sh
# Start the model server, then make sure the two configured models are
# present before anything is allowed to depend on them.
#
# Pulling on first boot rather than baking the models into an image keeps the
# image small and lets an operator pin different models without a rebuild. The
# pulls are idempotent: on later boots they are cache hits against the volume.
set -eu

EMBEDDING_MODEL="${RP_EMBEDDING_MODEL:-hf.co/nomic-ai/nomic-embed-code-GGUF:Q4_K_M}"
EXPANSION_MODEL="${RP_EXPANSION_MODEL:-qwen2.5-coder:7b-instruct}"

ollama serve &
server_pid=$!

# The server needs a moment before it will accept a pull.
attempt=0
until ollama list >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -gt 60 ]; then
        echo "ollama did not become responsive" >&2
        kill "$server_pid" 2>/dev/null || true
        exit 1
    fi
    sleep 2
done

for model in "$EMBEDDING_MODEL" "$EXPANSION_MODEL"; do
    echo "ensuring model: $model"
    # A pull can fail on a transient registry error; a missing model would then
    # only be discovered by a failing run, so retry before giving up.
    tries=0
    until ollama pull "$model"; do
        tries=$((tries + 1))
        if [ "$tries" -ge 3 ]; then
            echo "failed to pull $model" >&2
            kill "$server_pid" 2>/dev/null || true
            exit 1
        fi
        sleep 10
    done
done

echo "research retrieval models ready"
wait "$server_pid"
