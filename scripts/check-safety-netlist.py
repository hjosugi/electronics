#!/usr/bin/env python3
"""Validate safety-critical invariants in the exported KiCad netlist."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


REMOTE_SIGNALS = ("R_R0", "R_R1", "R_R2", "R_C0", "R_C1", "R_C2")
GPIO_NETS = (
    "L_R0",
    "L_R1",
    "L_R2",
    "L_C0",
    "L_C1",
    "L_C2",
    "R_R0_GPIO",
    "R_R1_GPIO",
    "R_R2_GPIO",
    "R_C0_GPIO",
    "R_C1_GPIO",
    "R_C2_GPIO",
)
CONNECTOR_NETS = ("GND", *REMOTE_SIGNALS, "GND")
FORBIDDEN_POWER = re.compile(r"(^|[_/+.-])(VCC|VBUS|VSYS|RAW|5V|3V3)([_/+.-]|$)", re.IGNORECASE)


@dataclass
class Netlist:
    values: dict[str, str]
    properties: dict[str, dict[str, str]]
    pin_nets: dict[tuple[str, str], str]


def normalize_net(name: str) -> str:
    return name.removeprefix("/")


def parse_netlist(path: Path) -> Netlist:
    root = ET.parse(path).getroot()
    values: dict[str, str] = {}
    properties: dict[str, dict[str, str]] = {}
    for component in root.findall("./components/comp"):
        reference = component.attrib["ref"]
        values[reference] = component.findtext("value", default="")
        properties[reference] = {
            item.attrib["name"]: item.attrib.get("value", "")
            for item in component.findall("property")
        }

    pin_nets: dict[tuple[str, str], str] = {}
    for net in root.findall("./nets/net"):
        name = normalize_net(net.attrib["name"])
        for node in net.findall("node"):
            pin_nets[(node.attrib["ref"], node.attrib["pin"])] = name
    return Netlist(values=values, properties=properties, pin_nets=pin_nets)


def physical_assignments(layout_path: Path) -> list[tuple[str, str, str, str]]:
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    result: list[tuple[str, str, str, str]] = []
    for hand, prefix in (("left", "L"), ("right", "R")):
        keys = [key for key in layout["keys"] if key["hand"] == hand]
        matrix = sorted(
            (key for key in keys if key["zone"] == "matrix"),
            key=lambda key: (key["column"], key["row"]),
        )
        thumbs = sorted(
            (key for key in keys if key["zone"] == "thumb"),
            key=lambda key: key["thumb_index"],
        )
        for key in matrix[:9]:
            result.append(
                (key["id"], "A", f"{prefix}_R{key['row']}", f"{prefix}_C{key['column']}")
            )
        for index, key in enumerate(matrix[9:] + thumbs):
            column, row = divmod(index, 3)
            result.append((key["id"], "B", f"{prefix}_C{column}", f"{prefix}_R{row}"))
    return result


def validate(netlist: Netlist, assignments: list[tuple[str, str, str, str]]) -> list[str]:
    errors: list[str] = []

    def expect_pin(reference: str, pin: int | str, expected: str) -> None:
        actual = netlist.pin_nets.get((reference, str(pin)))
        if actual != expected:
            errors.append(f"{reference}.{pin}: expected {expected}, got {actual}")

    for reference in ("J1", "J2"):
        value = netlist.values.get(reference, "")
        if "SPLIT ONLY / NO LAN" not in value:
            errors.append(f"{reference}: missing SPLIT ONLY / NO LAN marking")
        for pin, expected in enumerate(CONNECTOR_NETS, start=1):
            expect_pin(reference, pin, expected)
            actual = netlist.pin_nets.get((reference, str(pin)), "")
            if FORBIDDEN_POWER.search(actual):
                errors.append(f"{reference}.{pin}: forbidden center power net {actual}")

    for index, signal in enumerate(REMOTE_SIGNALS, start=1):
        reference = f"R{index}"
        if netlist.values.get(reference) != "470R":
            errors.append(f"{reference}: expected 470R, got {netlist.values.get(reference)}")
        if netlist.properties.get(reference, {}).get("MPN") != "ERJ3EKF4700V":
            errors.append(f"{reference}: expected orderable MPN ERJ3EKF4700V")
        attached = {
            netlist.pin_nets.get((reference, "1")),
            netlist.pin_nets.get((reference, "2")),
        }
        if attached != {signal, f"{signal}_GPIO"}:
            errors.append(f"{reference}: expected {signal} <-> {signal}_GPIO, got {sorted(attached)}")

    for pin, expected in enumerate(GPIO_NETS, start=1):
        expect_pin("J3", pin, expected)

    for reference in ("U1", "U2", "U3", "U4"):
        if netlist.values.get(reference) != "TPD4E05U06DQA":
            errors.append(f"{reference}: expected TPD4E05U06DQA")
        expect_pin(reference, 3, "GND")
        expect_pin(reference, 8, "GND")

    signal_tvs = {
        "R_R0": (("U1", "1"), ("U3", "1")),
        "R_R1": (("U1", "2"), ("U3", "2")),
        "R_R2": (("U1", "4"), ("U3", "4")),
        "R_C0": (("U1", "5"), ("U3", "5")),
        "R_C1": (("U2", "1"), ("U4", "1")),
        "R_C2": (("U2", "2"), ("U4", "2")),
    }
    for signal, pins in signal_tvs.items():
        for reference, pin in pins:
            expect_pin(reference, pin, signal)

    if len(assignments) != 36:
        errors.append(f"layout: expected 36 assignments, got {len(assignments)}")
    seen_key_ids: set[str] = set()
    for index, (key_id, bank, source, destination) in enumerate(assignments, start=1):
        switch = f"SW{index}"
        diode = f"D{index}"
        if netlist.properties.get(switch, {}).get("Key ID") != key_id:
            errors.append(f"{switch}: expected Key ID {key_id}")
        if netlist.properties.get(switch, {}).get("Duplex bank") != bank:
            errors.append(f"{switch}: expected duplex bank {bank}")
        if netlist.values.get(diode) != "1N4148W":
            errors.append(f"{diode}: expected 1N4148W")
        if netlist.properties.get(diode, {}).get("MPN") != "1N4148W-7-F":
            errors.append(f"{diode}: expected orderable MPN 1N4148W-7-F")
        expect_pin(switch, 1, source)
        expect_pin(diode, 1, destination)
        switch_internal = netlist.pin_nets.get((switch, "2"))
        diode_anode = netlist.pin_nets.get((diode, "2"))
        if switch_internal != diode_anode:
            errors.append(f"{switch}/{diode}: switch must connect to diode anode")
        seen_key_ids.add(key_id)
    if len(seen_key_ids) != 36:
        errors.append("matrix key IDs are not unique")

    return errors


def run_self_test(netlist: Netlist, assignments: list[tuple[str, str, str, str]]) -> None:
    forbidden_power = copy.deepcopy(netlist)
    forbidden_power.pin_nets[("J1", "2")] = "VBUS"
    if not any("forbidden center power" in item for item in validate(forbidden_power, assignments)):
        raise AssertionError("negative test did not reject center VBUS")

    wrong_resistor = copy.deepcopy(netlist)
    wrong_resistor.values["R3"] = "220R"
    if not any("R3: expected 470R" in item for item in validate(wrong_resistor, assignments)):
        raise AssertionError("negative test did not reject wrong series resistor")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("netlist", type=Path)
    parser.add_argument("--layout", required=True, type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    netlist = parse_netlist(args.netlist)
    assignments = physical_assignments(args.layout)
    errors = validate(netlist, assignments)
    if errors:
        print("safety netlist validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if args.self_test:
        run_self_test(netlist, assignments)
    print("安全回路構造検証に合格しました（36キー、中央無給電、470R x6、両端TVS）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
