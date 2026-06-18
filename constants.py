from enum import Enum

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
    [" ", "B", " ", "B", " ", "B", " ", "B"],
    ["B", " ", "B", " ", "B", " ", "B", " "],
    [" ", "B", " ", "B", " ", "B", " ", "B"],
    [" ", " ", " ", " ", " ", " ", " ", " "],
    [" ", " ", " ", " ", " ", " ", " ", " "],
    ["W", " ", "W", " ", "W", " ", "W", " "],
    [" ", "W", " ", "W", " ", "W", " ", "W"],
    ["W", " ", "W", " ", "W", " ", "W", " "],
]