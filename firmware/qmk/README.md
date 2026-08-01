# QMK firmware overlay

This directory is an overlay for `qmk/qmk_firmware`, pinned by
[`qmk-version.env`](qmk-version.env). It targets one Waveshare RP2040-Zero on
the left half and a passive right half connected by 8P8C. No split transport
and no centre-cable power rail are used.

The firmware files in this directory are licensed under
**GPL-2.0-or-later**, matching QMK. The repository's top-level MIT license
continues to apply to the original documentation, scripts, and simulation
models outside this directory.

Run `scripts/build-qmk.sh /path/to/qmk_firmware` from the repository root. It
runs the shared duplex-scanner GoogleTests and QMK lint before compiling. The
generated UF2 is copied to `dist/qmk/`, which is intentionally ignored by Git.
