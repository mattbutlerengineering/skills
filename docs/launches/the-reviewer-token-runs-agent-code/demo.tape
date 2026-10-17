Output "/private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-359cf2r3/raw.mp4"
Set Shell bash
Set Width 1280
Set Height 720
Set FontSize 18
Set TypingSpeed 50ms
Hide
Type `clear; printf '\033[1m%b\033[0m\n\n%b\n' 'The reviewer\0047s key stays out of reach' 'Untrusted code runs without it; the reviewer starts from main'`
Enter
Show
Sleep 6.3s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'The pull request\0047s code now runs in a job that holds no secret, and it hands over only its findings, as plain text with a size limit.'`
Enter
Show
Type `grep -n -E '^  (check|review|needs-review-label):$|secrets.FACTORY_REVIEW_TOKEN|ref: ' .github/workflows/validator.yml`
Enter
Sleep 9.5s
Hide
Type `clear; printf '\033[2m%b\033[0m\n\n' 'The reviewer then starts from the trusted main branch, reads those findings as data, and takes its pass or fail verdict from the check\0047s result, never from the text.'`
Enter
Show
Type `python3 -m unittest tests.test_validator_workflow 2>&1 | tail -3`
Enter
Sleep 10.3s
Hide
Type `clear; printf '\033[1m%b\033[0m\n' 'A pull request written by an agent can no longer borrow the reviewer\0047s identity to approve itself or act on the repository.'`
Enter
Show
Sleep 7.9s
