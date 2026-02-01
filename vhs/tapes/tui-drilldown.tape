# Drill-down navigation: select sender, drill down, sort, navigate back
Output ./output/tui-drilldown.webm

Set Theme "dark"
Set FontFamily "MesloLGS NF"
Set FontSize 14
Set Width 1200
Set Height 600
Set Framerate 25

Type "msgvault tui"
Enter
Sleep 2s

# Navigate to a sender
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 500ms

# Drill down
Enter
Sleep 1.5s

# Sort by size
Type "s"
Sleep 1s
Type "s"
Sleep 1s

# Reverse sort
Type "r"
Sleep 1s

# Scroll through results
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 300ms
Down
Sleep 500ms

# Navigate back
Escape
Sleep 1s

# Try another sender
Down
Sleep 300ms
Down
Sleep 300ms
Enter
Sleep 1.5s

# Back again
Escape
Sleep 1s

Type "q"
Sleep 500ms
