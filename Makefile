SHELL := /usr/bin/env bash

.PHONY: notebooklm check-notebooklm layout check-layout check-document-css check-project-graph check-links check-qmk build-qmk check check-kicad check-kicad-negative check-safety-schematic environment order-readiness simulate validate validate-hardware package

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

check-project-graph:
	python3 ./scripts/check-project-graph.py --self-test

check-links:
	./scripts/check-markdown-links.sh

check-qmk:
	python3 ./scripts/check-qmk-source.py

build-qmk:
	@test -n "$(QMK_HOME)" || { echo "QMK_HOME=/path/to/qmk_firmware を指定してください" >&2; exit 1; }
	./scripts/build-qmk.sh "$(QMK_HOME)"

check: check-notebooklm check-layout check-document-css check-project-graph check-links check-qmk
	./scripts/validate.sh

check-kicad:
	bash ./scripts/check-kicad.sh

check-kicad-negative:
	bash ./scripts/check-kicad-negative.sh

check-safety-schematic:
	bash ./scripts/check-safety-schematic.sh

environment:
	bash ./scripts/check-environment.sh --report

order-readiness:
	python3 ./scripts/check-order-readiness.py

simulate:
	./scripts/check-spice.sh

validate:
	./scripts/run-validation.sh --base

validate-hardware:
	./scripts/run-validation.sh --hardware

package:
	@test -n "$(VERSION)" || { echo "VERSION=v0.1.0 のように指定してください" >&2; exit 1; }
	./scripts/package_release.sh "$(VERSION)"

.PHONY: graphify-setup graphify-update

## Install graphify and register its skill with Claude, Copilot and Codex.
graphify-setup:
	@sh scripts/graphify.sh setup

## Upgrade graphify, refresh the skill, and update the knowledge graph.
graphify-update:
	@sh scripts/graphify.sh update
