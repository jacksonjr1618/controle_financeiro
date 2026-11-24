"""
Controle Financeiro Pessoal - Projeto Integrado: Laboratório de Programação

Registra receitas e despesas por categoria, calcula saldo, gera relatórios
por período, alerta sobre gastos excessivos, acompanha uma meta de economia
e salva tudo em arquivo (CSV para lançamentos, JSON para configurações).

Só usa a biblioteca padrão do Python (Python 3.8+). Para rodar:
    python main.py
"""

import csv
import json
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
ARQUIVO_CSV = "lancamentos.csv"
ARQUIVO_JSON = "config.json"
CAMPOS_CSV = ["id", "data", "tipo", "categoria", "descricao", "valor"]

CATEGORIAS = {
    "receita": ["salario", "extra", "outros"],
    "despesa": ["alimentacao", "moradia", "transporte", "saude",
                "educacao", "lazer", "outros"],
}


# ---------------------------------------------------------------------------
# Formatação e leitura/validação de entradas
# ---------------------------------------------------------------------------
def formatar_moeda(valor):
    """Retorna o valor no formato brasileiro: R$ 1.234,56."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return "R$ " + texto


def ler_texto(mensagem):
    """Lê um texto não vazio (sem espaços sobrando nas pontas)."""
    while True:
        texto = input(mensagem).strip()
        if texto != "":
            return texto
        print("  Entrada vazia. Tente de novo.")


def ler_valor(mensagem):
    """Lê um número maior que zero (aceita vírgula ou ponto)."""
    while True:
        texto = input(mensagem).strip().replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            print("  Valor inválido. Digite um número, ex.: 150,50")
            continue
        if valor <= 0:
            print("  O valor precisa ser maior que zero.")
        else:
            return round(valor, 2)


def data_valida(texto):
    """True se o texto estiver no formato AAAA-MM-DD e for uma data real."""
    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def ler_data(mensagem):
    """Lê uma data AAAA-MM-DD. Enter vazio = hoje."""
    while True:
        texto = input(mensagem).strip()
        if texto == "":
            return datetime.now().strftime("%Y-%m-%d")
        if data_valida(texto):
            return texto
        print("  Data inválida. Use o formato AAAA-MM-DD, ex.: 2026-11-23")


def ler_mes(mensagem):
    """Lê um mês no formato AAAA-MM. Enter vazio = mês atual."""
    while True:
        texto = input(mensagem).strip()
        if texto == "":
            return datetime.now().strftime("%Y-%m")
        if len(texto) == 7 and data_valida(texto + "-01"):
            return texto
        print("  Mês inválido. Use o formato AAAA-MM, ex.: 2026-11")


def ler_opcao(mensagem, opcoes):
    """Lê uma opção que precisa estar dentro da lista 'opcoes'."""
    while True:
        texto = input(mensagem).strip().lower()
        if texto in opcoes:
            return texto
        print("  Opção inválida. Escolha entre:", ", ".join(opcoes))


def ler_inteiro(mensagem):
    """Lê um número inteiro."""
    while True:
        texto = input(mensagem).strip()
        try:
            return int(texto)
        except ValueError:
            print("  Digite um número inteiro.")


# ---------------------------------------------------------------------------
# Algoritmos feitos à mão (sem sorted() e sem list.sort())
# ---------------------------------------------------------------------------
def fora_de_ordem(a, b, decrescente):
    """Diz se 'a' deveria vir depois de 'b' na ordenação."""
    if decrescente:
        return a < b
    return a > b


def ordenar_insercao(lista, chave, decrescente=False):
    """
    Ordenação por INSERÇÃO. Devolve uma cópia ordenada (não mexe na original).
    'chave' é uma função que diz por qual campo comparar cada item.
    """
    resultado = []
    for item in lista:
        resultado.append(item)

    for i in range(1, len(resultado)):
        atual = resultado[i]
        j = i - 1
        while j >= 0 and fora_de_ordem(chave(resultado[j]), chave(atual),
                                       decrescente):
            resultado[j + 1] = resultado[j]
            j -= 1
        resultado[j + 1] = atual
    return resultado


def busca_sequencial_descricao(lancamentos, termo):
    """Busca SEQUENCIAL: devolve os lançamentos cuja descrição contém o termo."""
    termo = termo.strip().lower()
    achados = []
    for lanc in lancamentos:
        if termo in lanc["descricao"].lower():
            achados.append(lanc)
    return achados


def busca_binaria_id(ordenada_por_id, alvo):
    """
    Busca BINÁRIA por id. A lista PRECISA estar ordenada por id.
    Devolve (posição ou -1, quantidade de comparações feitas).
    """
    inicio = 0
    fim = len(ordenada_por_id) - 1
    comparacoes = 0
    while inicio <= fim:
        meio = (inicio + fim) // 2
        comparacoes += 1
        id_meio = ordenada_por_id[meio]["id"]
        if id_meio == alvo:
            return meio, comparacoes
        if id_meio < alvo:
            inicio = meio + 1
        else:
            fim = meio - 1
    return -1, comparacoes


def indice_de(lista, valor):
    """Posição de 'valor' na lista (busca sequencial) ou -1."""
    for i in range(len(lista)):
        if lista[i] == valor:
            return i
    return -1


def soma_recursiva(valores, inicio, fim):
    """
    Soma os valores de valores[inicio:fim] usando RECURSÃO
    (divide a lista no meio, então a profundidade fica pequena).
    """
    if inicio >= fim:
        return 0.0
    if fim - inicio == 1:
        return valores[inicio]
    meio = (inicio + fim) // 2
    return soma_recursiva(valores, inicio, meio) + soma_recursiva(valores, meio, fim)


# ---------------------------------------------------------------------------
# Pilha (usada no "desfazer último lançamento")
# ---------------------------------------------------------------------------
def pilha_empilhar(pilha, item):
    pilha.append(item)


def pilha_desempilhar(pilha):
    """Remove e devolve o topo da pilha, ou None se estiver vazia."""
    if len(pilha) == 0:
        return None
    return pilha.pop()


# ---------------------------------------------------------------------------
# Regras de negócio
# ---------------------------------------------------------------------------
def novo_id(lancamentos):
    """Próximo id disponível (maior id existente + 1)."""
    maior = 0
    for lanc in lancamentos:
        if lanc["id"] > maior:
            maior = lanc["id"]
    return maior + 1


def criar_lancamento(lancamentos, data, tipo, categoria, descricao, valor):
    """Monta um registro (dicionário) com um id novo e único."""
    return {
        "id": novo_id(lancamentos),
        "data": data,
        "tipo": tipo,
        "categoria": categoria,
        "descricao": descricao,
        "valor": valor,
    }


def filtrar_periodo(lancamentos, inicio, fim):
    """Lançamentos com data entre 'inicio' e 'fim' (inclusive)."""
    selecionados = []
    for lanc in lancamentos:
        if inicio <= lanc["data"] <= fim:
            selecionados.append(lanc)
    return selecionados


def valores_por_tipo(lancamentos, tipo):
    """Lista só com os valores dos lançamentos de um tipo."""
    valores = []
    for lanc in lancamentos:
        if lanc["tipo"] == tipo:
            valores.append(lanc["valor"])
    return valores


def calcular_totais(lancamentos):
    """Devolve (total de receitas, total de despesas, saldo)."""
    receitas = soma_recursiva(valores_por_tipo(lancamentos, "receita"), 0,
                              len(valores_por_tipo(lancamentos, "receita")))
    lista_despesas = valores_por_tipo(lancamentos, "despesa")
    despesas = soma_recursiva(lista_despesas, 0, len(lista_despesas))
    return receitas, despesas, receitas - despesas


def total_por_categoria(lancamentos, tipo):
    """Dicionário {categoria: total} para o tipo informado."""
    totais = {}
    for lanc in lancamentos:
        if lanc["tipo"] == tipo:
            cat = lanc["categoria"]
            if cat not in totais:
                totais[cat] = 0.0
            totais[cat] += lanc["valor"]
    return totais


def estatisticas_despesas(lancamentos):
    """Devolve (média, maior, menor) das despesas, ou None se não houver."""
    contador = 0
    acumulador = 0.0
    maior = None
    menor = None
    for lanc in lancamentos:
        if lanc["tipo"] != "despesa":
            continue
        contador += 1
        acumulador += lanc["valor"]
        if maior is None or lanc["valor"] > maior["valor"]:
            maior = lanc
        if menor is None or lanc["valor"] < menor["valor"]:
            menor = lanc
    if contador == 0:
        return None
    return acumulador / contador, maior, menor


def meses_existentes(lancamentos):
    """Lista de meses (AAAA-MM) presentes nos lançamentos, em ordem."""
    meses = []
    for lanc in lancamentos:
        mes = lanc["data"][:7]
        if indice_de(meses, mes) == -1:
            meses.append(mes)
    return ordenar_insercao(meses, lambda m: m)


def matriz_categoria_mes(lancamentos):
    """
    MATRIZ de despesas: cada linha é uma categoria e cada coluna um mês.
    Devolve (categorias, meses, matriz).
    """
    categorias = CATEGORIAS["despesa"]
    meses = meses_existentes(lancamentos)
    matriz = []
    for _ in categorias:
        matriz.append([0.0] * len(meses))

    for lanc in lancamentos:
        if lanc["tipo"] != "despesa":
            continue
        linha = indice_de(categorias, lanc["categoria"])
        coluna = indice_de(meses, lanc["data"][:7])
        if linha != -1 and coluna != -1:
            matriz[linha][coluna] += lanc["valor"]
    return categorias, meses, matriz


def gerar_alertas(lancamentos, config, mes):
    """Devolve uma lista de textos de alerta para o mês informado."""
    alertas = []
    do_mes = filtrar_periodo(lancamentos, mes + "-01", mes + "-31")
    receitas, despesas, _ = calcular_totais(do_mes)
    gastos = total_por_categoria(do_mes, "despesa")

    for categoria, limite in config["limites"].items():
        gasto = gastos.get(categoria, 0.0)
        if gasto > limite:
            alertas.append(f"[ALERTA] '{categoria}' estourou o limite: "
                           f"{formatar_moeda(gasto)} de {formatar_moeda(limite)}")
        elif gasto >= 0.8 * limite:
            alertas.append(f"[ATENCAO] '{categoria}' já usou "
                           f"{gasto / limite * 100:.0f}% do limite "
                           f"({formatar_moeda(gasto)} de {formatar_moeda(limite)})")

    if despesas > receitas and despesas > 0:
        alertas.append("[ALERTA] As despesas do mês são maiores que as receitas!")
    elif receitas > 0 and despesas >= 0.8 * receitas:
        alertas.append(f"[ATENCAO] Você já gastou {despesas / receitas * 100:.0f}% "
                       "da receita do mês.")
    return alertas


# ---------------------------------------------------------------------------
# Arquivos: CSV (lançamentos) e JSON (configurações)
# ---------------------------------------------------------------------------
def salvar_csv(lancamentos, caminho=ARQUIVO_CSV):
    with open(caminho, "w", newline="", encoding="utf-8") as arq:
        escritor = csv.DictWriter(arq, fieldnames=CAMPOS_CSV)
        escritor.writeheader()
        for lanc in lancamentos:
            escritor.writerow(lanc)


def carregar_csv(caminho=ARQUIVO_CSV):
    """Lê os lançamentos do CSV. Linhas com problema são ignoradas."""
    lancamentos = []
    if not os.path.exists(caminho):
        return lancamentos
    ignoradas = 0
    with open(caminho, "r", newline="", encoding="utf-8") as arq:
        for linha in csv.DictReader(arq):
            try:
                lanc = {
                    "id": int(linha["id"]),
                    "data": linha["data"],
                    "tipo": linha["tipo"],
                    "categoria": linha["categoria"],
                    "descricao": linha["descricao"],
                    "valor": float(linha["valor"]),
                }
                if (data_valida(lanc["data"]) and lanc["valor"] > 0
                        and lanc["tipo"] in CATEGORIAS):
                    lancamentos.append(lanc)
                else:
                    ignoradas += 1
            except (KeyError, ValueError, TypeError):
                ignoradas += 1
    if ignoradas > 0:
        print(f"Aviso: {ignoradas} linha(s) inválida(s) do CSV foram ignoradas.")
    return lancamentos


def config_padrao():
    return {"limites": {}, "meta": {"descricao": "", "valor": 0.0}}


def salvar_config(config, caminho=ARQUIVO_JSON):
    with open(caminho, "w", encoding="utf-8") as arq:
        json.dump(config, arq, ensure_ascii=False, indent=2)


def carregar_config(caminho=ARQUIVO_JSON):
    if not os.path.exists(caminho):
        return config_padrao()
    try:
        with open(caminho, "r", encoding="utf-8") as arq:
            config = json.load(arq)
        if "limites" in config and "meta" in config:
            return config
    except (json.JSONDecodeError, OSError):
        pass
    print("Aviso: config.json inválido, usando configuração padrão.")
    return config_padrao()


# ---------------------------------------------------------------------------
# Telas (menu)
# ---------------------------------------------------------------------------
def mostrar_lancamentos(lista):
    if len(lista) == 0:
        print("  (nenhum lançamento)")
        return
    print(f"  {'ID':<4} {'DATA':<11} {'TIPO':<8} {'CATEGORIA':<12} "
          f"{'DESCRIÇÃO':<22} {'VALOR':>14}")
    for l in lista:
        print(f"  {l['id']:<4} {l['data']:<11} {l['tipo']:<8} "
              f"{l['categoria']:<12} {l['descricao'][:22]:<22} "
              f"{formatar_moeda(l['valor']):>14}")


def tela_cadastrar(lancamentos, pilha):
    print("\n--- Novo lançamento ---")
    tipo = ler_opcao("Tipo (receita/despesa): ", ["receita", "despesa"])
    print("Categorias:", ", ".join(CATEGORIAS[tipo]))
    categoria = ler_opcao("Categoria: ", CATEGORIAS[tipo])
    descricao = ler_texto("Descrição: ")
    valor = ler_valor("Valor (R$): ")
    data = ler_data("Data AAAA-MM-DD (Enter = hoje): ")

    lanc = criar_lancamento(lancamentos, data, tipo, categoria, descricao, valor)
    lancamentos.append(lanc)
    pilha_empilhar(pilha, lanc["id"])
    salvar_csv(lancamentos)
    print(f"Lançamento #{lanc['id']} cadastrado e salvo.")


def tela_listar(lancamentos):
    print("\n--- Listar lançamentos ---")
    print("Ordenar por: 1) data  2) valor (maior primeiro)  3) id")
    escolha = ler_opcao("Opção: ", ["1", "2", "3"])
    if escolha == "1":
        lista = ordenar_insercao(lancamentos, lambda l: l["data"])
    elif escolha == "2":
        lista = ordenar_insercao(lancamentos, lambda l: l["valor"], True)
    else:
        lista = ordenar_insercao(lancamentos, lambda l: l["id"])
    mostrar_lancamentos(lista)


def tela_buscar(lancamentos):
    print("\n--- Buscar ---")
    print("1) Por id (busca binária)  2) Por descrição (busca sequencial)")
    escolha = ler_opcao("Opção: ", ["1", "2"])
    if escolha == "1":
        alvo = ler_inteiro("Id: ")
        ordenada = ordenar_insercao(lancamentos, lambda l: l["id"])
        pos, comparacoes = busca_binaria_id(ordenada, alvo)
        if pos == -1:
            print(f"  Id {alvo} não encontrado ({comparacoes} comparações).")
        else:
            print(f"  Encontrado com {comparacoes} comparação(ões):")
            mostrar_lancamentos([ordenada[pos]])
    else:
        termo = ler_texto("Termo: ")
        mostrar_lancamentos(busca_sequencial_descricao(lancamentos, termo))


def tela_relatorio(lancamentos):
    print("\n--- Relatório por período ---")
    inicio = ler_data("Data inicial AAAA-MM-DD (Enter = hoje): ")
    fim = ler_data("Data final   AAAA-MM-DD (Enter = hoje): ")
    if inicio > fim:
        print("  A data inicial é maior que a final. Invertendo.")
        inicio, fim = fim, inicio

    periodo = filtrar_periodo(lancamentos, inicio, fim)
    if len(periodo) == 0:
        print("  Nenhum lançamento nesse período.")
        return

    receitas, despesas, saldo = calcular_totais(periodo)
    print(f"\nPeríodo: {inicio} a {fim}  ({len(periodo)} lançamentos)")
    print(f"  Receitas: {formatar_moeda(receitas)}")
    print(f"  Despesas: {formatar_moeda(despesas)}")
    print(f"  Saldo:    {formatar_moeda(saldo)}")

    por_cat = total_por_categoria(periodo, "despesa")
    if len(por_cat) > 0:
        print("\n  Despesas por categoria (maior primeiro):")
        itens = []
        for cat in por_cat:
            itens.append({"categoria": cat, "total": por_cat[cat]})
        itens = ordenar_insercao(itens, lambda i: i["total"], True)
        for item in itens:
            pct = item["total"] / despesas * 100
            print(f"    {item['categoria']:<12} {formatar_moeda(item['total']):>14}"
                  f"  ({pct:.1f}%)")

    stats = estatisticas_despesas(periodo)
    if stats is not None:
        media, maior, menor = stats
        print(f"\n  Média por despesa: {formatar_moeda(media)}")
        print(f"  Maior despesa: {maior['descricao']} ({formatar_moeda(maior['valor'])})")
        print(f"  Menor despesa: {menor['descricao']} ({formatar_moeda(menor['valor'])})")


def tela_matriz(lancamentos):
    print("\n--- Despesas: categoria x mês ---")
    categorias, meses, matriz = matriz_categoria_mes(lancamentos)
    if len(meses) == 0:
        print("  (sem dados)")
        return
    cabecalho = f"  {'':<12}"
    for mes in meses:
        cabecalho += f"{mes:>14}"
    print(cabecalho)
    for i in range(len(categorias)):
        linha = f"  {categorias[i]:<12}"
        for j in range(len(meses)):
            linha += f"{formatar_moeda(matriz[i][j]):>14}"
        print(linha)


def tela_alertas(lancamentos, config):
    print("\n--- Alertas de gastos ---")
    mes = ler_mes("Mês AAAA-MM (Enter = mês atual): ")
    alertas = gerar_alertas(lancamentos, config, mes)
    if len(alertas) == 0:
        print(f"  Tudo certo em {mes}, nenhum alerta.")
    for texto in alertas:
        print("  " + texto)


def tela_limite(config):
    print("\n--- Definir limite mensal por categoria ---")
    print("Categorias:", ", ".join(CATEGORIAS["despesa"]))
    categoria = ler_opcao("Categoria: ", CATEGORIAS["despesa"])
    limite = ler_valor("Limite mensal (R$): ")
    config["limites"][categoria] = limite
    salvar_config(config)
    print(f"Limite de '{categoria}' definido em {formatar_moeda(limite)}.")


def tela_meta(lancamentos, config):
    print("\n--- Meta de economia ---")
    meta = config["meta"]
    if meta["valor"] > 0:
        _, _, saldo = calcular_totais(lancamentos)
        progresso = saldo / meta["valor"] if meta["valor"] > 0 else 0
        pct = max(0.0, min(progresso, 1.0))
        cheias = int(pct * 20)
        barra = "#" * cheias + "-" * (20 - cheias)
        print(f"  Meta: {meta['descricao']} ({formatar_moeda(meta['valor'])})")
        print(f"  Economizado (saldo): {formatar_moeda(saldo)}")
        print(f"  [{barra}] {max(progresso, 0) * 100:.1f}%")
        if saldo >= meta["valor"]:
            print("  Meta atingida! Parabéns!")
        else:
            print(f"  Faltam {formatar_moeda(meta['valor'] - saldo)}.")
    else:
        print("  Nenhuma meta definida ainda.")

    if ler_opcao("Definir/alterar a meta? (s/n): ", ["s", "n"]) == "s":
        meta["descricao"] = ler_texto("Descrição da meta (ex.: reserva de emergência): ")
        meta["valor"] = ler_valor("Valor da meta (R$): ")
        salvar_config(config)
        print("Meta salva.")


def tela_desfazer(lancamentos, pilha):
    print("\n--- Desfazer último lançamento ---")
    id_topo = pilha_desempilhar(pilha)
    if id_topo is None:
        print("  Nada para desfazer nesta sessão.")
        return
    for i in range(len(lancamentos)):
        if lancamentos[i]["id"] == id_topo:
            removido = lancamentos.pop(i)
            salvar_csv(lancamentos)
            print(f"  Lançamento #{removido['id']} ({removido['descricao']}) removido.")
            return


def dados_exemplo():
    """Alguns lançamentos para testar o programa rapidamente."""
    base = [
        ("2026-10-05", "receita", "salario", "Salário outubro", 2500.00),
        ("2026-10-08", "despesa", "moradia", "Aluguel", 900.00),
        ("2026-10-10", "despesa", "alimentacao", "Mercado", 420.50),
        ("2026-10-15", "despesa", "lazer", "Cinema", 60.00),
        ("2026-11-05", "receita", "salario", "Salário novembro", 2500.00),
        ("2026-11-06", "receita", "extra", "Freela", 300.00),
        ("2026-11-08", "despesa", "moradia", "Aluguel", 900.00),
        ("2026-11-12", "despesa", "alimentacao", "Mercado", 650.00),
        ("2026-11-14", "despesa", "transporte", "Passagens", 180.00),
        ("2026-11-20", "despesa", "lazer", "Pizza com amigos", 120.00),
    ]
    lancamentos = []
    for data, tipo, cat, desc, valor in base:
        lancamentos.append(criar_lancamento(lancamentos, data, tipo, cat, desc, valor))
    return lancamentos


def mostrar_menu():
    print("\n========== CONTROLE FINANCEIRO ==========")
    print(" 1) Cadastrar receita/despesa")
    print(" 2) Listar lançamentos (ordenados)")
    print(" 3) Buscar lançamento")
    print(" 4) Relatório por período")
    print(" 5) Matriz de despesas (categoria x mês)")
    print(" 6) Alertas de gastos do mês")
    print(" 7) Definir limite por categoria")
    print(" 8) Meta de economia")
    print(" 9) Desfazer último lançamento")
    print("10) Carregar dados de exemplo")
    print(" 0) Sair")


def main():
    lancamentos = carregar_csv()
    config = carregar_config()
    pilha_desfazer = []

    print(f"Bem-vindo! {len(lancamentos)} lançamento(s) carregado(s) do arquivo.")
    rodando = True
    while rodando:
        mostrar_menu()
        opcao = ler_opcao("Escolha: ", ["0", "1", "2", "3", "4", "5", "6",
                                        "7", "8", "9", "10"])
        if opcao == "1":
            tela_cadastrar(lancamentos, pilha_desfazer)
        elif opcao == "2":
            tela_listar(lancamentos)
        elif opcao == "3":
            tela_buscar(lancamentos)
        elif opcao == "4":
            tela_relatorio(lancamentos)
        elif opcao == "5":
            tela_matriz(lancamentos)
        elif opcao == "6":
            tela_alertas(lancamentos, config)
        elif opcao == "7":
            tela_limite(config)
        elif opcao == "8":
            tela_meta(lancamentos, config)
        elif opcao == "9":
            tela_desfazer(lancamentos, pilha_desfazer)
        elif opcao == "10":
            if len(lancamentos) > 0:
                print("Já existem dados. Exemplo só carrega com a lista vazia.")
            else:
                lancamentos = dados_exemplo()
                salvar_csv(lancamentos)
                print(f"{len(lancamentos)} lançamentos de exemplo carregados.")
        else:
            rodando = False

    salvar_csv(lancamentos)
    salvar_config(config)
    print("Dados salvos. Até a próxima!")


if __name__ == "__main__":
    main()
