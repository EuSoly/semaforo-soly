import pygame, sys, random

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
T_VERMELHO  = 1.0   # tudo vermelho entre fases (momento de decisao)
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


# ===========================================================================
#  PARTE MATEMATICA
# ===========================================================================

# --- Teoria dos conjuntos ---------------------------------------------------
# VIAS    = vias de veiculos
# GRUPOS  = uniao das vias com o grupo de pedestres  (VIAS ∪ {'PED'})
# ESTADOS = conjunto formal de estados possiveis da maquina de estados
VIAS    = {'NS', 'LO'}
GRUPOS  = VIAS | {'PED'}
ESTADOS = {
    'NS_VERDE', 'NS_AMARELO',
    'LO_VERDE', 'LO_AMARELO',
    'PED_VERDE', 'TUDO_VERMELHO',
}

# Cada estado: cor de cada semaforo, duracao e uma descricao curta.
ESTADO_INFO = {
    'NS_VERDE':      {'ns': 'verde',    'lo': 'vermelho', 'ped': 'vermelho', 'dur': T_VERDE,    'desc': 'Via NS liberada'},
    'NS_AMARELO':    {'ns': 'amarelo',  'lo': 'vermelho', 'ped': 'vermelho', 'dur': T_AMARELO,  'desc': 'NS fechando'},
    'LO_VERDE':      {'ns': 'vermelho', 'lo': 'verde',    'ped': 'vermelho', 'dur': T_VERDE,    'desc': 'Via LO liberada'},
    'LO_AMARELO':    {'ns': 'vermelho', 'lo': 'amarelo',  'ped': 'vermelho', 'dur': T_AMARELO,  'desc': 'LO fechando'},
    'PED_VERDE':     {'ns': 'vermelho', 'lo': 'vermelho', 'ped': 'verde',    'dur': T_PEDESTRE, 'desc': 'Pedestres atravessam'},
    'TUDO_VERMELHO': {'ns': 'vermelho', 'lo': 'vermelho', 'ped': 'vermelho', 'dur': T_VERMELHO, 'desc': 'Tudo vermelho (decidindo)'},
}


# --- Logica proposicional (operadores explicitos) ---------------------------
# Python ja tem and/or/not, mas deixamos escrito pra mostrar a algebra booleana.
def NAO(a: bool) -> bool: return not a
def E(a: bool, b: bool) -> bool: return a and b
def OU(a: bool, b: bool) -> bool: return a or b


# --- Regras de decisao ------------------------------------------------------
# Entradas: A = carro na via NS, B = carro na via LO, P = pedestre aguardando.
# Prioridade definida: Pedestre > Via NS > Via LO.
#   atende_PED = P
#   atende_NS  = A E (NAO P)
#   atende_LO  = B E (NAO P) E (NAO A)
# Se ninguem solicita -> OCIOSO (permanece tudo vermelho).
def decidir(A: bool, B: bool, P: bool) -> str:
    atende_ped = P
    atende_ns  = E(A, NAO(P))
    atende_lo  = E(B, E(NAO(P), NAO(A)))

    if atende_ped: return 'PED'
    if atende_ns:  return 'NS'
    if atende_lo:  return 'LO'
    return 'OCIOSO'


# Para qual estado de saida cada decisao leva.
DECISAO_PARA_ESTADO = {
    'PED': 'PED_VERDE',
    'NS':  'NS_VERDE',
    'LO':  'LO_VERDE',
    'OCIOSO': 'TUDO_VERMELHO',
}


# --- Representacao binaria --------------------------------------------------
# 8 bits: NS_R NS_Y NS_G | LO_R LO_Y LO_G | PED_R PED_G  (1 = luz acesa)
def binario_do_estado(estado: str) -> str:
    info = ESTADO_INFO[estado]
    def trio(cor):
        return (
            '1' if cor == 'vermelho' else '0',
            '1' if cor == 'amarelo'  else '0',
            '1' if cor == 'verde'    else '0',
        )
    ns = ''.join(trio(info['ns']))
    lo = ''.join(trio(info['lo']))
    ped = ('1' if info['ped'] == 'vermelho' else '0') + ('1' if info['ped'] == 'verde' else '0')
    return f'{ns} {lo} {ped}'


