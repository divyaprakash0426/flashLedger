# flashLedger Enterprise 100,000 Transaction Batch Cluster Tape
# Run from repo root: vhs assets/vhs/enterprise_100k.tape

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 860
Set Padding 18
Set WindowBar Colorful
Set Theme "Catppuccin Macchiato"
Set TypingSpeed 45ms

Output "assets/showcase/enterprise_100k.gif"

# Setup clean shell environment
Hide
Type "source .venv/bin/activate && clear"
Enter
Sleep 600ms
Show

# Launch the Enterprise Batch Cluster Demo (100,000 transactions)
Type "flash-ledger demo"
Sleep 500ms
Enter

# Watch the 100-batch cluster matrix cascade and audit 100,000 transactions
Sleep 8.5s

# Pause on the final executive scorecard and economic telemetry
Sleep 5s
