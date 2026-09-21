---
stage: verify
run: maintenance:isdigit-is-not-an-int-guard
date: 2026-08-31
assumptions: []
---

# Verification: `str.isdigit()` is not an `int()` guard

## 1. Reproduced before any test was written — PASS

Live server on 127.0.0.1, raw sockets, before the change:

```
  Content-Length: 2                -> HTTP/1.0 404 Not Found
  Content-Length: abc              -> <connection closed, no response>
  Content-Length: -1               -> TIMED OUT after 2.5s (handler thread stuck)
  Content-Length: 99999 (overstated) -> TIMED OUT after 2.5s (handler thread stuck)
  no Content-Length header         -> HTTP/1.0 404 Not Found
```

with this on the server's stderr:

```
  File "/Users/mbutler/github/skills/dashboard.py", line 610, in do_POST
    length = int(self.headers.get("Content-Length") or 0)
ValueError: invalid literal for int() with base 10: 'abc'
```

And the two CLI sites, called directly:

```
validator.parse(["review", "--status", "\xb2"])
   *** RAISED ValueError: invalid literal for int() with base 10: '²'

assembler.main(["find-pr", "\xb2"])
   *** RAISED ValueError: invalid literal for int() with base 10: '²'
```

## 2. Red before green — PASS

`validator` and `assembler`, before the change:

```
  File "/Users/mbutler/github/skills/assembler.py", line 281, in main
    number, problems = pr_for_issue(int(argv[1]), run=run)
                                    ~~~^^^^^^^^^
ValueError: invalid literal for int() with base 10: '²'

----------------------------------------------------------------------
Ran 135 tests in 0.099s

FAILED (errors=2)
```

`dashboard`, before the change — the two well-formed controls pass and
all three malformed cases fail:

```
test_a_valid_length_is_read_and_routed ... ok
test_an_absent_header_is_read_as_an_empty_body ... ok
test_a_digit_that_int_refuses_answers_400 ... ERROR
test_a_non_numeric_length_answers_400_instead_of_dropping ... ERROR
test_a_negative_length_answers_400_before_the_read ... FAIL
```

The two `ERROR`s are the raise itself. The `FAIL` is `-1`: over a
`BytesIO` `read(-1)` succeeds and returns 404, so only a real socket
shows the hang — the test pins the `400` that is correct either way.

## 3. Green after — PASS

```
Ran 145 tests in 0.094s

OK
```

## 4. The live behaviour actually changed — PASS

Same raw-socket script, after the change:

```
  Content-Length: 2                -> HTTP/1.0 404 Not Found
  Content-Length: abc              -> HTTP/1.0 400 Bad Request
  Content-Length: \xb2 (isdigit!)  -> HTTP/1.0 400 Bad Request
  Content-Length: -1               -> HTTP/1.0 400 Bad Request
  Content-Length: 99999 (overstated) -> TIMED OUT after 2.5s
  no Content-Length                -> HTTP/1.0 404 Not Found

server stderr: (empty)
```

Server stderr is empty — no traceback on any request. The overstated
length still times out; see **Not fixed** below.

## 5. Full battery — PASS

```
Ran 1356 tests in 16.382s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

1344 on `origin/main` + 12 new = 1356. `one_owner.py` reports the same
nine pre-existing problems as `main`.

## 6. Mirrors and manifest — PASS

`validator.py` and `assembler.py` are in `factory_init.MIRRORS`.
`python3 factory_init.py update-manifest` ran and reported
`factory-init: 0 problem(s)`; the regenerated payload copies and
`factory/manifest.json` are committed with the change. Detector E is
green above, which is the gate over exactly that.

## Not fixed — disclosed

**An overstated `Content-Length` still wedges the handler thread.** It is
visible in the after-run above, unchanged. The remedy is a socket
timeout (`timeout` on the handler class), which changes behaviour for
*every* request rather than rejecting bad input, so it is a server
policy decision and not this run's to take. `-1` and non-numeric values
no longer reach the read at all, which is the part the guard owns.

## Not verified

- **Concurrency.** The thread-exhaustion claim is inferred from
  `ThreadingHTTPServer` semantics plus the single-request hang measured
  above; no test opens N connections to exhaust the pool.
- **Encodings other than latin-1 for the header.** `http.client` decodes
  headers as latin-1, so that is the reachable set; other Unicode digit
  forms (`٣`, `⁵`) were checked in the interpreter, not through a socket.
