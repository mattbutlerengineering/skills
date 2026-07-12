# Factory product-repo Makefile — stamped by factory-init (ADR-0032).
#
# `make check` is the canonical local gate and exactly what CI runs: the
# stamped .github/workflows/validator.yml names no commands of its own, it
# calls these targets. Same targets as the factory repo's own root Makefile
# (its tools sit at the root, these under tools/factory/, and the plugin's
# structural lint has no product-repo counterpart).

.PHONY: check review wo-merged

# Set by the validator workflow's review job; defaults keep `make review`
# runnable by hand.
FINDINGS ?= findings.txt
STATUS ?= 0

check:
	python3 tools/factory/gates.py
	python3 tools/factory/gates.py --selftest
	python3 -m unittest discover -q tests

review:
	python3 tools/factory/validator.py review --findings $(FINDINGS) --status $(STATUS)

wo-merged:
	python3 tools/factory/validator.py lifecycle --label wo:merged
