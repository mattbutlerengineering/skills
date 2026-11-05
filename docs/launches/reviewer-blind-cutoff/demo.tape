Output "/private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-xu00ty6h/raw.mp4"
Set Shell bash
Set Width 1280
Set Height 720
Set FontSize 18
Set TypingSpeed 50ms
Hide
Type `clear; printf '\033[1m%b\033[0m\n\n%b\n' 'The reviewer scores blind' 'The line is set by the queue, and every score is shown'`
Enter
Show
Sleep 6.7s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'A score at or above the line passes, a lower one flags, and a score that is missing or makes no sense is treated as an error that never merges.'`
Enter
Show
Type `python3 reviewer_verdict.py 7; python3 reviewer_verdict.py 6; python3 reviewer_verdict.py abc`
Enter
Sleep 9.0s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'Every verdict comment now opens with the score and the result, so anyone can read how each pull request was judged.'`
Enter
Show
Type `python3 -m unittest tests.test_reviewer_verdict 2>&1 | tail -3`
Enter
Sleep 8.2s
Hide
Type `clear; printf '\033[1m%b\033[0m\n' 'Because every score is now posted, the Owner can later check whether scores bunch up at the line, which was impossible before.'`
Enter
Show
Sleep 7.4s
