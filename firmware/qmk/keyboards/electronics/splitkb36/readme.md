# Electronics SplitKB36

A 36-key, one-MCU split keyboard for a Waveshare RP2040-Zero. Both halves use
3 x 3 Japanese duplex matrices. The right half is passive and connects through
six protected matrix signals plus ground; no power rail crosses the centre
cable.

Build from the pinned QMK checkout through the repository wrapper:

```sh
./scripts/build-qmk.sh /path/to/qmk_firmware
```

See `docs/14-qmk-firmware.md` in the electronics repository for the GPIO map,
safety boundary, reproducible build instructions, and validation evidence.

The scanner uses a topology-specific conservative ghost filter. If an
alternating three-edge path makes a phantom position electrically ambiguous,
the affected half keeps its previous state; the opposite half continues to
update. See `docs/15-qmk-matrix-tests.md` for the tested model and limitations.
