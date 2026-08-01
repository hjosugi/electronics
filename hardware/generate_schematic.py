#!/usr/bin/env python3
"""Generate the reviewed split-keyboard reference schematic.

The checked-in ``.kicad_sch`` remains the CI input.  This generator documents
the source of truth for the repetitive 36-key matrix and protection network.
It requires kicad-sch-api 0.5.6 and the KiCad 10 standard symbol libraries.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import kicad_sch_api as ksa


ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = ROOT / "docs/layout/36-key-choc-v1.layout.json"
OUTPUT_PATH = ROOT / "hardware/split-keyboard/split-keyboard.kicad_sch"

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


def add_pin_label(schematic, reference: str, pin: str, net: str) -> None:
    schematic.add_label(net, pin=(reference, pin), size=1.0)


def add_no_connect(schematic, reference: str, pin: str) -> None:
    position = schematic.get_component_pin_position(reference, pin)
    if position is None:
        raise RuntimeError(f"pin not found: {reference}.{pin}")
    schematic.no_connects.add(position)


def hide_properties(component, *names: str) -> None:
    component.hidden_properties.update(names)


def matrix_assignment(keys: list[dict]) -> list[tuple[dict, str, str, str]]:
    """Map 18 physical keys to two diode-direction banks of one 3x3 matrix."""
    matrix_keys = sorted(
        (key for key in keys if key["zone"] == "matrix"),
        key=lambda key: (key["column"], key["row"]),
    )
    thumbs = sorted(
        (key for key in keys if key["zone"] == "thumb"),
        key=lambda key: key["thumb_index"],
    )
    bank_a = matrix_keys[:9]
    bank_b = matrix_keys[9:] + thumbs
    if len(bank_a) != 9 or len(bank_b) != 9:
        raise ValueError("each half must map to two 9-key duplex banks")

    result: list[tuple[dict, str, str, str]] = []
    for key in bank_a:
        result.append((key, "A", f"R{key['row']}", f"C{key['column']}"))
    for index, key in enumerate(bank_b):
        column, row = divmod(index, 3)
        result.append((key, "B", f"C{column}", f"R{row}"))
    return result


def add_half_matrix(schematic, hand: str, keys: list[dict], x: float) -> int:
    prefix = "L" if hand == "left" else "R"
    offset = 0 if hand == "left" else 18
    assignments = matrix_assignment(keys)

    schematic.add_text(
        f"{hand.upper()} HALF: 3 x 3 Japanese duplex matrix (18 keys)",
        (x + 45, 15),
        size=1.4,
        bold=True,
    )
    schematic.add_text(
        "Bank A: ROW -> COL / Bank B: COL -> ROW; K=pin 1, A=pin 2",
        (x + 45, 20),
        size=1.0,
    )

    for index, (key, bank, source, destination) in enumerate(assignments):
        y = 32 + index * 12
        switch_ref = f"SW{offset + index + 1}"
        diode_ref = f"D{offset + index + 1}"
        switch = schematic.components.add(
            lib_id="Switch:SW_Push",
            reference=switch_ref,
            value="KEY",
            position=(x + 18, y),
            **{"Key ID": key["id"], "Duplex bank": bank},
        )
        hide_properties(switch, "Value", "Key ID", "Duplex bank")
        diode = schematic.components.add(
            lib_id="Device:D_Small",
            reference=diode_ref,
            value="1N4148W",
            position=(x + 32, y),
            footprint="Diode_SMD:D_SOD-123",
            rotation=180,
            **{"Key ID": key["id"], "MPN": "1N4148W-7-F"},
        )
        hide_properties(diode, "Value", "Key ID", "MPN")
        schematic.add_wire_between_pins(switch.reference, "2", diode.reference, "2")
        add_pin_label(schematic, switch.reference, "1", f"{prefix}_{source}")
        add_pin_label(schematic, diode.reference, "1", f"{prefix}_{destination}")
        schematic.add_text(f"{bank} {key['id']}", (x + 42, y), size=0.8)

    return len(assignments)


def add_mcu_header(schematic) -> None:
    schematic.add_text(
        "WAVESHARE RP2040-ZERO GPIO ABSTRACTION (module power is intentionally omitted)",
        (145, 15),
        size=1.3,
        bold=True,
    )
    header = schematic.components.add(
        lib_id="Connector_Generic:Conn_01x12",
        reference="J3",
        value="RP2040-Zero GPIO0..GPIO11",
        position=(175, 55),
        **{"Module": "Waveshare RP2040-Zero"},
    )
    hide_properties(header, "Module")
    for pin, net in enumerate(GPIO_NETS, start=1):
        add_pin_label(schematic, header.reference, str(pin), net)

    for index, net in enumerate(GPIO_NETS):
        schematic.add_text(f"GPIO{index}: {net}", (145, 76 + index * 4), size=0.9)


def add_series_resistors(schematic) -> None:
    schematic.add_text(
        "MCU-SIDE FAULT CURRENT LIMITING: six independent 470 ohm paths",
        (145, 132),
        size=1.2,
        bold=True,
    )
    for index, signal in enumerate(REMOTE_SIGNALS):
        y = 141 + index * 9
        resistor = schematic.components.add(
            lib_id="Device:R",
            reference=f"R{index + 1}",
            value="470R",
            position=(180, y),
            footprint="Resistor_SMD:R_0603_1608Metric",
            rotation=90,
            **{
                "MPN": "ERJ3EKF4700V",
                "Purpose": "center-cable GPIO fault-current limiting",
            },
        )
        hide_properties(resistor, "MPN", "Purpose")
        add_pin_label(schematic, resistor.reference, "1", f"{signal}_GPIO")
        add_pin_label(schematic, resistor.reference, "2", signal)


def add_tvs_array(schematic, reference: str, signals: tuple[str, ...], position: tuple[float, float]) -> None:
    array = schematic.components.add(
        lib_id="Power_Protection:TPD4E05U06DQA",
        reference=reference,
        value="TPD4E05U06DQA",
        position=position,
        footprint="Package_SON:USON-10_2.5x1.0mm_P0.5mm",
        **{"MPN": "TPD4E05U06DQA", "Role": "connector-entry ESD clamp"},
    )
    hide_properties(array, "MPN", "Role")
    channel_pins = ("1", "2", "4", "5")
    for pin, signal in zip(channel_pins, signals, strict=False):
        add_pin_label(schematic, array.reference, pin, signal)
    for pin in channel_pins[len(signals) :]:
        add_no_connect(schematic, array.reference, pin)
    add_pin_label(schematic, array.reference, "3", "GND")
    for pin in ("6", "7", "9", "10"):
        add_no_connect(schematic, array.reference, pin)


def add_cable_connector(schematic, reference: str, position: tuple[float, float], side: str) -> None:
    connector = schematic.components.add(
        lib_id="Connector:8P8C",
        reference=reference,
        value=f"8P8C {side} - SPLIT ONLY / NO LAN",
        position=position,
        **{"Cable": "dedicated straight-through 8P8C"},
    )
    hide_properties(connector, "Value", "Cable")
    pin_nets = ("GND", *REMOTE_SIGNALS, "GND")
    for pin, net in enumerate(pin_nets, start=1):
        add_pin_label(schematic, connector.reference, str(pin), net)


def build(output: Path) -> None:
    layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    keys_by_hand = {
        hand: [key for key in layout["keys"] if key["hand"] == hand]
        for hand in ("left", "right")
    }
    schematic = ksa.create_schematic("split-keyboard")
    schematic.set_paper_size("A3")
    schematic.set_title_block(
        title="36-key passive split keyboard reference circuit",
        date="2026-08-01",
        rev="0.2",
        company="hjosugi/electronics",
        comments={
            1: "SPLIT ONLY / NO LAN",
            2: "Reference circuit; PCB and hardware validation incomplete",
        },
    )

    left_count = add_half_matrix(schematic, "left", keys_by_hand["left"], 20)
    right_count = add_half_matrix(schematic, "right", keys_by_hand["right"], 315)
    if (left_count, right_count) != (18, 18):
        raise ValueError("expected exactly 18 keys on each half")

    add_mcu_header(schematic)
    add_series_resistors(schematic)

    schematic.add_text(
        "CENTER LINK: GND + 6 matrix signals only; NEVER VCC / 5V / 3V3 / VBUS / RAW",
        (145, 205),
        size=1.35,
        bold=True,
    )
    schematic.add_text(
        "Dedicated straight-through cable. This circuit is NOT Ethernet or PoE compatible.",
        (145, 211),
        size=1.05,
    )
    add_cable_connector(schematic, "J1", (195, 218), "LEFT")
    add_cable_connector(schematic, "J2", (250, 218), "RIGHT")
    add_tvs_array(schematic, "U1", REMOTE_SIGNALS[:4], (165, 239))
    add_tvs_array(schematic, "U2", REMOTE_SIGNALS[4:], (205, 239))
    add_tvs_array(schematic, "U3", REMOTE_SIGNALS[:4], (245, 239))
    add_tvs_array(schematic, "U4", REMOTE_SIGNALS[4:], (285, 239))

    ground_flag = schematic.components.add(
        lib_id="power:PWR_FLAG",
        reference="#FLG0101",
        value="PWR_FLAG",
        position=(220, 257),
    )
    add_pin_label(schematic, ground_flag.reference, "1", "GND")
    ground = schematic.components.add(
        lib_id="power:GND",
        reference="#PWR0101",
        value="GND",
        position=(235, 257),
    )
    add_pin_label(schematic, ground.reference, "1", "GND")

    schematic.add_text(
        "SAFETY BOUNDARY: no center power removes one short path; it does not prove hot-plug, ESD, miswire, or PoE safety.",
        (130, 266),
        size=1.05,
        bold=True,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    schematic.save(str(output))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    build(args.output.resolve())
    print(f"generated {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
