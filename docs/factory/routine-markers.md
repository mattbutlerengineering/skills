# Routine markers on GitHub

The shared reference every routine protocol under `docs/factory/`
(`*-routine.md`) cites from its own §Markers on GitHub: one place for
the rules that find, write and create the HTML-comment markers a
routine's journal, state lines and PR bodies carry. Each protocol names
its own markers; this file holds the rules they all obey. Like the
protocols, it is tuned by PR and never edited by a routine (ADR-0044).

The cloud environment may reach GitHub only through the GitHub MCP
tools, with no `gh` CLI (#844). Each `gh` command a routine protocol
names states the intent; carry it out with whichever is present.
Over MCP, a written `<!--` and `-->` have been stored HTML-escaped
as `&lt;!--` and `--&gt;`, which hides the marker from every later lookup: the queue
groomer missed its journal and opened a duplicate, and most of the
improvement journal's state markers went unread. Every marker a routine
protocol names obeys three rules:

1. **Find by both forms.** A marker is matched in its raw form
   (`<!-- … -->`) and in its HTML-escaped form (`&lt;!-- … --&gt;`).
   Search by the marker's name, which both forms contain, then check
   the start of the body or comment against both. An escaped match
   counts as found, and is repaired by rule 2.
2. **Write raw, then verify.** Write the marker as literal `<!--` and
   `-->`, never pre-escaped. After every write that carries one (issue
   body, journal comment, PR body), re-read what GitHub stored; if it
   holds the escaped form, update that body or comment to the raw form
   and re-read again. Still escaped after the update → say so in the
   run's report and carry on.
3. **Never create on doubt.** Create a journal only when the marker
   search succeeded and matched no open issue in either form. If the
   search errored, or matched more than one open issue, create nothing:
   report it under Health in the session log and stop.
