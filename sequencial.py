import time
import numpy as np

# Função principal que faz a mágica do Jogo da Vida.
# Eu uso NumPy aqui para não precisar fazer 2 loops for (o que seria lento demais em Python).
def atualizar_faixa_numpy(grade, nova_grade, linha_inicio, linha_fim):
    altura, largura = grade.shape

    # Verificações básicas para não dar erro de índice
    if largura <= 2 or altura <= 2: return False
    if linha_inicio < 1: linha_inicio = 1
    if linha_fim > altura - 1: linha_fim = altura - 1
    if linha_fim <= linha_inicio: return False

    # Pego o meio da matriz (sem as bordas)
    interior_atual = grade[linha_inicio:linha_fim, 1:-1]

    # Pego a matriz inteira e desloco ela nas 8 direções. Somando tudo, tenho os vizinhos de todo mundo de uma vez.
    acima = grade[linha_inicio - 1:linha_fim - 1, :]
    meio = grade[linha_inicio:linha_fim, :]
    abaixo = grade[linha_inicio + 1:linha_fim + 1, :]

    vizinhos = (
        acima[:, 0:-2] + acima[:, 1:-1] + acima[:, 2:] +
        meio[:, 0:-2] +                   meio[:, 2:] +
        abaixo[:, 0:-2] + abaixo[:, 1:-1] + abaixo[:, 2:]
    )

    # Regras do jogo usando 0/1
    vivas = (interior_atual == 1)
    mortas = (interior_atual == 0)

    # Regra 1: Continua viva se tem 2 ou 3 vizinhos
    sobrevive = vivas & ((vizinhos == 2) | (vizinhos == 3))
    
    # Regra 2: Nasce se tiver 3 vizinhos
    nasce = mortas & (vizinhos == 3)

    # Junta tudo e converte para 0 ou 1
    interior_novo = np.where(sobrevive | nasce, 1, 0)

    # Joga o resultado na nova matriz
    nova_grade[linha_inicio:linha_fim, 1:-1] = interior_novo

    # Retorna se mudou alguma coisa (para saber se o jogo estagnou)
    return not np.array_equal(interior_novo, interior_atual)


class VidaSequencial:
    def __init__(self, largura, altura, prob_viva=0.2):
        # Seed fixa para garantir que o teste seja igual sempre
        np.random.seed(42)

        self.largura = largura
        self.altura = altura

        # Cria matriz aleatória (0=morto, 1=vivo)
        self.grade = np.random.choice([0, 1], size=(altura, largura), p=[1 - prob_viva, prob_viva])

        # Zera as bordas para facilitar o cálculo
        self._zerar_bordas()

        # Crio uma cópia para escrever o próximo estado
        self.nova_grade = np.zeros_like(self.grade)

    def _zerar_bordas(self):
        self.grade[0, :] = 0
        self.grade[-1, :] = 0
        self.grade[:, 0] = 0
        self.grade[:, -1] = 0

    def atualizar(self):
        # Calcula tudo de uma vez
        mudou = atualizar_faixa_numpy(self.grade, self.nova_grade, 1, self.altura - 1)

        # Garante bordas zeradas na nova também
        self.nova_grade[0, :] = 0
        self.nova_grade[-1, :] = 0
        self.nova_grade[:, 0] = 0
        self.nova_grade[:, -1] = 0

        # Troca as matrizes (o novo vira o atual)
        self.grade, self.nova_grade = self.nova_grade, self.grade
        return mudou

    def simular(self, iteracoes):
        iteracoes_reais = 0
        for it in range(iteracoes):
            mudou = self.atualizar()
            iteracoes_reais = it + 1
            if not mudou:
                break # Se não mudou nada, para, para economizar tempo
        return iteracoes_reais

# Função para rodar e medir tempo
def executar_simulacao_sequencial(largura, altura, iteracoes, prob_viva=0.2):
    print(f"--- Simulação sequencial {largura}x{altura} ---")

    t0 = time.perf_counter()
    simulacao = VidaSequencial(largura, altura, prob_viva=prob_viva)
    reais = simulacao.simular(iteracoes)
    t1 = time.perf_counter()

    tempo = t1 - t0
    print(f"  Iterações: {iteracoes} (feitas: {reais})")
    print(f"  Tempo:     {tempo:.4f} s")
    return tempo

if __name__ == "__main__":
    # Teste rápido
    executar_simulacao_sequencial(100, 100, 1000)