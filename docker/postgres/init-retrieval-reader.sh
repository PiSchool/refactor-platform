#!/usr/bin/env bash
set -euo pipefail

: "${RETRIEVAL_DB_READER_PASSWORD:?RETRIEVAL_DB_READER_PASSWORD is required}"

psql --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=reader_password="$RETRIEVAL_DB_READER_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE retrieval_reader LOGIN PASSWORD %L', :'reader_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'retrieval_reader') \gexec
ALTER ROLE retrieval_reader PASSWORD :'reader_password';
GRANT CONNECT ON DATABASE refactor_retrieval TO retrieval_reader;
GRANT USAGE ON SCHEMA public TO retrieval_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO retrieval_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO retrieval_reader;
SQL