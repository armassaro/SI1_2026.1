from __future__ import annotations
from board import Board
from piece import Piece
from copy import deepcopy
from random import choice
from typing import Any
from libc.string cimport strcpy, strlen
from libc.stdlib cimport malloc, free
from libc.math cimport log, sqrt
from libc.stdint cimport u_int_8

cdef class MCTSNode:
	# Tem que saber ainda como é recebido esse tipo Board
	cdef Board board
	cdef char* turn
	cdef MCTSNode parent
	cdef MCTSNode** children
	cdef u_int_8 wins
	cdef u_int_8 visits
	cdef dict[str, {"piece_index": int, "position": int, "eats_piece": bool}] move

	def __init__(self, Board board, char* turn, MCTSNode parent, dict[str, {"piece_index": int, "position": int, "eats_piece": bool}] move) -> None:
		self.board: Board = board
		self.turn: str = turn
		self.parent: MCTSNode | None = parent
		self.move: dict[str, Any] | None = move  # {"piece_index": int, "position": int, "eats_piece": bool}
		self.children: list[MCTSNode] = []
		self.wins: float = 0.0
		self.visits: int = 0
		self._untried_moves: list[dict[str, Any]] | None = None

	# Retorna todos os movimentos não feitos considerando o tabuleiro atual
	def untried_moves(self) -> list[dict[str, Any]]:
		if self._untried_moves is None:
			self._untried_moves = self._get_legal_moves()
		return self._untried_moves

	# Obtém todos os movimentos possíveis de se fazer no tabuleiro atual
	def _get_legal_moves(self) -> list[dict[str, Any]]:
		moves: list[dict[str, Any]] = []
		for i, piece in enumerate(self.board.get_pieces()):
			if piece.get_color() == self.turn:
				for m in piece.get_moves(self.board):
					moves.append({"piece_index": i, "position": int(m["position"]), "eats_piece": m["eats_piece"]})
		jumps: list[dict[str, Any]] = [m for m in moves if m["eats_piece"]]
		return jumps if jumps else moves

	# Determina se o jogo já possui um vencedor
	def is_terminal(self) -> bool:
		return self.board.get_winner() is not None

	# Determina se a árvore já foi expandida ao máximo
	def is_fully_expanded(self) -> bool:
		return len(self.untried_moves()) == 0

	# Aqui é o coração do MCTS, essa fórmula estabelece uma relação entre o número de vitórias e o número de visitas, 
	# providenciando um coeficiente que representa o quão confiável é um nó. 
	# Quanto maior esse coeficiente, mais confiável o nó é para escolha. 
	def uct_value(self, c: float = 1.41) -> float:
		# if self.visits == 0:
		# 	return float('inf')
		return self.wins / self.visits + c * sqrt(log(self.parent.visits) / self.visits)

	# Seleciona o melhor nó filho com base na política de escolha de nós
	def best_child(self, c: float = 1.41) -> MCTSNode:
		return max(self.children, key=lambda n: n.uct_value(c))

	# Cria-se um novo nó a partir de um nó pai com um novo movimento
	def expand(self, color_up: str) -> MCTSNode:
		move: dict[str, Any] = self.untried_moves().pop()
		next_board: Board = Board(deepcopy(self.board.get_pieces()), color_up)
		next_board.move_piece(move["piece_index"], move["position"])
		next_turn: str = "B" if self.turn == "W" else "W"
		child: MCTSNode = MCTSNode(next_board, next_turn, parent=self, move=move)
		self.children.append(child)
		return child

