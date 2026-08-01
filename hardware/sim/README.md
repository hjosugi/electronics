# Protection selection simulations

[`rj45-protection-selection.cir`](rj45-protection-selection.cir)はIssue #9の採用判断用ngspice回路です。
教育用の一般モデルは[`spice/`](../../spice/)に置き、採用回路へ直接結び付く感度解析だけをこのディレクトリへ置きます。

```bash
ngspice -b hardware/sim/rj45-protection-selection.cir
```

モデル値、測定結果、採用判断は次を参照してください。

- [基準結果](../../docs/09-simulation-results.md)
- [回路と故障分析](../../docs/13-matrix-rj45-safety.md)
- [ADR 0003](../../docs/adr/0003-use-470-ohm-and-dual-ended-tvs.md)

このモデルは集中定数のRC近似です。伝送線路反射、IEC 61000-4-2波形、TVSの動的クランプ、
RP2040の損傷限界を再現せず、PoEやUSBを実機へ接続する許可にもなりません。
