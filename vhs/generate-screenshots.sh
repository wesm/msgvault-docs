#!/usr/bin/env bash
# Runs inside the Docker container. Drives tmux + freeze to produce SVG screenshots.
set -euo pipefail

OUTPUT_DIR="${1:-/output}"
FREEZE_CFG="/tapes/freeze.json"
SESSION="mv"

mkdir -p "$OUTPUT_DIR"

# Helper: capture current tmux pane to SVG via freeze
capture() {
    local name="$1"
    tmux capture-pane -pet "$SESSION" | freeze -o "$OUTPUT_DIR/${name}.svg" --language ansi -c "$FREEZE_CFG"
    echo "  captured $name.svg"
}

# Helper: send keys and wait
send() {
    tmux send-keys -t "$SESSION" "$@"
}

wait_for() {
    sleep "${1:-1}"
}

# --- Start tmux session ---
tmux new-session -d -s "$SESSION" -x 120 -y 40

# =====================
# TUI Screenshots
# =====================
echo "==> TUI screenshots"

send "MSGVAULT_HOME=/data msgvault tui" Enter
wait_for 5

# 1. Senders view (default)
capture "tui-senders"

# 2. Drill into a sender
send Down
wait_for 0.2
send Down
wait_for 0.2
send Down
wait_for 0.2
send Enter
wait_for 2
capture "tui-drilldown"

# Navigate back
send Escape
wait_for 1

# 3. Domains view (cycle: Senders -> Recipients -> Domains)
send "g"
wait_for 0.5
send "g"
wait_for 1.5
capture "tui-domains"

# 4. Labels view
send "g"
wait_for 1.5
capture "tui-labels"

# 5. Time view
send "g"
wait_for 1.5
capture "tui-time"

# 6. Multi-row selection (back to Senders first)
send "g"
wait_for 1
send Down
wait_for 0.2
send Space
wait_for 0.2
send Down
wait_for 0.2
send Space
wait_for 0.2
send Down
wait_for 0.2
send Space
wait_for 0.5
capture "tui-selection"

# Quit TUI
send "q"
wait_for 1

# =====================
# CLI Screenshots
# =====================
echo "==> CLI screenshots"

# 7. stats
send "MSGVAULT_HOME=/data msgvault stats" Enter
wait_for 2
capture "stats"

# 8. list-senders
send "MSGVAULT_HOME=/data msgvault list-senders --limit 15" Enter
wait_for 2
capture "list-senders"

# Cleanup
tmux kill-session -t "$SESSION" 2>/dev/null || true

echo ""
echo "Done! Generated $(ls "$OUTPUT_DIR"/*.svg 2>/dev/null | wc -l) SVG files in $OUTPUT_DIR"
