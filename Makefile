SHELL := /usr/bin/env bash

SPICE_FILES := \
	spice/trrs-vcc-short.cir \
	spice/gpio-series-resistors.cir \
	spice/passive-connector-bounce.cir

.PHONY: notebooklm check-notebooklm check-links check simulate validate package

notebooklm:
	./scripts/build-notebooklm.sh

check-notebooklm:
	./scripts/check-notebooklm.sh

check-links:
	./scripts/check-markdown-links.sh

check: check-notebooklm check-links
	./scripts/validate.sh

simulate:
	@command -v ngspice >/dev/null || { echo "ngspice が必要です" >&2; exit 1; }
	@set -euo pipefail; for circuit in $(SPICE_FILES); do \
		echo "==> $$circuit"; \
		ngspice -b "$$circuit"; \
	done

validate: check simulate

package:
	@test -n "$(VERSION)" || { echo "VERSION=v0.1.0 のように指定してください" >&2; exit 1; }
	./scripts/package_release.sh "$(VERSION)"
