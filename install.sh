#!/usr/bin/env bash
# Dewaguard Titan — no docker, no database server, no Python packages.
# Creates the state directory, links the CLI into ~/.local/bin and verifies the install.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${TITAN_BIN_DIR:-$HOME/.local/bin}"

say() { printf '  %s\n' "$*"; }

echo "Dewaguard Titan installer"
echo "repo: $HERE"

# 1. python
PY="$(command -v python3 || true)"
[[ -n "$PY" ]] || { echo "python3 not found" >&2; exit 1; }
"$PY" - <<'EOF' || { echo "python >= 3.10 required" >&2; exit 1; }
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
EOF
say "python: $($PY -V)"

# 2. launcher
chmod +x "$HERE/bin/titan"
say "launcher: $HERE/bin/titan"

# 3. link
mkdir -p "$BIN_DIR"
ln -sf "$HERE/bin/titan" "$BIN_DIR/titan"
say "linked: $BIN_DIR/titan"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo
     echo "  note: $BIN_DIR is not on your PATH. Add this to ~/.zshrc or ~/.bashrc:"
     echo "        export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

# 4. initialise state (db + dirs + skill index)
"$HERE/bin/titan" init

# 5. verify
echo
if "$HERE/bin/titan" doctor; then
  cat <<'EOF'

  Ready. Next:
    1. configure the model (interactive; stores the key in ~/.titan/secrets.json 0600):
         titan setup
    2. create an engagement:
         titan new "Find and prove the highest-impact entry point on app.example.com" \
           --scope domain=example.com
    3. run it:
         titan run 1
    4. watch it:
         titan serve        # http://127.0.0.1:9911  (read-only)
         titan status 1
EOF
else
  echo "  Installed, but 'doctor' reported problems (see above)." >&2
fi
