---
type: llm
---

PASS if the reply gives concrete cuts that include both of these: deleting `legacy_total` because nothing references it, and replacing the `Formatter` / `CurrencyFormatter` / `FormatterFactory` classes with a direct formatting expression (for example an f-string inside `order_total`).
FAIL if it recommends deleting `order_total` or anything `main.py` imports, if it gives only general advice with no specific cut, or if it says it changed a file.
