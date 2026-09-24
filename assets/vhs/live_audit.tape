# flashLedger Live Compliance Audit with TypeSafe Jev (Vercel AI Gateway)
# Run from repo root: vhs assets/vhs/live_audit.tape

Set Shell "bash"
Set FontSize 13
Set Width 1200
Set Height 880
Set Padding 18
Set WindowBar Colorful
Set Theme "Catppuccin Macchiato"
Set TypingSpeed 40ms

Output "assets/showcase/live_audit.gif"

# Setup clean shell environment
Hide
Type "source .venv/bin/activate && clear"
Enter
Sleep 600ms
Show

# Run live compliance audit on the real transaction dataset with Vercel Jev
Type "flash-ledger audit data/mitulshah_sample.csv -n 15 -p vercel"
Sleep 500ms
Enter

# Wait for live API audit and formatted compliance table to render
Sleep 6s

# Pause to inspect the IRS audit risk scores, OpEx/CapEx classifications, and flags
Sleep 5s
