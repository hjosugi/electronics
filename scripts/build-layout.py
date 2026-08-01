#!/usr/bin/env python3
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""調整可能プロファイルからIssue #5の36キーレイアウトを生成する。"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = REPO_ROOT / "docs/layout/profiles/balanced-kinesis-inspired.json"
DEFAULT_OUTPUT_DIRECTORY = REPO_ROOT / "docs/layout"
CANONICAL_FILENAME = "36-key-choc-v1.layout.json"
KLE_FILENAME = "36-key-choc-v1.kle.json"

COLUMN_STAGGER_LIMITS = (
    (10.0, 22.0),
    (2.0, 10.0),
    (0.0, 0.0),
    (2.0, 10.0),
    (5.0, 14.0),
)
THUMB_LIMITS = (
    {"x_mm": (44.0, 52.0), "y_mm": (56.0, 66.0), "rotation_deg": (-10.0, 10.0)},
    {"x_mm": (64.0, 72.0), "y_mm": (58.0, 69.0), "rotation_deg": (-25.0, -5.0)},
    {"x_mm": (84.0, 93.0), "y_mm": (61.0, 72.0), "rotation_deg": (45.0, 70.0)},
)


def read_profile(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"プロファイルが見つかりません: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"プロファイルJSONが不正です: {path}: {error}") from error


def require_range(name: str, value: float, limits: tuple[float, float]) -> None:
    lower, upper = limits
    if not lower <= value <= upper:
        raise ValueError(f"{name}は{lower}から{upper}の範囲で指定してください（現在: {value}）")


def validate_profile(profile: dict[str, Any]) -> None:
    if profile.get("profile_version") != 1:
        raise ValueError("profile_versionは1である必要があります")
    if profile.get("switch_family") != "Kailh PG1350 (Choc v1)":
        raise ValueError("初号機のスイッチ系統はKailh PG1350 (Choc v1)に固定します")

    matrix = profile["matrix"]
    if matrix["horizontal_pitch_mm"] != 18.0 or matrix["vertical_pitch_mm"] != 17.0:
        raise ValueError("初号機のキーピッチは横18.0 mm、縦17.0 mmに固定します")

    staggers = matrix["column_top_y_mm"]
    splays = matrix["column_splay_deg"]
    if len(staggers) != 5 or len(splays) != 5:
        raise ValueError("column_top_y_mmとcolumn_splay_degは外側から5列分必要です")
    for index, (stagger, limits) in enumerate(zip(staggers, COLUMN_STAGGER_LIMITS, strict=True)):
        require_range(f"column_top_y_mm[{index}]", float(stagger), limits)
    for index, splay in enumerate(splays):
        require_range(f"column_splay_deg[{index}]", float(splay), (-3.0, 3.0))

    thumbs = profile["thumb_keys"]
    if len(thumbs) != 3:
        raise ValueError("親指キーは片側3個に固定します")
    for index, (thumb, limits) in enumerate(zip(thumbs, THUMB_LIMITS, strict=True)):
        if thumb.get("thumb_index") != index:
            raise ValueError("thumb_indexは外側から0、1、2の順に指定してください")
        for field, field_limits in limits.items():
            require_range(f"thumb_keys[{index}].{field}", float(thumb[field]), field_limits)

    fit = profile["desk_fit"]
    require_range("desk_fit.separation_mm", float(fit["separation_mm"]), (120.0, 260.0))
    require_range("desk_fit.half_yaw_deg", float(fit["half_yaw_deg"]), (0.0, 15.0))
    if fit["tent_steps_deg"] != [0.0, 10.0, 20.0]:
        raise ValueError("初号機ケースのtent_steps_degは[0.0, 10.0, 20.0]に固定します")
    if fit["default_tent_deg"] not in fit["tent_steps_deg"]:
        raise ValueError("default_tent_degはtent_steps_degから選んでください")
    if profile["surface"] != {"type": "flat", "concave_keywell": False}:
        raise ValueError("単一平面PCBではconcave keywellを有効化できません")


def rotate_point(
    x_mm: float,
    y_mm: float,
    pivot_x_mm: float,
    pivot_y_mm: float,
    angle_deg: float,
) -> tuple[float, float]:
    radians = math.radians(angle_deg)
    relative_x = x_mm - pivot_x_mm
    relative_y = y_mm - pivot_y_mm
    return (
        pivot_x_mm + relative_x * math.cos(radians) - relative_y * math.sin(radians),
        pivot_y_mm + relative_x * math.sin(radians) + relative_y * math.cos(radians),
    )


def build_keys(profile: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = profile["matrix"]
    horizontal_pitch_mm = float(matrix["horizontal_pitch_mm"])
    vertical_pitch_mm = float(matrix["vertical_pitch_mm"])
    keys: list[dict[str, Any]] = []

    for hand in ("left", "right"):
        prefix = "L" if hand == "left" else "R"
        mirror = 1.0 if hand == "left" else -1.0
        for column, (top_y_mm, splay_deg) in enumerate(
            zip(matrix["column_top_y_mm"], matrix["column_splay_deg"], strict=True)
        ):
            x_mm = column * horizontal_pitch_mm
            pivot_y_mm = float(top_y_mm) + vertical_pitch_mm
            for row in range(3):
                base_y_mm = float(top_y_mm) + row * vertical_pitch_mm
                rotated_x_mm, rotated_y_mm = rotate_point(
                    x_mm,
                    base_y_mm,
                    x_mm,
                    pivot_y_mm,
                    float(splay_deg),
                )
                rotation_deg = mirror * float(splay_deg)
                if rotation_deg == 0.0:
                    rotation_deg = 0.0
                keys.append(
                    {
                        "id": f"{prefix}-M-C{column}-R{row}",
                        "hand": hand,
                        "zone": "matrix",
                        "column": column,
                        "row": row,
                        "local_x_mm": round(rotated_x_mm, 4),
                        "local_y_mm": round(rotated_y_mm, 4),
                        "rotation_deg": rotation_deg,
                    }
                )

        for thumb in profile["thumb_keys"]:
            rotation_deg = mirror * float(thumb["rotation_deg"])
            if rotation_deg == 0.0:
                rotation_deg = 0.0
            keys.append(
                {
                    "id": f"{prefix}-T{thumb['thumb_index']}",
                    "hand": hand,
                    "zone": "thumb",
                    "thumb_index": thumb["thumb_index"],
                    "local_x_mm": float(thumb["x_mm"]),
                    "local_y_mm": float(thumb["y_mm"]),
                    "rotation_deg": rotation_deg,
                }
            )
    return keys


def build_canonical_layout(
    profile_path: Path,
    profile: dict[str, Any],
    keys: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        profile_source = str(profile_path.relative_to(REPO_ROOT))
    except ValueError:
        profile_source = str(profile_path)
    return {
        "format_version": 1,
        "name": "split-36-choc-v1",
        "profile_name": profile["profile_name"],
        "profile_source": profile_source,
        "decision_record": "../adr/0002-use-36-key-choc-v1-layout.md",
        "units": "mm",
        "license": "CERN-OHL-P-2.0",
        "provenance": {
            "upstream": "https://github.com/pashutk/chocofi",
            "upstream_commit": "273676d11b06785fb5a1a94860a39fc36c38baba",
            "upstream_file": "pcb/chocofi-topplate.kicad_pcb",
            "kinesis_principles": [
                "左右分離",
                "指の自然な運動に沿う縦列",
                "独立した親指クラスタ",
                "tentingをケース側で段階調整",
            ],
            "modifications": [
                "スイッチ中心座標を片側ローカル原点へ正規化",
                "左右鏡像のキー集合と安定したキーIDを生成",
                "column splayと親指位置を制限付きプロファイル化",
                "KLE表示用JSONを生成",
            ],
        },
        "requirements": {
            "total_keys": 36,
            "keys_per_half": 18,
            "matrix_per_half": {"rows": 3, "columns": 5},
            "thumb_keys_per_half": 3,
            "rotary_encoder": False,
            "surface": profile["surface"],
        },
        "switch": {
            "family": profile["switch_family"],
            "default_switch_part_number": "CPG135001D01",
            "default_switch_description": "Choc Red, linear",
            "hotswap_contact_part_number": "CPG135001S30",
            "footprint_status": "Issue #6で最新メーカー図面と実部品を照合して確定する",
        },
        "geometry": {
            "coordinate_system": {
                "scope": "片側ローカル座標。右手側はX方向と回転角を鏡像化して配置する",
                "origin": "C0中心のX=0とC2最上段中心のY=0が作る基準点",
                "x_positive": "外側小指列から内側人差し指列へ",
                "y_positive": "指先側から手首側へ",
            },
            "matrix": profile["matrix"],
            "thumb_keys": profile["thumb_keys"],
            "desk_fit": profile["desk_fit"],
        },
        "keys": keys,
    }


def build_kle_layout(profile: dict[str, Any], keys: list[dict[str, Any]]) -> list[Any]:
    rows: list[Any] = [
        {
            "name": "split-36-choc-v1",
            "author": "hjosugi/electronics",
            "notes": (
                "Issue #5 / ADR 0002。KLEは配置確認用。"
                "製造寸法は36-key-choc-v1.layout.jsonを正本とする。"
            ),
            "switchMount": "Kailh Choc hot-swap",
            "switchBrand": "Kailh",
            "switchType": "PG1350 (Choc v1)",
        }
    ]
    horizontal_pitch_mm = float(profile["matrix"]["horizontal_pitch_mm"])
    vertical_pitch_mm = float(profile["matrix"]["vertical_pitch_mm"])

    # KLEは抽象表示のため、X軸1 unit = 18 mm、Y軸1 unit = 17 mmとする。
    for key in keys:
        if key["hand"] == "left":
            x = key["local_x_mm"] / horizontal_pitch_mm
        else:
            x = 8.0 + (4.0 - key["local_x_mm"] / horizontal_pitch_mm)
        y = key["local_y_mm"] / vertical_pitch_mm
        rows.append(
            [
                {
                    "r": key["rotation_deg"],
                    "rx": round(x, 4),
                    "ry": round(y, 4),
                },
                key["id"],
            ]
        )
    return rows


def minimum_center_distance(keys: list[dict[str, Any]], hand: str) -> float:
    half_keys = [key for key in keys if key["hand"] == hand]
    distances = []
    for index, first in enumerate(half_keys):
        for second in half_keys[index + 1 :]:
            distances.append(
                math.hypot(
                    first["local_x_mm"] - second["local_x_mm"],
                    first["local_y_mm"] - second["local_y_mm"],
                )
            )
    return min(distances)


def validate_layout(canonical: dict[str, Any], kle: list[Any]) -> None:
    keys = canonical["keys"]
    if len(keys) != 36:
        raise ValueError(f"キー数は36である必要があります（現在: {len(keys)}）")
    ids = [key["id"] for key in keys]
    if len(ids) != len(set(ids)):
        raise ValueError("キーIDが重複しています")
    if Counter(key["hand"] for key in keys) != Counter({"left": 18, "right": 18}):
        raise ValueError("左右は18キーずつである必要があります")

    for hand in ("left", "right"):
        matrix = [key for key in keys if key["hand"] == hand and key["zone"] == "matrix"]
        thumbs = [key for key in keys if key["hand"] == hand and key["zone"] == "thumb"]
        if len(matrix) != 15 or len(thumbs) != 3:
            raise ValueError(f"{hand}側が3x5+3ではありません")
        distance = minimum_center_distance(keys, hand)
        if distance < 15.5:
            raise ValueError(f"{hand}側のキー中心が近すぎます: {distance:.2f} mm")

    if canonical["requirements"]["rotary_encoder"] is not False:
        raise ValueError("初号機にはロータリーエンコーダを含めません")
    if canonical["requirements"]["surface"]["concave_keywell"] is not False:
        raise ValueError("単一平面PCBではconcave keywellを有効化できません")

    kle_labels = [item for row in kle[1:] for item in row if isinstance(item, str)]
    if Counter(kle_labels) != Counter(ids):
        raise ValueError("KLE JSONと正本JSONのキー集合が一致しません")


def serialize(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def expected_outputs(profile_path: Path) -> dict[str, str]:
    profile = read_profile(profile_path)
    validate_profile(profile)
    keys = build_keys(profile)
    canonical = build_canonical_layout(profile_path, profile, keys)
    kle = build_kle_layout(profile, keys)
    validate_layout(canonical, kle)
    return {
        CANONICAL_FILENAME: serialize(canonical),
        KLE_FILENAME: serialize(kle),
    }


def run_guardrail_tests(profile_path: Path) -> None:
    profile = read_profile(profile_path)
    validate_profile(profile)

    allowed = copy.deepcopy(profile)
    allowed["matrix"]["column_splay_deg"][0] = 3.0
    validate_profile(allowed)
    allowed_keys = build_keys(allowed)
    allowed_canonical = build_canonical_layout(profile_path, allowed, allowed_keys)
    validate_layout(allowed_canonical, build_kle_layout(allowed, allowed_keys))

    invalid_profiles = []
    invalid_splay = copy.deepcopy(profile)
    invalid_splay["matrix"]["column_splay_deg"][0] = 3.01
    invalid_profiles.append(invalid_splay)
    invalid_pitch = copy.deepcopy(profile)
    invalid_pitch["matrix"]["horizontal_pitch_mm"] = 18.1
    invalid_profiles.append(invalid_pitch)
    invalid_keywell = copy.deepcopy(profile)
    invalid_keywell["surface"]["concave_keywell"] = True
    invalid_profiles.append(invalid_keywell)

    for invalid in invalid_profiles:
        try:
            validate_profile(invalid)
        except ValueError:
            continue
        raise ValueError("変更禁止または範囲外のプロファイルを拒否できませんでした")

    print("プロファイル境界テストに合格しました（許容1件、拒否3件）")


def write_outputs(output_directory: Path, outputs: dict[str, str]) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    for filename, content in outputs.items():
        path = output_directory / filename
        path.write_text(content, encoding="utf-8")
        print(f"generated {path}")


def check_outputs(output_directory: Path, outputs: dict[str, str]) -> int:
    stale: list[Path] = []
    for filename, expected in outputs.items():
        path = output_directory / filename
        try:
            actual = path.read_text(encoding="utf-8")
            json.loads(actual)
        except (FileNotFoundError, json.JSONDecodeError):
            stale.append(path)
            continue
        if actual != expected:
            stale.append(path)

    if stale:
        for path in stale:
            print(f"レイアウトJSONが未生成または古いです: {path}", file=sys.stderr)
        print("更新コマンド: make layout", file=sys.stderr)
        return 1

    print("レイアウトJSON検証に合格しました（36キー、左右18キー、3x5+3）")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--check", action="store_true", help="生成物を変更せず整合性だけ検査する")
    parser.add_argument("--self-test", action="store_true", help="プロファイル境界も検査する")
    args = parser.parse_args()
    try:
        profile_path = args.profile.resolve()
        outputs = expected_outputs(profile_path)
        if args.self_test:
            run_guardrail_tests(profile_path)
        if args.check:
            return check_outputs(args.output_dir.resolve(), outputs)
        write_outputs(args.output_dir.resolve(), outputs)
    except (KeyError, TypeError, ValueError) as error:
        print(f"レイアウト生成エラー: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
