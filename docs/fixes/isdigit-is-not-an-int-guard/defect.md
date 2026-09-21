---
stage: diagnose
run: maintenance:isdigit-is-not-an-int-guard
date: 2026-08-31
assumptions: []
---

# Defect: `str.isdigit()` is not an `int()` guard

Two findings, one root cause. Found by sweeping every `int()` call in
root modules for whether a guard stands between it and its input.

## 1. `do_POST` parses `Content-Length` with no guard at all

`dashboard.py:610` was:

```python
length = int(self.headers.get("Content-Length") or 0)
```

inside a handler whose own docstring calls it a *"thin shim over
respond(): JSON in, JSON out, no logic."* It is the one piece of logic
there, it was unguarded, and `do_POST` had **no tests** — `respond_post`
(the pure half) is well covered; the HTTP plumbing was not.

Against a live server on 127.0.0.1, before the fix:

```
  Content-Length: 2                -> HTTP/1.0 404 Not Found
  Content-Length: abc              -> <connection closed, no response>
  Content-Length: -1               -> TIMED OUT after 2.5s (handler thread stuck)
  Content-Length: 99999            -> TIMED OUT after 2.5s (handler thread stuck)
  (no Content-Length header)       -> HTTP/1.0 404 Not Found
```

Three distinct failures:

- **`abc`** raises `ValueError` out of `do_POST`. `socketserver` catches
  it, logs a traceback and closes the connection, so the client gets no
  HTTP response at all where it is owed a `400`.
- **`-1`** reaches `rfile.read(-1)`, which reads to EOF and wedges the
  handler thread.
- **an overstated length** blocks on a read that never satisfies.

In a `ThreadingHTTPServer` the last two each hold a thread.

## 2. The obvious guard does not work

The fix that suggests itself is `.isdigit()` — the guard this repo
already uses at its two other string-to-int boundaries. It is not a
guard:

```
value        repr       isdigit()  int() result
'12'         '12'       True       12
'²'          '\xb2'     True       *** ValueError
'¹'          '\xb9'     True       *** ValueError
'⁵'          '⁵'   True       *** ValueError
'٣'          '٣'   True       3
```

Superscripts satisfy `isdigit()` and `int()` refuses them. This is not a
contrivance: **U+00B2 is latin-1 byte 0xB2**, and `http.client` decodes
header values as latin-1, so `Content-Length: \xb2` is an ordinary
request that reaches the crash.

Both existing sites have the hole, and both were confirmed raising:

```
validator.parse(["review", "--status", "\xb2"])
   *** RAISED ValueError: invalid literal for int() with base 10: '²'

assembler.main(["find-pr", "\xb2"])
   *** RAISED ValueError: invalid literal for int() with base 10: '²'
```

`validator.py:462` takes `status` from `make review STATUS=$FINDINGS_RC`
and `assembler.py:281` takes the issue number from `make find-pr
ISSUE=...`. Both are CLI boundaries, where a traceback instead of a
clean problem string is exactly what `cli.report`'s contract exists to
prevent.

## Not a crash site

`validator.py:467` and `:470` also guard with `.isdigit()`, but
`options["issue"]` stays a string — the only `int()` calls in that
module are `:249` (over a regex `\d+` capture) and `:462`. Those two are
format checks, not int guards, and are left alone.

## Scope

`validator.py` and `assembler.py` are in `factory_init.MIRRORS`, so the
payload mirrors and `factory/manifest.json` move with them.
`dashboard.py` is root-only (it says so at line 11).
