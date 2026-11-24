# Controle Financeiro Pessoal (Python)

Projeto Integrado: Laboratório de Programação.

Programa de terminal para organizar as finanças: registra receitas e despesas
por categoria, calcula o saldo, gera relatórios por período, alerta sobre gastos
excessivos, acompanha uma meta de economia e salva tudo em arquivo.

## Como rodar

Precisa só do Python 3.8 ou superior (nenhuma biblioteca extra).

```
python main.py
```

(em alguns sistemas o comando é `python3 main.py`)

Dica para testar rápido: na primeira execução, escolha a opção **10** para
carregar dados de exemplo.

## Arquivos gerados

- `lancamentos.csv`: todas as receitas e despesas
- `config.json`: limites por categoria e meta de economia

## Quadro de requisitos

| Pergunta | Resposta |
|---|---|
| Problema | Famílias sem educação financeira têm dificuldade de saber para onde o dinheiro vai |
| Entradas | Data, tipo, categoria, descrição e valor de cada lançamento; limites e meta |
| Saídas | Lista ordenada, busca, relatório por período, matriz categoria x mês, alertas, progresso da meta |
| Requisitos funcionais | Cadastrar, listar, buscar, ordenar, gerar relatório, alertar, acompanhar meta, desfazer, salvar e carregar |
| Regras | Valor maior que zero; data válida; tipo e categoria de listas fixas; id único |
| Armazenamento | Lista de dicionários na memória; CSV e JSON no disco |

## Onde cada conteúdo da disciplina aparece (em `main.py`)

| Conteúdo | Função |
|---|---|
| Laços, decisões, contadores e acumuladores | `estatisticas_despesas`, `total_por_categoria` |
| Registros e lista de registros | lista de dicionários `lancamentos`, `criar_lancamento` |
| Pesquisa sequencial e binária | `busca_sequencial_descricao`, `busca_binaria_id` |
| Matriz | `matriz_categoria_mes` |
| Recursão | `soma_recursiva` |
| CSV e JSON | `salvar_csv`, `carregar_csv`, `salvar_config`, `carregar_config` |
| Média, maior e menor | `estatisticas_despesas` |
| Strings | `lower()`, `strip()`, `replace()`, `formatar_moeda`, busca por descrição |
| Ordenação à mão (sem `sorted()`) | `ordenar_insercao` |
| Funções com parâmetros e retorno | o programa inteiro |
| Pilha com função real | `pilha_empilhar`, `pilha_desempilhar` (desfazer último lançamento) |
| Validação de entradas | `ler_valor`, `ler_data`, `ler_mes`, `ler_opcao`, `ler_inteiro` |
