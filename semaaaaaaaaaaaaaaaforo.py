import pygame, sys

pygame.init()

LARGURA         = 900
ALTURA          = 540
FPS             = 60
ALTURA_PAINEL   = 120                      
ALTURA_DESENHO  = ALTURA - ALTURA_PAINEL   
CENTRO_VERTICAL = ALTURA_DESENHO // 2 - 10  

# tempo de cada fase em seg
T_VERDE     = 8.0
T_AMARELO   = 3.0
T_PEDESTRE  = 6.0
T_PISCA     = 0.48  

FUNDO         = (11,  16,  28)
COR_PAINEL    = (7,   11,  21)
DIVISOR       = (25,  38,  60)
COR_POSTE     = (72,  84, 102)
CAIXOTE       = (16,  23,  38)
CAIXOTE_BORDA = (44,  54,  70)

# rgb das luzes
LAMPADA = {
    'vermelho': {'aceso': (255,  60,  60), 'apagado': ( 58, 10, 10), 'brilho': (180,  20,  20)},
    'amarelo':  {'aceso': (251, 191,  36), 'apagado': ( 60, 40,  0), 'brilho': (200, 150,  10)},
    'verde':    {'aceso': ( 34, 212, 110), 'apagado': (  3, 43, 20), 'brilho': ( 12, 160,  60)},
}

X_NS  = 180   # carros norte sul
X_PED = 450   # pedestres
X_LO  = 720   # carros leste oeste


