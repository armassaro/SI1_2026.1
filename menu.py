import pygame

def mostrar_menu():
    pygame.init()
    pygame.display.set_caption('Menu Inicial')

    janela = pygame.display.set_mode((700, 500))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 30)
    font_menor = pygame.font.SysFont("Arial", 15)

    botao_jogar_esquerda = pygame.Rect(0, 0, 200, 80)
    botao_jogar_esquerda.center = (175, 400)

    botao_jogar_direita = pygame.Rect(0, 0, 200, 80)
    botao_jogar_direita.center = (525, 400)

    caixa_texto = pygame.Rect(393.75, 320, 250, 20)

    radio_btt_modo = 1
    radio_btt_cpu = 1
    radio_btt_humano = 1
    opcao1 = (400, 240)
    opcao2 = (400, 260)
    opcao3 = (235, 240)
    opcao4 = (235, 260)
    opcao5 = (50, 240)
    opcao6 = (50, 260)

    caixa_texto_ativa = False
    texto_quantidade = ""

    resultado = None  # vai guardar o dicionário de retorno quando o usuário clicar em JOGAR


    rodando = True
    while rodando:
        janela.fill((20, 20, 20))
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()  # fecha o programa todo se o usuário fechar a janela do menu

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                # Botão "Humano VS CPU"
                if botao_jogar_esquerda.collidepoint(event.pos):
                    resultado = {
                        "modo": "humano_vs_cpu",
                        "humano": "MCTS" if radio_btt_humano == 1 else "Sem MCTS",
                        "cpu_algoritmo": "Minimax" if radio_btt_cpu == 1 else "MCTS"
                    }
                    rodando = False

                # Botão "CPU VS CPU"
                elif botao_jogar_direita.collidepoint(event.pos):
                    quantidade = int(texto_quantidade) if texto_quantidade.isdigit() else 0
                    resultado = {
                        "modo": "cpu_vs_cpu",
                        "tipo": "Gráfico" if radio_btt_modo == 1 else "Simulação",
                        "quantidade_partidas": quantidade
                    }
                    rodando = False

                # clicar na caixa de texto ativa/desativa o "foco"
                if radio_btt_modo == 2 and caixa_texto.collidepoint(event.pos):
                    caixa_texto_ativa = True
                else:
                    caixa_texto_ativa = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = event.pos
                if ((mouse[0]-opcao1[0])**2 + (mouse[1]-opcao1[1])**2) <= 20**2:
                    radio_btt_modo = 1

                if ((mouse[0]-opcao2[0])**2 + (mouse[1]-opcao2[1])**2) <= 20**2:
                    radio_btt_modo = 2

                if ((mouse[0]-opcao3[0])**2 + (mouse[1]-opcao3[1])**2) <= 20**2:
                    radio_btt_cpu = 1

                if ((mouse[0]-opcao4[0])**2 + (mouse[1]-opcao4[1])**2) <= 20**2:
                    radio_btt_cpu = 2

                if ((mouse[0]-opcao5[0])**2 + (mouse[1]-opcao5[1])**2) <= 20**2:
                    radio_btt_humano = 1

                if ((mouse[0]-opcao6[0])**2 + (mouse[1]-opcao6[1])**2) <= 20**2:
                    radio_btt_humano = 2

            if event.type == pygame.KEYDOWN and caixa_texto_ativa:
                if event.key == pygame.K_BACKSPACE:
                    texto_quantidade = texto_quantidade[:-1]
                elif event.unicode.isdigit():
                    if len(texto_quantidade) < 3:
                        texto_quantidade += event.unicode

        for opcao in [opcao1, opcao2, opcao3, opcao4, opcao5, opcao6]:
            pygame.draw.circle(janela, (255,255,255), opcao, 8, 2)

        if radio_btt_modo == 1:
            pygame.draw.circle(janela, (0,150,255), opcao1, 4)
        if radio_btt_modo == 2:
            pygame.draw.circle(janela, (0,150,255), opcao2, 4)
        if radio_btt_cpu == 1:
            pygame.draw.circle(janela, (0,150,255), opcao3, 4)
        if radio_btt_cpu == 2:
            pygame.draw.circle(janela, (0,150,255), opcao4, 4)
        if radio_btt_humano == 1:
            pygame.draw.circle(janela, (0,150,255), opcao5, 4)
        if radio_btt_humano == 2:
            pygame.draw.circle(janela, (0,150,255), opcao6, 4)

        texto = font.render("JOGAR", True, (255, 255, 255))
        texto_botao = texto.get_rect(center=botao_jogar_esquerda.center)
        pygame.draw.rect(janela, (0, 128, 255), botao_jogar_esquerda)
        janela.blit(texto, texto_botao)

        texto = font.render("JOGAR", True, (255, 255, 255))
        texto_botao = texto.get_rect(center=botao_jogar_direita.center)
        pygame.draw.rect(janela, (0, 128, 255), botao_jogar_direita)
        janela.blit(texto, texto_botao)

        texto = font.render("Damas", True, (255, 255, 255))
        janela.blit(texto, texto.get_rect(center=(350, 100)))

        pygame.draw.line(janela, (255, 255, 255), (350, 130), (350, 460), 1)

        texto = font_menor.render("CPU VS CPU", True, (255, 255, 255))
        janela.blit(texto, texto.get_rect(center=(525, 150)))

        texto = font_menor.render("Modo de jogo:", True, (255, 255, 255))
        janela.blit(texto, texto.get_rect(center=(437.5, 200)))

        texto = font_menor.render("Gráfico", True, (255, 255, 255))
        janela.blit(texto, (412, 231))

        texto = font_menor.render("Simulação", True, (255, 255, 255))
        janela.blit(texto, (412, 252))

        if radio_btt_modo == 2:
            texto = font_menor.render("Quantidade de partidas:", True, (255, 255, 255))
            janela.blit(texto, (393.75, 300))

            cor_borda = (0, 150, 255) if caixa_texto_ativa else (255, 255, 255)
            pygame.draw.rect(janela, cor_borda, caixa_texto, 2)

            texto_digitado = font_menor.render(texto_quantidade, True, (255, 255, 255))
            janela.blit(texto_digitado, (caixa_texto.x + 8, caixa_texto.y + 2))

            if caixa_texto_ativa and pygame.time.get_ticks() % 1000 < 500:
                cursor_x = caixa_texto.x + 8 + texto_digitado.get_width() + 2
                pygame.draw.line(janela, (255, 255, 255),
                                  (cursor_x, caixa_texto.y + 3),
                                  (cursor_x, caixa_texto.y + 17), 1)

        texto = font_menor.render("Humano VS CPU", True, (255, 255, 255))
        janela.blit(texto, texto.get_rect(center=(175, 150)))

        texto = font_menor.render("Humano", True, (255, 255, 255))
        janela.blit(texto, texto.get_rect(center=(87.5, 200)))

        texto = font_menor.render("Com MCTS", True, (255, 255, 255))
        janela.blit(texto, (62, 231))

        texto = font_menor.render("Sem MCTS", True, (255, 255, 255))
        janela.blit(texto, (62, 252))

        texto = font_menor.render("CPU", True, (255, 255, 255))
        janela.blit(texto, texto.get_rect(center=(262.5, 200)))

        texto = font_menor.render("Minimax", True, (255, 255, 255))
        janela.blit(texto, (247, 231))

        texto = font_menor.render("MCTS", True, (255, 255, 255))
        janela.blit(texto, (247,  252))

        pygame.display.update()

    return resultado