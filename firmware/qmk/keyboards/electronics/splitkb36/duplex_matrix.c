// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright 2026 hjosugi

#include "duplex_matrix.h"

static duplex_row_t col_mask(uint8_t col) {
    return (duplex_row_t)1U << col;
}

static void neutralize_half(const duplex_half_t *half, const duplex_io_t *io) {
    for (uint8_t index = 0; index < DUPLEX_PHYSICAL_LINES; ++index) {
        io->set_input_high(io->context, half->rows[index]);
        io->set_input_high(io->context, half->cols[index]);
    }
}

static void record_pressed(duplex_row_t matrix[], uint8_t row, uint8_t col, duplex_pin_t pin, const duplex_io_t *io) {
    if (!io->read_pin(io->context, pin)) {
        matrix[row] |= col_mask(col);
    }
}

static void scan_half(duplex_row_t matrix[], const duplex_half_t *half, const duplex_io_t *io) {
    /* Bank A: drive column low, read rows; logical columns base + 0..2. */
    for (uint8_t drive_col = 0; drive_col < DUPLEX_PHYSICAL_LINES; ++drive_col) {
        neutralize_half(half, io);
        io->set_output_low(io->context, half->cols[drive_col]);
        io->settle(io->context);

        for (uint8_t row = 0; row < DUPLEX_PHYSICAL_LINES; ++row) {
            record_pressed(matrix, row, half->logical_col_base + drive_col, half->rows[row], io);
        }
    }

    /* Bank B: drive row low, read columns; transpose into base + 3..5. */
    for (uint8_t drive_row = 0; drive_row < DUPLEX_PHYSICAL_LINES; ++drive_row) {
        neutralize_half(half, io);
        io->set_output_low(io->context, half->rows[drive_row]);
        io->settle(io->context);

        for (uint8_t row = 0; row < DUPLEX_PHYSICAL_LINES; ++row) {
            record_pressed(matrix, row, half->logical_col_base + DUPLEX_PHYSICAL_LINES + drive_row, half->cols[row], io);
        }
    }

    neutralize_half(half, io);
}

void duplex_matrix_scan_raw(duplex_row_t matrix[DUPLEX_LOGICAL_ROWS], const duplex_half_t halves[], size_t half_count, const duplex_io_t *io) {
    for (uint8_t row = 0; row < DUPLEX_LOGICAL_ROWS; ++row) {
        matrix[row] = 0;
    }

    for (size_t index = 0; index < half_count; ++index) {
        scan_half(matrix, &halves[index], io);
    }
}

static bool pressed(const duplex_row_t matrix[], uint8_t row, uint8_t col) {
    return (matrix[row] & col_mask(col)) != 0;
}

bool duplex_matrix_half_has_ghost_risk(const duplex_row_t matrix[DUPLEX_LOGICAL_ROWS], uint8_t base) {
    /*
     * The opposite diode banks form a directed bipartite graph. A three-edge
     * alternating path can pull down a fourth logical position. Detect both
     * path directions and reject the whole half conservatively; four genuine
     * keys in the same pattern are intentionally rejected too.
     */
    for (uint8_t first_row = 0; first_row < DUPLEX_PHYSICAL_LINES; ++first_row) {
        for (uint8_t second_row = 0; second_row < DUPLEX_PHYSICAL_LINES; ++second_row) {
            if (first_row == second_row) {
                continue;
            }
            for (uint8_t first_col = 0; first_col < DUPLEX_PHYSICAL_LINES; ++first_col) {
                for (uint8_t second_col = 0; second_col < DUPLEX_PHYSICAL_LINES; ++second_col) {
                    if (first_col == second_col) {
                        continue;
                    }

                    const bool row_to_col_path =
                        pressed(matrix, first_row, base + first_col) &&
                        pressed(matrix, first_col, base + DUPLEX_PHYSICAL_LINES + second_row) &&
                        pressed(matrix, second_row, base + second_col);
                    const bool col_to_row_path =
                        pressed(matrix, first_col, base + DUPLEX_PHYSICAL_LINES + first_row) &&
                        pressed(matrix, first_row, base + second_col) &&
                        pressed(matrix, second_col, base + DUPLEX_PHYSICAL_LINES + second_row);

                    if (row_to_col_path || col_to_row_path) {
                        return true;
                    }
                }
            }
        }
    }

    return false;
}

bool duplex_matrix_filter_ghosts(const duplex_row_t raw[DUPLEX_LOGICAL_ROWS], const duplex_row_t previous[DUPLEX_LOGICAL_ROWS], duplex_row_t filtered[DUPLEX_LOGICAL_ROWS], const duplex_half_t halves[], size_t half_count) {
    bool ghost_risk = false;

    for (uint8_t row = 0; row < DUPLEX_LOGICAL_ROWS; ++row) {
        filtered[row] = raw[row];
    }

    for (size_t index = 0; index < half_count; ++index) {
        const uint8_t base = halves[index].logical_col_base;
        if (!duplex_matrix_half_has_ghost_risk(raw, base)) {
            continue;
        }

        ghost_risk = true;
        const duplex_row_t half_mask = (duplex_row_t)0x3FU << base;
        for (uint8_t row = 0; row < DUPLEX_LOGICAL_ROWS; ++row) {
            filtered[row] = (filtered[row] & ~half_mask) | (previous[row] & half_mask);
        }
    }

    return ghost_risk;
}
