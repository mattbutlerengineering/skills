Output "/private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-w9fpr8kz/raw.mp4"
Set Shell bash
Set Width 1280
Set Height 720
Set FontSize 18
Set TypingSpeed 50ms
Hide
Type `clear; printf '\033[1m%b\033[0m\n\n%b\n' 'Earlier pull-request checks' 'Catch a bad description before the pull request exists'`
Enter
Show
Sleep 5.9s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'When the description is missing its work-order line or its closing line, the command is stopped before the pull request exists.'`
Enter
Show
Type `try(){ python3 -c 'import json,sys;print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.argv[1]}}))' "$1" | python3 pr_body_preflight.py 2>&1; echo "exit $?"; }`
Enter
Type `clear`
Enter
Type `try $'cat > b.md <<EOF\nJust a summary.\nEOF\ngh pr create --title t --body-file b.md'`
Enter
Sleep 7.4s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'When the description has both lines, the command goes through untouched.'`
Enter
Show
Type `try $'cat > b.md <<EOF\nNo work order: a demo.\nCloses #1\nEOF\ngh pr create --title t --body-file b.md'`
Enter
Sleep 4.4s
Hide
Type `clear; printf '\033[1m%b\033[0m\n' 'Now it fails in seconds, with the same two reasons the build would give.'`
Enter
Show
Sleep 4.4s
