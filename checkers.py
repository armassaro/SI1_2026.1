import pygame as pg
import logging
from sys import exit
from pygame.locals import *
from board_gui import BoardGUI
from game_control import GameControl
from menu import mostrar_menu
from constants import AIEnum
from stats_panel import StatsPanel

PLAYER_COLOR = "W"


def criar_game_control_e_stats(escolha: dict) -> tuple:
    """
    Monta o GameControl (e o StatsPanel, se aplicavel) a partir da escolha
    feita no menu, para os modos "graficos" (humano vs CPU, e CPU vs CPU
    no modo Grafico). O modo de Simulacao e tratado separadamente em
    executar_simulacao(), pois nao usa essa tela de jogo.
    """
    game_control = None
    stats_panel = None
    cpu_ativa = False
    eh_cpu_vs_cpu = False

    if escolha["modo"] == "humano_vs_cpu":
        cpu_ativa = True
        human_mcts_selected = escolha["humano"] == "MCTS"
        algoritmo_cpu = AIEnum.MCTS if escolha["cpu_algoritmo"] == "MCTS" else AIEnum.minimax
        game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=True, cpu_algoritmo=algoritmo_cpu, human_mcts_enabled=human_mcts_selected)

        if human_mcts_selected:
            stats_panel = StatsPanel()

    elif escolha["modo"] == "cpu_vs_cpu":
        cpu_ativa = True
        eh_cpu_vs_cpu = True
        game_control = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=False, cpu_algoritmo=AIEnum.minimax, cpu_vs_cpu=True)

    return game_control, stats_panel, cpu_ativa, eh_cpu_vs_cpu


def _desenhar_tela_simulacao(display, main_font, small_font, partidas_concluidas, quantidade_partidas, barra_rect, botao_cancelar) -> None:
    display.fill((20, 20, 20))
    titulo = main_font.render("Simulando partidas...", True, (255, 255, 255))
    display.blit(titulo, titulo.get_rect(center=(350, 140)))
    subtitulo = small_font.render("Minimax (Pretas) vs MCTS (Brancas)", True, (180, 180, 180))
    display.blit(subtitulo, subtitulo.get_rect(center=(350, 168)))
    texto_contagem = small_font.render(f"Partida {min(partidas_concluidas + 1, quantidade_partidas)} de {quantidade_partidas}", True, (200, 200, 200))
    display.blit(texto_contagem, texto_contagem.get_rect(center=(350, 200)))

    # barra de progresso
    pg.draw.rect(display, (60, 60, 60), barra_rect)
    pg.draw.rect(display, (255, 255, 255), barra_rect, 2)

    progresso = partidas_concluidas / quantidade_partidas if quantidade_partidas > 0 else 0
    largura_preenchida = int(barra_rect.width * progresso)
    if largura_preenchida > 0:
        barra_preenchida = pg.Rect(barra_rect.x, barra_rect.y, largura_preenchida, barra_rect.height)
        pg.draw.rect(display, (0, 150, 255), barra_preenchida)

    texto_pct = small_font.render(f"{progresso * 100:.0f}%", True, (255, 255, 255))
    display.blit(texto_pct, texto_pct.get_rect(center=barra_rect.center))

    # botao cancelar
    pg.draw.rect(display, (150, 40, 40), botao_cancelar)
    pg.draw.rect(display, (255, 255, 255), botao_cancelar, 1)
    texto_cancelar = small_font.render("Cancelar", True, (255, 255, 255))
    display.blit(texto_cancelar, texto_cancelar.get_rect(center=botao_cancelar.center))


