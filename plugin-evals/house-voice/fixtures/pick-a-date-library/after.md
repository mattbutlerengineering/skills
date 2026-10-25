Use the standard library: `datetime` with `zoneinfo`, which ships with
Python 3.9 and later and reads the system's time zone database.

Add `python-dateutil` only if you must parse free-form date strings; its
`dateutil.parser` handles formats `datetime` rejects.
