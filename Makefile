SHELL := /usr/bin/env bash

.PHONY: notebooklm check-notebooklm layout check-layout check-document-css check-links check check-kicad check-kicad-negative check-safety-schematic environment simulate validate validate-hardware package

notebooklm:
	./scripts/build-notebooklm.sh

check-notebooklm:
	./scripts/check-notebooklm.sh

layout:
	python3 ./scripts/build-layout.py

check-layout:
	python3 ./scripts/build-layout.py --check --self-test

check-document-css:
	python3 ./scripts/check-document-css.py

check-links:
	./scripts/check-markdown-links.sh

check: check-notebooklm check-layout check-document-css check-links
	./scripts/validate.sh

check-kicad:
	bash ./scripts/check-kicad.sh

check-kicad-negative:
	bash ./scripts/check-kicad-negative.sh

check-safety-schematic:
	bash ./scripts/check-safety-schematic.sh

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
