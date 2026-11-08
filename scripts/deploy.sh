#!/usr/bin/env bash
# Deploy a git ref with Docker Compose and roll back if the bot stays unhealthy.
# Usage: ./scripts/deploy.sh [git-ref]        default ref: feat/button-ui
set -euo pipefail

ref="${1:-feat/button-ui}"
remote="${REMOTE:-origin}"
timeout="${HEALTH_TIMEOUT:-240}"

# Resolve the repository from the current directory, so the script may live
# outside the tree it deploys and survive the checkout it performs.
cd "$(git rev-parse --show-toplevel)"
[ -f .env ] || { echo "Missing .env; copy .env.example and set the real values." >&2; exit 1; }
docker compose version >/dev/null

# Untracked files are left alone; only tracked edits can be lost by a checkout.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "Tracked changes present; commit or stash them before deploying:" >&2
  git status --short --untracked-files=no >&2
  exit 1
fi

previous="$(git rev-parse HEAD)"
echo "Current revision: $previous"

git fetch --prune "$remote"
git checkout --detach "$(git rev-parse --verify "${remote}/${ref}" 2>/dev/null || echo "$ref")"
target="$(git rev-parse HEAD)"
echo "Deploying revision: $target ($ref)"

health() {
  docker compose ps --format '{{.Service}} {{.Health}} {{.State}}' bot 2>/dev/null || true
}

wait_for_health() {
  local waited=0
  while [ "$waited" -lt "$timeout" ]; do
    case "$(health)" in
      *healthy*) return 0 ;;
      *unhealthy*|*exited*|*restarting*) sleep 5 ;;
      *) sleep 5 ;;
    esac
    waited=$((waited + 5))
    printf '.'
  done
  printf '\n'
  return 1
}

# Migrations run inside the bot container entrypoint before the bot starts.
docker compose up -d --build

if wait_for_health; then
  printf '\n'
  docker compose ps
  echo "Deployed $target successfully."
  echo "Logs: docker compose logs --tail=100 -f bot"
  exit 0
fi

echo "Bot did not become healthy within ${timeout}s. Last logs:" >&2
docker compose logs --tail=50 bot >&2
# Code rolls back; applied Alembic migrations do not. Check the data first.
echo "Rolling back code to $previous" >&2
git checkout --detach "$previous"
docker compose up -d --build
docker compose ps >&2
echo "Rolled back. Nothing from $ref is running." >&2
exit 1
