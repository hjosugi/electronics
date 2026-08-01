# ngspiceサンプル

このディレクトリの`.cir`は、分割キーボード中央コネクタの故障モードを小さく切り出した教育用モデルです。

## 実行

```bash
make simulate
```

または個別に実行します。

```bash
ngspice -b spice/trrs-vcc-short.cir
```

各モデルは`.meas`で測定値を表示します。電源・GPIOの内部抵抗、接点抵抗、ケーブル容量は仮定値です。実際の部品とケーブルを決めたら、データシートまたは実測値へ置き換えてください。

## 対応する解説

- [OSS回路シミュレーション手順](../docs/03-simulation-guide.md)
- [付属ngspice回路の解説](../docs/04-spice-models.md)
- [基板化と実機検証](../docs/05-hardware-validation.md)
- [KiCad 10開発環境とスモークテスト](../docs/10-kicad-environment.md)
