# Factory product-repo Makefile — stamped by factory-init (ADR-0032).
#
# `make check` is the canonical local gate and exactly what CI runs: the
# stamped .github/workflows/validator.yml names no commands of its own, it
# calls these targets. Same targets as the factory repo's own root Makefile
# (its tools sit at the root, these under tools/factory/, and the plugin's
# structural lint has no product-repo counterpart).

.PHONY: check review wo-merged wo-in-progress wo-needs-review wo-failed
.PHONY: wo-record assembler cost-report gate-digest web-quality

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
	python3 tools/factory/gates.py
	python3 tools/factory/gates.py --selftest
	python3 -m unittest discover -q tests

review:
	python3 tools/factory/validator.py review --findings $(FINDINGS) --status $(STATUS)

wo-merged:
	python3 tools/factory/validator.py lifecycle --label wo:merged

wo-in-progress:
	python3 tools/factory/validator.py lifecycle --label wo:in-progress --issue $(ISSUE)

wo-needs-review:
	python3 tools/factory/validator.py lifecycle --label wo:needs-review --uncited skip

wo-failed:
	python3 tools/factory/validator.py lifecycle --label wo:failed --issue $(ISSUE) --verdict skip

# Set by the assembler workflow's record step: the dispatched run's spend,
# machine-written to the append-only cost ledger (issue #222; ADR-0034).
wo-record:
	python3 tools/factory/budget_guard.py record-run $(WO) $(RUN_ID) $(MODEL) $(FILE) $(OUTCOME)

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
		npx --yes playwright@$(PLAYWRIGHT_VERSION) install --with-deps; \
		npx --yes playwright@$(PLAYWRIGHT_VERSION) test; \
	else \
		echo "web-quality: no playwright.config.* — skipping (no web app to test)"; \
	fi
