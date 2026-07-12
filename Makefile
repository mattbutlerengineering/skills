# The factory's canonical command set (PRD-0001; ADR-0033 gate 3).
#
# `make check` is the local gate and *exactly* what CI runs:
# .github/workflows/validator.yml names no commands of its own, it calls
# these targets — so local and CI cannot drift apart. The same workflow is
# mirrored into the template payload, where factory/templates/Makefile is
# this file's product-repo twin (tools under tools/factory/, no plugin
# lint); tests/test_factory_gates.py::TestLockstep pins the pair.

.PHONY: check review wo-merged assembler

# Set by the validator workflow's review job; defaults keep `make review`
# runnable by hand.
FINDINGS ?= findings.txt
STATUS ?= 0

check:
	python3 lint.py
	python3 gates.py
	python3 gates.py --selftest
	python3 -m unittest discover tests

review:
	python3 validator.py review --findings $(FINDINGS) --status $(STATUS)

wo-merged:
	python3 validator.py lifecycle --label wo:merged

assembler:
	python3 assembler.py resolve
