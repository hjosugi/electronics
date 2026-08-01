// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright 2026 hjosugi

#include "gtest/gtest.h"

#include <array>
#include <cstdint>
#include <queue>

extern "C" {
#include "duplex_matrix.h"
}

namespace {

constexpr std::array<duplex_half_t, 2> kHalves = {{
    {{0, 1, 2}, {3, 4, 5}, 0},
    {{6, 7, 8}, {9, 10, 11}, 6},
}};

class MatrixModel {
   public:
    MatrixModel() {
        io.context = this;
        io.set_input_high = SetInputHigh;
        io.set_output_low = SetOutputLow;
        io.read_pin = ReadPin;
        io.settle = Settle;
        Reset();
    }

    void Reset() {
        for (auto &row : pressed) {
            row.fill(false);
        }
        pin_is_output.fill(false);
        connected = {true, true};
        active_output = -1;
        settled = false;
        safety_violations = 0;
        settle_count = 0;
    }

    void Press(uint8_t row, uint8_t col) { pressed[row][col] = true; }
    void DisconnectRight() { connected[1] = false; }

    std::array<duplex_row_t, DUPLEX_LOGICAL_ROWS> ScanRaw() {
        std::array<duplex_row_t, DUPLEX_LOGICAL_ROWS> matrix{};
        duplex_matrix_scan_raw(matrix.data(), kHalves.data(), kHalves.size(), &io);
        return matrix;
    }

    duplex_io_t io{};
    std::array<std::array<bool, DUPLEX_LOGICAL_COLS>, DUPLEX_LOGICAL_ROWS> pressed{};
    std::array<bool, DUPLEX_LOGICAL_COLS> pin_is_output{};
    std::array<bool, 2> connected{};
    int active_output = -1;
    bool settled = false;
    int safety_violations = 0;
    int settle_count = 0;

   private:
    static MatrixModel &Self(void *context) { return *static_cast<MatrixModel *>(context); }

    static void SetInputHigh(void *context, duplex_pin_t pin) {
        auto &self = Self(context);
        self.pin_is_output.at(pin) = false;
        if (self.active_output == static_cast<int>(pin)) {
            self.active_output = -1;
        }
        self.settled = false;
    }

    static void SetOutputLow(void *context, duplex_pin_t pin) {
        auto &self = Self(context);
        const int half = pin >= 6 ? 1 : 0;
        const int start = half * 6;

        if (self.active_output != -1) {
            ++self.safety_violations;
        }
        for (int index = start; index < start + 6; ++index) {
            if (self.pin_is_output.at(index)) {
                ++self.safety_violations;
            }
        }

        self.pin_is_output.at(pin) = true;
        self.active_output = static_cast<int>(pin);
        self.settled = false;
    }

    static void Settle(void *context) {
        auto &self = Self(context);
        if (self.active_output == -1) {
            ++self.safety_violations;
        }
        self.settled = true;
        ++self.settle_count;
    }

    static bool ReadPin(void *context, duplex_pin_t pin) {
        auto &self = Self(context);
        if (!self.settled || self.active_output == -1) {
            ++self.safety_violations;
            return true;
        }

        const int input_half = pin >= 6 ? 1 : 0;
        const int output_half = self.active_output >= 6 ? 1 : 0;
        if (input_half != output_half || !self.connected.at(input_half)) {
            return true;
        }

        return !self.HasDirectedPath(input_half, static_cast<int>(pin) - input_half * 6,
                                     self.active_output - output_half * 6);
    }

