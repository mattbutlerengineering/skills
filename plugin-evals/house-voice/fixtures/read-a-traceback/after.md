The dictionary `row` has no 'user_id' key when that line runs, so the lookup
raises `KeyError`.

Add `print(row.keys())` before the line to see which keys arrived. If the
field can be missing, read it with `row.get('user_id')`, which returns
`None` instead of raising.
