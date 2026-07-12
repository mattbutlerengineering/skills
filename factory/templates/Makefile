# Factory product-repo Makefile — stamped by factory-init (ADR-0032).
# `make check` is the canonical local gate and exactly what CI runs.

.PHONY: check

check:
	python3 tools/factory/gates.py
	python3 tools/factory/gates.py --selftest
	python3 -m unittest discover -q tests
