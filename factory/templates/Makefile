# Factory product-repo Makefile — stamped by factory-init (ADR-0032).
#
# `make check` is the canonical local gate and exactly what CI runs: the
# stamped .github/workflows/validator.yml names no commands of its own, it
# calls these targets. Same targets as the factory repo's own root Makefile
# (its tools sit at the root, these under tools/factory/, and the plugin's
# structural lint has no product-repo counterpart).

.PHONY: check review wo-merged assembler cost-report gate-digest web-quality

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

assembler:
	python3 tools/factory/assembler.py resolve

cost-report:
	python3 tools/factory/cost_report.py report

gate-digest:
	python3 tools/factory/gate_digest.py daily

# The design pipeline's job body (.github/workflows/design.yml; ADR-0033
# gate 2), run when a PR touches docs/design/**. Playwright drives the UI
# quality / accessibility / Core Web Vitals checks. It SKIPS gracefully when
# the repo has no web app to test (no playwright.config.*) — this factory repo
# has none, and the target is for stamped product repos that do. Same
# skip-when-absent shape as the sweeps sentry job. Path-agnostic, so both
# Makefiles carry it verbatim.
web-quality:
	@if ls playwright.config.* >/dev/null 2>&1; then \
		npx --yes playwright install --with-deps; \
		npx --yes playwright test; \
	else \
		echo "web-quality: no playwright.config.* — skipping (no web app to test)"; \
	fi
