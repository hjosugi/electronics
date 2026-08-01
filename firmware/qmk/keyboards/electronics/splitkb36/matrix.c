// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright 2026 hjosugi

#include "duplex_matrix.h"
#include "gpio.h"
#include "matrix.h"
#include "wait.h"

/* One RP2040 scans both halves; no power rail or split transport is used. */
static const duplex_half_t halves[] = {
    {
        .rows = {GP0, GP1, GP2},
        .cols = {GP3, GP4, GP5},
        .logical_col_base = 0,
    },
    {
        .rows = {GP6, GP7, GP8},
        .cols = {GP9, GP10, GP11},
        .logical_col_base = 6,
    },
};

static void set_input_high(void *context, duplex_pin_t pin) {
    (void)context;
    gpio_set_pin_input_high((pin_t)pin);
}

static void set_output_low(void *context, duplex_pin_t pin) {
    (void)context;
    /* Unflagged RP2040 push-pull is slow-slew, 2 mA drive in ChibiOS. */
    gpio_write_pin_low((pin_t)pin);
    gpio_set_pin_output((pin_t)pin);
    gpio_write_pin_low((pin_t)pin);
}

static bool read_pin(void *context, duplex_pin_t pin) {
    (void)context;
    return gpio_read_pin((pin_t)pin);
}

static void settle(void *context) {
    (void)context;
    wait_us(MATRIX_SETTLE_US);
}

static const duplex_io_t io = {
    .context = NULL,
    .set_input_high = set_input_high,
    .set_output_low = set_output_low,
    .read_pin = read_pin,
    .settle = settle,
};

void matrix_init_custom(void) {
    for (uint8_t index = 0; index < ARRAY_SIZE(halves); ++index) {
        for (uint8_t pin = 0; pin < DUPLEX_PHYSICAL_LINES; ++pin) {
            gpio_set_pin_input_high((pin_t)halves[index].rows[pin]);
            gpio_set_pin_input_high((pin_t)halves[index].cols[pin]);
        }
    }
}

bool matrix_scan_custom(matrix_row_t current_matrix[]) {
    duplex_row_t raw[DUPLEX_LOGICAL_ROWS];
    duplex_row_t previous[DUPLEX_LOGICAL_ROWS];
    duplex_row_t filtered[DUPLEX_LOGICAL_ROWS];
    bool changed = false;

    for (uint8_t row = 0; row < DUPLEX_LOGICAL_ROWS; ++row) {
        previous[row] = (duplex_row_t)current_matrix[row];
    }

    duplex_matrix_scan_raw(raw, halves, ARRAY_SIZE(halves), &io);
    duplex_matrix_filter_ghosts(raw, previous, filtered, halves, ARRAY_SIZE(halves));

    for (uint8_t row = 0; row < MATRIX_ROWS; ++row) {
        if (current_matrix[row] != (matrix_row_t)filtered[row]) {
            current_matrix[row] = (matrix_row_t)filtered[row];
            changed = true;
        }
    }

    return changed;
}
