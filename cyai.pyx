# cython: boundscheck=False, wraparound=False, cdivision=True, nonecheck=False, language_level=3

from board import Board
from random import choice
from typing import Any
import time
import os
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from libc.math cimport sqrt, log
from constants import AIEnum, EXEC_PARAMS
from utils import get_coloured_message

def _minimax_worker(args):
    cdef int score
    color_up, pieces, depth, is_maximizing, turn, cpu_color = args
    board = Board(color_up, pieces)
    ai = MinimaxAI(cpu_color)
    ai.stats.reset(depth)
    score = ai.minimax(board, is_maximizing, depth, turn)
    return score, ai.stats.nodes_evaluated, ai.stats.max_depth_reached


def _mcts_worker(args):
    color_up, pieces, cpu_color, n_iterations, max_steps, c = args
    board = Board(color_up, pieces)
    ai = MCTSAI(cpu_color, n_iterations, max_steps, c)
    root = ai._run_mcts(board, n_iterations)
    return [(child.move, child.visits, child.wins) for child in root.children]


# ── Stats ──────────────────────────────────────────────────────────────────────

class MinimaxStats:
    def __init__(self):
        self.nodes_evaluated = 0
        self.max_depth_reached = 0
        self.elapsed_time = 0.0
        self.best_score = 0
        self._initial_depth = 0

    def reset(self, initial_depth):
        self.nodes_evaluated = 0
        self.max_depth_reached = 0
        self.elapsed_time = 0.0
        self.best_score = 0
        self._initial_depth = initial_depth

    def report(self):
        return (
            get_coloured_message(f"[Minimax Stats] Nós avaliados: {self.nodes_evaluated}", AIEnum.minimax) +
            f"Profundidade máxima: {self.max_depth_reached} | "
            f"Melhor pontuação: {self.best_score} | "
            f"Tempo: {self.elapsed_time:.4f}s"
        )


class MCTSStats:
    def __init__(self):
        self.iterations = 0
        self.nodes_created = 0
        self.max_tree_depth = 0
        self.elapsed_time = 0.0
        self.best_move_visits = 0
        self.best_move_win_rate = 0.0
        self.total_rollout_steps = 0
        self.nodes_reused = 0

    def reset(self):
        self.iterations = 0
        self.nodes_created = 0
        self.max_tree_depth = 0
        self.elapsed_time = 0.0
        self.best_move_visits = 0
        self.best_move_win_rate = 0.0
        self.total_rollout_steps = 0
        self.nodes_reused = 0

    @property
    def avg_rollout_steps(self):
        return self.total_rollout_steps / self.iterations if self.iterations > 0 else 0.0

    def report(self):
        reuse_str = f"Nós reutilizados: {self.nodes_reused} | " if self.nodes_reused > 0 else ""
        return (
            f"[MCTS Stats] Iterações: {self.iterations} | "
            f"{reuse_str}"
            f"Nós criados: {self.nodes_created} | "
            f"Profundidade máxima: {self.max_tree_depth} | "
            f"Visitas ao melhor filho: {self.best_move_visits} | "
            f"Win rate do melhor filho: {self.best_move_win_rate:.2%} | "
            f"Média de passos por rollout: {self.avg_rollout_steps:.1f} | "
            f"Tempo: {self.elapsed_time:.4f}s"
        )


# ── MCTSNode (cdef class: atributos C-level, UCT e backprop sem overhead Python) ─

cdef class MCTSNode:
    cdef public object board
    cdef public str turn
    cdef public MCTSNode parent
    cdef public object move
    cdef public list children
    cdef public double wins
    cdef public int visits
    cdef public int depth
    cdef list _untried_moves

    def __init__(self, board, str turn, MCTSNode parent=None, object move=None, int depth=0):
        self.board = board
        self.turn = turn
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0.0
        self.visits = 0
        self.depth = depth
        self._untried_moves = None

    cpdef list untried_moves(self):
        if self._untried_moves is None:
            self._untried_moves = self._get_legal_moves()
        return self._untried_moves

    cdef list _get_legal_moves(self):
        cdef list moves = [], jumps
        cdef int r, c
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

    cpdef bint is_terminal(self):
        return self.board.get_winner() is not None or (
            len(self.untried_moves()) == 0 and not self.children
        )

    cpdef bint is_fully_expanded(self):
        return len(self.untried_moves()) == 0

    # cdef: só acessível de C — sem overhead de despacho Python no loop UCT
    cdef double uct_value(self, double c):
        if self.visits == 0:
            return 1.7976931348623157e+308  # proxy para inf
        return (self.wins / self.visits +
                c * sqrt(log(<double>self.parent.visits) / <double>self.visits))

    cpdef MCTSNode best_child(self, double c=1.41):
        cdef MCTSNode node, best_node
        cdef double best_val = -1.7976931348623157e+308
        cdef double val
        for node in self.children:
            val = node.uct_value(c)
            if val > best_val:
                best_val = val
                best_node = node
        return best_node

    def expand(self, str color_up):
        cdef str next_turn
        move = self.untried_moves().pop()
        next_board = Board(color_up, self.board.pieces.copy())
        next_board.move_piece(move["from_row"], move["from_col"], move["to_row"], move["to_col"])
        next_turn = "B" if self.turn == "W" else "W"
        child = MCTSNode(next_board, next_turn, parent=self, move=move, depth=self.depth + 1)
        self.children.append(child)
        return child


