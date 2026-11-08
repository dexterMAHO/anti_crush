#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${BACKUP_RECIPIENT:?Set age public recipient key}"
mkdir -p backups
output="backups/confession-$(date -u +%Y%m%dT%H%M%S).dump.age"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' |
  age -r "$BACKUP_RECIPIENT" -o "$output"
echo "$output"
