Run `git reset --soft HEAD~1`. It moves the branch back one commit and keeps
the changes staged, so you can fix them and commit again.

To drop the work instead, run `git reset --hard HEAD~1`. It deletes the
changes from your working tree, and you cannot easily get them back.
