# View modes demo: cycle through all 5 view modes
Output ./output/tui-views.webm

Set Theme "UltraDark"
Set FontFamily "MesloLGS NF"
Set FontSize 14
Set Width 1000
Set Height 800
Set Framerate 25

Type "msgvault tui"
Enter
Sleep 2s

# Senders view (default)
Sleep 1.5s

# Cycle to Recipients
Type "g"
Sleep 1.5s

# Cycle to Domains
Type "g"
Sleep 1.5s

# Cycle to Labels
Type "g"
Sleep 1.5s

# Cycle to Time
Type "g"
Sleep 1.5s

# Back to Senders
Type "g"
Sleep 1s

Type "q"
Sleep 500ms
