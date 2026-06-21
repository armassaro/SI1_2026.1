from enum import Enum
from typing import Final

# Cores utilizadas para os prints de mensagem do Minimax e MCTS
class ColorEnum(Enum):
    GREEN_BACKGROUND = "\033[42m"
    YELLOW_TEXT = "\033[33m"
    BLUE_BACKGROUND = "\033[44m"
    WHITE_TEXT = "\033[37m"
    RESET = "\033[0m"

# Strings utilizadas para decidir qual IA utilizar
class AIEnum(Enum):
	MCTS='MCTS',
	minimax='Minimax'
      
BOARD = [
    ["B", " ", "B", " ", "B", " ", "B", " "],
    [" ", "B", " ", "B", " ", "B", " ", "B"],
    ["B", " ", "B", " ", "B", " ", "B", " "],
    [" ", " ", " ", " ", " ", " ", " ", " "],
    [" ", " ", " ", " ", " ", " ", " ", " "],
    [" ", "w", " ", "w", " ", "w", " ", "w"],
    ["w", " ", "w", " ", "w", " ", "w", " "],
    [" ", "w", " ", "w", " ", "w", " ", "w"],
]
      
EXEC_PARAMS:Final = {
    # Habilita a execução dos módulos pré-compilados em linguagem C
    "cython": True,
    # Habilita a execução de simulações simultâneas
    "threaded_simulations": True,
    # Determina a quantidade de threads para execução de simulações simultâneas, só possui efeito se 'threaded_simulations' estiver como True
    "max_threaded_simulations": 8,
    # Parâmetros específicos da execução do MCTS (CPU)
    "mcts": {
        # Coeficiente de cálculo da política de seleção de nós
        "c": 1.41,
        # Quantidade máxima de nós iterados na árvore de escolhas MCTS
        "n_iterations": 2000,
        # Quantidade máxima de nós expandidos por nó pai
        "max_steps": 128
    },
    # Parâmetros espeacíficos da execução do MCTS auxiliar
    "human_mcts": {
        # Coeficiente de cálculo da política de seleção de nós
        "c": 1.41,
        # Quantidade máxima de nós iterados na árvore de escolhas MCTS
        "n_iterations": 500,
        # Quantidade máxima de nós expandidos por nó pai
        "max_steps": 64
    }
}