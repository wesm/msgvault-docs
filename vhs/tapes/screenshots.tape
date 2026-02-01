# Generate static SVG screenshots for documentation

Set Theme "UltraDark"
Set FontFamily "MesloLGS NF"
Set FontSize 14
Set Width 1000
Set Height 800
Set Framerate 25

# --- TUI Screenshots ---

Type "msgvault tui"
Enter
Sleep 5s

# Senders view (default landing / hero)
Screenshot ./output/tui-senders.svg
Sleep 500ms

# Drill down into a sender
Down
Sleep 200ms
Down
Sleep 200ms
Down
Sleep 200ms
Enter
Sleep 2s
Screenshot ./output/tui-drilldown.svg
Sleep 500ms

# Navigate back
Escape
Sleep 1s

# Domains view (Senders -> Recipients -> Domains)
Type "g"
Sleep 500ms
Type "g"
Sleep 1.5s
Screenshot ./output/tui-domains.svg
Sleep 500ms

# Labels view
Type "g"
Sleep 1.5s
Screenshot ./output/tui-labels.svg
Sleep 500ms

# Time view
Type "g"
Sleep 1.5s
Screenshot ./output/tui-time.svg
Sleep 500ms

# Back to Senders for selection demo
Type "g"
Sleep 1s
Down
Sleep 200ms
Space
Sleep 200ms
Down
Sleep 200ms
Space
Sleep 200ms
Down
Sleep 200ms
Space
Sleep 500ms
Screenshot ./output/tui-selection.svg
Sleep 500ms

# Quit TUI
Type "q"
Sleep 1s

# --- CLI Screenshots ---

Type "msgvault stats"
Enter
Sleep 2s
Screenshot ./output/stats.svg
Sleep 500ms

Type "msgvault list-senders --limit 15"
Enter
Sleep 2s
Screenshot ./output/list-senders.svg
Sleep 500ms
