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

# Helper: poll tmux pane (plain text, no ANSI) until a pattern appears (or timeout)
wait_until() {
    local pattern="$1"
    local timeout="${2:-30}"
    local elapsed=0
    while ! tmux capture-pane -pt "$SESSION" | grep -q "$pattern"; do
        sleep 0.5
        elapsed=$((elapsed + 1))
        if [[ $elapsed -ge $((timeout * 2)) ]]; then
            echo "  WARNING: timed out waiting for pattern: $pattern"
            return 1
        fi
    done
}

# --- Start tmux session ---
tmux new-session -d -s "$SESSION" -x 120 -y 40

# =====================
# TUI Screenshots
# =====================
echo "==> TUI screenshots"

send "MSGVAULT_HOME=/data msgvault tui" Enter
wait_until "Sender"

# 1. Senders view (default)
sleep 0.5
capture "tui-senders"

# 2. Drill into a sender
send Down
sleep 0.3
send Down
sleep 0.3
send Down
sleep 0.3
send Enter
wait_until "Date"
sleep 0.5
capture "tui-drilldown"

# Navigate back
send Escape
sleep 1

# 3. Domains view (cycle: Sender -> Recipient -> Domain)
send "g"
wait_until "Recipient"
send "g"
wait_until "Domain"
sleep 0.5
capture "tui-domains"

# 4. Labels view
send "g"
wait_until "Label"
sleep 0.5
capture "tui-labels"

# 5. Time view
send "g"
wait_until "Time"
sleep 0.5
capture "tui-time"

# 6. Multi-row selection (back to Sender first)
send "g"
wait_until "Sender"
sleep 0.5
send Down
sleep 0.3
send Space
sleep 0.3
send Down
sleep 0.3
send Space
sleep 0.3
send Down
sleep 0.3
send Space
sleep 0.5
capture "tui-selection"

# 7. Group deletion confirmation dialog
send Down
sleep 0.3
send D
wait_until "Confirm Deletion"
sleep 0.5
capture "tui-deletion"

# Cancel and quit
send "n"
sleep 0.5
send "q"
sleep 1

# =====================
# CLI Screenshots
# =====================
echo "==> CLI screenshots"

# Set up a clean prompt and export MSGVAULT_HOME so it doesn't appear in commands
send "export PS1='$ '" Enter
sleep 0.3
send "export MSGVAULT_HOME=/data" Enter
sleep 0.3
send "clear" Enter
sleep 0.5

# 8. stats
send "msgvault stats" Enter
wait_until "Database:"
sleep 0.5
capture "stats"

# 9. list-senders
send "clear" Enter
sleep 0.5
send "msgvault list-senders --limit 15" Enter
wait_until "SENDER"
sleep 0.5
capture "list-senders"

# Cleanup
tmux kill-session -t "$SESSION" 2>/dev/null || true

echo ""
echo "Done! Generated $(ls "$OUTPUT_DIR"/*.svg 2>/dev/null | wc -l) SVG files in $OUTPUT_DIR"
