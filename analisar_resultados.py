import json
import matplotlib.pyplot as plt

# Função simples pra ler o JSON.
# Se o arquivo não existir, o Python avisa com erro, não preciso tratar aqui.
def carregar_dados():
    with open("resultados/resultados_benchmark.json", "r", encoding="utf-8") as f:
        return json.load(f)

def calcular_metricas(dados):
    # 1. Primeiro preciso achar os tempos do Sequencial pra usar de base (Speedup = 1)
    tempos_seq = {}
    for d in dados:
        if d['versao'] == 'sequencial':
            tempos_seq[(d['largura'], d['altura'])] = d['tempo']

    lista_final = []
    
    # 2. Agora calculo Speedup e Eficiência pra todo mundo
    for d in dados:
        chave = (d['largura'], d['altura'])
        tempo_base = tempos_seq.get(chave)
        
        # Se não tiver tempo base ou tempo for 0, speedup é 0
        speedup = 0.0
        eficiencia = 0.0
        
        if tempo_base and d['tempo'] > 0:
            speedup = tempo_base / d['tempo']
            if d['recursos'] > 0:
                eficiencia = speedup / d['recursos']

        # Adiciono os campos novos no dicionário
        d['speedup'] = speedup
        d['eficiencia'] = eficiencia
        lista_final.append(d)

    return lista_final

def mostrar_tabela(dados):
    print("\n" + "="*85)
    print(f"{'VERSÃO':<15} | {'TAMANHO':<12} | {'RECURSOS':<10} | {'TEMPO (s)':<10} | {'SPEEDUP':<10} | {'EFIC.':<10}")
    print("-" * 85)

    # --- GAMBIARRA PRA ORDENAR ---
    # Quero que apareça na ordem: Sequencial -> Paralelo -> Distribuído.
    # Crio um mapinha de prioridade pra forçar essa ordem no sort.
    ordem = {'sequencial': 1, 'paralelo': 2, 'distribuido': 3}

    # Ordena por: Tipo (1,2,3) -> Tamanho -> Recursos
    dados.sort(key=lambda x: (ordem.get(x['versao'], 9), x['largura'], x['recursos']))

    for d in dados:
        tam = f"{d['largura']}x{d['altura']}"
        print(f"{d['versao']:<15} | {tam:<12} | {d['recursos']:<10} | {d['tempo']:<10.4f} | {d['speedup']:<10.2f} | {d['eficiencia']:<10.2f}")
    print("="*85 + "\n")

def gerar_graficos(dados):
    # Pega os tamanhos únicos que testamos (ex: 100x100, 200x200...)
    # Uso 'set' pra remover duplicados
    tamanhos = sorted(list(set((d['largura'], d['altura']) for d in dados)))

    for w, h in tamanhos:
        # Pega só os dados desse tamanho específico
        dados_tamanho = [d for d in dados if d['largura'] == w and d['altura'] == h]

        # Separa por versão
        sequencial = [d for d in dados_tamanho if d['versao'] == 'sequencial']
        paralelos = [d for d in dados_tamanho if d['versao'] == 'paralelo']
        paralelos.sort(key=lambda x: x['recursos'])
        distrib = [d for d in dados_tamanho if d['versao'] == 'distribuido']
        distrib.sort(key=lambda x: x['recursos'])

        # ========== GRÁFICO 1: TEMPO DE EXECUÇÃO ==========
        plt.figure(figsize=(10, 6))

        # Sequencial: linha horizontal (não varia com recursos)
        if sequencial:
            tempo_seq = sequencial[0]['tempo']
            # Desenha linha horizontal do menor ao maior recurso
            max_rec = max([d['recursos'] for d in dados_tamanho])
            plt.plot([1, max_rec], [tempo_seq, tempo_seq],
                     label='Sequencial', color='green', linestyle='-', linewidth=2)

        # Paralelo
        if paralelos:
            plt.plot([x['recursos'] for x in paralelos], [y['tempo'] for y in paralelos],
                     marker='o', label='Paralelo (Threads)', color='blue')

        # Distribuído
        if distrib:
            plt.plot([x['recursos'] for x in distrib], [y['tempo'] for y in distrib],
                     marker='s', label='Distribuído (Workers)', color='red', linestyle='--')

        plt.title(f"Tempo de Execução - Matriz {w}x{h}")
        plt.xlabel("Número de Recursos (Threads/Workers)")
        plt.ylabel("Tempo (segundos)")
        plt.legend()
        plt.grid(True, alpha=0.3)

        nome_arq = f"resultados/tempo_{w}x{h}.png"
        plt.savefig(nome_arq)
        print(f"Gráfico salvo: {nome_arq}")
        plt.close()

        # ========== GRÁFICO 2: SPEEDUP ==========
        plt.figure(figsize=(10, 6))

        # Paralelo
        if paralelos:
            plt.plot([x['recursos'] for x in paralelos], [y['speedup'] for y in paralelos],
                     marker='o', label='Paralelo (Threads)', color='blue')

        # Distribuído
        if distrib:
            plt.plot([x['recursos'] for x in distrib], [y['speedup'] for y in distrib],
                     marker='s', label='Distribuído (Workers)', color='red', linestyle='--')

        plt.title(f"Speedup - Matriz {w}x{h}")
        plt.xlabel("Número de Recursos (Threads/Workers)")
        plt.ylabel("Speedup")
        plt.legend()
        plt.grid(True, alpha=0.3)

        nome_arq = f"resultados/speedup_{w}x{h}.png"
        plt.savefig(nome_arq)
        print(f"Gráfico salvo: {nome_arq}")
        plt.close()

if __name__ == "__main__":
    # Script principal: carrega -> calcula -> mostra -> desenha
    dados = carregar_dados()
    dados = calcular_metricas(dados)
    mostrar_tabela(dados)
    gerar_graficos(dados)