# ── MinimaxAI (cdef class: minimax cpdef permite recursão C-level) ─────────────

cdef class MinimaxAI:
    cdef public str color
    cdef public object stats

    def __init__(self, str cpu_color):
        self.color = cpu_color
        self.stats = MinimaxStats()

    # Alpha-beta pruning: reduz busca de O(b^d) para ~O(b^(d/2))
    cpdef int minimax(self, object board, bint is_maximizing, int depth, str turn,
                      int alpha=-999, int beta=999):
        cdef int best, val, current_level
        cdef str next_turn, color_up
        cdef list all_moves, jumps
        cdef int r, c

        self.stats.nodes_evaluated += 1
        current_level = self.stats._initial_depth - depth
        if current_level > self.stats.max_depth_reached:
            self.stats.max_depth_reached = current_level

        if depth == 0 or board.get_winner() is not None:
            return self.get_value(board)

        next_turn = 'B' if turn == 'W' else 'W'
        color_up = board.get_color_up()

        all_moves = []
        for r, c in board.get_pieces():
            if board.get_color_at(r, c) == turn:
                for m in board.get_moves(r, c):
                    all_moves.append({"from_row": r, "from_col": c, **m})

        jumps = [m for m in all_moves if m["eats_piece"]]
        if jumps:
            all_moves = jumps

        if is_maximizing:
            best = -999
            for move in all_moves:
                aux = Board(color_up, board.pieces.copy())
                aux.move_piece(move["from_row"], move["from_col"], move["to_row"], move["to_col"])
                val = self.minimax(aux, False, depth - 1, next_turn, alpha, beta)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if beta <= alpha:
                    break
            return best
        else:
            best = 999
            for move in all_moves:
                aux = Board(color_up, board.pieces.copy())
                aux.move_piece(move["from_row"], move["from_col"], move["to_row"], move["to_col"])
                val = self.minimax(aux, True, depth - 1, next_turn, alpha, beta)
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if beta <= alpha:
                    break
            return best

    def get_move(self, current_board):
        cdef int best_score, depth
        _cfg = EXEC_PARAMS["minimax"]
        depth = _cfg["depth"]
        color_up = current_board.get_color_up()
        next_turn = "W" if self.color == "B" else "B"

        all_moves = []
        for r, c in current_board.get_pieces():
            if current_board.get_color_at(r, c) == self.color:
                for m in current_board.get_moves(r, c):
                    all_moves.append({"from_row": r, "from_col": c, **m})

        jumps = [m for m in all_moves if m["eats_piece"]]
        if jumps:
            all_moves = jumps

        self.stats.reset(depth)
        start = time.time()

        worker_args = []
        for move in all_moves:
            aux = Board(color_up, current_board.pieces.copy())
            aux.move_piece(move["from_row"], move["from_col"], move["to_row"], move["to_col"])
            worker_args.append((color_up, aux.pieces.copy(), depth, False, next_turn, self.color))

        if _cfg["threaded"]:
            with ProcessPoolExecutor(max_workers=_cfg["max_workers"]) as executor:
                results = list(executor.map(_minimax_worker, worker_args))
        else:
            results = [_minimax_worker(args) for args in worker_args]

        scores = [r[0] for r in results]
        self.stats.nodes_evaluated = sum(r[1] for r in results)
        self.stats.max_depth_reached = max((r[2] for r in results), default=0)
        self.stats.elapsed_time = time.time() - start

        best_score = max(scores)
        self.stats.best_score = best_score
        best_moves = [m for m, s in zip(all_moves, scores) if s == best_score]

        chosen = choice(best_moves)
        result = {
            "position_from": Board.pos_from_row_col(chosen["from_row"], chosen["from_col"]),
            "position_to": Board.pos_from_row_col(chosen["to_row"], chosen["to_col"]),
        }
        print(get_coloured_message("[Minimax] => Nova posição definida!", AIEnum.minimax))
        print(f"Posição antiga: {chosen['from_row']},{chosen['from_col']}")
        print(f"Posição nova: {chosen['to_row']},{chosen['to_col']}")
        return result

    cpdef int get_value(self, object board):
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


# ── MCTSAI (cdef class: rollout e backprop C-level) ────────────────────────────

