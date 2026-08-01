#!/usr/bin/env python3
"""Validate the QMK overlay without downloading or compiling QMK."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QMK_ROOT = ROOT / "firmware" / "qmk"
KEYBOARD = QMK_ROOT / "keyboards" / "electronics" / "splitkb36"
EXPECTED_QMK_REF = "4ffb1ab16c443f2def5949d39b56057c0c88c88b"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"QMK source validation failed: {message}")


def main() -> None:
    info = json.loads((KEYBOARD / "keyboard.json").read_text(encoding="utf-8"))
    rules = (KEYBOARD / "rules.mk").read_text(encoding="utf-8")
    matrix = (KEYBOARD / "matrix.c").read_text(encoding="utf-8")
    scanner = (KEYBOARD / "duplex_matrix.c").read_text(encoding="utf-8")
    tests = (QMK_ROOT / "tests" / "electronics_splitkb36" / "test_duplex_matrix.cpp").read_text(encoding="utf-8")
    build_script = (ROOT / "scripts" / "build-qmk.sh").read_text(encoding="utf-8")
    version = (QMK_ROOT / "qmk-version.env").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "qmk-ci.yml").read_text(encoding="utf-8")

    require(info["processor"] == "RP2040", "processor must be RP2040")
    require(info["bootloader"] == "rp2040", "bootloader must emit UF2")
    require(info["matrix_pins"]["custom_lite"] is True, "custom_lite matrix is required")
    require("split" not in info, "one-MCU design must not enable QMK split transport")

    layout = info["layouts"]["LAYOUT_split_3x5_3"]["layout"]
    coordinates = {tuple(key["matrix"]) for key in layout}
    expected_coordinates = {(row, col) for row in range(3) for col in range(12)}
    require(len(layout) == 36, "layout must expose exactly 36 keys")
    require(coordinates == expected_coordinates, "logical matrix must be a complete 3 x 12 grid")

    require(re.search(r"^CUSTOM_MATRIX\s*=\s*lite$", rules, re.MULTILINE) is not None,
            "rules.mk must select the current lite custom-matrix API")
    require(re.search(r"^BOARD\s*=\s*GENERIC_RP_RP2040$", rules, re.MULTILINE) is not None,
            "rules.mk must select the generic RP2040 board")

    pins = re.findall(r"\bGP(?:[0-9]|1[01])\b", matrix)
    require(set(pins) == {f"GP{index}" for index in range(12)}, "matrix must use GP0 through GP11")
    require(all(pins.count(f"GP{index}") == 1 for index in range(12)), "each GPIO must be assigned once")
    combined_scanner = matrix + scanner
    for symbol in ("neutralize_half", "gpio_set_pin_input_high", "gpio_set_pin_output", "wait_us(MATRIX_SETTLE_US)"):
        require(symbol in combined_scanner, f"matrix safety primitive missing: {symbol}")
    require(not re.search(r"\b(?:VBUS|VCC|RAW|5V)\b", matrix), "matrix scanner must not depend on a power rail")
    require("duplex_matrix_filter_ghosts" in combined_scanner, "topology-specific ghost filter is required")
    for test_name in ("EveryLogicalPositionMapsExactlyOnce", "DisconnectingRightHalfReleasesItsKeys", "AlternatingThreeEdgePathNeverEmitsPhantomKey"):
        require(test_name in tests, f"QMK unit-test contract missing: {test_name}")
    require("qmk test-c" in build_script, "reproducible build must run QMK C unit tests")

    ref_match = re.search(r"^QMK_REF=([0-9a-f]{40})$", version, re.MULTILINE)
    require(ref_match is not None, "qmk-version.env needs a full commit SHA")
    require(ref_match.group(1) == EXPECTED_QMK_REF, "unexpected QMK commit")
    require(f"QMK_REF: {EXPECTED_QMK_REF}" in workflow, "workflow and version pin must match")

    print("QMK source validation passed (RP2040, 36 keys, 12 unique GPIOs, pinned QMK)")


if __name__ == "__main__":
    main()
