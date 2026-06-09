"""
Cruzamento de Semáforos
2 semáforos de carro (N-S e L-O) + 1 semáforo de pedestre

Regras:
  Pedestre abre SOMENTE quando ambos os carros estão fechados (vermelho)
  Interruptor ativa modo noturno manual (pisca-amarelo nos carros, pedestre vermelho)

[N] / Interruptor  — modo noturno
[Espaco]           — pausar / continuar
[+/-]              — velocidade
[Esc]              — sair
"""
import pygame, sys

pygame.init()

# ── Configurações da janela ────────────────────────────────────────────────────
# LARGURA e ALTURA definem o tamanho da janela em pixels.
# ALTURA_PAINEL é a faixa inferior reservada para o painel de informações.
# ALTURA_DESENHO é o espaço útil acima do painel, onde os semáforos ficam.
# CENTRO_VERTICAL é a linha y no qual os 3 semáforos ficam alinhados.
LARGURA         = 900
ALTURA          = 540
FPS             = 60           # quadros por segundo — controla a suavidade da animação
ALTURA_PAINEL   = 120          # altura do painel inferior de informações
ALTURA_DESENHO  = ALTURA - ALTURA_PAINEL  # espaço disponível para os semáforos (= 420 px)
CENTRO_VERTICAL = ALTURA_DESENHO // 2 - 10  # ponto central vertical dos semáforos

# ── Duração de cada fase (em segundos) ────────────────────────────────────────
# Esses valores controlam por quanto tempo cada luz permanece acesa.
# T_PEDESTRE é o tempo que o pedestre tem para atravessar.
# T_PISCA é o meio-período do pisca no modo noturno (aceso/apagado a cada intervalo).
T_VERDE     = 8.0   # tempo do verde dos carros
T_AMARELO   = 3.0   # tempo do amarelo (transição entre fases)
T_PEDESTRE  = 6.0   # tempo do verde do pedestre
T_PISCA     = 0.48  # intervalo do pisca-pisca noturno

# ── Cores (formato RGB) ────────────────────────────────────────────────────────
# Cada cor é uma tupla (R, G, B) com valores de 0 a 255.
FUNDO         = (11,  16,  28)   # fundo da janela (azul muito escuro)
COR_PAINEL    = (7,   11,  21)   # fundo do painel inferior
DIVISOR       = (25,  38,  60)   # linha separadora entre semáforos e painel
COR_POSTE     = (72,  84, 102)   # cor do poste metálico
CAIXOTE       = (16,  23,  38)   # cor do caixote do semáforo
CAIXOTE_BORDA = (44,  54,  70)   # cor da borda do caixote

# Dicionário com as cores de cada lâmpada em três estados:
#   'aceso'   — lâmpada ligada (cor viva)
#   'apagado' — lâmpada desligada (cor escura, quase preta)
#   'halo'    — cor do brilho ao redor da lâmpada acesa
LAMPADA = {
    'vermelho': {'aceso': (255,  60,  60), 'apagado': ( 58, 10, 10), 'halo': (180,  20,  20)},
    'amarelo':  {'aceso': (251, 191,  36), 'apagado': ( 60, 40,  0), 'halo': (200, 150,  10)},
    'verde':    {'aceso': ( 34, 212, 110), 'apagado': (  3, 43, 20), 'halo': ( 12, 160,  60)},
}

# Posições horizontais (eixo X) dos 3 semáforos na janela.
# Ficam igualmente espaçados: esquerda (N-S), centro (pedestre), direita (L-O).
X_NS  = 180   # semáforo de carros Norte-Sul
X_PED = 450   # semáforo de pedestres
X_LO  = 720   # semáforo de carros Leste-Oeste


