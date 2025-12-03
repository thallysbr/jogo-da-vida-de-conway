import socket
import struct
import time
import pickle
import numpy as np
import sys

# --- SERVIDOR ---

class VidaDistribuida:
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

        self.workers = []
        self.faixas = []

    def _zerar_bordas(self):
        self.grade[0, :] = 0
        self.grade[-1, :] = 0
        self.grade[:, 0] = 0
        self.grade[:, -1] = 0

    def add_worker(self, sock, ini, fim):
        self.workers.append(sock)
        self.faixas.append((ini, fim))

    # Função auxiliar para receber bytes até completar o tamanho N
    def _recvall(self, sock, n):
        dados = b''
        while len(dados) < n:
            pedaco = sock.recv(n - len(dados))
            if not pedaco: return None
            dados += pedaco
        return dados

    def atualizar(self):
        if not self.workers: return False

        # 1. Manda pedaços para os workers
        for sock, (ini, fim) in zip(self.workers, self.faixas):
            # Pega linhas + sobra para calcular vizinhos
            i_envio = max(0, ini - 1)
            f_envio = min(self.altura, fim + 1)

            fatia = self.grade[i_envio:f_envio, :].copy()
            
            # Serializa a matriz
            dados = pickle.dumps(fatia, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Manda tamanho (4 bytes) + dados
            sock.sendall(struct.pack("!I", len(dados)))
            sock.sendall(dados)

        # 2. Recebe respostas
        for sock, (ini, fim) in zip(self.workers, self.faixas):
            # Lê tamanho
            cabecalho = self._recvall(sock, 4)
            if not cabecalho: return False
            (tam,) = struct.unpack("!I", cabecalho)

            # Lê dados
            dados = self._recvall(sock, tam)
            if not dados: return False

            fatia_volta = pickle.loads(dados)

            # Encaixa de volta na matriz principal
            i_envio = max(0, ini - 1)
            offset = ini - i_envio
            linhas = fim - ini

            self.nova_grade[ini:fim, 1:-1] = fatia_volta[offset:offset+linhas, 1:-1]

        # Garante bordas zeradas na nova também
        self._zerar_bordas()
        mudou = not np.array_equal(self.nova_grade, self.grade)
        self.grade, self.nova_grade = self.nova_grade, self.grade
        return mudou

    def simular(self, iteracoes):
        reais = 0
        for it in range(iteracoes):
            if not self.atualizar(): break
            reais = it + 1
        return reais


# --- WORKER ---

# Essa função é quase igual a do sequencial, só mudei que aqui não precisa
# dos índices de início/fim porque eu já recebo a fatia cortada
def atualizar_faixa_numpy(grade, nova_grade):
    alt, larg = grade.shape
    
    # Verificações básicas para não dar erro de índice
    if alt <= 2: return

    # Pego o meio da matriz (sem as bordas)
    interior = grade[1:-1, 1:-1]
    
    # Pego a matriz inteira e desloco ela nas 8 direções. Somando tudo, tenho os vizinhos de todo mundo de uma vez.
    acima = grade[:-2, :]
    meio = grade[1:-1, :]
    abaixo = grade[2:, :]

    vizinhos = (
        acima[:, 0:-2] + acima[:, 1:-1] + acima[:, 2:] +
        meio[:, 0:-2] +                   meio[:, 2:] +
        abaixo[:, 0:-2] + abaixo[:, 1:-1] + abaixo[:, 2:]
    )

    # Regras do jogo usando 0/1
    vivas = (interior == 1)
    
    # Regra 1: Continua viva se tem 2 ou 3 vizinhos
    sobrevive = vivas & ((vizinhos == 2) | (vizinhos == 3))
    
    # Regra 2: Nasce se tiver 3 vizinhos
    nasce = (interior == 0) & (vizinhos == 3)

    # Junta tudo e converte para 0 ou 1
    nova_grade[1:-1, 1:-1] = np.where(sobrevive | nasce, 1, 0)

def executar_worker_distribuido(host, porta):
    print(f"Worker rodando em {host}:{porta}")
    
    # Loop eterno para não morrer quando o teste acaba
    # Assim o benchmark pode reutilizar o processo
    while True:
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, porta))
            
            while True:
                # 1. Lê tamanho
                head = b''
                while len(head) < 4:
                    p = s.recv(4 - len(head))
                    if not p: raise Exception()
                    head += p
                (tam,) = struct.unpack("!I", head)
                
                # 2. Lê dados
                dados = b''
                while len(dados) < tam:
                    p = s.recv(tam - len(dados))
                    if not p: raise Exception()
                    dados += p
                
                # 3. Processa
                grade = pickle.loads(dados)
                nova = grade.copy()
                atualizar_faixa_numpy(grade, nova)
                
                # 4. Manda de volta
                resp = pickle.dumps(nova, protocol=pickle.HIGHEST_PROTOCOL)
                s.sendall(struct.pack("!I", len(resp)))
                s.sendall(resp)

        except Exception:
            # Se der erro (servidor caiu), espera um pouco e tenta reconectar
            if s: s.close()
            time.sleep(0.5)
            continue


# --- MAIN ---

def executar_servidor_distribuido(larg, alt, it, n_workers, porta=8888, prob_viva=0.2):
    print(f"--- Servidor distribuído {larg}x{alt} com {n_workers} workers ---")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", porta))
    s.listen(n_workers)
    
    # Timeout de 1 min para não travar para sempre se der ruim
    s.settimeout(60)

    vida = VidaDistribuida(larg, alt, prob_viva)
    conexoes = []

    # Divide carga
    linhas = max(1, alt - 2)
    reais = min(n_workers, linhas)
    qnt = linhas // reais
    resto = linhas % reais
    
    ini = 1
    try:
        # Aceita conexões
        for i in range(reais):
            conn, addr = s.accept()
            conexoes.append(conn)
            
            tam = qnt + (1 if i < resto else 0)
            fim = ini + tam
            
            vida.add_worker(conn, ini, fim)
            ini = fim

        s.settimeout(None)
        
        t0 = time.perf_counter()
        reais = vida.simular(it)
        t1 = time.perf_counter()
        tempo = t1 - t0

        print(f"  Iterações: {reais}")
        print(f"  Tempo:     {tempo:.4f} s")
        return tempo

    finally:
        # Fecha sockets para liberar workers
        for c in conexoes:
            try: c.close()
            except: pass
        s.close()

if __name__ == "__main__":
    # Pega argumentos passados no terminal
    if len(sys.argv) > 1:
        modo = sys.argv[1]
        if modo == "worker":
            executar_worker_distribuido(sys.argv[2], int(sys.argv[3]))
        elif modo == "server":
            executar_servidor_distribuido(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]))