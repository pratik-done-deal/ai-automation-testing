#!/usr/bin/env bash
# Run every automated test of star-seller-fundraising (SSF) in a visible Chromium window.
#
# Usage (from the suite folder: this repo, or donedeal-web/automation):
#   scripts/run_star_seller_tests.sh               # against QA (DD_APP_URL from .env), the default
#   scripts/run_star_seller_tests.sh local         # against your local app, http://localhost:3000
#   scripts/run_star_seller_tests.sh qa -m smoke              # extra args go to pytest (name the target first)
#   scripts/run_star_seller_tests.sh qa -k s12_01             # one case
#   SLOWMO=800 scripts/run_star_seller_tests.sh               # slower, easier to follow
#   scripts/run_star_seller_tests.sh local --pause-on-failure # keep the window open on a failure
#
# local: the feature is on your branch, so its pending_feature tests run as normal tests (DD_SHIPPED).
#        Logins are kept apart from the QA ones, in auth/local/ (saved against localhost on first run).
# qa:    the feature is not on QA yet, so pending_feature tests run as strict xfail, as the suite expects.
#
# Each case browses Sellers > "Star Sellers" / "Non Star Sellers" for a seller in the state it needs and
# opens it with the row's Actions "View" (utils/ssf_browse.py); no uids. Many cases are destructive: they
# star sellers, change objectives and upload or delete documents on the backend your app talks to.
set -euo pipefail

cd "$(dirname "$0")/.."   # automation/

TARGET="${1:-qa}"
if [[ "$TARGET" == "local" || "$TARGET" == "qa" ]]; then
  shift || true
else
  TARGET="qa"
fi

# --- Python environment (README "One-time setup") ---
if [[ ! -x .venv/bin/python ]]; then
  echo "Creating automation/.venv and installing requirements..."
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
  .venv/bin/python -m playwright install chromium
fi
PY=.venv/bin/python

# --- Target app and sessions ---
if [[ "$TARGET" == "local" ]]; then
  export DD_APP_URL="${DD_APP_URL_LOCAL:-http://localhost:3000/}"
  export DD_SHIPPED="star-seller-fundraising${DD_SHIPPED:+,$DD_SHIPPED}"
  export DD_ADMIN_STATE="auth/local/admin.json"
  export DD_BIZ_USER_STATE="auth/local/biz_user.json"
  if ! curl -s -o /dev/null --max-time 5 "$DD_APP_URL"; then
    echo "Your app isn't answering at $DD_APP_URL. Start it first (npm start in donedeal-web)." >&2
    exit 1
  fi
fi
ADMIN_STATE="${DD_ADMIN_STATE:-auth/admin.json}"
BIZ_STATE="${DD_BIZ_USER_STATE:-auth/biz_user.json}"

if [[ ! -f "$ADMIN_STATE" ]]; then
  echo "No admin session at $ADMIN_STATE. A browser opens: log in as an admin (userType 2), then press Enter."
  "$PY" scripts/save_auth_state.py admin
fi
if [[ ! -f "$BIZ_STATE" ]]; then
  read -r -p "No biz user session at $BIZ_STATE (biz-user tests will skip). Save one now? [y/N] " answer
  if [[ "$answer" =~ ^[Yy]$ ]]; then
    "$PY" scripts/save_auth_state.py biz_user
  fi
fi

# --- Run, in the order of test-cases.md section 6 (later files use sellers earlier ones produce) ---
echo "Running star-seller-fundraising tests against ${DD_APP_URL:-DD_APP_URL from .env} in Chromium (headed)..."
exec "$PY" -m pytest \
  test_cases/admin_test_cases/test_admin_star_seller_marking.py \
  test_cases/admin_test_cases/test_admin_star_seller_objective.py \
  test_cases/biz_user_test_cases/test_biz_user_star_seller.py \
  test_cases/e2e/test_star_seller_legacy.py \
  --headed --slowmo "${SLOWMO:-400}" \
  "$@"
