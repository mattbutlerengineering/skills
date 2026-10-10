---
type: regex
target: { source: file, path: dates.py }
pattern: '^\s*(?:import|from)\s+(?:re|dateutil|pendulum|arrow)\b'
flags: m
match: not_contains
---
