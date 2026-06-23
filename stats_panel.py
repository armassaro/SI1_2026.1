import pygame


class StatsPanel:
    PANEL_RECT = pygame.Rect(510, 60, 180, 340)
    BACKGROUND_COLOR = (30, 30, 30)
    BORDER_COLOR = (255, 255, 255)
    TEXT_COLOR = (255, 255, 255)
    BEST_BAR_COLOR = (80, 200, 120)
    REGULAR_BAR_COLOR = (80, 140, 220)
    BAR_BACKGROUND_COLOR = (50, 50, 50)

    def __init__(self):
        self.surface = pygame.Surface((self.PANEL_RECT.width, self.PANEL_RECT.height), pygame.SRCALPHA)
        self.scores = []
        self.visible = False
        self.title_font = pygame.font.SysFont("Arial", 18, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 15)
        self.small_font = pygame.font.SysFont("Arial", 13)

    def update(self, scores):
        self.scores = scores or []
        self.visible = len(self.scores) > 0

    def clear(self):
        self.scores = []
        self.visible = False

    def draw(self, display_surface):
        self.surface.fill((0, 0, 0, 0))

        pygame.draw.rect(self.surface, self.BACKGROUND_COLOR, self.surface.get_rect())
        pygame.draw.rect(self.surface, self.BORDER_COLOR, self.surface.get_rect(), 2)

        title = self.title_font.render("MCTS Sugestões", True, self.TEXT_COLOR)
        self.surface.blit(title, (12, 12))

        y = 40
        if self.visible:
            for index, score in enumerate(self.scores):
                if y + 60 > self.PANEL_RECT.height:
                    break

                # compute directional letters: E = esquerda, D = direita, B = baixo
                def _pos_row_col(pos: int):
                    row = int(pos) // 4
                    remainder = int(pos) % 4
                    col = remainder * 2
                    if row % 2 == 1:
                        col += 1
                    return row, col

                row_from, col_from = _pos_row_col(score['from'])
                row_to, col_to = _pos_row_col(score['to'])
                dir_letters = ''
                if col_to < col_from:
                    dir_letters = 'E'
                elif col_to > col_from:
                    dir_letters = 'D'
                # if move goes downward (to a larger row number), append B
                if row_to > row_from:
                    dir_letters = dir_letters + 'B' if dir_letters else 'B'

                move_text = f"{score['from']} → {score['to']}  {dir_letters}"
                rate_text = f"{score['win_rate'] * 100:.0f}%"
                line_text = self.text_font.render(move_text, True, self.TEXT_COLOR)
                rate_label = self.text_font.render(rate_text, True, self.TEXT_COLOR)
                self.surface.blit(line_text, (12, y))
                self.surface.blit(rate_label, (self.PANEL_RECT.width - rate_label.get_width() - 12, y))
                y += 20

                sim_text = f"({score['simulations']} simulações)"
                self.surface.blit(self.small_font.render(sim_text, True, self.TEXT_COLOR), (12, y))
                y += 18

                bar_width = int((self.PANEL_RECT.width - 24) * score['win_rate'])
                bar_color = self.BEST_BAR_COLOR if index == 0 else self.REGULAR_BAR_COLOR
                pygame.draw.rect(self.surface, self.BAR_BACKGROUND_COLOR, (12, y, self.PANEL_RECT.width - 24, 12))
                pygame.draw.rect(self.surface, bar_color, (12, y, bar_width, 12))
                pygame.draw.rect(self.surface, self.BORDER_COLOR, (12, y, self.PANEL_RECT.width - 24, 12), 1)
                y += 24
        else:
            hint = self.text_font.render("CPU pensando...", True, self.TEXT_COLOR)
            self.surface.blit(hint, (12, 40))

        display_surface.blit(self.surface, self.PANEL_RECT.topleft)


class AIStatsPanel:
    BG = (20, 22, 38)
    MINIMAX_COLOR = (255, 185, 70)
    MCTS_COLOR = (90, 205, 255)
    TEXT_COLOR = (215, 215, 215)
    # cpu_vs_cpu mode: two sections side by side
    CPU_VS_CPU_RECT = pygame.Rect(509, 50, 185, 118)
    # single AI mode: one section
    SINGLE_RECT = pygame.Rect(509, 50, 185, 54)

    _TITLE_H = 19
    _LINE_H = 15

    def __init__(self) -> None:
        self._title_font = pygame.font.SysFont("Arial", 13, bold=True)
        self._line_font = pygame.font.SysFont("Arial", 11)
        self.minimax_snap: dict | None = None
        self.mcts_snap: dict | None = None

    def update_minimax(self, snap: dict | None) -> None:
        self.minimax_snap = snap

    def update_mcts(self, snap: dict | None) -> None:
        self.mcts_snap = snap

    def _draw_section(self, surf: pygame.Surface, x: int, y: int, w: int,
                      title: str, color: tuple, lines: list[str]) -> int:
        h = self._TITLE_H + len(lines) * self._LINE_H + 4
        pygame.draw.rect(surf, self.BG, (x, y, w, h))
        pygame.draw.rect(surf, color, (x, y, w, h), 1)
        surf.blit(self._title_font.render(title, True, color), (x + 4, y + 3))
        for i, line in enumerate(lines):
            surf.blit(self._line_font.render(line, True, self.TEXT_COLOR),
                      (x + 4, y + self._TITLE_H + i * self._LINE_H))
        return h

    def draw(self, display_surface: pygame.Surface, rect: pygame.Rect) -> None:
        x, y, w = rect.x, rect.y, rect.width

        if self.minimax_snap:
            s = self.minimax_snap
            lines = [
                f"Nós: {s['nodes_evaluated']}  Prof: {s['max_depth_reached']}  Score: {s['best_score']}",
                f"Tempo: {s['elapsed_time']:.3f}s",
            ]
            h = self._draw_section(display_surface, x, y, w, "Minimax (Pretas)", self.MINIMAX_COLOR, lines)
            y += h + 4

        if self.mcts_snap:
            s = self.mcts_snap
            lines = [
                f"Iter: {s['iterations']}  Nós: {s['nodes_created']}  Prof: {s['max_tree_depth']}",
                f"WR: {s['best_move_win_rate']:.1%} | Vis: {s['best_move_visits']} | T: {s['elapsed_time']:.3f}s",
            ]
            self._draw_section(display_surface, x, y, w, "MCTS (Brancas)", self.MCTS_COLOR, lines)
