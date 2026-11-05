Output "/private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-9mnrdsha/raw.mp4"
Set Shell bash
Set Width 1280
Set Height 720
Set FontSize 18
Set TypingSpeed 50ms
Hide
Type `clear; printf '\033[1m%b\033[0m\n\n%b\n' 'Interface review' 'Catch what a change quietly took away'`
Enter
Show
Sleep 4.9s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'When a change removes a spoken label, a focus outline or a motion preference, the review reports it.'`
Enter
Show
Type `grep -c Interface skills/review/references/domain-reviewers.md`
Enter
Sleep 6.5s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'When the same change puts an equivalent back in the same place, the review stays quiet.'`
Enter
Show
Type `python3 -m unittest tests.test_review_domain_table 2>&1 | tail -3`
Enter
Sleep 5.4s
Hide
Type `clear; printf '\033[1m%b\033[0m\n' 'Now it is caught while the change is still a draft.'`
Enter
Show
Sleep 3.2s
