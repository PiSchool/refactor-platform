#!/usr/bin/env bash
# Stands in for an AI CLI: reads the prompt, edits one file, and writes the
# event log the adapter reads back.
set -euo pipefail
prompt="$1"
events="$2"

stamp() { date -u +%Y-%m-%dT%H:%M:%S.000Z; }
emit() { printf '%s\n' "$1" >> "$events"; }

echo "prompt: $prompt"
emit "{\"type\":\"session.start\",\"timestamp\":\"$(stamp)\",\"data\":{\"producer\":\"example-agent\"}}"

if [[ -f greet.py ]]; then
  sed -i 's/return f"hello, {name}"/return f"hello, {name}".upper()/' greet.py
  echo "edited greet.py"
fi

emit "{\"type\":\"assistant.message\",\"timestamp\":\"$(stamp)\",\"data\":{\"content\":\"Uppercased the greeting.\"}}"
emit "{\"type\":\"session.shutdown\",\"timestamp\":\"$(stamp)\",\"data\":{}}"
