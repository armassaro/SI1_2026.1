import pygame as pg
import logging
from sys import exit
from pygame.locals import *
from board_gui import BoardGUI
from game_control import GameControl
from menu import mostrar_menu
from ai import AIEnum
from stats_panel import StatsPanel

def main():
    pg.init()
    logging.basicConfig(level=logging.INFO)
    FPS = 120
    PLAYER_COLOR = "W"

    # roda o menu criado, e passa a escolha feita
    escolha = mostrar_menu()

    DISPLAYSURF = pg.display.set_mode((700, 500))
    pg.display.set_caption('Checkers in Python')
    fps_clock = pg.time.Clock()
    game_control = None
    stats_panel = None
    cpu_ativa = False # controlar se a CPU deve jogar automaticamente


    if escolha["modo"] == "humano_vs_cpu":
        cpu_ativa = True
        human_mcts_selected = escolha["humano"] == "MCTS"

        if escolha["humano"] == "Sem MCTS" and escolha["cpu_algoritmo"] == "Minimax":
            game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=True, cpu_algoritmo=AIEnum.minimax)

        if escolha["humano"] == "Sem MCTS" and escolha["cpu_algoritmo"] == "MCTS":
            game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=True, cpu_algoritmo=AIEnum.MCTS)

        if escolha["humano"] == "MCTS" and escolha["cpu_algoritmo"] == "Minimax":
            # Humano com MCTS selecionado; CPU usará Minimax como escolhido
            game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=True, cpu_algoritmo=AIEnum.minimax, human_mcts_enabled=True)

        if escolha["humano"] == "MCTS" and escolha["cpu_algoritmo"] == "MCTS":
            # Humano e CPU com MCTS selecionados; habilita MCTS para humano
            game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=True, cpu_algoritmo=AIEnum.MCTS, human_mcts_enabled=True)

        # Para rodar mesmo nao tendo implementado
        if game_control is None:
            logging.warning("Combinação Humano/CPU com MCTS não suportada; usando Minimax como fallback.")
            game_control = GameControl(PLAYER_COLOR, True, AIEnum.minimax, human_mcts_enabled=human_mcts_selected)

        if human_mcts_selected:
            stats_panel = StatsPanel()

    elif escolha["modo"] == "cpu_vs_cpu":
        cpu_ativa = True
        # TODO: implementar os modos de CPU vs CPU, usando as escolhas feitas para definir os algoritmos usados por cada CPU
        
        # Para rodar mesmo nao tendo implementado
        print("[AVISO] Modo CPU vs CPU ainda não implementado.")
        print("        Abrindo modo Humano vs CPU (Minimax) como fallback.")
        game_control = GameControl(PLAYER_COLOR, True, AIEnum.minimax)
        

    # Font setup
    main_font = pg.font.SysFont("Arial", 25)
    status_font = pg.font.SysFont("Arial", 20)
    turn_rect = (509, 26)
    winner_rect = (509, 152)
    # move the back button slightly up and reduce height so it fits the window
    botao_voltar_menu = pg.Rect(525, 456, 150, 36)
    small_font = pg.font.SysFont("Arial", 14)
    # place the legend button above the back button with a clear gap
    legend_button = pg.Rect(540, 418, 120, 30)
    legend_visible = False
    # Modal rectangle for detailed legend (centered)
    # modal size adjusted to better fit available space
    modal_rect = pg.Rect(110, 80, 480, 320)
    modal_close_rect = pg.Rect(modal_rect.x + modal_rect.w - 90, modal_rect.y + modal_rect.h - 46, 80, 36)

    while True:
        voltar_ao_menu = False

        # GUI
        DISPLAYSURF.fill((0, 0, 0))
        game_control.draw_screen(DISPLAYSURF)

        if stats_panel is not None:
            stats_panel.draw(DISPLAYSURF)


        if game_control.get_winner() is not None:
            winner_display_text = "Vitória das brancas" if game_control.get_winner() == "W" else "Vitória das pretas"
            DISPLAYSURF.blit(status_font.render(winner_display_text, True, (255, 255, 255)), turn_rect)
        else:
            turn_display_text = "Turno das brancas" if game_control.get_turn() == "W" else "Turno das pretas"
            DISPLAYSURF.blit(status_font.render(turn_display_text, True, (255, 255, 255)), turn_rect)

        # Draw legenda button (small) above the back button only when MCTS human mode is active
        if stats_panel is not None:
            pg.draw.rect(DISPLAYSURF, (40, 40, 40), legend_button)
            pg.draw.rect(DISPLAYSURF, (255, 255, 255), legend_button, 1)
            texto_legenda = small_font.render("Legenda", True, (255, 255, 255))
            texto_legenda_rect = texto_legenda.get_rect(center=legend_button.center)
            DISPLAYSURF.blit(texto_legenda, texto_legenda_rect)

        # If legend visible, draw a modal with detailed explanations
        if legend_visible:
            pg.draw.rect(DISPLAYSURF, (20, 20, 20), modal_rect)
            pg.draw.rect(DISPLAYSURF, (255, 255, 255), modal_rect, 2)
            title = main_font.render("Legenda e explicações do MCTS", True, (255, 255, 255))
            DISPLAYSURF.blit(title, (modal_rect.x + 12, modal_rect.y + 10))
            detailed_lines = [
                "Formato das entradas:",
                "- '21 -> 9' significa origem -> destino (posição numerada).",
                "- Letras: E = esquerda, D = direita, B = baixo;",
                "  ex.: 'EB' = esquerda-baixo (diagonal).",
                "",
                "Interpretação das métricas do MCTS:",
                "- Percentual: taxa de vitória estimada a partir desse movimento.",
                "- (N simulações): número de visitas ao nó (quanto maior,",
                "  mais confiança na estimativa).",
                "- Barra: comprimento proporcional às visitas; verde = melhor,",
                "  azul = outras opções.",
            ]
            ly = modal_rect.y + 44
            for ln in detailed_lines:
                surf = small_font.render(ln, True, (255, 255, 255))
                DISPLAYSURF.blit(surf, (modal_rect.x + 12, ly))
                ly += 20
            # close button
            pg.draw.rect(DISPLAYSURF, (80, 80, 80), modal_close_rect)
            pg.draw.rect(DISPLAYSURF, (255, 255, 255), modal_close_rect, 1)
            close_text = small_font.render("Fechar", True, (255, 255, 255))
            close_rect = close_text.get_rect(center=modal_close_rect.center)
            DISPLAYSURF.blit(close_text, close_rect)
        # Draw back button
        pg.draw.rect(DISPLAYSURF, (50, 50, 50), botao_voltar_menu)
        pg.draw.rect(DISPLAYSURF, (255, 255, 255), botao_voltar_menu, 2)
        texto_voltar = main_font.render("Voltar", True, (255, 255, 255))
        texto_rect = texto_voltar.get_rect(center=botao_voltar_menu.center)
        DISPLAYSURF.blit(texto_voltar, texto_rect)

        # Event handling
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                return

            if event.type == MOUSEBUTTONDOWN:
                if legend_visible:
                    # If modal is open, close it if click is outside or on Close
                    if not modal_rect.collidepoint(event.pos) or modal_close_rect.collidepoint(event.pos):
                        legend_visible = False
                    # consume click; do not interact with board while modal open
                elif botao_voltar_menu.collidepoint(event.pos):
                    voltar_ao_menu = True
                elif stats_panel is not None and legend_button.collidepoint(event.pos):
                    legend_visible = True
                else:
                    scores = game_control.hold_piece(event.pos)
                    if stats_panel is not None:
                        if scores is None:
                            stats_panel.clear()
                        else:
                            stats_panel.update(scores)

            if event.type == MOUSEBUTTONUP:
                previous_turn = game_control.get_turn()
                game_control.release_piece()

                if stats_panel is not None and previous_turn == PLAYER_COLOR and game_control.get_turn() != PLAYER_COLOR:
                    stats_panel.clear()

                if game_control.get_turn() != PLAYER_COLOR and cpu_ativa:
                    pg.time.set_timer(USEREVENT, 400)

            if event.type == USEREVENT:
                # AI movement
                if game_control.get_winner() is not None:
                    continue

                game_control.move_ai()

                if game_control.get_turn() == PLAYER_COLOR:
                    pg.time.set_timer(USEREVENT, 0)

        if voltar_ao_menu:
            escolha = mostrar_menu()

            if escolha["modo"] == "humano_vs_cpu":
                cpu_ativa = True
                human_mcts_selected = escolha["humano"] == "MCTS"
                stats_panel = None

                if escolha["humano"] == "Sem MCTS" and escolha["cpu_algoritmo"] == "Minimax":
                    game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=True, cpu_algoritmo=AIEnum.minimax)

                if escolha["humano"] == "Sem MCTS" and escolha["cpu_algoritmo"] == "MCTS":
                    game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=True, cpu_algoritmo=AIEnum.MCTS)

                if escolha["humano"] == "MCTS" and escolha["cpu_algoritmo"] == "Minimax":
                    # Humano com MCTS selecionado; CPU usará Minimax como escolhido
                    game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=True, cpu_algoritmo=AIEnum.minimax, human_mcts_enabled=True)

                if escolha["humano"] == "MCTS" and escolha["cpu_algoritmo"] == "MCTS":
                    # Humano e CPU com MCTS selecionados; habilita MCTS para humano
                    game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=True, cpu_algoritmo=AIEnum.MCTS, human_mcts_enabled=True)

                if game_control is None:
                    print("[AVISO] Combinação Humano/CPU com MCTS ainda não implementada.")
                    print("        Rodando com Minimax padrão como fallback.")
                    game_control = GameControl(PLAYER_COLOR, True, AIEnum.minimax, human_mcts_enabled=human_mcts_selected)

                if human_mcts_selected:
                    stats_panel = StatsPanel()

            elif escolha["modo"] == "cpu_vs_cpu":
                cpu_ativa = True
                logging.warning("Modo CPU vs CPU ainda não implementado; abrindo modo Humano vs CPU (Minimax) como fallback.")
                game_control = GameControl(PLAYER_COLOR, True, AIEnum.minimax)

            game_control.draw_screen(DISPLAYSURF)

        pg.display.update()
        fps_clock.tick(FPS)

if __name__ == '__main__':
    main()
    exit()