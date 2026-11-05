Output "/private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-2tyai3a_/raw.mp4"
Set Shell bash
Set Width 1280
Set Height 720
Set FontSize 18
Set TypingSpeed 50ms
Hide
Type `clear; printf '\033[1m%b\033[0m\n\n%b\n' 'A mechanical check for diagrams' 'Broken pictures named in a second'`
Enter
Show
Sleep 5.0s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'It names every broken link, repeated name and missing size it finds in the picture.'`
Enter
Show
Type `python3 -I svg_check.py tests/fixtures/svg-check/all-four.svg`
Enter
Sleep 5.5s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'When the picture is clean, it says so and reports the smallest text size at the width the picture will have on a page.'`
Enter
Show
Type `python3 -I svg_check.py tests/fixtures/svg-check/clean.svg`
Enter
Sleep 7.3s
Hide
Type `clear; printf '\033[1m%b\033[0m\n' 'Mistakes that used to be found later by someone squinting at a rendered page are now caught in a second, before the diagram is handed over.'`
Enter
Show
Sleep 8.1s
