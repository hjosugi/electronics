// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright 2026 hjosugi
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum {
    DUPLEX_PHYSICAL_LINES = 3,
    DUPLEX_LOGICAL_ROWS = 3,
    DUPLEX_LOGICAL_COLS = 12,
};

typedef uint32_t duplex_pin_t;
typedef uint16_t duplex_row_t;

typedef struct {
    duplex_pin_t rows[DUPLEX_PHYSICAL_LINES];
    duplex_pin_t cols[DUPLEX_PHYSICAL_LINES];
    uint8_t logical_col_base;
} duplex_half_t;

typedef struct {
    void *context;
    void (*set_input_high)(void *context, duplex_pin_t pin);
    void (*set_output_low)(void *context, duplex_pin_t pin);
    bool (*read_pin)(void *context, duplex_pin_t pin);
    void (*settle)(void *context);
} duplex_io_t;

void duplex_matrix_scan_raw(duplex_row_t matrix[DUPLEX_LOGICAL_ROWS], const duplex_half_t halves[], size_t half_count, const duplex_io_t *io);

bool duplex_matrix_half_has_ghost_risk(const duplex_row_t matrix[DUPLEX_LOGICAL_ROWS], uint8_t logical_col_base);

bool duplex_matrix_filter_ghosts(const duplex_row_t raw[DUPLEX_LOGICAL_ROWS], const duplex_row_t previous[DUPLEX_LOGICAL_ROWS], duplex_row_t filtered[DUPLEX_LOGICAL_ROWS], const duplex_half_t halves[], size_t half_count);
