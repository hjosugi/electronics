# Split keyboard reference schematic

`split-keyboard.kicad_sch`は、初号機36キーのmatrixと8P8C保護回路を確認するKiCad 10参照回路です。
PCBはまだなく、このディレクトリだけで発注できる状態ではありません。

回路の正本となる反復構造は[`../generate_schematic.py`](../generate_schematic.py)にあり、
36キーのIDと配置元は[`docs/layout/36-key-choc-v1.layout.json`](../../docs/layout/36-key-choc-v1.layout.json)です。

## 再生成

KiCad 10標準symbol libraryが見える環境で、任意のPython仮想環境を使います。

```bash
python -m venv /tmp/electronics-kicad-generator
/tmp/electronics-kicad-generator/bin/pip install -r hardware/requirements-generator.txt
KICAD_SYMBOL_DIR=/path/to/kicad/10.0/symbols \
  /tmp/electronics-kicad-generator/bin/python hardware/generate_schematic.py
kicad-cli sch upgrade --force hardware/split-keyboard/split-keyboard.kicad_sch
make validate-hardware
```

生成器は開発用であり、CIはネットワークからPython packageを取得しません。CIではchecked-in回路図に対して
KiCad ERCとXML netlist構造検査を実行します。生成後は差分を確認し、ERC、negative test、文書の割当表を
同じcommitで更新してください。

## 見るべき証拠

- [matrix、pinout、部品、安全性](../../docs/13-matrix-rj45-safety.md)
- [470 Ωと両端TVSのADR](../../docs/adr/0003-use-470-ohm-and-dual-ended-tvs.md)
- [`make check-safety-schematic`](../../scripts/check-safety-schematic.sh)
- [第三者通知](../THIRD_PARTY_NOTICES.md)

KiCad標準symbol/footprintのlibrary tableには`${KICAD10_SYMBOL_DIR}`と`${KICAD10_FOOTPRINT_DIR}`を使います。
製造前に採用する8P8Cジャック、Choc v1 switch、RP2040-Zero実装フットプリントをメーカー図面と照合し、
PCB DRC、3D干渉、実物導通を追加してください。
