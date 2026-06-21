from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from board import Board

class Piece:
    def __init__(self, name: str) -> None:
        # Format: <position><color><isKing?> e.g. "16WN"
        self.name: str = name
        self.has_eaten: bool = False

    def get_name(self) -> str:
        return self.name

    def get_position(self) -> str:
        return self.name[:-2]

    def get_color(self) -> str:
        return self.name[-2]

    def is_king(self) -> bool:
        return self.name[-1] == 'Y'

    def get_has_eaten(self) -> bool:
        return self.has_eaten

    def set_position(self, new_position: int | str) -> None:
        split: int = 1 if len(self.name) == 3 else 2
        self.name = str(new_position) + self.name[split:]

    def set_is_king(self, value: bool) -> None:
        self.name = self.name[:-1] + ('Y' if value else 'N')

    def set_has_eaten(self, value: bool) -> None:
        self.has_eaten = value

    def get_adjacent_squares(self, board: Board) -> list[tuple[int, int]]:
        row, col = board.row_col_from_pos(int(self.get_position()))
        return [(m["to_row"], m["to_col"]) for m in board.get_moves(row, col)]

    def get_moves(self, board: Board) -> list[dict]:
        row, col = board.row_col_from_pos(int(self.get_position()))
        result: list[dict] = []
        for m in board.get_moves(row, col):
            pos: int = board.pos_from_row_col(m["to_row"], m["to_col"])
            result.append({"position": str(pos), "eats_piece": m["eats_piece"]})
        return result
