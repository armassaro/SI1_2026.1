from __future__ import annotations
from board import Board
from piece import Piece
from copy import deepcopy
from random import choice
from typing import Any
import math
import time
from constants import *
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
			get_coloured_message(msg=f"[Minimax Stats] Nós avaliados: {self.nodes_evaluated}", ai=AIEnum.minimax) +
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
			"[MCTS Stats] Iterações: {self.iterations} | "
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
		self.move: dict[str, Any] | None = move  # {"piece_index": int, "position": int, "eats_piece": bool}
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
		for i, piece in enumerate(self.board.get_pieces()):
			if piece.get_color() == self.turn:
				for m in piece.get_moves(self.board):
					moves.append({"piece_index": i, "position": int(m["position"]), "eats_piece": m["eats_piece"]})
		jumps: list[dict[str, Any]] = [m for m in moves if m["eats_piece"]]
		return jumps if jumps else moves

	def is_terminal(self) -> bool:
		return self.board.get_winner() is not None

	def is_fully_expanded(self) -> bool:
		return len(self.untried_moves()) == 0

	def uct_value(self, c: float = 1.41) -> float:
		if self.visits == 0:
			return float('inf')
		return self.wins / self.visits + c * math.sqrt(math.log(self.parent.visits) / self.visits)

	def best_child(self, c: float = 1.41) -> MCTSNode:
		return max(self.children, key=lambda n: n.uct_value(c))

	def expand(self, color_up: str) -> MCTSNode:
		move: dict[str, Any] = self.untried_moves().pop()
		next_board: Board = Board(deepcopy(self.board.get_pieces()), color_up)
		next_board.move_piece(move["piece_index"], move["position"])
		next_turn: str = "B" if self.turn == "W" else "W"
		child: MCTSNode = MCTSNode(next_board, next_turn, parent=self, move=move, depth=self.depth + 1)
		self.children.append(child)
		return child


class MinimaxAI:
	def __init__(self, cpu_color: str) -> None:
		self.color: str = cpu_color
		self.stats: MinimaxStats = MinimaxStats()

	def minimax(self, current_board: Board, is_maximizing: bool, depth: int, turn: str) -> int:
		self.stats.nodes_evaluated += 1
		current_level: int = self.stats._initial_depth - depth
		if current_level > self.stats.max_depth_reached:
			self.stats.max_depth_reached = current_level

		if depth == 0 or current_board.get_winner() is not None:
			return self.get_value(current_board)

		next_turn: str = 'B' if turn == 'W' else 'W'
		board_color_up: str = current_board.get_color_up()
		current_pieces: list[Piece] = current_board.get_pieces()
		piece_moves: list[list[dict[str, Any]] | bool] = list(map(lambda piece: piece.get_moves(current_board) if piece.get_color() == turn else False, current_pieces))

		if is_maximizing:
			maximum: int = -999
			for index, moves in enumerate(piece_moves):
				if moves == False:
					continue

				for move in moves:
					aux_board: Board = Board(deepcopy(current_pieces), board_color_up)
					aux_board.move_piece(index, int(move["position"]))
					maximum = max(self.minimax(aux_board, False, depth - 1, next_turn), maximum)

			return maximum
		else:
			minimum: int = 999
			for index, moves in enumerate(piece_moves):
				if moves == False:
					continue

				for move in moves:
					aux_board: Board = Board(deepcopy(current_pieces), board_color_up)
					aux_board.move_piece(index, int(move["position"]))
					minimum = min(self.minimax(aux_board, True, depth - 1, next_turn), minimum)

			return minimum

	def get_move(self, current_board: Board) -> dict[str, int]:
		board_color_up: str = current_board.get_color_up()
		current_pieces: list[Piece] = current_board.get_pieces()
		next_turn: str = "W" if self.color == "B" else "B"
		player_pieces: list[Piece | bool] = list(map(lambda piece: piece if piece.get_color() == self.color else False, current_pieces))
		possible_moves: list[dict[str, Any]] = []
		move_scores: list[int] = []

		for index, piece in enumerate(player_pieces):
			if piece == False:
				continue

			for move in piece.get_moves(current_board):
				possible_moves.append({"piece": index, "move": move})

		jump_moves: list[dict[str, Any]] = list(filter(lambda move: move["move"]["eats_piece"] == True, possible_moves))

		if len(jump_moves) != 0:
			possible_moves = jump_moves

		self.stats.reset(initial_depth=2)
		for move in possible_moves:
			aux_board: Board = Board(deepcopy(current_pieces), board_color_up)
			aux_board.move_piece(move["piece"], int(move["move"]["position"]))
			move_scores.append(self.minimax(aux_board, False, 2, next_turn))

		best_score: int = max(move_scores)
		self.stats.best_score = best_score
		best_moves: list[dict[str, Any]] = []

		for index, move in enumerate(possible_moves):
			if move_scores[index] == best_score:
				best_moves.append(move)

		move_chosen: dict[str, Any] = choice(best_moves)
		move = {"position_to": move_chosen["move"]["position"], "position_from": player_pieces[move_chosen["piece"]].get_position()}
		print(get_coloured_message("[Minimax] => Nova posição definida!", AIEnum.minimax))
		print(move)
		return move

	def get_value(self, board: Board) -> int:
		board_pieces: list[Piece] = board.get_pieces()

		if board.get_winner() is not None:
			if board_pieces[0].get_color() == self.color:
				return 2
			else:
				return -2

		total_pieces: int = len(board_pieces)
		player_pieces: int = len(list(filter(lambda piece: piece.get_color() == self.color, board_pieces)))
		opponent_pieces: int = total_pieces - player_pieces

		if player_pieces == opponent_pieces:
			return 0

		return 1 if player_pieces > opponent_pieces else -1


