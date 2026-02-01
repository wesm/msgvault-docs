# Hero banner recording: launch TUI, browse senders, drill down, navigate back
Output ./output/tui-hero.webm

Set Theme "dark"
Set FontFamily "MesloLGS NF"
Set FontSize 14
Set Width 1200
Set Height 600
Set Framerate 25

Type "msgvault tui"
Enter
Sleep 2s

# Browse the Senders view
Sleep 1s
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 500ms

# Drill down into a sender
Enter
Sleep 1.5s

# Scroll through messages
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 500ms

# Navigate back
Escape
Sleep 1s

# Cycle to Domains view
Type "g"
Sleep 1s

# Scroll domains
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 500ms

# Cycle to Labels view
Type "g"
Sleep 1s

Down
Sleep 300ms
Down
Sleep 500ms

Sleep 1.5s

# Quit
Type "q"
Sleep 500ms
