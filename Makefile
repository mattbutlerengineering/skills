# The factory's canonical command set (PRD-0001; ADR-0033 gate 3).
#
# `make check` is the local gate and *exactly* what CI runs:
# .github/workflows/validator.yml names no commands of its own, it calls
# these targets — so local and CI cannot drift apart. The same workflow is
# mirrored into the template payload, where factory/templates/Makefile is
# this file's product-repo twin (tools under tools/factory/, no plugin
# lint); tests/test_factory_gates.py::TestLockstep pins the pair.

.PHONY: check review wo-merged wo-in-progress wo-needs-review wo-failed
.PHONY: assembler cost-report gate-digest web-quality

# Set by the validator workflow's review job; defaults keep `make review`
# runnable by hand.
FINDINGS ?= findings.txt
STATUS ?= 0

# Set by the assembler workflow's claim step (the issue the label event
# fired on); an empty ISSUE makes validator.py print usage and exit 2.
ISSUE ?=

# Plain `=`, not `?=`: the pin must not be overridable from the environment,
# or a repo's CI could change behavior when a new playwright ships. Bump
# deliberately alongside the design workflow's Node LTS.
PLAYWRIGHT_VERSION = 1.62.1

check:
	python3 lint.py
	python3 gates.py
	python3 gates.py --selftest
	python3 -m unittest discover tests

review:
	python3 validator.py review --findings $(FINDINGS) --status $(STATUS)

wo-merged:
	python3 validator.py lifecycle --label wo:merged

wo-in-progress:
	python3 validator.py lifecycle --label wo:in-progress --issue $(ISSUE)

wo-needs-review:
	python3 validator.py lifecycle --label wo:needs-review --uncited skip

wo-failed:
	python3 validator.py lifecycle --label wo:failed --issue $(ISSUE) --verdict skip

assembler:
	python3 assembler.py resolve

cost-report:
	python3 cost_report.py report

gate-digest:
	python3 gate_digest.py daily

# The design pipeline's job body (.github/workflows/design.yml; ADR-0033
# gate 2), run when a PR touches docs/design/**. Playwright drives the UI
# quality / accessibility / Core Web Vitals checks. It SKIPS gracefully when
# the repo has no web app to test (no playwright.config.*) — this factory repo
# has none, and the target is for stamped product repos that do. Same
# skip-when-absent shape as the sweeps sentry job. Path-agnostic, so both
# Makefiles carry it verbatim.
web-quality:
	@if ls playwright.config.* >/dev/null 2>&1; then \
		npx --yes playwright@$(PLAYWRIGHT_VERSION) install --with-deps; \
		npx --yes playwright@$(PLAYWRIGHT_VERSION) test; \
	else \
		echo "web-quality: no playwright.config.* — skipping (no web app to test)"; \
	fi
