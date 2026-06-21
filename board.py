from __future__ import annotations
import numpy as np
from constants import BOARD


class Board:
    def __init__(self, color_up: str, pieces=None, moves: list[str] | None = None) -> None:
        self.pieces: np.ndarray = np.array(pieces if pieces is not None else BOARD, dtype="U1")
        self.color_up: str = color_up
        self.moves: list[str] = moves if moves is not None else []
        self.white_pieces: int = int(np.sum((self.pieces == 'w') | (self.pieces == 'k')))
        self.black_pieces: int = int(np.sum((self.pieces == 'B') | (self.pieces == 'K')))

    def get_color_up(self) -> str:
        return self.color_up

    def get_pieces(self) -> list[tuple[int, int]]:
        rows, cols = np.where(self.pieces != ' ')
        return list(zip(rows.tolist(), cols.tolist()))

    def get_piece_by_index(self, row: int, col: int) -> str:
        return self.pieces[row, col]

    def has_piece(self, row: int, col: int) -> bool:
        return self.pieces[row, col] != ' '

    def get_color_at(self, row: int, col: int) -> str:
        return 'W' if self.pieces[row, col] in ('w', 'k') else 'B'

    def is_king_at(self, row: int, col: int) -> bool:
        return self.pieces[row, col] in ('k', 'K')

    @staticmethod
    def row_col_from_pos(pos: int) -> tuple[int, int]:
        row = pos // 4
        col = (pos % 4) * 2 + (1 if row % 2 != 0 else 0)
        return (row, col)

    @staticmethod
    def pos_from_row_col(row: int, col: int) -> int:
        return row * 4 + col // 2

    def get_moves(self, row: int, col: int) -> list[dict]:
        ch = self.pieces[row, col]
        if ch == ' ':
            return []
        is_white = ch in ('w', 'k')
        is_king = ch in ('k', 'K')
        # White pieces move toward row 0, black toward row 7
        forward = -1 if is_white else 1
        dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)] if is_king else [(forward, -1), (forward, 1)]

        jumps, normals = [], []
        for dr, dc in dirs:
            nr, nc = row + dr, col + dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                continue
            target = self.pieces[nr, nc]
            if target == ' ':
                normals.append({"to_row": nr, "to_col": nc, "eats_piece": False})
            elif (is_white and target in ('B', 'K')) or (not is_white and target in ('w', 'k')):
                lr, lc = row + 2 * dr, col + 2 * dc
                if 0 <= lr < 8 and 0 <= lc < 8 and self.pieces[lr, lc] == ' ':
                    jumps.append({"to_row": lr, "to_col": lc, "eats_piece": True})

        return jumps if jumps else normals

    def move_piece(self, from_row: int, from_col: int, to_row: int, to_col: int) -> None:
        ch = self.pieces[from_row, from_col]
        move_str = f"{ch}{from_row}{from_col}"

        if abs(to_row - from_row) == 2:
            eaten_row = (from_row + to_row) // 2
            eaten_col = (from_col + to_col) // 2
            eaten_ch = self.pieces[eaten_row, eaten_col]
            move_str += eaten_ch
            self.pieces[eaten_row, eaten_col] = ' '
            if eaten_ch in ('w', 'k'):
                self.white_pieces -= 1
            else:
                self.black_pieces -= 1

        if ch == 'w' and to_row == 0:
            ch = 'k'
        elif ch == 'B' and to_row == 7:
            ch = 'K'

        self.pieces[to_row, to_col] = ch
        self.pieces[from_row, from_col] = ' '
        self.moves.append(f"{move_str}{ch}{to_row}{to_col}")

    def undo_last_move(self) -> None:
        if not self.moves:
            return
        last = self.moves.pop()
        original_ch = last[0]
        from_row, from_col = int(last[1]), int(last[2])

        if len(last) == 6:
            # No capture: {ch}{fr}{fc}{ch_after}{tr}{tc}
            to_row, to_col = int(last[4]), int(last[5])
            self.pieces[from_row, from_col] = original_ch
            self.pieces[to_row, to_col] = ' '
        else:
            # Capture: {ch}{fr}{fc}{eaten_ch}{ch_after}{tr}{tc}
            eaten_ch = last[3]
            to_row, to_col = int(last[5]), int(last[6])
            self.pieces[from_row, from_col] = original_ch
            self.pieces[to_row, to_col] = ' '
            eaten_row = (from_row + to_row) // 2
            eaten_col = (from_col + to_col) // 2
            self.pieces[eaten_row, eaten_col] = eaten_ch
            if eaten_ch in ('w', 'k'):
                self.white_pieces += 1
            else:
                self.black_pieces += 1

    def get_winner(self) -> str | None:
        if self.white_pieces <= 0:
            return 'B'
        if self.black_pieces <= 0:
            return 'W'
        return None
