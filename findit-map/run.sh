#!/usr/bin/env bash
# One-command run for Find It. Creates a virtualenv, installs pinned dependencies, downloads the
# public data for the cities you name (or the four demo cities), scores the sites and opens the map.
#
#   ./run.sh                          # Irvine, Santa Ana, Costa Mesa, Anaheim (about 10 minutes)
#   ./run.sh --city brea              # one city (a minute or two)
#   ./run.sh --all                    # every Orange County jurisdiction (30 to 60 minutes)
#   ./run.sh --build-only             # re-score cached data without downloading
#
# Needs Python 3.10+ and internet access for the first run. No accounts or API keys.
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
if [ ! -x .venv/bin/python ]; then
  echo "Creating virtualenv..."
  "$PY" -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt

CITIES=(--city irvine --city santa-ana --city costa-mesa --city anaheim)
PICKED=0
BUILD_ONLY=0
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --all) CITIES=(); PICKED=1; shift ;;
    --city) if [ "$PICKED" = 0 ]; then CITIES=(); PICKED=1; fi; CITIES+=(--city "$2"); shift 2 ;;
    --build-only) BUILD_ONLY=1; shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

if [ "$BUILD_ONLY" = 0 ]; then
  # The OC building-footprint server has been unreliable; skip it so a run always completes.
  # Drop "--skip footprints" to try it (coverage is then measured instead of taken from reported use).
  .venv/bin/python -u fetch.py ${CITIES[@]+"${CITIES[@]}"} --skip footprints ${ARGS[@]+"${ARGS[@]}"}
fi
.venv/bin/python build.py

case "$(uname -s)" in
  Darwin) open site/index.html ;;
  Linux) xdg-open site/index.html >/dev/null 2>&1 || echo "Open site/index.html in a browser." ;;
  *) echo "Open site/index.html in a browser." ;;
esac