class MCTSAI:
	def __init__(self, cpu_color: str) -> None:
		self.color: str = cpu_color
		self.stats: MCTSStats = MCTSStats()

	def mcts(self, current_board: Board, n_iterations: int = 500) -> dict[str, Any]:
		self.stats.reset()
		start: float = time.time()

		root: MCTSNode = MCTSNode(deepcopy(current_board), self.color)
		color_up: str = current_board.get_color_up()

		for _ in range(n_iterations):
			self.stats.iterations += 1

			node: MCTSNode = root
			while not node.is_terminal() and node.is_fully_expanded():
				node = node.best_child()

			if not node.is_terminal() and not node.is_fully_expanded():
				node = node.expand(color_up)
				self.stats.nodes_created += 1
				if node.depth > self.stats.max_tree_depth:
					self.stats.max_tree_depth = node.depth

			result: float = self._rollout(node, color_up)
			self._backpropagate(node, result)

		best: MCTSNode = max(root.children, key=lambda n: n.visits)
		self.stats.elapsed_time = time.time() - start
		self.stats.best_move_visits = best.visits
		self.stats.best_move_win_rate = best.wins / best.visits if best.visits > 0 else 0.0
		return best.move

	def get_move_scores(self, current_board: Board, selected_piece_index: int | None = None, n_iterations: int = 300) -> list[dict[str, Any]]:
		self.stats.reset()
		start: float = time.time()

		root: MCTSNode = MCTSNode(deepcopy(current_board), self.color)
		color_up: str = current_board.get_color_up()

		for _ in range(n_iterations):
			self.stats.iterations += 1

			node: MCTSNode = root
			while not node.is_terminal() and node.is_fully_expanded():
				node = node.best_child()

			if not node.is_terminal() and not node.is_fully_expanded():
				node = node.expand(color_up)
				self.stats.nodes_created += 1
				if node.depth > self.stats.max_tree_depth:
					self.stats.max_tree_depth = node.depth

			result: float = self._rollout(node, color_up)
			self._backpropagate(node, result)

		self.stats.elapsed_time = time.time() - start

		scores: list[dict[str, Any]] = []
		for child in root.children:
			move = child.move
			if move is None:
				continue
			if selected_piece_index is not None and move["piece_index"] != selected_piece_index:
				continue
			piece_pos = int(current_board.get_pieces()[move["piece_index"]].get_position())
			scores.append({
				"from": piece_pos,
				"to": move["position"],
				"win_rate": child.wins / child.visits if child.visits > 0 else 0.0,
				"simulations": child.visits,
			})

		return sorted(scores, key=lambda item: (-item["win_rate"], -item["simulations"]))

	def get_move(self, current_board: Board) -> dict[str, int]:
		move: dict[str, Any] = self.mcts(current_board, n_iterations=2000)
		pieces: list[Piece] = current_board.get_pieces()
		piece_from: Piece = pieces[move["piece_index"]]
		move = {"position_to": move["position"], "position_from": piece_from.get_position()}
		print(get_coloured_message("[MCTS] => Nova posição definida!", AIEnum.MCTS))
		print(move)
		return move

	def _rollout(self, node: MCTSNode, color_up: str, max_steps: int = 64) -> float:
		board: Board = Board(deepcopy(node.board.get_pieces()), color_up)
		turn: str = node.turn

		for _ in range(max_steps):
			winner: str | None = board.get_winner()
			if winner is not None:
				return 1.0 if winner == self.color else 0.0

			moves: list[tuple[int, int, bool]] = []
			for i, piece in enumerate(board.get_pieces()):
				if piece.get_color() == turn:
					for m in piece.get_moves(board):
						moves.append((i, int(m["position"]), m["eats_piece"]))

			jumps: list[tuple[int, int, bool]] = [(i, p, e) for i, p, e in moves if e]
			moves = jumps if jumps else moves

			if not moves:
				break

			chosen: tuple[int, int, bool] = choice(moves)
			board.move_piece(chosen[0], chosen[1])
			turn = "B" if turn == "W" else "W"

		return 0.5

	def _backpropagate(self, node: MCTSNode, result: float) -> None:
		while node is not None:
			node.visits += 1
			if node.turn != self.color:
				node.wins += result
			else:
				node.wins += (1.0 - result)
			node = node.parent
