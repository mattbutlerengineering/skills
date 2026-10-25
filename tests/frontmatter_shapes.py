"""The one shape table for where a file's frontmatter ends (ADR-0118).

Every row is (name, text, expected end): the index of the closing fence
line in TEXT's lines, or None when TEXT has no frontmatter. The owner
test (protocol.frontmatter_end) and each caller's agreement test read
this table, so the rule is written down once, not once per suite.
A block holds `status: ok` and a body is `# Body`, as in
docs/fixes/one-frontmatter-end/defect.md's verdict table.
"""

SHAPES = (
    # The nine rows of architecture.md's rule table.
    ("lf exact fences", "---\nstatus: ok\n---\n# Body\n", 2),
    ("crlf", "---\r\nstatus: ok\r\n---\r\n# Body\r\n", 2),
    ("opener with trailing whitespace", "--- \nstatus: ok\n---\n# Body\n", 2),
    ("closer with trailing whitespace", "---\nstatus: ok\n--- \n# Body\n", 2),
    ("unterminated opener", "---\nstatus: ok\n# Body\n", None),
    ("no frontmatter", "status: ok\n# Body\n", None),
    ("empty block", "---\n---\n# Body\n", 1),
    ("closer at end of file, no newline", "---\nstatus: ok\n---", 2),
    ("opener with leading whitespace", " ---\nstatus: ok\n---\n# Body\n",
     None),
    # The extra shapes the old-against-new comparison turned up.
    ("empty block with a later fence line",
     "---\n---\nstatus: ok\n---\n# Body\n", 1),
    ("indented closer", "---\nstatus: ok\n ---\n# Body\n", None),
    ("tab after the opener", "---\t\nstatus: ok\n---\n# Body\n", 2),
    ("lone carriage returns", "---\rstatus: ok\r---\r# Body\r", 2),
    ("empty text", "", None),
    ("a single fence line", "---", None),
)
