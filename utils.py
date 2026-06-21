from constants import AIEnum, ColorEnum


def get_piece_rc(coords: tuple[int, int], square_dist: int, top_left_coords: tuple[int, int]) -> tuple[int, int]:
    col = (coords[0] - top_left_coords[0]) // square_dist
    row = (coords[1] - top_left_coords[1]) // square_dist
    return (row, col)


def get_piece_gui_coords(coords: tuple[int, int], square_dist: int, top_left_coords: tuple[int, int]) -> tuple[int, int]:
    piece_row, piece_col = coords[0], coords[1]
    x_pos = top_left_coords[0] + (square_dist * 2 * (piece_col // 2))
    x_pos = x_pos if piece_row % 2 == 0 else x_pos + square_dist
    y_pos = top_left_coords[1] + (square_dist * piece_row)
    return (x_pos, y_pos)


def get_surface_mouse_offset(surface_pos: tuple[int, int], mouse_pos: tuple[int, int]) -> tuple[int, int]:
    return (surface_pos[0] - mouse_pos[0], surface_pos[1] - mouse_pos[1])


def get_coloured_message(msg: str, ai: AIEnum) -> str:
    if ai == AIEnum.MCTS:
        return f"{ColorEnum.GREEN_BACKGROUND.value}{ColorEnum.YELLOW_TEXT.value}{msg}{ColorEnum.RESET.value}"
    return f"{ColorEnum.BLUE_BACKGROUND.value}{ColorEnum.WHITE_TEXT.value}{msg}{ColorEnum.RESET.value}"
