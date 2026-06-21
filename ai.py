from __future__ import annotations
from board import Board
from random import choice
from typing import Any
import math
import time
import numpy as np
from constants import AIEnum
from utils import get_coloured_message


class MinimaxStats:
    def __init__(self) -> None:
        self.nodes_evaluated: int = 0
        self.max_depth_reached: int = 0
        self.elapsed_time: float = 0.0
        self.best_score: int = 0
        self._initial_depth: int = 0

    def reset(self, initial_depth: int) -> None:
        self.nodes_evaluated = 0
        self.max_depth_reached = 0
        self.elapsed_time = 0.0
        self.best_score = 0
        self._initial_depth = initial_depth

    def report(self) -> str:
        return (
            get_coloured_message(f"[Minimax Stats] Nós avaliados: {self.nodes_evaluated}", AIEnum.minimax) +
            f"Profundidade máxima: {self.max_depth_reached} | "
            f"Melhor pontuação: {self.best_score} | "
            f"Tempo: {self.elapsed_time:.4f}s"
        )


class MCTSStats:
    def __init__(self) -> None:
        self.iterations: int = 0
        self.nodes_created: int = 0
        self.max_tree_depth: int = 0
        self.elapsed_time: float = 0.0
        self.best_move_visits: int = 0
        self.best_move_win_rate: float = 0.0
        self.total_rollout_steps: int = 0

    def reset(self) -> None:
        self.iterations = 0
        self.nodes_created = 0
        self.max_tree_depth = 0
        self.elapsed_time = 0.0
        self.best_move_visits = 0
        self.best_move_win_rate = 0.0
        self.total_rollout_steps = 0

    @property
    def avg_rollout_steps(self) -> float:
        return self.total_rollout_steps / self.iterations if self.iterations > 0 else 0.0

    def report(self) -> str:
        return (
            f"[MCTS Stats] Iterações: {self.iterations} | "
            f"Nós criados: {self.nodes_created} | "
            f"Profundidade máxima: {self.max_tree_depth} | "
            f"Visitas ao melhor filho: {self.best_move_visits} | "
            f"Win rate do melhor filho: {self.best_move_win_rate:.2%} | "
            f"Média de passos por rollout: {self.avg_rollout_steps:.1f} | "
            f"Tempo: {self.elapsed_time:.4f}s"
        )


class MCTSNode:
    def __init__(self, board: Board, turn: str, parent: MCTSNode | None = None, move: dict[str, Any] | None = None, depth: int = 0) -> None:
        self.board: Board = board
        self.turn: str = turn
        self.parent: MCTSNode | None = parent
        self.move: dict[str, Any] | None = move
        self.children: list[MCTSNode] = []
        self.wins: float = 0.0
        self.visits: int = 0
        self.depth: int = depth
        self._untried_moves: list[dict[str, Any]] | None = None

    def untried_moves(self) -> list[dict[str, Any]]:
        if self._untried_moves is None:
            self._untried_moves = self._get_legal_moves()
        return self._untried_moves

    def _get_legal_moves(self) -> list[dict[str, Any]]:
        moves: list[dict[str, Any]] = []
        for r, c in self.board.get_pieces():
            if self.board.get_color_at(r, c) == self.turn:
                for m in self.board.get_moves(r, c):
                    moves.append({
                        "from_row": r, "from_col": c,
                        "to_row": m["to_row"], "to_col": m["to_col"],
                        "eats_piece": m["eats_piece"],
                    })
        jumps = [m for m in moves if m["eats_piece"]]
        return jumps if jumps else moves

    def is_terminal(self) -> bool:
        if self.board.get_winner() is not None:
            return True
        return len(self.untried_moves()) == 0 and not self.children

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves()) == 0

    def uct_value(self, c: float) -> float:
        if self.visits == 0:
            return float('inf')
        return self.wins / self.visits + c * math.sqrt(math.log(self.parent.visits) / self.visits)

    def best_child(self, c: float = 1.41) -> MCTSNode:
        return max(self.children, key=lambda n: n.uct_value(c))

    def expand(self, color_up: str) -> MCTSNode:
        move = self.untried_moves().pop()
        next_board = Board(color_up, self.board.pieces.copy())
        next_board.move_piece(move["from_row"], move["from_col"], move["to_row"], move["to_col"])
        next_turn = "B" if self.turn == "W" else "W"
        child = MCTSNode(next_board, next_turn, parent=self, move=move, depth=self.depth + 1)
        self.children.append(child)
        return child


