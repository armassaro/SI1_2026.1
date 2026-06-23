from __future__ import annotations
import datetime
import os
from constants import EXEC_PARAMS
from board import Board
from board_gui import BoardGUI
from held_piece import HeldPiece
if EXEC_PARAMS["cython"]:
    from cyai import MinimaxAI, MCTSAI, AIEnum
    print("Utilizando Cython!")
else:
    from ai import MinimaxAI, MCTSAI, AIEnum

from utils import get_surface_mouse_offset

class GameControl:
    def __init__(self, player_color: str, is_computer_opponent: bool, cpu_algoritmo: AIEnum, human_mcts_enabled: bool = False, cpu_vs_cpu: bool = False) -> None:
        self.turn: str = player_color
        self.winner: str | None = None
        self.no_capture_count: int = 0
        self.NO_CAPTURE_LIMIT: int = EXEC_PARAMS["no_capture_limit"]
        self.board: Board | None = None
        self.board_draw: BoardGUI | None = None
        self.held_piece: HeldPiece | None = None
        self.ai_control: MinimaxAI | MCTSAI | None = None
        self.human_mcts_enabled: bool = human_mcts_enabled
        self.human_mcts_ai: MCTSAI | None = (
            MCTSAI(player_color, n_iterations=EXEC_PARAMS["human_mcts"]["n_iterations"],
                   max_steps=EXEC_PARAMS["human_mcts"]["max_steps"], c=EXEC_PARAMS["human_mcts"]["c"])
            if human_mcts_enabled else None
        )
        self.cpu_vs_cpu: bool = cpu_vs_cpu
        self.ai_pretas: MinimaxAI | None = None
        self.ai_brancas: MCTSAI | None = None
        self.move_log: list[dict] = []
        self.last_minimax_snap: dict | None = None
        self.last_mcts_snap: dict | None = None
        self._log_written: bool = False

        if is_computer_opponent:
            cpu_color: str = "B" if player_color == "W" else "W"
            self.ai_control = (
                MCTSAI(cpu_color, n_iterations=EXEC_PARAMS["mcts"]["n_iterations"],
                       max_steps=EXEC_PARAMS["mcts"]["max_steps"], c=EXEC_PARAMS["mcts"]["c"])
                if cpu_algoritmo == AIEnum.MCTS else MinimaxAI(cpu_color)
            )
        elif cpu_vs_cpu:
            self.ai_pretas = MinimaxAI("B")
            self.ai_brancas = MCTSAI(
                "W",
                n_iterations=EXEC_PARAMS["mcts"]["n_iterations"],
                max_steps=EXEC_PARAMS["mcts"]["max_steps"],
                c=EXEC_PARAMS["mcts"]["c"]
            )

        self.setup()

    def get_turn(self) -> str:
        return self.turn

    def get_winner(self) -> str | None:
        return self.winner

    def get_last_minimax_snap(self) -> dict | None:
        return self.last_minimax_snap

    def get_last_mcts_snap(self) -> dict | None:
        return self.last_mcts_snap

    @staticmethod
    def _snap_minimax(ai) -> dict:
        s = ai.stats
        return {
            'nodes_evaluated': s.nodes_evaluated,
            'max_depth_reached': s.max_depth_reached,
            'elapsed_time': s.elapsed_time,
            'best_score': s.best_score,
        }

    @staticmethod
    def _snap_mcts(ai) -> dict:
        s = ai.stats
        return {
            'iterations': s.iterations,
            'nodes_created': s.nodes_created,
            'max_tree_depth': s.max_tree_depth,
            'elapsed_time': s.elapsed_time,
            'best_move_visits': s.best_move_visits,
            'best_move_win_rate': s.best_move_win_rate,
            'avg_rollout_steps': s.avg_rollout_steps,
            'nodes_reused': s.nodes_reused,
        }

    def write_game_log(self) -> None:
        if self._log_written:
            return
        self._log_written = True
        os.makedirs("log", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"log/game_{ts}.log"
        winner_map = {'W': 'Brancas venceram', 'B': 'Pretas venceram', 'empate': 'Empate'}
        winner_text = winner_map.get(self.winner or '', f'desconhecido ({self.winner})')
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Jogo de Damas — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Resultado: {winner_text}\n")
            f.write(f"Total de jogadas: {len(self.move_log)}\n\n")
            for i, entry in enumerate(self.move_log, 1):
                f.write(f"--- Jogada {i} ({entry['color']}) ---\n")
                if 'minimax' in entry:
                    s = entry['minimax']
                    f.write(
                        f"  [Minimax] Nós: {s['nodes_evaluated']} | Prof.: {s['max_depth_reached']} | "
                        f"Score: {s['best_score']} | Tempo: {s['elapsed_time']:.4f}s\n"
                    )
                if 'mcts' in entry:
                    s = entry['mcts']
                    f.write(
                        f"  [MCTS] Iterações: {s['iterations']} | Nós criados: {s['nodes_created']} | "
                        f"Prof. máx: {s['max_tree_depth']} | Visitas ao melhor: {s['best_move_visits']} | "
                        f"WR: {s['best_move_win_rate']:.2%} | Média passos/rollout: {s['avg_rollout_steps']:.1f} | "
                        f"Reutilizados: {s['nodes_reused']} | Tempo: {s['elapsed_time']:.4f}s\n"
                    )
            f.write(f"\nFim de jogo. Resultado: {winner_text}\n")

    # Esse método é chamado após cada jogada, para atualizar o contador de jogadas sem captura e verificar se a partida deve ser declarada empate.
    def _registrar_resultado_jogada(self, was_eating: bool) -> None:
        if was_eating:
            self.no_capture_count = 0
        else:
            self.no_capture_count += 1
            if self.no_capture_count >= self.NO_CAPTURE_LIMIT and self.winner is None:
                self.winner = "empate"

    # verificar se o jogador da vez tem movimentos disponiveis; se nao tiver, declarar o adversario vencedor
    def _verificar_sem_movimentos(self) -> None:
        if self.winner is not None:
            return

        tem_movimento_disponivel: bool = any(
            self.board.get_moves(r, c)
            for r, c in self.board.get_pieces()
            if self.board.get_color_at(r, c) == self.turn
        )

        if not tem_movimento_disponivel:
            self.winner = "B" if self.turn == "W" else "W"

    def setup(self) -> None:
        self.board = Board(self.turn)
        self.board_draw = BoardGUI(self.board)

    def draw_screen(self, display_surface: object) -> None:
        self.board_draw.draw_board(display_surface)
        self.board_draw.draw_pieces(display_surface)
        if self.held_piece is not None:
            self.held_piece.draw_piece(display_surface)

    def hold_piece(self, mouse_pos: tuple[int, int]) -> list | None:
        piece_clicked = self.board_draw.get_piece_on_mouse(mouse_pos)
        if piece_clicked is None or piece_clicked["color"] != self.turn:
            return

        from_row, from_col = piece_clicked["row"], piece_clicked["col"]
        piece_moves: list[dict] = self.board.get_moves(from_row, from_col)

        has_jump_restraint: bool = any(
            m["eats_piece"]
            for r, c in self.board.get_pieces()
            if self.board.get_color_at(r, c) == self.turn
            for m in self.board.get_moves(r, c)
        )

        if has_jump_restraint:
            piece_moves = [m for m in piece_moves if m["eats_piece"]]

        if not piece_moves:
            return

        self.board_draw.set_move_marks([(m["to_row"], m["to_col"]) for m in piece_moves])
        self.board_draw.hide_piece(from_row, from_col)
        self._set_held_piece(from_row, from_col, mouse_pos)

        if self.human_mcts_enabled:
            return self.get_move_scores(from_row, from_col)

    def release_piece(self) -> None:
        if self.held_piece is None:
            return

        position_released = self.held_piece.check_collision(self.board_draw.get_move_marks())
        from_rc: tuple[int, int] | None = self.board_draw.show_piece()

        if position_released is not None and from_rc is not None:
            from_row, from_col = from_rc
            to_row, to_col = self.board_draw.get_position_by_rect(position_released)
            self.board.move_piece(from_row, from_col, to_row, to_col)
            self.board_draw.set_pieces(self.board_draw.get_piece_properties(self.board))
            self.winner = self.board.get_winner()

            was_eating: bool = abs(to_row - from_row) == 2
            can_eat_again: bool = any(m["eats_piece"] for m in self.board.get_moves(to_row, to_col))
            self._registrar_resultado_jogada(was_eating)

            if not (was_eating and can_eat_again):
                self.turn = "B" if self.turn == "W" else "W"
                self._verificar_sem_movimentos()

        self.held_piece = None
        self.board_draw.set_move_marks([])

    def _set_held_piece(self, row: int, col: int, mouse_pos: tuple[int, int]) -> None:
        surface = self.board_draw.get_surface(row, col)
        rect = self.board_draw.get_piece_rect(row, col)
        offset = get_surface_mouse_offset((rect.x, rect.y), mouse_pos)
        self.held_piece = HeldPiece(surface, offset)

    def get_move_scores(self, row: int, col: int, n_iterations: int = EXEC_PARAMS["human_mcts"]["n_iterations"]) -> list:
        if not self.human_mcts_enabled or self.human_mcts_ai is None:
            return []
        piece_index = next(
            (i for i, (r, c) in enumerate(self.board.get_pieces()) if r == row and c == col),
            None
        )
        if piece_index is None:
            return []
        return self.human_mcts_ai.get_move_scores(self.board, selected_piece_index=piece_index, n_iterations=n_iterations)

    def move_ai(self) -> None:
        if self.turn == "W" or self.ai_control is None:
            return

        turn_color = self.turn
        optimal_move: dict = self.ai_control.get_move(self.board)

        if type(self.ai_control).__name__ == 'MinimaxAI':
            snap = self._snap_minimax(self.ai_control)
            self.last_minimax_snap = snap
            self.move_log.append({'color': turn_color, 'minimax': snap})
        else:
            snap = self._snap_mcts(self.ai_control)
            self.last_mcts_snap = snap
            self.move_log.append({'color': turn_color, 'mcts': snap})

        from_pos: int = int(optimal_move["position_from"])
        to_pos: int = int(optimal_move["position_to"])
        from_row, from_col = Board.row_col_from_pos(from_pos)
        to_row, to_col = Board.row_col_from_pos(to_pos)

        self.board.move_piece(from_row, from_col, to_row, to_col)
        self.board_draw.set_pieces(self.board_draw.get_piece_properties(self.board))
        self.winner = self.board.get_winner()

        was_eating: bool = abs(to_row - from_row) == 2
        can_eat_again: bool = any(m["eats_piece"] for m in self.board.get_moves(to_row, to_col))
        self._registrar_resultado_jogada(was_eating)

        if not (was_eating and can_eat_again):
            self.turn = "B" if self.turn == "W" else "W"
            self._verificar_sem_movimentos()

    def move_ai_cpu_vs_cpu(self) -> None:
        if self.winner is not None:
            return

        turn_color = self.turn
        ai_atual: MinimaxAI | MCTSAI = self.ai_pretas if turn_color == "B" else self.ai_brancas
        optimal_move: dict = ai_atual.get_move(self.board)

        if turn_color == "B":
            snap = self._snap_minimax(ai_atual)
            self.last_minimax_snap = snap
            self.move_log.append({'color': turn_color, 'minimax': snap})
        else:
            snap = self._snap_mcts(ai_atual)
            self.last_mcts_snap = snap
            self.move_log.append({'color': turn_color, 'mcts': snap})

        from_pos: int = int(optimal_move["position_from"])
        to_pos: int = int(optimal_move["position_to"])
        from_row, from_col = Board.row_col_from_pos(from_pos)
        to_row, to_col = Board.row_col_from_pos(to_pos)

        self.board.move_piece(from_row, from_col, to_row, to_col)
        self.board_draw.set_pieces(self.board_draw.get_piece_properties(self.board))
        self.winner = self.board.get_winner()

        was_eating: bool = abs(to_row - from_row) == 2
        can_eat_again: bool = any(m["eats_piece"] for m in self.board.get_moves(to_row, to_col))
        self._registrar_resultado_jogada(was_eating)

        if not (was_eating and can_eat_again):
            self.turn = "B" if self.turn == "W" else "W"
            self._verificar_sem_movimentos()