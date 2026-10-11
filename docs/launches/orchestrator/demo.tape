Output "/private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-3vabrpz1/raw.mp4"
Set Shell bash
Set Width 1280
Set Height 720
Set FontSize 18
Set TypingSpeed 50ms
Hide
Type `clear; printf '\033[1m%b\033[0m\n\n%b\n' 'The Conductor' 'A batch of issues, one question at a time'`
Enter
Show
Sleep 6.8s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'You hand it a batch of issues, and it asks you each question one at a time, with the option it recommends first.'`
Enter
Show
Type `D=$(mktemp -d) && cp *.py $D && mkdir -p $D/.git $D/docs/factory/batches/demo && touch $D/docs/factory/batches/demo/ledger.jsonl && cd $D`
Enter
Type `python3 conductor.py ask demo --kind spend --question "Spend up to 40 dollars on this batch?" --option approve --option decline --recommended approve --why "four small issues"`
Enter
Sleep 7.6s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'It refuses an answer that is not one of the options, and it refuses any answer written by one of its own workers.'`
Enter
Show
Type `python3 conductor.py answer demo ask-1 maybe`
Enter
Type `CONDUCTOR_WORKER=1 python3 conductor.py answer demo ask-1 approve`
Enter
Sleep 7.0s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'Only your own pick is written down, and only once.'`
Enter
Show
Type `python3 conductor.py answer demo ask-1 approve`
Enter
Type `python3 conductor.py answer demo ask-1 approve`
Enter
Type `cat docs/factory/batches/demo/ledger.jsonl`
Enter
Sleep 3.2s
Hide
Type `clear; printf '\033[1m%b\033[0m\n' 'Nothing spends money or merges until you have said yes.'`
Enter
Show
Sleep 3.9s