class MinimaxAI:
    def __init__(self, cpu_color: str) -> None:
        self.color: str = cpu_color
        self.stats: MinimaxStats = MinimaxStats()

    def minimax(self, current_board: Board, is_maximizing: bool, depth: int, turn: str) -> int:
        self.stats.nodes_evaluated += 1
        current_level = self.stats._initial_depth - depth
        if current_level > self.stats.max_depth_reached:
            self.stats.max_depth_reached = current_level

        if depth == 0 or current_board.get_winner() is not None:
            return self.get_value(current_board)

        next_turn = 'B' if turn == 'W' else 'W'
        color_up = current_board.get_color_up()
        pieces = current_board.get_pieces()

        all_moves: list[dict[str, Any]] = []
        for r, c in pieces:
            if current_board.get_color_at(r, c) == turn:
                for m in current_board.get_moves(r, c):
                    all_moves.append({"from_row": r, "from_col": c, **m})

        jumps = [m for m in all_moves if m["eats_piece"]]
        all_moves = jumps if jumps else all_moves

        if is_maximizing:
            best = -999
            for move in all_moves:
                aux = Board(color_up, current_board.pieces.copy())
                aux.move_piece(move["from_row"], move["from_col"], move["to_row"], move["to_col"])
                best = max(self.minimax(aux, False, depth - 1, next_turn), best)
            return best
        else:
            best = 999
            for move in all_moves:
                aux = Board(color_up, current_board.pieces.copy())
                aux.move_piece(move["from_row"], move["from_col"], move["to_row"], move["to_col"])
                best = min(self.minimax(aux, True, depth - 1, next_turn), best)
            return best

    def get_move(self, current_board: Board) -> dict[str, int]:
        color_up = current_board.get_color_up()
        next_turn = "W" if self.color == "B" else "B"

        all_moves: list[dict[str, Any]] = []
        for r, c in current_board.get_pieces():
            if current_board.get_color_at(r, c) == self.color:
                for m in current_board.get_moves(r, c):
                    all_moves.append({"from_row": r, "from_col": c, **m})

        jumps = [m for m in all_moves if m["eats_piece"]]
        all_moves = jumps if jumps else all_moves

        self.stats.reset(initial_depth=2)
        scores: list[int] = []
        for move in all_moves:
            aux = Board(color_up, current_board.pieces.copy())
            aux.move_piece(move["from_row"], move["from_col"], move["to_row"], move["to_col"])
            scores.append(self.minimax(aux, False, 2, next_turn))

        best_score = max(scores)
        self.stats.best_score = best_score
        best_moves = [m for m, s in zip(all_moves, scores) if s == best_score]

        chosen = choice(best_moves)
        result = {
            "position_from": Board.pos_from_row_col(chosen["from_row"], chosen["from_col"]),
            "position_to": Board.pos_from_row_col(chosen["to_row"], chosen["to_col"]),
        }
        print(get_coloured_message("[Minimax] => Nova posição definida!", AIEnum.minimax))
        print(f"Posição antiga: {move["from_row"]},{move["from_col"]}")
        print(f"Posição nova: {move["to_row"]},{move["to_col"]}")
        return result

    def get_value(self, board: Board) -> int:
        winner = board.get_winner()
        if winner is not None:
            return 2 if winner == self.color else -2

        if self.color == 'W':
            player, opp = board.white_pieces, board.black_pieces
        else:
            player, opp = board.black_pieces, board.white_pieces

        if player == opp:
            return 0
        return 1 if player > opp else -1


