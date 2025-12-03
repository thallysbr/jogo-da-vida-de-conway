import sys
import os
import time
import json
import subprocess
import argparse
import atexit

# Importo as funcoes das outras versoes
from sequencial import executar_simulacao_sequencial
from paralelo import executar_simulacao_paralela
from distribuido import executar_servidor_distribuido


class BenchmarkVida:
    def __init__(self, iteracoes, tamanhos, recursos):
        self.iteracoes = iteracoes
        self.resultados = []
        
        # Crio as tuplas (largura, altura)
        self.tamanhos = [(t, t) for t in tamanhos]
        self.lista_recursos = recursos
        
        # Abrir e fechar processo no Windows demora muito
        # e trava as portas TCP. Entao, em vez de criar workers pra cada teste,
        # eu crio um "pool" no comeco e deixo eles rodando em background.
        # O servidor so conecta neles quando precisa.
        self.porta_distribuida = 9999
        self.max_workers = max(recursos)
        self.processos_workers = []
        
        self._iniciar_pool_workers()

    def _iniciar_pool_workers(self):
        print(f"\nIniciando Pool de {self.max_workers} Workers na porta {self.porta_distribuida}...")
        
        for _ in range(self.max_workers):
            # Chamo o script distribuido no modo worker
            cmd = [sys.executable, "distribuido.py", "worker", "localhost", str(self.porta_distribuida)]
            
            # Mando a saida pro DEVNULL pro terminal nao virar uma bagunca de prints
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.processos_workers.append(p)
        
        # Espero um pouco pra garantir que todos subiram
        time.sleep(3)
        print("Pool pronto.\n")

    def limpar_pool(self):
        # Se ja limpei, nao faco de novo
        if not self.processos_workers:
            return

        print("\nMatando Workers sobrando...")
        for p in self.processos_workers:
            if p.poll() is None: # Se ainda ta vivo
                p.terminate()
        
        for p in self.processos_workers:
            p.wait()
            
        self.processos_workers = []
        print("Limpeza concluida.")

    def rodar_sequencial(self):
        print("\n=== INICIANDO BENCHMARK SEQUENCIAL ===")
        
        for largura, altura in self.tamanhos:
            try:
                # Roda e pega o tempo
                tempo = executar_simulacao_sequencial(largura, altura, self.iteracoes)
                
                self.resultados.append({
                    "versao": "sequencial",
                    "largura": largura, 
                    "altura": altura,
                    "recursos": 1,
                    "tempo": tempo
                })
            except Exception as e:
                print(f"Deu ruim no sequencial {largura}x{altura}: {e}")

    def rodar_paralelo(self):
        print("\n=== INICIANDO BENCHMARK PARALELO ===")
        
        for largura, altura in self.tamanhos:
            for n_threads in self.lista_recursos:
                try:
                    tempo = executar_simulacao_paralela(largura, altura, self.iteracoes, n_threads)
                    
                    self.resultados.append({
                        "versao": "paralelo",
                        "largura": largura,
                        "altura": altura,
                        "recursos": n_threads,
                        "tempo": tempo
                    })
                except Exception as e:
                    print(f"Deu ruim no paralelo {largura}x{altura} ({n_threads} threads): {e}")

    def rodar_distribuido(self):
        print("\n=== INICIANDO BENCHMARK DISTRIBUÍDO ===")
        
        for largura, altura in self.tamanhos:
            for n_workers in self.lista_recursos:
                try:
                    # Aqui eh rapido: o servidor so aceita as conexoes dos workers
                    # que ja estao parados esperando no Pool.
                    tempo = executar_servidor_distribuido(
                        largura, altura, self.iteracoes, n_workers, self.porta_distribuida
                    )
                    
                    self.resultados.append({
                        "versao": "distribuido",
                        "largura": largura,
                        "altura": altura,
                        "recursos": n_workers,
                        "tempo": tempo
                    })
                    
                    # Dou uma respirada pro Windows liberar as conexoes TCP antigas
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Deu ruim no distribuido {largura}x{altura} ({n_workers} workers): {e}")

    def salvar_resultados(self, arquivo="resultados_benchmark.json"):
        # Crio a pasta se nao existir
        os.makedirs("resultados", exist_ok=True)
        caminho = os.path.join("resultados", arquivo)
        
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(self.resultados, f, indent=4)
        print(f"\nResultados salvos em: {caminho}")


if __name__ == "__main__":
    # Uso argparse pra poder configurar os testes pela linha de comando
    parser = argparse.ArgumentParser(description="Benchmark Jogo da Vida")
    
    parser.add_argument("--iteracoes", type=int, default=100)
    parser.add_argument("--tamanhos", nargs='+', type=int, default=[100, 200, 500])
    parser.add_argument("--recursos", nargs='+', type=int, default=[2, 4, 8, 16])

    args = parser.parse_args()

    print(f"Configuração: {args.iteracoes} iterações")
    print(f"Tamanhos: {args.tamanhos}")
    print(f"Recursos: {args.recursos}")

    app = BenchmarkVida(
        iteracoes=args.iteracoes,
        tamanhos=args.tamanhos,
        recursos=args.recursos
    )
    
    # Garanto que vou limpar a bagunca (matar processos) quando o script acabar
    atexit.register(app.limpar_pool)
    
    try:
        app.rodar_sequencial()
        app.rodar_paralelo()
        app.rodar_distribuido()
        app.salvar_resultados()
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario.")
    finally:
        # Chama a limpeza so pra garantir
        app.limpar_pool()