# Rewrite rules by job

Generic advice ("be clear") cannot be checked. These rules are scoped to
the job a string does. Sources: Nielsen Norman Group's error-message
guidelines and usability heuristics, the Mailchimp Content Style Guide,
Vercel's web-interface-guidelines, and Impeccable's `clarify` command
(restated, not copied). Each section ends with the check.

## Every message about a state

Order the content by what the person needs:

1. **The fact they need now.** What happened, or what this is.
2. **The next action.** What they can do about it.
3. **Context that changes the decision.** Only if it would change what
   they do.

Tone comes last: it shapes the words of all three, it is never a fourth
sentence.

## Actions — buttons, menu items, links that do something

- Verb plus object, naming the outcome: "Save changes", "Send invite",
  "Delete project".
- Not the gesture or the mechanism: no "OK", "Submit", "Yes", "No",
  "Click here".
- The confirm button repeats the verb of the question: "Delete project?"
  is answered by "Delete project", not "OK".
- An ellipsis when more input follows before anything happens:
  "Rename…".
- **Check:** read the label alone. Do you know what will happen?

## Labels and helper text

- A visible label, never a placeholder standing in for one.
- Requirements stated before submit, not discovered through an error.
- Helper text says why or how, not what the label already said.
- **Check:** cover the field. Does the label alone say what goes in it?

## Errors

- **What failed**, in the person's terms. **Why**, if it is known and
  useful. **How to recover**, always.
- Shown next to its cause, and not by colour alone.
- Severity matches the display: a field error inline, a page error in a
  banner, a blocking error in a dialog.
- No blame ("You entered an invalid..."), no humour, no exclamation
  marks.
- The person's input is kept. An error that clears the form is two
  errors.
- No codes as the primary message. A code belongs after the sentence, for
  support.
- Validation does not fire before the person has finished typing.
- **Check:** could someone fix it from the message alone?

## Empty states

Name which empty this is, because each needs different words:

| Empty | Says |
|---|---|
| **First use** | What will live here, and how to add the first one |
| **No results** | Nothing matched, and how to widen the search |
| **Filtered out** | Filters are hiding things, and how to clear them |
| **No permission** | Who can grant access, or how to ask |
| **Failed to load** | It is an error, not an empty list — use the error rules |

- **Check:** does it say why it is empty and what to do?

## Confirmations and destructive actions

- Name the object and the consequence: "Delete 'Q3 plan'? Its 12 tasks
  will be deleted too."
- Say whether it can be undone. If it can, prefer undo to asking first.
- **Check:** does the dialog make sense to someone who did not read the
  screen behind it?

## Loading and progress

- Name the real operation: "Uploading 3 files", not "Please wait".
- An ellipsis for an operation in progress: "Saving…".
- Never fake progress. A bar that is not measuring anything is a lie.
- A loading button keeps its label, so the layout does not jump.
- **Check:** does the person know what is happening and whether it is
  stuck?

## Success

- Brief, and only when the result is not already visible.
- Say what happened and, if useful, where to find it: "Invoice sent to
  Ana".
- **Check:** would they notice if the message were gone? If not, remove
  it.

## Links and navigation

- Link text makes sense out of context: "Read the billing policy", not
  "Learn more" or "here".
- No directional language: "in the sidebar on the right" fails on a
  phone and for a screen-reader user.
- Navigation labels are nouns the glossary uses.
- **Check:** read the list of links alone. Is each one distinct?

## Notifications

- Lead with what changed and for whom; the product name is not news.
- One notification, one event. Batch the rest.
- **Check:** could the person act on it from the lock screen or the
  email preview?