def _desenhar_tela_resultado_simulacao(display, main_font, small_font, resultados, partidas_concluidas, quantidade_partidas, cancelado, botao_voltar) -> None:
    display.fill((20, 20, 20))
    titulo_texto = "Simulação cancelada" if cancelado else "Simulação concluída"
    titulo = main_font.render(titulo_texto, True, (255, 255, 255))
    display.blit(titulo, titulo.get_rect(center=(350, 110)))
    total = max(partidas_concluidas, 1)  # evita divisao por zero se cancelado antes de concluir alguma partida
    pct_minimax = resultados["B"] / total * 100
    pct_mcts = resultados["W"] / total * 100
    pct_empate = resultados["empate"] / total * 100
    linhas = [
        f"Partidas concluidas: {partidas_concluidas} de {quantidade_partidas}",
        "",
        f"Minimax (Pretas) venceu: {resultados['B']}  ({pct_minimax:.1f}%)",
        f"MCTS (Brancas) venceu: {resultados['W']}  ({pct_mcts:.1f}%)",
        f"Empates: {resultados['empate']}  ({pct_empate:.1f}%)",
    ]

    y = 170
    for linha in linhas:
        if linha:
            surf = small_font.render(linha, True, (255, 255, 255))
            display.blit(surf, surf.get_rect(center=(350, y)))
        y += 28

    pg.draw.rect(display, (50, 50, 50), botao_voltar)
    pg.draw.rect(display, (255, 255, 255), botao_voltar, 2)
    texto_voltar = small_font.render("Voltar ao Menu", True, (255, 255, 255))
    display.blit(texto_voltar, texto_voltar.get_rect(center=botao_voltar.center))


def executar_simulacao(DISPLAYSURF, fps_clock, FPS, quantidade_partidas: int) -> None:
    main_font = pg.font.SysFont("Arial", 24)
    small_font = pg.font.SysFont("Arial", 16)

    barra_rect = pg.Rect(0, 0, 420, 30)
    barra_rect.center = (350, 250)

    botao_cancelar = pg.Rect(0, 0, 140, 40)
    botao_cancelar.center = (350, 320)

    botao_voltar = pg.Rect(0, 0, 200, 46)
    botao_voltar.center = (350, 350)

    resultados = {"W": 0, "B": 0, "empate": 0}
    cancelado = False
    partidas_concluidas = 0

    if quantidade_partidas <= 0:
        aguardando = True
        while aguardando:
            DISPLAYSURF.fill((20, 20, 20))
            texto = main_font.render("Quantidade de partidas inválida.", True, (255, 255, 255))
            DISPLAYSURF.blit(texto, texto.get_rect(center=(350, 200)))
            texto2 = small_font.render("Volte ao menu e digite um número de 1 a 999.", True, (200, 200, 200))
            DISPLAYSURF.blit(texto2, texto2.get_rect(center=(350, 230)))

            pg.draw.rect(DISPLAYSURF, (50, 50, 50), botao_voltar)
            pg.draw.rect(DISPLAYSURF, (255, 255, 255), botao_voltar, 2)
            texto_voltar = small_font.render("Voltar ao Menu", True, (255, 255, 255))
            DISPLAYSURF.blit(texto_voltar, texto_voltar.get_rect(center=botao_voltar.center))

            for event in pg.event.get():
                if event.type == QUIT:
                    pg.quit()
                    exit()
                if event.type == MOUSEBUTTONDOWN and botao_voltar.collidepoint(event.pos):
                    aguardando = False

            pg.display.update()
            fps_clock.tick(FPS)
        return

    for _ in range(quantidade_partidas):
        gc = GameControl(player_color=PLAYER_COLOR, is_computer_opponent=False, cpu_algoritmo=AIEnum.minimax, cpu_vs_cpu=True)
        
        while gc.get_winner() is None and not cancelado:
            gc.move_ai_cpu_vs_cpu()

            for event in pg.event.get():
                if event.type == QUIT:
                    pg.quit()
                    exit()
                if event.type == MOUSEBUTTONDOWN and botao_cancelar.collidepoint(event.pos):
                    cancelado = True

            _desenhar_tela_simulacao(DISPLAYSURF, main_font, small_font, partidas_concluidas, quantidade_partidas, barra_rect, botao_cancelar)
            pg.display.update()
            fps_clock.tick(FPS)

        if cancelado:
            break

        vencedor = gc.get_winner()
        if vencedor in resultados:
            resultados[vencedor] += 1
        partidas_concluidas += 1

    aguardando = True
    while aguardando:
        _desenhar_tela_resultado_simulacao(DISPLAYSURF, main_font, small_font, resultados, partidas_concluidas, quantidade_partidas, cancelado, botao_voltar)

        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                exit()
            if event.type == MOUSEBUTTONDOWN and botao_voltar.collidepoint(event.pos):
                aguardando = False

        pg.display.update()
        fps_clock.tick(FPS)