class MCTSAI:
    def __init__(self, cpu_color: str, n_iterations: int = 500, max_steps: int = 64, c: float = 1.41) -> None:
        self.color: str = cpu_color
        self.n_iterations: int = n_iterations
        self.max_steps: int = max_steps
        self.stats: MCTSStats = MCTSStats()
        self.c: float = c

    def _run_mcts(self, current_board: Board, n_iterations: int) -> MCTSNode:
        root = MCTSNode(Board(current_board.get_color_up(), current_board.pieces.copy()), self.color)
        color_up = current_board.get_color_up()

        for _ in range(n_iterations):
            self.stats.iterations += 1
            node = root
            while not node.is_terminal() and node.is_fully_expanded():
                node = node.best_child(self.c)

            if not node.is_terminal() and not node.is_fully_expanded():
                node = node.expand(color_up)
                self.stats.nodes_created += 1
                if node.depth > self.stats.max_tree_depth:
                    self.stats.max_tree_depth = node.depth

            result = self._rollout(node, color_up)
            self._backpropagate(node, result)

        return root

    def mcts(self, current_board: Board) -> dict[str, Any]:
        self.stats.reset()
        start = time.time()
        root = self._run_mcts(current_board, self.n_iterations)
        best = max(root.children, key=lambda n: n.visits)
        self.stats.elapsed_time = time.time() - start
        self.stats.best_move_visits = best.visits
        self.stats.best_move_win_rate = best.wins / best.visits if best.visits > 0 else 0.0
        return best.move

    def get_move_scores(self, current_board: Board, selected_piece_index: int | None = None, n_iterations: int | None = None) -> list[dict[str, Any]]:
        self.stats.reset()
        start = time.time()
        iters = n_iterations if n_iterations is not None else self.n_iterations
        root = self._run_mcts(current_board, iters)
        self.stats.elapsed_time = time.time() - start

        sel_row, sel_col = None, None
        if selected_piece_index is not None:
            pieces_list = current_board.get_pieces()
            if selected_piece_index < len(pieces_list):
                sel_row, sel_col = pieces_list[selected_piece_index]

        scores: list[dict[str, Any]] = []
        for child in root.children:
            move = child.move
            if move is None:
                continue
            if sel_row is not None and (move["from_row"] != sel_row or move["from_col"] != sel_col):
                continue
            scores.append({
                "from": Board.pos_from_row_col(move["from_row"], move["from_col"]),
                "to": Board.pos_from_row_col(move["to_row"], move["to_col"]),
                "win_rate": child.wins / child.visits if child.visits > 0 else 0.0,
                "simulations": child.visits,
            })

        return sorted(scores, key=lambda item: (-item["win_rate"], -item["simulations"]))

    def get_move(self, current_board: Board) -> dict[str, int]:
        move = self.mcts(current_board)
        result = {
            "position_from": Board.pos_from_row_col(move["from_row"], move["from_col"]),
            "position_to": Board.pos_from_row_col(move["to_row"], move["to_col"]),
        }
        print(get_coloured_message("[MCTS] => Nova posição definida!", AIEnum.MCTS))
        print(f"Posição antiga: {move["from_row"]},{move["from_col"]}")
        print(f"Posição nova: {move["to_row"]},{move["to_col"]}")
        return result

    def _rollout(self, node: MCTSNode, color_up: str) -> float:
        board = Board(color_up, node.board.pieces.copy())
        turn = node.turn

        for _ in range(self.max_steps):
            winner = board.get_winner()
            if winner is not None:
                return 1.0 if winner == self.color else 0.0

            moves: list[tuple[int, int, int, int, bool]] = []
            for r, c in board.get_pieces():
                if board.get_color_at(r, c) == turn:
                    for m in board.get_moves(r, c):
                        moves.append((r, c, m["to_row"], m["to_col"], m["eats_piece"]))

            jumps = [(r, c, tr, tc, e) for r, c, tr, tc, e in moves if e]
            moves = jumps if jumps else moves

            if not moves:
                return 0.0 if turn == self.color else 1.0

            fr, fc, tr, tc, _ = choice(moves)
            board.move_piece(fr, fc, tr, tc)
            turn = "B" if turn == "W" else "W"

        return 0.5

    def _backpropagate(self, node: MCTSNode, result: float) -> None:
        while node is not None:
            node.visits += 1
            node.wins += result if node.turn != self.color else (1.0 - result)
            node = node.parent
