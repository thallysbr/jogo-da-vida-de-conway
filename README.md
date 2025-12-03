Este projeto implementa o Jogo da Vida (Game of Life) em três versões para análise de desempenho: **Sequencial**, **Paralela** (Threads) e **Distribuída** (Sockets TCP).

## Pré-requisitos

Certifique-se de ter o **Python 3.7 ou superior** instalado.

As bibliotecas externas necessárias são:

```bash
pip install numpy matplotlib
```

As demais bibliotecas (`socket`, `threading`, `pickle`, etc.) já vêm com o Python.

---

## Como Rodar Individualmente

### 1\. Versão Sequencial

Executa a simulação em um único processo.

```bash
python sequencial.py
```

### 2\. Versão Paralela

Executa a simulação utilizando _Threads_ para dividir o processamento da matriz.

```bash
python paralelo.py
```

### 3\. Versão Distribuída

Arquitetura Cliente/Servidor.

**Passo 1: Iniciar Workers (em terminais separados)**

```bash
python distribuido.py worker localhost 9000
```

_(Repita para quantos workers desejar)_

**Passo 2: Iniciar Servidor**

```bash
# Sintaxe: server [largura] [altura] [iterações] [num_workers] [porta]
python distribuido.py server 500 500 200 1 9000
```

---

## Características Técnicas

- **Reprodutibilidade**: Todos os scripts usam seed fixa (`np.random.seed(42)`) pra garantir que os testes sejam iguais sempre.
- **Probabilidade inicial**: Células têm 20% de chance de nascer vivas.
- **Bordas**: Sempre zeradas pra facilitar o cálculo dos vizinhos.
- **Workers persistentes**: No benchmark, os workers ficam rodando em background e são reutilizados entre os testes (isso é importante no Windows, que demora pra criar processos).

---

## Benchmark Automatizado

O script `benchmark.py` gerencia a criação e encerramento dos processos workers automaticamente e salva os dados na pasta `resultados/`.

### Execução Padrão

Roda os testes com as configurações padrão (100 iterações, matrizes de 100x100 a 500x500, 2 a 16 recursos):

```bash
python benchmark.py
```

### Execução Personalizada (CLI)

Você pode personalizar os testes usando argumentos:

- `--iteracoes`: Número de iterações por simulação.
- `--tamanhos`: Lista de tamanhos da matriz (NxN).
- `--recursos`: Lista de quantidades de Threads/Workers.

**Exemplo 1: Configuração padrão explícita**

```bash
py benchmark.py --iteracoes 100 --tamanhos 100 200 500 --recursos 2 4 8 16
```

**Exemplo 2: Teste rápido (para verificar funcionamento)**

```bash
py benchmark.py --iteracoes 10 --tamanhos 100 --recursos 2
```

**Exemplo 3: Teste de Estresse (Matrizes grandes e muitos núcleos)**

```bash
py benchmark.py --iteracoes 50 --tamanhos 2000 3000 --recursos 8 16
```

---

## Análise dos Resultados

Após rodar o benchmark, gere tabelas e gráficos com:

```bash
python analisar_resultados.py
```

O script irá:

1. Ler o arquivo `resultados/resultados_benchmark.json`.
2. Exibir a tabela de **Speedup** e **Eficiência** no terminal.
3. Salvar os gráficos `.png` comparativos dentro da pasta `resultados/`.

---

## Estrutura de Saída

Após rodar o benchmark e a análise, a pasta `resultados/` terá:

```
resultados/
├── resultados_benchmark.json    # Dados brutos (tempo, speedup, eficiência)
├── tempo_100x100.png            # Gráfico de tempo de execução
├── speedup_100x100.png          # Gráfico de speedup
├── tempo_200x200.png
├── speedup_200x200.png
└── ...                          # Um par de gráficos para cada tamanho testado
```

**Exemplo do JSON:**

```json
[
  {
    "versao": "sequencial",
    "largura": 100,
    "altura": 100,
    "recursos": 1,
    "tempo": 0.1234
  },
  {
    "versao": "paralelo",
    "largura": 100,
    "altura": 100,
    "recursos": 4,
    "tempo": 0.0456
  }
]
```

---

## Referência

O código base da lógica do Jogo da Vida foi adaptado de:

> VILLARES, Alexandre. **Autômatos Celulares - Python em um contexto visual.** Disponível em: <https://abav.lugaralgum.com/material-aulas/Processing-Python-py5/automatos-celulares.html>

```

```
