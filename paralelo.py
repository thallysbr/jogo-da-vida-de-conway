import threading
import time
import numpy as np

# Função principal Jogo da Vida.
# Eu uso NumPy aqui para não precisar fazer 2 loops for (o que seria lento demais em Python).
def atualizar_faixa_numpy(grade, nova_grade, linha_inicio, linha_fim):
    altura, largura = grade.shape

    # Verificações básicas para não dar erro de índice
    if largura <= 2 or altura <= 2: return False
    if linha_inicio < 1: linha_inicio = 1
    if linha_fim > altura - 1: linha_fim = altura - 1
    if linha_fim <= linha_inicio: return False

    # Pego só o meio da matriz (sem as bordas)
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


class VidaParalela:
    def __init__(self, largura, altura, num_threads, prob_viva=0.2):
        # Seed fixa para garantir que o teste seja igual sempre
        np.random.seed(42)
        self.largura = largura
        self.altura = altura
        
        # Não deixo criar mais threads que linhas para não dar erro
        linhas = max(1, altura - 2)
        self.num_threads = max(1, min(num_threads, linhas))

        # Cria matriz aleatória (0=morto, 1=vivo)
        self.grade = np.random.choice([0, 1], size=(altura, largura), p=[1 - prob_viva, prob_viva])
        
        # Zera as bordas para facilitar o cálculo
        self._zerar_bordas()
        
        # Crio uma cópia para escrever o próximo estado
        self.nova_grade = np.zeros_like(self.grade)

        # Sincronização com barreiras
        # barreira_inicio: Todo mundo começa junto a iteração
        # barreira_fim: Ninguém troca a matriz antes de todo mundo terminar de ler
        self.barreira_inicio = threading.Barrier(self.num_threads + 1)
        self.barreira_fim = threading.Barrier(self.num_threads + 1)
        self.stop_event = threading.Event()

        self.mudou_locais = [False] * self.num_threads
        self.faixas = self._dividir_faixas()
        self.threads = []
        self._start_threads()

    def _zerar_bordas(self):
        self.grade[0, :] = 0
        self.grade[-1, :] = 0
        self.grade[:, 0] = 0
        self.grade[:, -1] = 0

    def _dividir_faixas(self):
        # Divide a matriz em fatias iguais para as threads
        linhas = max(1, self.altura - 2)
        qnt = linhas // self.num_threads
        resto = linhas % self.num_threads
        faixas = []
        ini = 1
        for i in range(self.num_threads):
            tam = qnt + (1 if i < resto else 0)
            fim = ini + tam
            if fim > self.altura - 1: fim = self.altura - 1
            faixas.append((ini, fim))
            ini = fim
        return faixas

    def _trabalho_thread(self, id_t, ini, fim):
        while True:
            try:
                # 1. Espera o sinal para começar
                self.barreira_inicio.wait()
            except: break

            if self.stop_event.is_set():
                try: self.barreira_fim.wait()
                except: pass
                break

            # 2. Trabalha só no pedaço dele
            # Reuso a mesma função do sequencial aqui
            self.mudou_locais[id_t] = atualizar_faixa_numpy(self.grade, self.nova_grade, ini, fim)

            try:
                # 3. Espera os outros terminarem
                self.barreira_fim.wait()
            except: break

    def _start_threads(self):
        for i, (ini, fim) in enumerate(self.faixas):
            t = threading.Thread(target=self._trabalho_thread, args=(i, ini, fim))
            t.start()
            self.threads.append(t)

    def _parar_tudo(self):
        self.stop_event.set()
        try:
            self.barreira_inicio.wait()
            self.barreira_fim.wait()
        except: pass
        for t in self.threads: t.join()

    def atualizar(self):
        try:
            self.barreira_inicio.wait() # Libera threads
            self.barreira_fim.wait()    # Espera threads
        except: return False

        # Garante bordas zeradas na nova também
        self._zerar_bordas()
        
        mudou = any(self.mudou_locais)
        
        # Troca as matrizes (o novo vira o atual)
        self.grade, self.nova_grade = self.nova_grade, self.grade
        return mudou

    def simular(self, iteracoes):
        reais = 0
        try:
            for it in range(iteracoes):
                if not self.atualizar(): break
                reais = it + 1
        finally:
            self._parar_tudo()
        return reais

def executar_simulacao_paralela(largura, altura, iteracoes, num_threads, prob_viva=0.2):
    print(f"--- Simulação paralela {largura}x{altura} com {num_threads} threads ---")
    t0 = time.perf_counter()
    sim = VidaParalela(largura, altura, num_threads, prob_viva)
    reais = sim.simular(iteracoes)
    t1 = time.perf_counter()
    tempo = t1 - t0
    print(f"  Iterações: {iteracoes} (feitas: {reais})")
    print(f"  Tempo:     {tempo:.4f} s")
    return tempo

if __name__ == "__main__":
    executar_simulacao_paralela(200, 200, 500, 4)