class AI:
	def __init__(self, color: str) -> None:
		# 'color' is the color this AI will play with (B or W)
		self.color: str = color

	# {Cython} (Minimax)
	def minimax(self, current_board: Board, is_maximizing: bool, depth: int, turn: str) -> int:
		# Tries to find recursively the best value depending on which player is passed as an argument to the function
		if depth == 0 or current_board.get_winner() is not None:
			return self.get_value(current_board)

		next_turn: str = 'B' if turn == 'W' else 'W'
		board_color_up: str = current_board.get_color_up()
		current_pieces: list[Piece] = current_board.get_pieces()
		piece_moves: list[list[dict[str, Any]] | bool] = list(map(lambda piece: piece.get_moves(current_board) if piece.get_color() == turn else False, current_pieces))

		if is_maximizing:
			# A max player will attempt to get the highest value possible.
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
			# A min player will attempt to get the lowest value possible.
			minimum: int = 999
			for index, moves in enumerate(piece_moves):
				if moves == False:
					continue

				for move in moves:
					aux_board: Board = Board(deepcopy(current_pieces), board_color_up)
					aux_board.move_piece(index, int(move["position"]))
					minimum = min(self.minimax(aux_board, True, depth - 1, next_turn), minimum)

			return minimum

	# {Cython} (MCTS)
	# Implementação do algoritmo Monte Carlo Tree Search, definindo um número padrão de iterações como 1000
	def mcts(self, current_board: Board, n_iterations: int = 500) -> dict[str, Any]:
		# Considera como nó raiz considerando o estado inicial do tabuleiro
		root: MCTSNode = MCTSNode(deepcopy(current_board), self.color)
		color_up: str = current_board.get_color_up()

		for _ in range(n_iterations):
			# Etapa de 'selection', desce pela árvore usando UCT (política de seleção de nós)
			node: MCTSNode = root
			while not node.is_terminal() and node.is_fully_expanded():
				node = node.best_child()

			# Etapa de 'expansion, adiciona um novo nó filho não explorado à árvore de escolhas
			if not node.is_terminal() and not node.is_fully_expanded():
				node = node.expand(color_up)

			# Etapa de 'simulation', reproduz um jogo aleatório até chegar a um vencedor ou ao número limite de iterações definido na função
			result: float = self._rollout(node, color_up)

			# Etapa de 'backpropagation', atualiza wins/visits subindo até a raiz
			self._backpropagate(node, result)

		# Retorna o filho mais visitado (mais robusto que o com maior win rate)
		best: MCTSNode = max(root.children, key=lambda n: n.visits)
		return best.move

	# {Cython} (MCTS)
	# Simula uma partida aleatória a partir do estado do nó recebido.
	# Retorna 1.0 se a IA vencer, 0.0 se o oponente vencer, ou 0.5 se atingir o limite de passos sem vencedor.
	def _rollout(self, node: MCTSNode, color_up: str, max_steps: int = 64) -> float:
		# Copia o tabuleiro para não alterar o estado real da árvore
		board: Board = Board(deepcopy(node.board.get_pieces()), color_up)
		turn: str = node.turn

		for _ in range(max_steps):
			# Encerra a simulação se já houver um vencedor
			winner: str | None = board.get_winner()
			if winner is not None:
				return 1.0 if winner == self.color else 0.0

			# Coleta todos os movimentos legais do jogador atual
			moves: list[tuple[int, int, bool]] = []
			for i, piece in enumerate(board.get_pieces()):
				if piece.get_color() == turn:
					for m in piece.get_moves(board):
						moves.append((i, int(m["position"]), m["eats_piece"]))

			# Aplica a regra de captura obrigatória: se houver captura disponível, só ela pode ser feita
			jumps: list[tuple[int, int, bool]] = [(i, p, e) for i, p, e in moves if e]
			moves = jumps if jumps else moves

			# Sem movimentos disponíveis: jogador bloqueado, encerra a simulação
			if not moves:
				break

			# Escolhe um movimento aleatório e executa
			chosen: tuple[int, int, bool] = choice(moves)
			board.move_piece(chosen[0], chosen[1])
			turn = "B" if turn == "W" else "W"

		# Limite de passos atingido sem vencedor — tratado como resultado neutro
		return 0.5

	# {Cython} (MCTS)
	# Método de backpropagating, onde os nós pais são atualizados com a quantidade de vitórias e visitas
	def _backpropagate(self, node: MCTSNode, result: float) -> None:
		while node is not None:
			node.visits += 1
			# wins armazena vitórias do ponto de vista de quem ESCOLHEU este nó (o pai)
			# Se node.turn == oponente, o AI fez o movimento para chegar aqui → credita result
			if node.turn != self.color:
				node.wins += result
			else:
				node.wins += (1.0 - result)
			node = node.parent

	# Função que pega o próximo movimento da IA
	def get_move(self, current_board: Board, ai: AIEnum) -> dict[str, int]:
		if(ai == AIEnum.MCTS):
			# Código que utiliza o MCTS
			move: dict[str, Any] = self.mcts(current_board, n_iterations=2000)
			pieces: list[Piece] = current_board.get_pieces()
			piece_from: Piece = pieces[move["piece_index"]]
			move = {"position_to": move["position"], "position_from": piece_from.get_position()}
			print(self.get_coloured_message("[MCTS] => Nova posição definida!"))
			print(move)
			return move
		else:
			# Restante de código que utiliza o Minimax
			# Receives a Board object, returns the move it finds best suited.
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
					# The value of the key "piece" is the index of the piece on player_pieces that can make the move assigned on the key "move".
					possible_moves.append({"piece": index, "move": move})

			# If any jump move is available, only jump moves can be made (checkers rule).
			jump_moves: list[dict[str, Any]] = list(filter(lambda move: move["move"]["eats_piece"] == True, possible_moves))

			if len(jump_moves) != 0:
				possible_moves = jump_moves

			# Calls minimax for all possible moves and stores the moves with higher values.
			for move in possible_moves:
				aux_board: Board = Board(deepcopy(current_pieces), board_color_up)
				aux_board.move_piece(move["piece"], int(move["move"]["position"]))
				move_scores.append(self.minimax(aux_board, False, 2, next_turn))

			best_score: int = max(move_scores)
			best_moves: list[dict[str, Any]] = []

			for index, move in enumerate(possible_moves):
				if move_scores[index] == best_score:
					best_moves.append(move)

			# Chooses a random move just in case there are more than one "good" move, then returns it properly.
			move_chosen: dict[str, Any] = choice(best_moves)
			move = {"position_to": move_chosen["move"]["position"], "position_from": player_pieces[move_chosen["piece"]].get_position()}
			print(self.get_coloured_message("[Minimax] => Nova posição definida!"))
			print(move)
			return move

	def get_value(self, board: Board) -> int:
		# Receives a Board object, returns a value depending on which player won or which player has the most pieces on board.
		# The value is higher if the board benefits this AI and lower otherwise.
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