# ── Classe Semaforo ────────────────────────────────────────────────────────────
# Responsável por desenhar um semáforo e controlar qual lâmpada está acesa.
# tipo='carro'    → 3 lâmpadas: vermelho, amarelo, verde
# tipo='pedestre' → 2 lâmpadas: vermelho, verde (sem amarelo)
class Semaforo:
    # Fonte compartilhada entre todas as instâncias (carregada uma só vez)
    _fonte: pygame.font.Font | None = None

    def __init__(self, x: int, y: int, tipo: str = 'carro', rotulo: str = '') -> None:
        self.x, self.y = x, y        # posição central do semáforo na tela
        self.tipo      = tipo        # 'carro' ou 'pedestre'
        self.rotulo    = rotulo      # texto exibido abaixo do poste
        self.estado    = 'vermelho'  # nome da lâmpada ativa no momento
        self.acesa     = True        # se False, a lâmpada fica apagada (efeito pisca)

        # Dimensões do caixote variam conforme o tipo:
        # semáforo de carro é mais alto pois tem 3 lâmpadas
        self.largura = 52 if tipo == 'carro' else 44
        self.altura  = 152 if tipo == 'carro' else 108

        # Tupla com os nomes das lâmpadas na ordem de cima para baixo
        self.lampadas = (
            ('vermelho', 'amarelo', 'verde') if tipo == 'carro'
            else ('vermelho', 'verde')
        )

        self.raio   = 14                            # raio de cada lâmpada em pixels
        self.espaco = self.altura // len(self.lampadas)  # espaço vertical por lâmpada

    def definir(self, estado: str, acesa: bool = True) -> None:
        """Muda o estado do semáforo. acesa=False apaga a lâmpada (usado no pisca noturno)."""
        self.estado, self.acesa = estado, acesa

    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha o poste, o caixote, as lâmpadas e o rótulo na superfície fornecida."""
        # Carrega a fonte na primeira vez que qualquer semáforo for desenhado
        if Semaforo._fonte is None:
            Semaforo._fonte = pygame.font.SysFont('Consolas', 10, bold=True)

        x, y         = self.x, self.y
        larg, alt    = self.largura, self.altura

        # Poste vertical: começa na borda inferior do caixote e desce 55 px
        # O círculo no fim representa a base chumbada no chão
        pygame.draw.line(tela, COR_POSTE, (x, y + alt // 2), (x, y + alt // 2 + 55), 6)
        pygame.draw.circle(tela, COR_POSTE, (x, y + alt // 2 + 56), 8)

        # Caixote: retângulo arredondado com 3 camadas para dar efeito de profundidade
        # 1ª camada — sombra deslocada 3 px para baixo/direita
        pygame.draw.rect(tela, (0, 0, 0),       (x-larg//2+3, y-alt//2+3, larg, alt), border_radius=6)
        # 2ª camada — corpo principal
        pygame.draw.rect(tela, CAIXOTE,         (x-larg//2,   y-alt//2,   larg, alt), border_radius=6)
        # 3ª camada — borda visível para dar volume
        pygame.draw.rect(tela, CAIXOTE_BORDA,   (x-larg//2,   y-alt//2,   larg, alt), 2, border_radius=6)
        # Interior levemente mais escuro que o corpo (recuo visual)
        pygame.draw.rect(tela, (9, 14, 25), (x-larg//2+4, y-alt//2+4, larg-8, alt-8), border_radius=4)

        # Lâmpadas: percorre cada lâmpada e calcula sua posição Y dentro do caixote
        for i, nome in enumerate(self.lampadas):
            # Centro Y da lâmpada: distribui uniformemente dentro do caixote
            y_lamp = y - alt // 2 + self.espaco // 2 + i * self.espaco
            ativa  = (nome == self.estado) and self.acesa
            cor    = LAMPADA[nome]['aceso'] if ativa else LAMPADA[nome]['apagado']

            # Halo de luz: superfície transparente com círculos de alfa decrescente
            # Cria o efeito de brilho difuso ao redor da lâmpada acesa
            if ativa:
                cor_halo = LAMPADA[nome]['halo']
                sup_halo = pygame.Surface((54, 54), pygame.SRCALPHA)  # superfície com transparência
                for raio in range(25, 7, -2):
                    # Quanto maior o raio, mais transparente (efeito de difusão da luz)
                    alfa = max(0, 115 - (25 - raio) * 10)
                    pygame.draw.circle(sup_halo, (*cor_halo, alfa), (27, 27), raio)
                tela.blit(sup_halo, (x - 27, y_lamp - 27))

            # Corpo da lâmpada (círculo principal)
            pygame.draw.circle(tela, cor, (x, y_lamp), self.raio)

            # Reflexo especular: pequeno círculo mais claro no canto superior esquerdo
            # Simula o brilho da luz incidindo na superfície da lâmpada
            if ativa:
                cor_brilho = tuple(min(255, c + 70) for c in cor)
                pygame.draw.circle(tela, cor_brilho,
                                   (x - self.raio // 3 + 1, y_lamp - self.raio // 3 + 1), 4)

        # Rótulo centralizado abaixo do poste
        texto_rotulo = Semaforo._fonte.render(self.rotulo, True, (88, 104, 128))
        tela.blit(texto_rotulo, (x - texto_rotulo.get_width() // 2, y + alt // 2 + 70))


# ── Classe Interruptor ─────────────────────────────────────────────────────────
# Representa o botão de alternância visual do modo noturno no painel.
# O usuário pode clicar nele com o mouse ou pressionar [N] no teclado.
class Interruptor:
    def __init__(self, x: int, y: int) -> None:
        self.x, self.y  = x, y       # posição do canto superior esquerdo
        self.ligado     = False       # False = desligado, True = ligado
        self.largura    = 64
        self.altura     = 32
        self._fonte_grande:  pygame.font.Font | None = None
        self._fonte_pequena: pygame.font.Font | None = None

    def alternar(self) -> None:
        """Inverte o estado do interruptor (liga/desliga)."""
        self.ligado = not self.ligado

    def clicado(self, mx: int, my: int) -> bool:
        """Retorna True se as coordenadas do clique do mouse estão dentro do interruptor."""
        return (self.x <= mx <= self.x + self.largura and
                self.y <= my <= self.y + self.altura)

    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha o interruptor com trilha, bolinha deslizante e textos de estado."""
        # Inicializa as fontes na primeira chamada
        if self._fonte_grande is None:
            self._fonte_grande  = pygame.font.SysFont('Consolas', 12, bold=True)
            self._fonte_pequena = pygame.font.SysFont('Consolas', 10)

        ligado = self.ligado

        # Trilha do interruptor: muda de cor conforme o estado
        # Ligado → dourado/amarelado    Desligado → azul escuro
        cor_trilha = (145, 106,  4) if ligado else (26, 40, 62)
        cor_borda  = (208, 160, 12) if ligado else (50, 70, 102)
        pygame.draw.rect(tela, cor_trilha, (self.x, self.y, self.largura, self.altura), border_radius=16)
        pygame.draw.rect(tela, cor_borda,  (self.x, self.y, self.largura, self.altura), 2, border_radius=16)

        # Bolinha deslizante: posição vai para a direita quando ligado
        x_bolinha   = self.x + self.largura - 18 if ligado else self.x + 18
        cor_bolinha = (238, 206, 80) if ligado else (190, 202, 218)
        pygame.draw.circle(tela, cor_bolinha, (x_bolinha, self.y + self.altura // 2), 12)
        pygame.draw.circle(tela, cor_borda,   (x_bolinha, self.y + self.altura // 2), 12, 1)

        # Título "MODO NOTURNO" centralizado acima do interruptor
        titulo = self._fonte_pequena.render('MODO NOTURNO', True, (130, 155, 195))
        tela.blit(titulo, (self.x + self.largura // 2 - titulo.get_width() // 2, self.y - 18))

        # Texto de estado ("LIGADO" / "DESLIGADO") centralizado abaixo do interruptor
        texto_estado = 'LIGADO' if ligado else 'DESLIGADO'
        cor_estado   = (251, 191, 36) if ligado else (60, 80, 112)
        sup_estado   = self._fonte_grande.render(texto_estado, True, cor_estado)
        tela.blit(sup_estado, (self.x + self.largura // 2 - sup_estado.get_width() // 2,
                               self.y + self.altura + 4))


# ── Classe Cruzamento ──────────────────────────────────────────────────────────
# Controlador principal: orquestra as fases dos semáforos,
# o modo noturno e o painel de informações.
class Cruzamento:
    # Tabela de fases: cada linha define o estado dos 3 semáforos,
    # a duração da fase e o texto descritivo exibido no painel.
    # Regra garantida aqui: pedestre ('verde') só aparece na fase de índice 2,
    # quando sem_ns='vermelho' E sem_lo='vermelho' ao mesmo tempo.
    FASES = [
        # sem_ns        sem_lo        pedestre      duracao      descricao
        ('verde',     'vermelho',  'vermelho',  T_VERDE,    'Verde N-S  |  L-O aguarda'),
        ('amarelo',   'vermelho',  'vermelho',  T_AMARELO,  'Amarelo N-S  |  Transicao'),
        ('vermelho',  'vermelho',  'verde',     T_PEDESTRE, 'Pedestres atravessam  (ambos fechados)'),
        ('vermelho',  'verde',     'vermelho',  T_VERDE,    'Verde L-O  |  N-S aguarda'),
        ('vermelho',  'amarelo',   'vermelho',  T_AMARELO,  'Amarelo L-O  |  Transicao'),
    ]

    def __init__(self) -> None:
        self.fase_idx    = 0      # índice da fase atual na tabela FASES
        self.fase_tempo  = 0.0    # tempo acumulado dentro da fase atual (segundos)
        self.pisca_tempo = 0.0    # tempo acumulado para o pisca noturno
        self.pisca       = True   # estado atual do pisca (True=aceso, False=apagado)
        self.noturno     = False  # indica se o modo noturno está ativo
        self.pausado     = False  # indica se a simulação está pausada
        self.velocidade  = 1.0    # multiplicador de velocidade (1.0 = tempo real)

        # Instancia os 3 semáforos nas posições definidas nas constantes
        self.sem_ns  = Semaforo(X_NS,  CENTRO_VERTICAL, 'carro',     'Carros N-S')
        self.sem_lo  = Semaforo(X_LO,  CENTRO_VERTICAL, 'carro',     'Carros L-O')
        self.sem_ped = Semaforo(X_PED, CENTRO_VERTICAL, 'pedestre',  'Pedestres')
        # Lista usada para iterar o desenho na ordem: esquerda, centro, direita
        self.semaforos = [self.sem_ns, self.sem_ped, self.sem_lo]

        # Interruptor de modo noturno posicionado no centro do painel inferior
        self.interruptor = Interruptor(LARGURA // 2 - 32, ALTURA - ALTURA_PAINEL + 28)

        # Aplica o estado inicial (fase 0: N-S verde)
        self._aplicar()

    def _aplicar(self) -> None:
        """Lê a fase atual da tabela e atualiza os 3 semáforos de uma vez."""
        ns, lo, ped, _, _ = self.FASES[self.fase_idx]
        self.sem_ns.definir(ns)
        self.sem_lo.definir(lo)
        self.sem_ped.definir(ped)

    def atualizar(self, dt: float) -> None:
        """
        Atualiza a lógica do cruzamento a cada quadro.
        dt = tempo em segundos desde o último quadro (fornecido pelo relogio do pygame).
        """
        if self.pausado:
            return  # nada muda enquanto pausado

        dt *= self.velocidade  # aplica o multiplicador de velocidade

        # Guarda o estado anterior do modo noturno para detectar a transição de saída
        era_noturno  = self.noturno
        self.noturno = self.interruptor.ligado  # modo noturno depende só do interruptor

        # Atualiza o timer do pisca-amarelo
        # Quando pisca_tempo atinge T_PISCA, inverte o estado (aceso ↔ apagado)
        self.pisca_tempo += dt
        if self.pisca_tempo >= T_PISCA:
            self.pisca_tempo = 0
            self.pisca       = not self.pisca

        if self.noturno:
            # Modo noturno: ambos os semáforos de carro piscam amarelo
            # self.pisca alterna True/False a cada T_PISCA segundos
            self.sem_ns.definir('amarelo', self.pisca)
            self.sem_lo.definir('amarelo', self.pisca)
            self.sem_ped.definir('vermelho', True)  # pedestre fica vermelho fixo
        else:
            # Se acabou de sair do modo noturno, reinicia o ciclo do zero
            if era_noturno:
                self.fase_idx   = 0
                self.fase_tempo = 0.0

            # Avança o temporizador da fase atual
            self.fase_tempo += dt
            _, _, _, duracao, _ = self.FASES[self.fase_idx]

            # Quando o tempo da fase se esgota, avança para a próxima
            # O operador % faz o ciclo voltar à fase 0 após a última
            if self.fase_tempo >= duracao:
                self.fase_tempo = 0.0
                self.fase_idx   = (self.fase_idx + 1) % len(self.FASES)

            # Aplica os estados dos semáforos conforme a fase atual
            self._aplicar()

    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha o fundo, os semáforos e o painel de informações."""
        tela.fill(FUNDO)  # limpa a tela com a cor de fundo a cada quadro

        # Linha fina que separa visualmente a área dos semáforos do painel
        pygame.draw.line(tela, DIVISOR, (0, ALTURA_DESENHO), (LARGURA, ALTURA_DESENHO), 1)

        # Desenha cada semáforo (sem_ns, sem_ped, sem_lo) da esquerda para a direita
        for sem in self.semaforos:
            sem.desenhar(tela)

        self._painel(tela)

    def _painel(self, tela: pygame.Surface) -> None:
        """Desenha o painel inferior com fase atual, contagem regressiva, interruptor e atalhos."""
        y_painel = ALTURA_DESENHO  # coordenada Y onde o painel começa

        # Fundo semitransparente do painel usando Surface com canal alfa
        sup_painel = pygame.Surface((LARGURA, ALTURA_PAINEL), pygame.SRCALPHA)
        sup_painel.fill((*COR_PAINEL, 252))  # quase opaco (252/255)
        tela.blit(sup_painel, (0, y_painel))

        # Fontes usadas no painel
        fonte_grande  = pygame.font.SysFont('Consolas', 13, bold=True)  # destaque
        fonte_pequena = pygame.font.SysFont('Consolas', 10)              # detalhes

        # Texto da fase/estado principal (linha superior do painel)
        if self.noturno:
            texto_fase, cor_texto = '  MODO NOTURNO  (pisca-amarelo)', (251, 191, 36)
        elif self.pausado:
            texto_fase, cor_texto = '  PAUSADO', (195, 195, 200)
        else:
            _, _, _, _, descricao = self.FASES[self.fase_idx]
            texto_fase, cor_texto = '  Fase: ' + descricao, (220, 232, 242)
        tela.blit(fonte_grande.render(texto_fase, True, cor_texto), (0, y_painel + 10))

        # Contagem regressiva até a próxima fase (só exibe fora do modo noturno/pausado)
        if not self.noturno and not self.pausado:
            _, _, _, duracao, _ = self.FASES[self.fase_idx]
            restante = f'  Proxima fase em: {max(0.0, duracao - self.fase_tempo):.1f}s'
            if self.velocidade != 1.0:
                restante += f'   (vel {self.velocidade:.2f}x)'  # exibe o multiplicador se ≠ 1
            tela.blit(fonte_pequena.render(restante, True, (88, 104, 128)), (0, y_painel + 34))

        # Desenha o interruptor de modo noturno centralizado no painel
        self.interruptor.desenhar(tela)

        # Linha de atalhos de teclado no rodapé do painel
        atalhos     = '[N]/Interruptor  Noturno     [Espaco]  Pausar     [+/-]  Velocidade     [Esc]  Sair'
        sup_atalhos = fonte_pequena.render(atalhos, True, (36, 52, 74))
        tela.blit(sup_atalhos, (LARGURA // 2 - sup_atalhos.get_width() // 2,
                                y_painel + ALTURA_PAINEL - 20))


# ── Função principal ───────────────────────────────────────────────────────────
# Inicializa a janela, o relogio de quadros e entra no loop principal do pygame.
def main() -> None:
    tela       = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption('Semaforos')
    relogio    = pygame.time.Clock()  # controla o FPS e fornece dt preciso
    cruzamento = Cruzamento()         # cria o cruzamento com todos os semáforos

    # Loop principal: roda a ~60 FPS até o usuário fechar a janela
    while True:
        # dt = tempo real do último quadro em segundos (ex: ~0.0167 a 60 FPS)
        dt = relogio.tick(FPS) / 1000.0

        # Processamento de eventos (teclado, mouse, fechar janela)
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif evento.key == pygame.K_n:
                    # [N] tem o mesmo efeito que clicar no interruptor
                    cruzamento.interruptor.alternar()
                elif evento.key == pygame.K_SPACE:
                    cruzamento.pausado = not cruzamento.pausado
                elif evento.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                    # Acelera a simulação até 8× (útil para testar o ciclo completo)
                    cruzamento.velocidade = min(8.0, cruzamento.velocidade + 0.5)
                elif evento.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    # Desacelera até 0.25× (câmera lenta)
                    cruzamento.velocidade = max(0.25, cruzamento.velocidade - 0.25)
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                # Clique com botão esquerdo: verifica se acertou o interruptor
                if cruzamento.interruptor.clicado(*evento.pos):
                    cruzamento.interruptor.alternar()

        cruzamento.atualizar(dt)   # atualiza a lógica (fases, timers, pisca)
        cruzamento.desenhar(tela)  # desenha tudo na tela
        pygame.display.flip()      # envia o quadro renderizado para a tela


if __name__ == '__main__':
    main()