    bool HasDirectedPath(int half, int source, int destination) const {
        bool edges[6][6] = {};
        const uint8_t base = static_cast<uint8_t>(half * 6);

        for (uint8_t row = 0; row < 3; ++row) {
            for (uint8_t col = 0; col < 3; ++col) {
                if (pressed[row][base + col]) {
                    edges[row][3 + col] = true;  // Bank A: row -> column.
                }
                if (pressed[col][base + 3 + row]) {
                    edges[3 + col][row] = true;  // Bank B: column -> row.
                }
            }
        }

        std::queue<int> pending;
        bool seen[6] = {};
        pending.push(source);
        seen[source] = true;

        while (!pending.empty()) {
            const int node = pending.front();
            pending.pop();
            if (node == destination) {
                return true;
            }
            for (int next = 0; next < 6; ++next) {
                if (edges[node][next] && !seen[next]) {
                    seen[next] = true;
                    pending.push(next);
                }
            }
        }

        return false;
    }
};

duplex_row_t Bit(uint8_t col) { return static_cast<duplex_row_t>(1U << col); }

TEST(DuplexMatrix, EveryLogicalPositionMapsExactlyOnce) {
    for (uint8_t expected_row = 0; expected_row < DUPLEX_LOGICAL_ROWS; ++expected_row) {
        for (uint8_t expected_col = 0; expected_col < DUPLEX_LOGICAL_COLS; ++expected_col) {
            MatrixModel model;
            model.Press(expected_row, expected_col);
            const auto raw = model.ScanRaw();

            for (uint8_t row = 0; row < DUPLEX_LOGICAL_ROWS; ++row) {
                EXPECT_EQ(raw[row], row == expected_row ? Bit(expected_col) : 0)
                    << "row=" << static_cast<int>(expected_row)
                    << " col=" << static_cast<int>(expected_col);
            }
            EXPECT_EQ(model.safety_violations, 0);
            EXPECT_EQ(model.settle_count, 12);
        }
    }
}

TEST(DuplexMatrix, IndependentChordHasNoExtraPositions) {
    MatrixModel model;
    model.Press(0, 0);
    model.Press(1, 2);
    model.Press(2, 7);
    model.Press(0, 11);

    const auto raw = model.ScanRaw();
    EXPECT_EQ(raw[0], Bit(0) | Bit(11));
    EXPECT_EQ(raw[1], Bit(2));
    EXPECT_EQ(raw[2], Bit(7));
    EXPECT_EQ(model.safety_violations, 0);
}

TEST(DuplexMatrix, DisconnectingRightHalfReleasesItsKeys) {
    MatrixModel model;
    model.Press(1, 1);
    model.Press(2, 9);
    const auto previous = model.ScanRaw();

    model.DisconnectRight();
    const auto raw = model.ScanRaw();
    std::array<duplex_row_t, DUPLEX_LOGICAL_ROWS> filtered{};
    EXPECT_FALSE(duplex_matrix_filter_ghosts(raw.data(), previous.data(), filtered.data(), kHalves.data(), kHalves.size()));
    EXPECT_EQ(filtered[0], 0);
    EXPECT_EQ(filtered[1], Bit(1));
    EXPECT_EQ(filtered[2], 0);
}

TEST(DuplexMatrix, AlternatingThreeEdgePathNeverEmitsPhantomKey) {
    MatrixModel model;
    model.Press(0, 0);  // R0 -> C0 (Bank A).
    model.Press(0, 4);  // C0 -> R1 (Bank B).
    const auto previous = model.ScanRaw();

    model.Press(1, 1);  // R1 -> C1; creates a path R0 -> C0 -> R1 -> C1.
    const auto raw = model.ScanRaw();
    EXPECT_NE(raw[0] & Bit(1), 0);  // Ideal-diode worst case exposes the phantom.
    EXPECT_TRUE(duplex_matrix_half_has_ghost_risk(raw.data(), 0));

    std::array<duplex_row_t, DUPLEX_LOGICAL_ROWS> filtered{};
    EXPECT_TRUE(duplex_matrix_filter_ghosts(raw.data(), previous.data(), filtered.data(), kHalves.data(), kHalves.size()));
    EXPECT_EQ(filtered, previous);  // Freeze the ambiguous half; emit neither third nor phantom.
}

TEST(DuplexMatrix, ReverseAlternatingPathNeverEmitsPhantomKey) {
    MatrixModel model;
    model.Press(0, 3);  // C0 -> R0 (Bank B).
    model.Press(0, 1);  // R0 -> C1 (Bank A).
    const auto previous = model.ScanRaw();

    model.Press(1, 5);  // C1 -> R2; creates a path C0 -> R0 -> C1 -> R2.
    const auto raw = model.ScanRaw();
    EXPECT_NE(raw[0] & Bit(5), 0);
    EXPECT_TRUE(duplex_matrix_half_has_ghost_risk(raw.data(), 0));

    std::array<duplex_row_t, DUPLEX_LOGICAL_ROWS> filtered{};
    EXPECT_TRUE(duplex_matrix_filter_ghosts(raw.data(), previous.data(), filtered.data(), kHalves.data(), kHalves.size()));
    EXPECT_EQ(filtered, previous);
}

TEST(DuplexMatrix, GhostRiskOnLeftDoesNotFreezeRightHalf) {
    MatrixModel model;
    model.Press(0, 0);
    model.Press(0, 4);
    const auto previous = model.ScanRaw();

    model.Press(1, 1);
    model.Press(2, 10);
    const auto raw = model.ScanRaw();
    std::array<duplex_row_t, DUPLEX_LOGICAL_ROWS> filtered{};
    EXPECT_TRUE(duplex_matrix_filter_ghosts(raw.data(), previous.data(), filtered.data(), kHalves.data(), kHalves.size()));
    EXPECT_EQ(filtered[0], previous[0]);
    EXPECT_EQ(filtered[1], previous[1]);
    EXPECT_EQ(filtered[2], previous[2] | Bit(10));
}

}  // namespace
