Output "/private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-cgww8zbp/raw.mp4"
Set Shell bash
Set Width 1280
Set Height 720
Set FontSize 18
Set TypingSpeed 50ms
Hide
Type `clear; printf '\033[1m%b\033[0m\n\n%b\n' 'The pipeline board' 'Every run, on its step, at a glance'`
Enter
Show
Sleep 6.3s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'You ask for the board and a small tool reads every run\0047s notes to state which step each one is on.'`
Enter
Show
Type `python3 board.py . | jq '{generated, repo, runs: (.runs | length)}'`
Enter
Sleep 5.8s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'It lists every active run once, tells feature work from maintenance work, and shows how far along the building step has come.'`
Enter
Show
Type `python3 board.py . | jq -c '.runs[] | select(.slug=="launch-demo") | .ladder[] | [.stage, .state]'`
Enter
Sleep 8.0s
Hide
Type `clear; printf '\033[1m%b\033[0m\n' 'Instead of walking folders and running commands, you find where every run stands in one glance.'`
Enter
Show
Sleep 6.0s
