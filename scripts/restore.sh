#!/usr/bin/env bash
set -euo pipefail
# Target must be an explicitly provided EMPTY database, never the running service DB.
: "${RESTORE_DATABASE_URL:?Set an empty PostgreSQL target database URL}"
: "${AGE_IDENTITY:?Set path to age private key}"
test "$#" -eq 1
age -d -i "$AGE_IDENTITY" "$1" |
  pg_restore --exit-on-error --no-owner --no-acl -d "$RESTORE_DATABASE_URL"
