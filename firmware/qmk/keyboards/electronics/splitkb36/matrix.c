// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright 2026 hjosugi

#include "gpio.h"
#include "matrix.h"
#include "wait.h"

/*
 * One RP2040 scans both halves. The right half is passive: its six matrix
 * signals cross the 8P8C cable, but no power rail does.
 *
 * Each half is a 3 x 3 Japanese duplex matrix. Bank A drives a physical
 * column and reads the three physical rows. Bank B reverses that direction:
 * it drives a physical row and reads the three physical columns. This yields
 * 18 independently scanned switches from six GPIO signals per half.
 */

enum {
    PHYSICAL_LINES = 3,
    LEFT_LOGICAL_COL = 0,
    RIGHT_LOGICAL_COL = 6,
};

typedef struct {
    pin_t rows[PHYSICAL_LINES];
    pin_t cols[PHYSICAL_LINES];
    uint8_t logical_col_base;
} duplex_half_t;

static const duplex_half_t halves[] = {
    {
        .rows = {GP0, GP1, GP2},
        .cols = {GP3, GP4, GP5},
        .logical_col_base = LEFT_LOGICAL_COL,
    },
    {
        .rows = {GP6, GP7, GP8},
        .cols = {GP9, GP10, GP11},
        .logical_col_base = RIGHT_LOGICAL_COL,
    },
};

static void neutralize_half(const duplex_half_t *half) {
    for (uint8_t index = 0; index < PHYSICAL_LINES; ++index) {
        gpio_set_pin_input_high(half->rows[index]);
        gpio_set_pin_input_high(half->cols[index]);
    }
}

static void drive_low(pin_t pin) {
    /* RP2040's unflagged push-pull mode is slow-slew, 2 mA drive in ChibiOS. */
    gpio_write_pin_low(pin);
    gpio_set_pin_output(pin);
    gpio_write_pin_low(pin);
    wait_us(MATRIX_SETTLE_US);
}

static void record_pressed(matrix_row_t matrix[], uint8_t row, uint8_t col, pin_t pin) {
    if (!gpio_read_pin(pin)) {
        matrix[row] |= (matrix_row_t)1U << col;
    }
}

static void scan_half(matrix_row_t matrix[], const duplex_half_t *half) {
    /* Bank A: drive column low, read rows; logical columns base + 0..2. */
    for (uint8_t drive_col = 0; drive_col < PHYSICAL_LINES; ++drive_col) {
        neutralize_half(half);
        drive_low(half->cols[drive_col]);

        for (uint8_t row = 0; row < PHYSICAL_LINES; ++row) {
            record_pressed(matrix, row, half->logical_col_base + drive_col, half->rows[row]);
        }
    }

    /* Bank B: drive row low, read columns; transpose into base + 3..5. */
    for (uint8_t drive_row = 0; drive_row < PHYSICAL_LINES; ++drive_row) {
        neutralize_half(half);
        drive_low(half->rows[drive_row]);

        for (uint8_t row = 0; row < PHYSICAL_LINES; ++row) {
            record_pressed(matrix, row, half->logical_col_base + PHYSICAL_LINES + drive_row, half->cols[row]);
        }
    }

    neutralize_half(half);
}

void matrix_init_custom(void) {
    for (uint8_t index = 0; index < ARRAY_SIZE(halves); ++index) {
        neutralize_half(&halves[index]);
    }
}

bool matrix_scan_custom(matrix_row_t current_matrix[]) {
    matrix_row_t next_matrix[MATRIX_ROWS] = {0};
    bool changed = false;

    for (uint8_t index = 0; index < ARRAY_SIZE(halves); ++index) {
        scan_half(next_matrix, &halves[index]);
    }

    for (uint8_t row = 0; row < MATRIX_ROWS; ++row) {
        if (current_matrix[row] != next_matrix[row]) {
            current_matrix[row] = next_matrix[row];
            changed = true;
        }
    }

    return changed;
}
