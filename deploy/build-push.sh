#!/usr/bin/env bash
# Build and push all service images to GitHub Container Registry.
#
# One-time setup (for the developer pushing images):
#   1. Create a GitHub PAT with "write:packages" scope
#   2. echo $GITHUB_PAT | docker login ghcr.io -u micahchoo --password-stdin
#   3. Install as post-commit hook:  ./deploy/build-push.sh --install-hook
#
# Pulling does NOT require credentials — all packages are public.
#
# Usage:
#   ./deploy/build-push.sh              # uses git short SHA as tag
#   ./deploy/build-push.sh v1.2.3       # uses explicit tag
#   ./deploy/build-push.sh latest       # tags as latest
#   ./deploy/build-push.sh --install-hook  # install git post-commit hook

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REGISTRY="ghcr.io/micahchoo/papadam"

# ── Install hook command ─────────────────────────────────────────────────
if [[ "${1:-}" == "--install-hook" ]]; then
  HOOK="${ROOT}/.git/hooks/post-commit"
  cat > "${HOOK}" <<'HOOKEOF'
#!/usr/bin/env bash
# Auto-build and push images to ghcr.io after every commit.
# Runs in the background so your terminal isn't blocked.
echo "[post-commit] Building and pushing images in background..."
nohup "$(git rev-parse --show-toplevel)/deploy/build-push.sh" > /tmp/papadam-build-push.log 2>&1 &
echo "[post-commit] Build log: /tmp/papadam-build-push.log"
HOOKEOF
  chmod +x "${HOOK}"
  echo "Installed post-commit hook at ${HOOK}"
  exit 0
fi

# ── Build and push ───────────────────────────────────────────────────────
TAG="${1:-$(git -C "${ROOT}" rev-parse --short HEAD)}"

# Format: "name:context[:target]"
images=(
  "api:${ROOT}/api:api"
  "ui:${ROOT}/ui"
  "crdt:${ROOT}/crdt"
  "docs:${ROOT}/docs"
  # "transcribe:${ROOT}/transcribe"  # dormant — openai-whisper build is broken
)

echo "==> Building and pushing with tag: ${TAG}"

pids=()
logs=()

for entry in "${images[@]}"; do
  IFS=: read -r name context target <<< "${entry}"
  image="${REGISTRY}/${name}:${TAG}"
  logfile="/tmp/papadam-build-${name}.log"

  (
    echo "--- ${name} ---"
    if [[ -n "${target}" ]]; then
      docker build --target "${target}" -t "${image}" "${context}"
    else
      docker build -t "${image}" "${context}"
    fi
    docker push "${image}"

    if [[ "${TAG}" != "latest" ]]; then
      docker tag "${image}" "${REGISTRY}/${name}:latest"
      docker push "${REGISTRY}/${name}:latest"
    fi
    echo "--- ${name} done ---"
  ) > "${logfile}" 2>&1 &

  pids+=($!)
  logs+=("${name}:${logfile}")
done

# Wait for all builds and report results
failed=0
for i in "${!pids[@]}"; do
  IFS=: read -r name logfile <<< "${logs[$i]}"
  if wait "${pids[$i]}"; then
    echo "  ✓ ${name}"
  else
    echo "  ✗ ${name} — see ${logfile}"
    failed=1
  fi
done

if [[ "${failed}" -eq 1 ]]; then
  echo ""
  echo "==> Some builds failed. Check logs above."
  exit 1
fi

echo ""
echo "==> Done. All images pushed to ${REGISTRY} with tag ${TAG}"