def imprimir_tabela_verdade() -> None:
    """Imprime no console a tabela-verdade completa (8 linhas). Bom pra apresentacao."""
    print('\n=== TABELA-VERDADE ===')
    print('A=carro NS | B=carro LO | P=pedestre')
    print('-' * 58)
    print('A  B  P | Decisao | Estado de saida | Binario (NS LO PED)')
    print('-' * 58)
    for A in (0, 1):
        for B in (0, 1):
            for P in (0, 1):
                d = decidir(bool(A), bool(B), bool(P))
                est = DECISAO_PARA_ESTADO[d]
                print(f'{A}  {B}  {P} | {d:<7} | {est:<15} | {binario_do_estado(est)}')
    print('-' * 58)
    print(f'Conjunto de grupos: {GRUPOS}')
    print(f'Conjunto de estados: {ESTADOS}\n')


# ===========================================================================
#  PARTE VISUAL
# ===========================================================================

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

        titulo = self._fonte_pequena.render('EMERGENCIA', True, (130, 155, 195))
        tela.blit(titulo, (self.x + self.largura // 2 - titulo.get_width() // 2, self.y - 18))

        texto_estado = 'LIGADO' if ligado else 'DESLIGADO'
        cor_estado   = (251, 191, 36) if ligado else (60, 80, 112)
        sup_estado   = self._fonte_grande.render(texto_estado, True, cor_estado)
        tela.blit(sup_estado, (self.x + self.largura // 2 - sup_estado.get_width() // 2,
                               self.y + self.altura + 4))


class Cruzamento:

    def __init__(self) -> None:
        # estado da maquina de estados
        self.estado = 'NS_VERDE'
        self.tempo  = 0.0

        # entradas (sensores): carro NS, carro LO, pedestre aguardando
        self.in_ns  = True
        self.in_lo  = False
        self.in_ped = False
        self.decisao = 'NS'   # ultima decisao tomada (so pra mostrar no painel)

        self.pisca_tempo = 0.0
        self.pisca       = True
        self.noturno     = False     # modo emergencia (pisca amarelo)
        self.pausado     = False
        self.velocidade  = 1.0

        # as entradas sao geradas sozinhas (sensores simulados) pra logica rodar sem teclado
        self.auto_t = 0.0

        self.sem_ns  = Semaforo(X_NS,  CENTRO_VERTICAL, 'carro',     'Carros N-S')
        self.sem_lo  = Semaforo(X_LO,  CENTRO_VERTICAL, 'carro',     'Carros L-O')
        self.sem_ped = Semaforo(X_PED, CENTRO_VERTICAL, 'pedestre',  'Pedestres')
        self.semaforos = [self.sem_ns, self.sem_ped, self.sem_lo]

        self.interruptor = Interruptor(LARGURA // 2 - 32, ALTURA - ALTURA_PAINEL + 30)

        self._aplicar()

    def _aplicar(self) -> None:
        """Joga as cores do estado atual nos 3 semáforos."""
        info = ESTADO_INFO[self.estado]
        self.sem_ns.definir(info['ns'])
        self.sem_lo.definir(info['lo'])
        self.sem_ped.definir(info['ped'])

    def _proximo_estado(self) -> str:
        """Define a transicao da maquina de estados."""
        e = self.estado
        if e == 'NS_VERDE':   return 'NS_AMARELO'
        if e == 'NS_AMARELO': return 'TUDO_VERMELHO'
        if e == 'LO_VERDE':   return 'LO_AMARELO'
        if e == 'LO_AMARELO': return 'TUDO_VERMELHO'
        if e == 'PED_VERDE':  return 'TUDO_VERMELHO'
        # no tudo-vermelho a tabela-verdade decide quem vai
        self.decisao = decidir(self.in_ns, self.in_lo, self.in_ped)
        return DECISAO_PARA_ESTADO[self.decisao]

    def _conflito(self) -> set:
        """Checa seguranca via conjuntos: pedestre verde NAO pode coexistir com via verde.
        Retorna a intersecao (deve ser sempre vazia)."""
        verdes = set()
        if self.sem_ns.estado == 'verde' and self.sem_ns.acesa: verdes |= {'NS'}
        if self.sem_lo.estado == 'verde' and self.sem_lo.acesa: verdes |= {'LO'}
        ped_verde = self.sem_ped.estado == 'verde' and self.sem_ped.acesa
        if ped_verde:
            return verdes & VIAS   # intersecao
        return set()

    def atualizar(self, dt: float) -> None:
        """dt = segundos desde o último quadro."""
        if self.pausado:
            return

        dt *= self.velocidade

        # modo emergencia (interruptor) sobrepoe tudo: carros piscam amarelo
        era_noturno  = self.noturno
        self.noturno = self.interruptor.ligado

        self.pisca_tempo += dt
        if self.pisca_tempo >= T_PISCA:
            self.pisca_tempo = 0
            self.pisca       = not self.pisca

        if self.noturno:
            self.sem_ns.definir('amarelo', self.pisca)
            self.sem_lo.definir('amarelo', self.pisca)
            self.sem_ped.definir('vermelho', True)
            return

        # saiu da emergencia: recomeca no tudo-vermelho
        if era_noturno:
            self.estado = 'TUDO_VERMELHO'
            self.tempo  = 0.0

        # sensores simulados: atualiza as entradas de tempos em tempos
        self.auto_t += dt
        if self.auto_t >= 2.5:
            self.auto_t = 0.0
            self.in_ns = random.random() < 0.6
            self.in_lo = random.random() < 0.6
            if random.random() < 0.4:
                self.in_ped = True

        # avanca o tempo do estado atual
        self.tempo += dt
        if self.tempo >= ESTADO_INFO[self.estado]['dur']:
            self.tempo  = 0.0
            self.estado = self._proximo_estado()
            if self.estado == 'PED_VERDE':
                self.in_ped = False   # atende o pedido e zera o botao

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
        fonte_pequena = pygame.font.SysFont('Consolas', 11)

        # linha 1: estado atual
        if self.noturno:
            texto, cor = '  EMERGENCIA  (pisca-amarelo)', (251, 191, 36)
        elif self.pausado:
            texto, cor = '  PAUSADO', (195, 195, 200)
        else:
            info = ESTADO_INFO[self.estado]
            texto, cor = f'  Estado: {self.estado}  -  {info["desc"]}', (220, 232, 242)
        tela.blit(fonte_grande.render(texto, True, cor), (0, y_painel + 8))

        if not self.noturno and not self.pausado:
            # entradas + decisao (a logica rodando)
            decisao_live = decidir(self.in_ns, self.in_lo, self.in_ped)
            A, B, P = int(self.in_ns), int(self.in_lo), int(self.in_ped)
            l2 = f'  Entradas  A(NS)={A}  B(LO)={B}  P(ped)={P}   ->  decisao: {decisao_live}'
            tela.blit(fonte_pequena.render(l2, True, (150, 200, 170)), (0, y_painel + 32))

            # contagem pra proxima transicao
            restante = max(0.0, ESTADO_INFO[self.estado]['dur'] - self.tempo)
            l3 = f'  Proxima transicao em {restante:.1f}s'
            if self.velocidade != 1.0: l3 += f'   (vel {self.velocidade:.2f}x)'
            tela.blit(fonte_pequena.render(l3, True, (88, 104, 128)), (0, y_painel + 52))

        self.interruptor.desenhar(tela)

        atalhos = '[N] Emergencia     [Espaco] Pausar     [+/-] Velocidade     [Esc] Sair'
        sup = fonte_pequena.render(atalhos, True, (36, 52, 74))
        tela.blit(sup, (LARGURA // 2 - sup.get_width() // 2, y_painel + ALTURA_PAINEL - 18))


def main() -> None:
    imprimir_tabela_verdade()   # mostra a tabela no console ao iniciar

    tela       = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption('Semaforo Inteligente')
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