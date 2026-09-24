# flashLedger Showcase Tape
# Run from repo root: vhs assets/vhs/demo.tape

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 840
Set Padding 18
Set WindowBar Colorful
Set Theme "Catppuccin Macchiato"
Set TypingSpeed 50ms

Output "assets/showcase/demo.gif"

# Setup clean shell environment
Hide
Type "source .venv/bin/activate && clear"
Enter
Sleep 600ms
Show

# 1. Launch the Enterprise Batch Cluster Demo (100,000 transactions)
Type "flash-ledger demo"
Sleep 500ms
Enter

# Watch the 100-batch cluster matrix cascade and audit 100,000 transactions
Sleep 7.5s

# Pause to let viewers read the executive scorecard & telemetry
Sleep 4s
