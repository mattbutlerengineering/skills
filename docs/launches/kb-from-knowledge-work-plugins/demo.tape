Output "/private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-15bjffon/raw.mp4"
Set Shell bash
Set Width 1280
Set Height 720
Set FontSize 18
Set TypingSpeed 50ms
Hide
Type `clear; printf '\033[1m%b\033[0m\n\n%b\n' 'Outside facts that age' 'The knowledge base learns what it cannot see'`
Enter
Show
Sleep 5.2s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'A note about an outside system now carries the date it was last checked and how long that check stays good.'`
Enter
Show
Type `sed -n 6,8p docs/kb/main-unprotected.md`
Enter
Sleep 6.7s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'Once that time runs out, the routine check names the note and asks for a re-check, without going online.'`
Enter
Show
Type `python3 -m unittest -v tests.test_kb.TestAge.test_on_the_due_date_it_is_still_fresh tests.test_kb.TestAge.test_one_day_past_due_is_one_problem`
Enter
Sleep 6.4s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'The gathering step lists the moments a person corrected the agent or answered its question, and it pairs saved memories with the notes that already cover them.'`
Enter
Show
Type `python3 -m unittest tests.test_kb_harvest.TestHumanTurns tests.test_kb_harvest.TestMemory`
Enter
Sleep 9.2s
Hide
Type `clear; printf '\033[1m%b\033[0m\n' 'Facts about the world outside the code stop being trusted forever just because nobody looked again.'`
Enter
Show
Sleep 5.9s
