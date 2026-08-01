# Hardware third-party notices

## KiCad standard symbols and footprints

`hardware/split-keyboard/split-keyboard.kicad_sch` embeds symbol data from the
KiCad standard library and refers to standard KiCad footprints. The KiCad
libraries are licensed under CC-BY-SA-4.0 with the KiCad library exception:

- https://www.kicad.org/libraries/license/
- source snapshot used for generation: `kicad-symbols` revision packaged with
  KiCad 10.0.5 on 2026-08-01

The exception permits designs and generated design files to use library data
without imposing CC-BY-SA-4.0 on the design. This repository does not
redistribute the KiCad libraries as a collection.

## kicad-sch-api

`hardware/generate_schematic.py` uses `kicad-sch-api==0.5.6` as an optional
development-time generator. The dependency is not vendored or bundled in
release archives beyond the requirements declaration.

- project: https://github.com/circuit-synth/kicad-sch-api
- license: MIT
- version used: 0.5.6
