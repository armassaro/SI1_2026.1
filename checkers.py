import pygame as pg
from sys import exit
from pygame.locals import *
from board_gui import BoardGUI
from game_control import GameControl
from menu import mostrar_menu
from ai import AIEnum

def main():
    pg.init()
    FPS = 120
    PLAYER_COLOR = "W"

    # roda o menu criado, e passa a escolha feita
    escolha = mostrar_menu()

    DISPLAYSURF = pg.display.set_mode((700, 500))
    pg.display.set_caption('Checkers in Python')
    fps_clock = pg.time.Clock()
    game_control = None
    cpu_ativa = False # controlar se a CPU deve jogar automaticamente


    if escolha["modo"] == "humano_vs_cpu":
        cpu_ativa = True

        if escolha["humano"] == "Sem MCTS" and escolha["cpu_algoritmo"] == "Minimax":
            game_control = GameControl(PLAYER_COLOR, True, AIEnum.minimax)

        if escolha["humano"] == "Sem MCTS" and escolha["cpu_algoritmo"] == "MCTS":
            game_control = GameControl(PLAYER_COLOR, True, AIEnum.MCTS)

        if escolha["humano"] == "MCTS" and escolha["cpu_algoritmo"] == "Minimax":
            print("[AVISO] Humano com MCTS ainda não implementado.")
            print("        Rodando com Minimax padrão como fallback.")
            game_control = GameControl(PLAYER_COLOR, True, AIEnum.minimax)

        if escolha["humano"] == "MCTS" and escolha["cpu_algoritmo"] == "MCTS":
            print("[AVISO] Humano com MCTS e CPU com MCTS ainda não implementado.")
            print("        Rodando com Minimax padrão como fallback.")
            game_control = GameControl(PLAYER_COLOR, True, AIEnum.MCTS)

        # Para rodar mesmo nao tendo implementado
        if game_control is None:
            print("[AVISO] Combinação Humano/CPU com MCTS ainda não implementada.")
            print("        Rodando com Minimax padrão como fallback.")
            game_control = GameControl(PLAYER_COLOR, True, AIEnum.minimax)

    elif escolha["modo"] == "cpu_vs_cpu":
        cpu_ativa = True
        # TODO: implementar os modos de CPU vs CPU, usando as escolhas feitas para definir os algoritmos usados por cada CPU
        
        # Para rodar mesmo nao tendo implementado
        print("[AVISO] Modo CPU vs CPU ainda não implementado.")
        print("        Abrindo modo Humano vs CPU (Minimax) como fallback.")
        game_control = GameControl(PLAYER_COLOR, True, AIEnum.minimax)
        

    # Font setup
    main_font = pg.font.SysFont("Arial", 25)
    turn_rect = (509, 26)
    winner_rect = (509, 152)

    while True:
        # GUI
        DISPLAYSURF.fill((0, 0, 0))
        game_control.draw_screen(DISPLAYSURF)

        turn_display_text = "White's turn" if game_control.get_turn() == "W" else "Black's turn"
        DISPLAYSURF.blit(main_font.render(turn_display_text, True, (255, 255, 255)), turn_rect)

        if game_control.get_winner() is not None:
            winner_display_text = "White wins!" if game_control.get_winner() == "W" else "Black wins!"
            DISPLAYSURF.blit(main_font.render(winner_display_text, True, (255, 255, 255)), winner_rect)

        # Event handling
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                return

            if event.type == MOUSEBUTTONDOWN:
                game_control.hold_piece(event.pos)

            if event.type == MOUSEBUTTONUP:
                game_control.release_piece()

                if game_control.get_turn() != PLAYER_COLOR and cpu_ativa:
                    pg.time.set_timer(USEREVENT, 400)

            if event.type == USEREVENT:
                # AI movement
                if game_control.get_winner() is not None:
                    continue

                game_control.move_ai()

                if game_control.get_turn() == PLAYER_COLOR:
                    pg.time.set_timer(USEREVENT, 0)

        pg.display.update()
        fps_clock.tick(FPS)

if __name__ == '__main__':
    main()
    exit()