class Semaforo:
    """Desenha um semáforo e guarda qual lâmpada está acesa.
    tipo='carro' tem 3 luzes; tipo='pedestre' tem 2 (sem amarelo)."""

    _fonte: pygame.font.Font | None = None  

    def __init__(self, x: int, y: int, tipo: str = 'carro', rotulo: str = '') -> None:
        self.x, self.y = x, y
        self.tipo      = tipo
        self.rotulo    = rotulo
        self.estado    = 'vermelho'
        self.acesa     = True         # False = apagada

        # verificador se é do carro
        self.largura = 52 if tipo == 'carro' else 44
        self.altura  = 152 if tipo == 'carro' else 108

        self.lampadas = (
            ('vermelho', 'amarelo', 'verde') if tipo == 'carro'
            else ('vermelho', 'verde')
        )

        self.raio   = 14
        self.espaco = self.altura // len(self.lampadas)

    def definir(self, estado: str, acesa: bool = True) -> None:
        """Troca a lâmpada acesa. acesa=False apaga tudo (pisca noturno)."""
        self.estado, self.acesa = estado, acesa

    def desenhar(self, tela: pygame.Surface) -> None:
        if Semaforo._fonte is None:
            Semaforo._fonte = pygame.font.SysFont('Consolas', 10, bold=True)

        x, y      = self.x, self.y
        larg, alt = self.largura, self.altura

        # poste
        pygame.draw.line(tela, COR_POSTE, (x, y + alt // 2), (x, y + alt // 2 + 55), 6)
        pygame.draw.circle(tela, COR_POSTE, (x, y + alt // 2 + 56), 8)

        # Caixa do semaforo
        pygame.draw.rect(tela, (0, 0, 0),     (x-larg//2+3, y-alt//2+3, larg, alt), border_radius=6)
        pygame.draw.rect(tela, CAIXOTE,       (x-larg//2,   y-alt//2,   larg, alt), border_radius=6)
        pygame.draw.rect(tela, CAIXOTE_BORDA, (x-larg//2,   y-alt//2,   larg, alt), 2, border_radius=6)
        pygame.draw.rect(tela, (9, 14, 25),   (x-larg//2+4, y-alt//2+4, larg-8, alt-8), border_radius=4)

        for i, nome in enumerate(self.lampadas):
            y_lamp = y - alt // 2 + self.espaco // 2 + i * self.espaco
            ativa  = (nome == self.estado) and self.acesa
            cor    = LAMPADA[nome]['aceso'] if ativa else LAMPADA[nome]['apagado']

            # efeito de luz acesa/apagada
            if ativa:
                cor_brilho = LAMPADA[nome]['brilho']
                sup_brilho = pygame.Surface((54, 54), pygame.SRCALPHA)
                for raio in range(25, 7, -2):
                    alfa = max(0, 115 - (25 - raio) * 10)
                    pygame.draw.circle(sup_brilho, (*cor_brilho, alfa), (27, 27), raio)
                tela.blit(sup_brilho, (x - 27, y_lamp - 27))

            pygame.draw.circle(tela, cor, (x, y_lamp), self.raio)

            # reflexo da luz
            if ativa:
                cor_reflexo = tuple(min(255, c + 70) for c in cor)
                pygame.draw.circle(tela, cor_reflexo,
                                   (x - self.raio // 3 + 1, y_lamp - self.raio // 3 + 1), 4)

        texto_rotulo = Semaforo._fonte.render(self.rotulo, True, (88, 104, 128))
        tela.blit(texto_rotulo, (x - texto_rotulo.get_width() // 2, y + alt // 2 + 70))


class Interruptor:
    ## switch do iphone

    def __init__(self, x: int, y: int) -> None:
        self.x, self.y  = x, y
        self.ligado     = False
        self.largura    = 64
        self.altura     = 32
        self._fonte_grande:  pygame.font.Font | None = None
        self._fonte_pequena: pygame.font.Font | None = None

    def alternar(self) -> None:
        self.ligado = not self.ligado

    def clicado(self, mx: int, my: int) -> bool:
        """True se o clique caiu dentro da chavinha."""
        return (self.x <= mx <= self.x + self.largura and
                self.y <= my <= self.y + self.altura)

    def desenhar(self, tela: pygame.Surface) -> None:
        if self._fonte_grande is None:
            self._fonte_grande  = pygame.font.SysFont('Consolas', 12, bold=True)
            self._fonte_pequena = pygame.font.SysFont('Consolas', 10)

        ligado = self.ligado

        cor_trilha = (145, 106,  4) if ligado else (26, 40, 62)
        cor_borda  = (208, 160, 12) if ligado else (50, 70, 102)
        pygame.draw.rect(tela, cor_trilha, (self.x, self.y, self.largura, self.altura), border_radius=16)
        pygame.draw.rect(tela, cor_borda,  (self.x, self.y, self.largura, self.altura), 2, border_radius=16)
        x_bolinha   = self.x + self.largura - 18 if ligado else self.x + 18
        cor_bolinha = (238, 206, 80) if ligado else (190, 202, 218)
        pygame.draw.circle(tela, cor_bolinha, (x_bolinha, self.y + self.altura // 2), 12)
        pygame.draw.circle(tela, cor_borda,   (x_bolinha, self.y + self.altura // 2), 12, 1)

        titulo = self._fonte_pequena.render('MODO NOTURNO', True, (130, 155, 195))
        tela.blit(titulo, (self.x + self.largura // 2 - titulo.get_width() // 2, self.y - 18))

        texto_estado = 'LIGADO' if ligado else 'DESLIGADO'
        cor_estado   = (251, 191, 36) if ligado else (60, 80, 112)
        sup_estado   = self._fonte_grande.render(texto_estado, True, cor_estado)
        tela.blit(sup_estado, (self.x + self.largura // 2 - sup_estado.get_width() // 2,
                               self.y + self.altura + 4))


class Cruzamento:
    
    FASES = [
        # sem_ns       sem_lo       pedestre     duracao     descricao
        ('verde',    'vermelho', 'vermelho', T_VERDE,    'Verde N-S  |  L-O aguarda'),
        ('amarelo',  'vermelho', 'vermelho', T_AMARELO,  'Amarelo N-S  |  Transicao'),
        ('vermelho', 'vermelho', 'verde',    T_PEDESTRE, 'Pedestres atravessam  (ambos fechados)'),
        ('vermelho', 'verde',    'vermelho', T_VERDE,    'Verde L-O  |  N-S aguarda'),
        ('vermelho', 'amarelo',  'vermelho', T_AMARELO,  'Amarelo L-O  |  Transicao'),
    ]

    def __init__(self) -> None:
        self.fase_idx    = 0
        self.fase_tempo  = 0.0
        self.pisca_tempo = 0.0
        self.pisca       = True
        self.noturno     = False
        self.pausado     = False
        self.velocidade  = 1.0

        self.sem_ns  = Semaforo(X_NS,  CENTRO_VERTICAL, 'carro',     'Carros N-S')
        self.sem_lo  = Semaforo(X_LO,  CENTRO_VERTICAL, 'carro',     'Carros L-O')
        self.sem_ped = Semaforo(X_PED, CENTRO_VERTICAL, 'pedestre',  'Pedestres')
        self.semaforos = [self.sem_ns, self.sem_ped, self.sem_lo] 

        self.interruptor = Interruptor(LARGURA // 2 - 32, ALTURA - ALTURA_PAINEL + 28)

        self._aplicar()

    def _aplicar(self) -> None:
        """Joga a fase atual nos 3 semáforos."""
        ns, lo, ped, _, _ = self.FASES[self.fase_idx]
        self.sem_ns.definir(ns)
        self.sem_lo.definir(lo)
        self.sem_ped.definir(ped)

    def atualizar(self, dt: float) -> None:
        """dt = segundos desde o último quadro."""
        if self.pausado:
            return

        dt *= self.velocidade

        era_noturno  = self.noturno
        self.noturno = self.interruptor.ligado

        # timerzinho
        self.pisca_tempo += dt
        if self.pisca_tempo >= T_PISCA:
            self.pisca_tempo = 0
            self.pisca       = not self.pisca

        if self.noturno:
            self.sem_ns.definir('amarelo', self.pisca)
            self.sem_lo.definir('amarelo', self.pisca)
            self.sem_ped.definir('vermelho', True)
        else:
            # se sai do norturno ele zera
            if era_noturno:
                self.fase_idx   = 0
                self.fase_tempo = 0.0

            self.fase_tempo += dt
            _, _, _, duracao, _ = self.FASES[self.fase_idx]

            # reset da table
            if self.fase_tempo >= duracao:
                self.fase_tempo = 0.0
                self.fase_idx   = (self.fase_idx + 1) % len(self.FASES)

            self._aplicar()

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.fill(FUNDO)
        pygame.draw.line(tela, DIVISOR, (0, ALTURA_DESENHO), (LARGURA, ALTURA_DESENHO), 1)
        for sem in self.semaforos:
            sem.desenhar(tela)

        self._painel(tela)

    def _painel(self, tela: pygame.Surface) -> None:
        y_painel = ALTURA_DESENHO
        sup_painel = pygame.Surface((LARGURA, ALTURA_PAINEL), pygame.SRCALPHA)
        sup_painel.fill((*COR_PAINEL, 252))
        tela.blit(sup_painel, (0, y_painel))

        fonte_grande  = pygame.font.SysFont('Consolas', 13, bold=True)
        fonte_pequena = pygame.font.SysFont('Consolas', 10)

        if self.noturno:
            texto_fase, cor_texto = '  MODO NOTURNO  (pisca-amarelo)', (251, 191, 36)
        elif self.pausado:
            texto_fase, cor_texto = '  PAUSADO', (195, 195, 200)
        else:
            _, _, _, _, descricao = self.FASES[self.fase_idx]
            texto_fase, cor_texto = '  Fase: ' + descricao, (220, 232, 242)
        tela.blit(fonte_grande.render(texto_fase, True, cor_texto), (0, y_painel + 10))

        # timer da prox fase
        if not self.noturno and not self.pausado:
            _, _, _, duracao, _ = self.FASES[self.fase_idx]
            restante = f'  Proxima fase em: {max(0.0, duracao - self.fase_tempo):.1f}s'
            if self.velocidade != 1.0:
                restante += f'   (vel {self.velocidade:.2f}x)'
            tela.blit(fonte_pequena.render(restante, True, (88, 104, 128)), (0, y_painel + 34))

        self.interruptor.desenhar(tela)

        atalhos     = '[N]/Interruptor  Noturno     [Espaco]  Pausar     [+/-]  Velocidade     [Esc]  Sair'
        sup_atalhos = fonte_pequena.render(atalhos, True, (36, 52, 74))
        tela.blit(sup_atalhos, (LARGURA // 2 - sup_atalhos.get_width() // 2,
                                y_painel + ALTURA_PAINEL - 20))


def main() -> None:
    tela       = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption('Semaforos')
    relogio    = pygame.time.Clock()
    cruzamento = Cruzamento()

    while True:
        dt = relogio.tick(FPS) / 1000.0   

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif evento.key == pygame.K_n:
                    cruzamento.interruptor.alternar()
                elif evento.key == pygame.K_SPACE:
                    cruzamento.pausado = not cruzamento.pausado
                elif evento.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                    cruzamento.velocidade = min(8.0, cruzamento.velocidade + 0.5)
                elif evento.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    cruzamento.velocidade = max(0.25, cruzamento.velocidade - 0.25)
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if cruzamento.interruptor.clicado(*evento.pos):
                    cruzamento.interruptor.alternar()

        cruzamento.atualizar(dt)
        cruzamento.desenhar(tela)
        pygame.display.flip()


if __name__ == '__main__':
    main()