def main():
    pg.init()
    logging.basicConfig(level=logging.INFO)
    FPS = 120

    DISPLAYSURF = pg.display.set_mode((700, 500))
    pg.display.set_caption('Checkers in Python')
    fps_clock = pg.time.Clock()

    # Font setup
    main_font = pg.font.SysFont("Arial", 25)
    status_font = pg.font.SysFont("Arial", 20)
    turn_rect = (509, 26)
    botao_voltar_menu = pg.Rect(525, 456, 150, 36)
    small_font = pg.font.SysFont("Arial", 14)
    legend_button = pg.Rect(540, 418, 120, 30)
    modal_rect = pg.Rect(110, 80, 480, 320)
    modal_close_rect = pg.Rect(modal_rect.x + modal_rect.w - 90, modal_rect.y + modal_rect.h - 46, 80, 36)
    botao_autoplay    = pg.Rect(509, 200, 160, 40)
    botao_prox_jogada = pg.Rect(509, 250, 160, 40)

    AUTOPLAY_DELAY = 1000  # delay minimo de 1s entre jogadas no autoplay grafico

    escolha = mostrar_menu()

    while True:
        if escolha["modo"] == "cpu_vs_cpu" and escolha.get("tipo") == "Simulação":
            executar_simulacao(DISPLAYSURF, fps_clock, FPS, escolha.get("quantidade_partidas", 0))
            escolha = mostrar_menu()
            continue

        game_control, stats_panel, cpu_ativa, eh_cpu_vs_cpu = criar_game_control_e_stats(escolha)
        legend_visible = False
        autoplay_ativo = False
        proximo_horario_jogada = 0

        rodando_partida = True
        while rodando_partida:
            voltar_ao_menu = False

            DISPLAYSURF.fill((0, 0, 0))
            game_control.draw_screen(DISPLAYSURF)

            if stats_panel is not None:
                stats_panel.draw(DISPLAYSURF)

            if game_control.get_winner() is not None:
                if game_control.get_winner() == "empate":
                    DISPLAYSURF.blit(status_font.render("Empate", True, (255, 255, 255)), turn_rect)
                    texto_explicacao = small_font.render("(50 jogadas sem captura)", True, (255, 255, 255))
                    DISPLAYSURF.blit(texto_explicacao, (turn_rect[0], turn_rect[1] + 24))
                elif game_control.get_winner() == "W":
                    winner_display_text = "Vitória das brancas"
                    DISPLAYSURF.blit(status_font.render(winner_display_text, True, (255, 255, 255)), turn_rect)
                else:
                    winner_display_text = "Vitória das pretas"
                    DISPLAYSURF.blit(status_font.render(winner_display_text, True, (255, 255, 255)), turn_rect)
            else:
                if eh_cpu_vs_cpu:
                    turn_display_text = "Brancas (MCTS)" if game_control.get_turn() == "W" else "Pretas (Minimax)"
                else:
                    turn_display_text = "Turno das brancas" if game_control.get_turn() == "W" else "Turno das pretas"
                DISPLAYSURF.blit(status_font.render(turn_display_text, True, (255, 255, 255)), turn_rect)

            # botoes autoplay e proxima jogada
            if eh_cpu_vs_cpu and game_control.get_winner() is None:
                cor_autoplay = (0, 150, 50) if not autoplay_ativo else (150, 50, 0)
                pg.draw.rect(DISPLAYSURF, cor_autoplay, botao_autoplay)
                pg.draw.rect(DISPLAYSURF, (255, 255, 255), botao_autoplay, 1)
                label_autoplay = "Pausar" if autoplay_ativo else "Iniciar"
                texto = main_font.render(label_autoplay, True, (255, 255, 255))
                DISPLAYSURF.blit(texto, texto.get_rect(center=botao_autoplay.center))

                cor_prox = (40, 40, 120) if not autoplay_ativo else (60, 60, 60)
                pg.draw.rect(DISPLAYSURF, cor_prox, botao_prox_jogada)
                pg.draw.rect(DISPLAYSURF, (255, 255, 255), botao_prox_jogada, 1)
                texto = small_font.render("Proxima jogada", True, (255, 255, 255))
                DISPLAYSURF.blit(texto, texto.get_rect(center=botao_prox_jogada.center))

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
                title = main_font.render("Legenda e explicacoes do MCTS", True, (255, 255, 255))
                DISPLAYSURF.blit(title, (modal_rect.x + 12, modal_rect.y + 10))
                detailed_lines = [
                    "Formato das entradas:",
                    "- '21 -> 9' significa origem -> destino (posicao numerada).",
                    "- Letras: E = esquerda, D = direita, B = baixo;",
                    "  ex.: 'EB' = esquerda-baixo (diagonal).",
                    "",
                    "Interpretacao das metricas do MCTS:",
                    "- Percentual: taxa de vitoria estimada a partir desse movimento.",
                    "- (N simulacoes): numero de visitas ao no (quanto maior,",
                    "  mais confianca na estimativa).",
                    "- Barra: comprimento proporcional as visitas; verde = melhor,",
                    "  azul = outras opcoes.",
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
                        if not modal_rect.collidepoint(event.pos) or modal_close_rect.collidepoint(event.pos):
                            legend_visible = False

                    elif botao_voltar_menu.collidepoint(event.pos):
                        voltar_ao_menu = True

                    elif eh_cpu_vs_cpu and game_control.get_winner() is None:
                        if botao_autoplay.collidepoint(event.pos):
                            autoplay_ativo = not autoplay_ativo
                            if autoplay_ativo:
                                proximo_horario_jogada = pg.time.get_ticks() + AUTOPLAY_DELAY
                        elif botao_prox_jogada.collidepoint(event.pos) and not autoplay_ativo:
                            game_control.move_ai_cpu_vs_cpu()

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
                    if not eh_cpu_vs_cpu:
                        previous_turn = game_control.get_turn()
                        game_control.release_piece()

                        if stats_panel is not None and previous_turn == PLAYER_COLOR and game_control.get_turn() != PLAYER_COLOR:
                            stats_panel.clear()

                        if game_control.get_turn() != PLAYER_COLOR and cpu_ativa:
                            pg.time.set_timer(USEREVENT, 400)

                if event.type == USEREVENT:
                    if game_control.get_winner() is not None:
                        continue
                    game_control.move_ai()
                    if game_control.get_turn() == PLAYER_COLOR:
                        pg.time.set_timer(USEREVENT, 0)

            if eh_cpu_vs_cpu and autoplay_ativo and game_control.get_winner() is None:
                if pg.time.get_ticks() >= proximo_horario_jogada:
                    game_control.move_ai_cpu_vs_cpu()
                    if game_control.get_winner() is not None:
                        autoplay_ativo = False
                    proximo_horario_jogada = pg.time.get_ticks() + AUTOPLAY_DELAY

            if voltar_ao_menu:
                pg.time.set_timer(USEREVENT, 0)
                rodando_partida = False

            pg.display.update()
            fps_clock.tick(FPS)

        escolha = mostrar_menu()


if __name__ == '__main__':
    main()
    exit()