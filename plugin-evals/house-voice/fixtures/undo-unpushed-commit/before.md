Great question! Undoing a commit is something a lot of people run into, so
let me walk you through it.

So, you're asking how to undo your last commit when you have not pushed it
yet. The good news is that, since the commit only exists on your machine,
you have a few options here, and it's worth noting that they behave quite
differently.

If you want to keep your work, run `git reset --soft HEAD~1`. This moves the
branch back one commit and keeps the changes staged, so you can edit them
and commit again. Honestly, this is the one most people want.

If you want to throw the work away entirely, run `git reset --hard HEAD~1`.
This moves the branch back one commit and deletes the changes from your
working tree. Make no mistake, there is no easy way to get them back
afterwards, so be careful with it.

In summary, use the soft reset to keep your changes and the hard reset to
discard them. Hope this helps, and let me know if you run into anything
else!
