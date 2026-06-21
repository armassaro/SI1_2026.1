from __future__ import annotations
from typing import TYPE_CHECKING
from utils import get_piece_gui_coords, get_piece_rc
import pygame

if TYPE_CHECKING:
    from board import Board

BLACK_PIECE_SURFACE = pygame.image.load("images/black_piece.png")
WHITE_PIECE_SURFACE = pygame.image.load("images/white_piece.png")
BLACK_KING_PIECE_SURFACE = pygame.image.load("images/black_king_piece.png")
WHITE_KING_PIECE_SURFACE = pygame.image.load("images/white_king_piece.png")
MOVE_MARK = pygame.image.load("images/marking.png")
BOARD_SURFACE = pygame.image.load("images/board.png")

BOARD_POSITION = (26, 26)
TOPLEFTBORDER = (34, 34)
SQUARE_DIST = 56

class BoardGUI:
    def __init__(self, board: Board) -> None:
        self.pieces: list[dict] = self.get_piece_properties(board)
        self.hidden_piece: tuple[int, int] | None = None
        self.move_marks: list[pygame.Rect] = []

    def set_pieces(self, piece_list: list[dict]) -> None:
        self.pieces = piece_list

    def get_piece_properties(self, board: Board) -> list[dict]:
        pieces: list[dict] = []
        for row, col in board.get_pieces():
            pieces.append({
                "rect": pygame.Rect(get_piece_gui_coords((row, col), SQUARE_DIST, TOPLEFTBORDER), (41, 41)),
                "color": board.get_color_at(row, col),
                "is_king": board.is_king_at(row, col),
                "row": row,
                "col": col,
            })
        return pieces

    def get_piece_on_mouse(self, mouse_pos: tuple[int, int]) -> dict | None:
        for piece in self.pieces:
            if piece["rect"].collidepoint(mouse_pos):
                return piece
        return None

    def get_piece_rect(self, row: int, col: int) -> pygame.Rect | None:
        for piece in self.pieces:
            if piece["row"] == row and piece["col"] == col:
                return piece["rect"]
        return None

    def hide_piece(self, row: int, col: int) -> None:
        self.hidden_piece = (row, col)

    def show_piece(self) -> tuple[int, int] | None:
        rc = self.hidden_piece
        self.hidden_piece = None
        return rc

    def get_surface(self, row: int, col: int) -> pygame.Surface:
        for piece in self.pieces:
            if piece["row"] == row and piece["col"] == col:
                if piece["is_king"]:
                    return BLACK_KING_PIECE_SURFACE if piece["color"] == "B" else WHITE_KING_PIECE_SURFACE
                return BLACK_PIECE_SURFACE if piece["color"] == "B" else WHITE_PIECE_SURFACE
        return BLACK_PIECE_SURFACE

    def draw_pieces(self, display_surface: pygame.Surface) -> None:
        for piece in self.pieces:
            if self.hidden_piece == (piece["row"], piece["col"]):
                continue
            if piece["is_king"]:
                surface = BLACK_KING_PIECE_SURFACE if piece["color"] == "B" else WHITE_KING_PIECE_SURFACE
            else:
                surface = BLACK_PIECE_SURFACE if piece["color"] == "B" else WHITE_PIECE_SURFACE
            display_surface.blit(surface, piece["rect"])

    def draw_board(self, display_surface: pygame.Surface) -> None:
        display_surface.blit(BOARD_SURFACE, BOARD_POSITION)
        for rect in self.move_marks:
            display_surface.blit(MOVE_MARK, rect)

    def get_move_marks(self) -> list[pygame.Rect]:
        return self.move_marks

    def set_move_marks(self, position_list: list[tuple[int, int]]) -> None:
        self.move_marks = [
            pygame.Rect(get_piece_gui_coords((row, col), SQUARE_DIST, TOPLEFTBORDER), (44, 44))
            for row, col in position_list
        ]

    def get_position_by_rect(self, rect: pygame.Rect) -> tuple[int, int]:
        return get_piece_rc((rect.x, rect.y), SQUARE_DIST, TOPLEFTBORDER)
