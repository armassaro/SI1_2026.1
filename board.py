from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from constants import BOARD

if TYPE_CHECKING:
    from piece import Piece

class Board:
    def __init__(self, color_up:str, pieces: np.ndarray=BOARD, moves:list[str]=[]) -> None:
        # Example: [Piece('12WND'), Piece('14BNU'), Piece('24WYD')]
        # self.pieces: np.ndarray = np.array(pieces, dtype=object)
        self.pieces:np.ndarray = np.ndarray(pieces, dtype="U1")
        self.color_up: str = color_up # Defines which of the colors is moving up
        # Lista de strings que contém todas as jogadas feitas em formato de string para fácil manipulação
        self.moves:list[str] = moves # "K/B/k/w12K/B/k/w23"
        self.white_pieces:int = 12
        self.black_pieces:int = 12

    def get_color_up(self) -> str:
        return self.color_up

    def get_pieces(self) -> np.ndarray:
        return self.pieces

    def get_piece_by_index(self, row:int, col:int) -> str:
        return self.pieces[row][col]

    def has_piece(self, row:int, col:int) -> bool:
        return not not self.pieces[row][col]

    # Função a ser removida
    def get_row_number(self, position: int) -> int:
        # Receives position (e.g.: 1), returns the row this position is on the board.
        return position // 4

    # Função a ser removida
    def get_col_number(self, position: int) -> int:
        # There are four dark squares on each row where pieces can be placed.
        # The remainder of (position / 4) can be used to determine which of the four squares has the position.
        # We also take into account that odd rows on the board have a offset of 1 column.
        remainder: int = position % 4
        column_position: int = remainder * 2 # because the squares have a gap of one light square.
        is_row_odd: bool = not (self.get_row_number(position) % 2 == 0)
        return column_position + 1 if is_row_odd else column_position

    def get_row(self, row: int) -> set[Piece]:
        # Receives a row number, returns a set with all pieces contained in it.
        # [0, 1, 2, 3] represents the first row of the board. All rows contain four squares.
        # row_pos needs to contain strings on it because Piece.get_position() returns a number in type string.
        return set(self.pieces[row])

    def get_pieces_by_coords(self, *coords: list[int, int]) -> np.ndarray:
        # Receives a variable number of (row, column) pairs.
        # Returns a ordered list of same length with a Piece if found, otherwise None.
        row_memory: dict[int, set[Piece]] = dict() # Used to not have to keep calling get_row().
        results: list[Piece] = []

        for coord_pair in coords:
            if coord_pair[0] in row_memory:
                current_row: set[Piece] = row_memory[coord_pair[0]]
            else:
                current_row = self.get_row(coord_pair[0])
                row_memory[coord_pair[0]] = current_row

            for piece in current_row:
                if self.get_col_number(int(piece.get_position())) == coord_pair[1]:
                    results.append(piece)
                    break
            else:
                # This runs if 'break' isn't called on the for loop above.
                results.append(None)
        np.array()
        return results

    # Calcula a posição da peça que foi comida
    def get_eaten_index(old_position: list[int,int], new_position: list[int,int]) -> list[int,int]:
            x:int = new_position[0] - old_position[0]
            y:int = new_position[1] - old_position[1]
            eaten_index:list[int,int] = [0,0]

            if x < 0:
                eaten_index[0] = old_position[0] - 1
            else:
                eaten_index[0] = old_position[0] + 1

            if y < 0: 
                eaten_index[1] = old_position[1] - 1
            else:
                eaten_index[1] = old_position[1] + 1

            return eaten_index
    
    # Move uma peça de uma posição para outra
    def move_piece(self, old_position:list[int, int], new_position: list[int, int]) -> None:
        def is_king_movement(new_position:list[int,int]) -> bool:
            # Receives the piece moving and returns True if the move turns that piece into a king.
            return True if new_position[0] == 7 or new_position[0] == 0 else False
        move_str:str = ""
        piece_to_move:str = self.pieces[old_position[0]][old_position[1]]
        move_str = f"{piece_to_move}{old_position[0]}{old_position[1]}"

        # Delete piece from the board if this move eats another piece
        # If the difference in the rows of the current and next positions isn't 1, i.e. if the piece isn't moving one square,
        # then the piece is eating another piece.
        if abs(old_position[0] - new_position[1]) != 1:
            # self.pieces = np.delete(self.pieces, get_eaten_index(old_position, new_position))
            eaten_index:list[int,int] = get_eaten_index(new_position)
            # Adiciona a informação de captura de peça na string de movimentos
            move_str += f"{self.pieces[eaten_index[0]][eaten_index[1]]}"
            # Some com a peça
            self.pieces[eaten_index[0]][eaten_index[1]] = ""
            # Não entendi porque salvar essa informação, ent vou só comentar aqui
            # piece_to_move.set_has_eaten(True)
        # else:
            # piece_to_move.set_has_eaten(False)

        # Turn piece into a king if it reaches the other side of the board
        if is_king_movement(piece_to_move):
            # K = rei preto, k = rei branco
            piece_to_move = "K" if piece_to_move == "B" else "k"

        # Actually move
        self.pieces[new_position[0]][new_position[1]] = piece_to_move
        # piece_to_move.set_position(new_position)

        # Adiciona o último movimento feito à lista de strings
        self.moves.append(f"{move_str}{piece_to_move}{new_position[0]}{piece_to_move[1]}")

    # Desfaz o último movimento presente no topo da lista de movimentos do tabuleiro
    def undo_last_move(self) -> None:
        last_move:str = self.moves.pop()
        last_move_len:int = last_move.__len__()
        old_position:list[int,int] = [int(last_move[1]), int(last_move[2])]
        new_position:list[int,int]
        
        # Se a string de movimento for 6, o último movimento não capturou uma peça
        # Se tiver tamanho 7, o último movimento capturou uma peça 
        match last_move_len:
            case 6:
                # Pega as novas posições baseado no tamanho da string
                new_position = [int(last_move[4]), int(last_move[5])]
                # Retrocede a peça que se moveu para a posição original
                self.pieces[old_position[0]][old_position[1]] = last_move[0]
                # Esvazia a peça que foi movida da posição nova
                self.pieces[new_position[0]][new_position[1]] = ""
            case 7:
                # Pega as novas posições baseado no tamanho da string
                new_position = [int(last_move[5]), int(last_move[6])]
                # Retrocede a peça que se moveu para a posição original
                self.pieces[old_position[0]][old_position[1]] = last_move[0]
                # Calcula a posição da peça que foi comida
                eaten_piece_position = self.get_eaten_index(old_position, new_position)
                # Retorna a peça que foi comida ao tabuleiro
                self.pieces[eaten_piece_position[0]][eaten_piece_position[1]] = last_move[3]
                # Esvazia a peça que foi movida da posição nova
                self.pieces[new_position[0]][new_position[1]] = ""
                if last_move[3] == 'w' or last_move[3] == 'k':
                    self.white_pieces += 1
                else:
                    self.black_pieces += 1

    # Retorna W (white) ou B (black) ou None caso não houver ganhadores
    def get_winner(self) -> str | None:
        # # Returns the winning color or None if no player has won yet
        # current_color: str = self.pieces[0].get_color()

        # for piece in self.pieces:
        #     if piece.get_color() != current_color:
        #         break
        # else:
        #     return current_color

        # return None
        return "W" if self.white_pieces <= 0 else "B" if self.black_pieces <= 0 else None