SHELL := /usr/bin/env bash

.PHONY: notebooklm check-notebooklm check-links check check-kicad check-kicad-negative environment simulate validate validate-hardware package

notebooklm:
	./scripts/build-notebooklm.sh

check-notebooklm:
	./scripts/check-notebooklm.sh

check-links:
	./scripts/check-markdown-links.sh

check: check-notebooklm check-links
	./scripts/validate.sh

check-kicad:
	bash ./scripts/check-kicad.sh

check-kicad-negative:
	bash ./scripts/check-kicad-negative.sh

environment:
	bash ./scripts/check-environment.sh --report

simulate:
	./scripts/check-spice.sh

validate:
	./scripts/run-validation.sh --base

validate-hardware:
	./scripts/run-validation.sh --hardware

package:
	@test -n "$(VERSION)" || { echo "VERSION=v0.1.0 のように指定してください" >&2; exit 1; }
	./scripts/package_release.sh "$(VERSION)"