cdef class MCTSAI:
    cdef public str color
    cdef public int n_iterations
    cdef public int max_steps
    cdef public object stats
    cdef public double c
    cdef public MCTSNode _saved_root

    def __init__(self, str cpu_color, int n_iterations=500, int max_steps=64, double c=1.41):
        self.color = cpu_color
        self.n_iterations = n_iterations
        self.max_steps = max_steps
        self.stats = MCTSStats()
        self.c = c
        self._saved_root = None

    cpdef MCTSNode _try_reuse_root(self, object current_board):
        cdef MCTSNode child
        if self._saved_root is None:
            return None
        for child in self._saved_root.children:
            if np.array_equal(child.board.pieces, current_board.pieces):
                child.parent = None
                return child
        return None

    cpdef MCTSNode _run_mcts(self, object current_board, int n_iterations, MCTSNode root=None):
        cdef MCTSNode node
        cdef double result
        cdef str color_up = current_board.get_color_up()

        if root is None:
            root = MCTSNode(Board(color_up, current_board.pieces.copy()), self.color)

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

    def _parallel_mcts(self, current_board, int n_iterations):
        cdef int n_workers = min(os.cpu_count() or 4, n_iterations)
        cdef int iters_per_worker = n_iterations // n_workers
        color_up = current_board.get_color_up()

        args = [(color_up, current_board.pieces.copy(), self.color,
                 iters_per_worker, self.max_steps, self.c)] * n_workers

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            all_children = list(executor.map(_mcts_worker, args))

        move_stats = {}
        for worker_children in all_children:
            for move, visits, wins in worker_children:
                if move is None:
                    continue
                key = (move["from_row"], move["from_col"], move["to_row"], move["to_col"])
                if key not in move_stats:
                    move_stats[key] = {"move": move, "visits": 0, "wins": 0.0}
                move_stats[key]["visits"] += visits
                move_stats[key]["wins"] += wins

        self.stats.iterations = n_workers * iters_per_worker
        return move_stats

    def mcts(self, current_board):
        cdef MCTSNode reused, root, best_child
        self.stats.reset()
        start = time.time()

        reused = self._try_reuse_root(current_board)
        if reused is not None:
            self.stats.nodes_reused = reused.visits

        root = self._run_mcts(current_board, self.n_iterations, reused)

        best_child = max(root.children, key=lambda n: n.visits)

        self._saved_root = best_child
        self._saved_root.parent = None

        self.stats.elapsed_time = time.time() - start
        self.stats.best_move_visits = best_child.visits
        self.stats.best_move_win_rate = best_child.wins / best_child.visits if best_child.visits > 0 else 0.0
        return best_child.move

    def get_move_scores(self, current_board, selected_piece_index=None, n_iterations=None):
        self.stats.reset()
        start = time.time()
        iters = n_iterations if n_iterations is not None else self.n_iterations
        move_stats = self._parallel_mcts(current_board, iters)
        self.stats.elapsed_time = time.time() - start

        sel_row, sel_col = None, None
        if selected_piece_index is not None:
            pieces_list = current_board.get_pieces()
            if selected_piece_index < len(pieces_list):
                sel_row, sel_col = pieces_list[selected_piece_index]

        scores = []
        for data in move_stats.values():
            move = data["move"]
            if sel_row is not None and (move["from_row"] != sel_row or move["from_col"] != sel_col):
                continue
            scores.append({
                "from": Board.pos_from_row_col(move["from_row"], move["from_col"]),
                "to": Board.pos_from_row_col(move["to_row"], move["to_col"]),
                "win_rate": data["wins"] / data["visits"] if data["visits"] > 0 else 0.0,
                "simulations": data["visits"],
            })

        return sorted(scores, key=lambda item: (-item["win_rate"], -item["simulations"]))

    def get_move(self, current_board):
        move = self.mcts(current_board)
        result = {
            "position_from": Board.pos_from_row_col(move["from_row"], move["from_col"]),
            "position_to": Board.pos_from_row_col(move["to_row"], move["to_col"]),
        }
        print(get_coloured_message("[MCTS] => Nova posição definida!", AIEnum.MCTS))
        print(f"Posição antiga: {move['from_row']},{move['from_col']}")
        print(f"Posição nova: {move['to_row']},{move['to_col']}")
        return result

    # cdef: chamado apenas internamente — despacho C-level puro
    cpdef double _rollout(self, MCTSNode node, str color_up):
        cdef int step
        cdef str turn = node.turn
        cdef list moves, jumps

        board = Board(color_up, node.board.pieces.copy())

        for step in range(self.max_steps):
            winner = board.get_winner()
            if winner is not None:
                return 1.0 if winner == self.color else 0.0

            moves = []
            for r, c in board.get_pieces():
                if board.get_color_at(r, c) == turn:
                    for m in board.get_moves(r, c):
                        moves.append((r, c, m["to_row"], m["to_col"], m["eats_piece"]))

            jumps = [t for t in moves if t[4]]
            if jumps:
                moves = jumps

            if not moves:
                return 0.0 if turn == self.color else 1.0

            fr, fc, tr, tc, _ = choice(moves)
            board.move_piece(fr, fc, tr, tc)
            turn = "B" if turn == "W" else "W"

        return 0.5

    cdef void _backpropagate(self, MCTSNode node, double result):
        while node is not None:
            node.visits += 1
            node.wins += result if node.turn != self.color else (1.0 - result)
            node = node.parent
