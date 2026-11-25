"""
Controle Financeiro Pessoal - Projeto Integrado: Laboratório de Programação

Registra rendas e despesas por categoria, calcula o saldo, gera relatórios
por período, alerta sobre gastos excessivos, acompanha uma meta de economia
e salva tudo em arquivo (CSV e JSON).

Para rodar (main.py e busca_ordenacao.py na mesma pasta):  python main.py
"""

import csv
import json
import os
from datetime import datetime

from busca_ordenacao import ordenar_insercao, busca_sequencial, busca_binaria

ARQUIVO_CSV = "lancamentos.csv"
ARQUIVO_JSON = "config.json"
CAMPOS_CSV = ["id", "data", "tipo", "categoria", "valor"]

CATEGORIAS = {
    "renda": ["salario", "extra", "outros"],
    "despesa": ["alimentacao", "moradia", "transporte", "saude",
                "educacao", "lazer", "outros"],
}


# ---------------------------------------------------------------------------
# Formatação e leitura de dados do usuário (com validação)
# ---------------------------------------------------------------------------
def formatar_moeda(valor):
    """Valor no formato brasileiro: R$ 1.234,56."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "#").replace(".", ",").replace("#", ".")
    return "R$ " + texto


def data_valida(iso):
    """True se 'iso' (AAAA-MM-DD) for uma data real."""
    try:
        datetime.strptime(iso, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def normalizar_data(texto):
    """
    Aceita dd/mm/aaaa ou ddmmaaaa e devolve AAAA-MM-DD (ou None se inválida).
    Esse formato AAAA-MM-DD é o usado dentro do programa e no arquivo.
    """
    texto = texto.strip()
    if "/" in texto:
        partes = texto.split("/")
        if len(partes) != 3:
            return None
        dia, mes, ano = partes[0].zfill(2), partes[1].zfill(2), partes[2]
    elif len(texto) == 8:
        dia, mes, ano = texto[0:2], texto[2:4], texto[4:8]
    else:
        return None
    iso = ano + "-" + mes + "-" + dia
    if len(iso) == 10 and data_valida(iso):
        return iso
    return None


def normalizar_mes(texto):
    """Aceita mm/aaaa ou mmaaaa e devolve AAAA-MM (ou None)."""
    texto = texto.strip()
    if "/" in texto:
        iso = normalizar_data("01/" + texto)
    else:
        iso = normalizar_data("01" + texto)
    if iso is None:
        return None
    return iso[:7]


def formatar_data(iso):
    """AAAA-MM-DD -> DD/MM/AAAA."""
    return iso[8:10] + "/" + iso[5:7] + "/" + iso[0:4]


def formatar_mes(iso_mes):
    """AAAA-MM -> MM/AAAA."""
    return iso_mes[5:7] + "/" + iso_mes[0:4]


def ler_valor(mensagem):
    """Lê um número maior que zero (aceita vírgula ou ponto)."""
    while True:
        texto = input(mensagem).strip().replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            print("Valor inválido.")
            continue
        if 0 < valor < 1e12:
            return round(valor, 2)
        print("O valor precisa ser maior que zero.")


def ler_data(mensagem):
    """Lê uma data e devolve AAAA-MM-DD."""
    while True:
        iso = normalizar_data(input(mensagem))
        if iso is not None:
            return iso
        print("Data inválida.")


def ler_mes(mensagem):
    """Lê um mês e devolve AAAA-MM."""
    while True:
        iso = normalizar_mes(input(mensagem))
        if iso is not None:
            return iso
        print("Mês inválido.")


def ler_escolha(titulo, opcoes):
    """Mostra as opções numeradas e devolve o NOME da opção escolhida."""
    print(titulo)
    for i in range(len(opcoes)):
        print(f"  {i + 1}) {opcoes[i]}")
    while True:
        texto = input("Número: ").strip()
        if texto.isdigit() and 1 <= int(texto) <= len(opcoes):
            return opcoes[int(texto) - 1]
        print("Opção inválida.")


# ---------------------------------------------------------------------------
# Regras de negócio
# ---------------------------------------------------------------------------
def soma_recursiva(valores, inicio, fim):
    """Soma valores[inicio:fim] por RECURSÃO (divide a lista no meio)."""
    if inicio >= fim:
        return 0.0
    if fim - inicio == 1:
        return valores[inicio]
    meio = (inicio + fim) // 2
    return soma_recursiva(valores, inicio, meio) + soma_recursiva(valores, meio, fim)


def novo_id(lancamentos):
    """Maior id existente + 1."""
    maior = 0
    for lanc in lancamentos:
        if lanc["id"] > maior:
            maior = lanc["id"]
    return maior + 1


def criar_lancamento(lancamentos, data, tipo, categoria, valor):
    """Monta um registro (dicionário) com id novo e único."""
    return {"id": novo_id(lancamentos), "data": data, "tipo": tipo,
            "categoria": categoria, "valor": valor}


def filtrar_periodo(lancamentos, inicio, fim):
    """Lançamentos com data entre 'inicio' e 'fim' (inclusive)."""
    selecionados = []
    for lanc in lancamentos:
        if inicio <= lanc["data"] <= fim:
            selecionados.append(lanc)
    return selecionados


def valores_por_tipo(lancamentos, tipo):
    valores = []
    for lanc in lancamentos:
        if lanc["tipo"] == tipo:
            valores.append(lanc["valor"])
    return valores


def calcular_totais(lancamentos):
    """Devolve (total de rendas, total de despesas, saldo)."""
    rendas = valores_por_tipo(lancamentos, "renda")
    despesas = valores_por_tipo(lancamentos, "despesa")
    total_rendas = soma_recursiva(rendas, 0, len(rendas))
    total_despesas = soma_recursiva(despesas, 0, len(despesas))
    return total_rendas, total_despesas, total_rendas - total_despesas


def resumo_por_categoria(lancamentos, tipo):
    """
    Lista de {categoria, total, qtd} do tipo informado.
    Laço dentro de laço, com acumulador (total) e contador (qtd).
    """
    resumo = []
    for cat in CATEGORIAS[tipo]:
        total = 0.0
        qtd = 0
        for lanc in lancamentos:
            if lanc["tipo"] == tipo and lanc["categoria"] == cat:
                total += lanc["valor"]
                qtd += 1
        if qtd > 0:
            resumo.append({"categoria": cat, "total": total, "qtd": qtd})
    return resumo


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


def matriz_categoria_mes(lancamentos):
    """MATRIZ de despesas: linhas = categorias, colunas = meses."""
    categorias = CATEGORIAS["despesa"]
    meses = []
    for lanc in lancamentos:
        mes = lanc["data"][:7]
        if busca_sequencial(meses, mes)[0] == -1:
            meses.append(mes)
    meses = ordenar_insercao(meses, lambda m: m)

    matriz = []
    for _ in categorias:
        matriz.append([0.0] * len(meses))
    for lanc in lancamentos:
        if lanc["tipo"] == "despesa":
            linha = busca_sequencial(categorias, lanc["categoria"])[0]
            coluna = busca_sequencial(meses, lanc["data"][:7])[0]
            if linha != -1:
                matriz[linha][coluna] += lanc["valor"]
    return categorias, meses, matriz


def gerar_alertas(lancamentos, config, mes):
    """Lista de textos de alerta para o mês informado (AAAA-MM)."""
    alertas = []
    do_mes = filtrar_periodo(lancamentos, mes + "-01", mes + "-31")
    rendas, despesas, _ = calcular_totais(do_mes)

    for item in resumo_por_categoria(do_mes, "despesa"):
        limite = config["limites"].get(item["categoria"])
        if limite is None:
            continue
        gasto = item["total"]
        if gasto > limite:
            alertas.append(f"[ALERTA] '{item['categoria']}' passou do limite: "
                           f"{formatar_moeda(gasto)} de {formatar_moeda(limite)}")
        elif gasto >= 0.8 * limite:
            alertas.append(f"[ATENCAO] '{item['categoria']}' já usou "
                           f"{gasto / limite * 100:.0f}% do limite")

    if despesas > rendas and despesas > 0:
        alertas.append("[ALERTA] As despesas do mês são maiores que as rendas!")
    elif rendas > 0 and despesas >= 0.8 * rendas:
        alertas.append(f"[ATENCAO] Você já gastou {despesas / rendas * 100:.0f}% "
                       "da renda do mês.")
    return alertas


# ---------------------------------------------------------------------------
# Arquivos: CSV (lançamentos) e JSON (limites e meta)
# ---------------------------------------------------------------------------
def salvar_csv(lancamentos):
    with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8") as arq:
        escritor = csv.DictWriter(arq, fieldnames=CAMPOS_CSV)
        escritor.writeheader()
        escritor.writerows(lancamentos)


def carregar_csv():
    """Lê os lançamentos do CSV. Linhas com problema são ignoradas."""
    lancamentos = []
    if not os.path.exists(ARQUIVO_CSV):
        return lancamentos
    ignoradas = 0
    with open(ARQUIVO_CSV, newline="", encoding="utf-8") as arq:
        for linha in csv.DictReader(arq):
            try:
                tipo = linha["tipo"]
                if tipo == "receita":  # nome usado nas versões antigas
                    tipo = "renda"
                lanc = {"id": int(linha["id"]), "data": linha["data"],
                        "tipo": tipo, "categoria": linha["categoria"],
                        "valor": float(linha["valor"])}
                if lanc["tipo"] in CATEGORIAS and lanc["valor"] > 0 \
                        and data_valida(lanc["data"]):
                    lancamentos.append(lanc)
                else:
                    ignoradas += 1
            except (KeyError, ValueError, TypeError):
                ignoradas += 1
    if ignoradas > 0:
        print(f"Aviso: {ignoradas} linha(s) inválida(s) do CSV foram ignoradas.")
    return lancamentos


def config_padrao():
    return {"limites": {}, "meta": {"valor": 0.0}}


def salvar_config(config):
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as arq:
        json.dump(config, arq, ensure_ascii=False, indent=2)


def carregar_config():
    if not os.path.exists(ARQUIVO_JSON):
        return config_padrao()
    try:
        with open(ARQUIVO_JSON, encoding="utf-8") as arq:
            config = json.load(arq)
        if "limites" in config and "meta" in config:
            return config
    except (json.JSONDecodeError, OSError):
        pass
    print("Aviso: config.json inválido, usando a configuração padrão.")
    return config_padrao()


# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------
def mostrar_lancamentos(lista):
    if len(lista) == 0:
        print("  Nenhum lançamento.")
        return
    print(f"  {'DATA':<11} {'TIPO':<8} {'CATEGORIA':<12} {'VALOR':>14}")
    for l in lista:
        print(f"  {formatar_data(l['data']):<11} {l['tipo']:<8} "
              f"{l['categoria']:<12} {formatar_moeda(l['valor']):>14}")


def pedir_renda_inicial(lancamentos):
    """Primeiro uso (sem dados): pergunta a renda mensal e já a registra."""
    print("\nVamos começar!")
    valor = ler_valor("Qual é a sua renda mensal (R$)? ")
    hoje = datetime.now().strftime("%Y-%m-%d")
    lancamentos.append(criar_lancamento(lancamentos, hoje, "renda", "salario", valor))
    salvar_csv(lancamentos)


def tela_cadastrar(lancamentos, historico):
    print("\n--- Novo lançamento ---")
    tipo = ler_escolha("Tipo:", ["renda", "despesa"])
    categoria = ler_escolha("Categoria:", CATEGORIAS[tipo])
    valor = ler_valor("Valor (R$): ")
    data = ler_data("Data (dd/mm/aaaa): ")

    lanc = criar_lancamento(lancamentos, data, tipo, categoria, valor)
    lancamentos.append(lanc)
    historico.append(lanc["id"])  # pilha: o último a entrar é o primeiro a sair
    salvar_csv(lancamentos)
    print("Lançamento cadastrado.")


def tela_listar(lancamentos):
    print("\n--- Listar lançamentos ---")
    escolha = ler_escolha("Ordenar por:", ["data", "valor (maior primeiro)"])
    if escolha == "data":
        lista = ordenar_insercao(lancamentos, lambda l: l["data"])
    else:
        lista = ordenar_insercao(lancamentos, lambda l: l["valor"], True)
    mostrar_lancamentos(lista)


def tela_buscar(lancamentos):
    print("\n--- Buscar lançamentos (busca binária) ---")
    escolha = ler_escolha("Buscar por:", ["mês", "valor"])
    if escolha == "valor":
        alvo = ler_valor("Valor (R$): ")
        chave = lambda l: l["valor"]
    else:
        alvo = ler_mes("Mês (mm/aaaa): ")
        chave = lambda l: l["data"][:7]

    ordenada = ordenar_insercao(lancamentos, chave)
    pos, comparacoes = busca_binaria(ordenada, chave, alvo)
    if pos == -1:
        print(f"Nenhum lançamento encontrado ({comparacoes} comparações).")
        return

    achados = []
    while pos < len(ordenada) and chave(ordenada[pos]) == alvo:
        achados.append(ordenada[pos])
        pos += 1
    print(f"{len(achados)} encontrado(s) ({comparacoes} comparações):")
    mostrar_lancamentos(achados)


def tela_relatorio(lancamentos):
    print("\n--- Relatório por período ---")
    inicio = ler_data("Data inicial (dd/mm/aaaa): ")
    fim = ler_data("Data final (dd/mm/aaaa): ")
    if inicio > fim:
        inicio, fim = fim, inicio

    periodo = filtrar_periodo(lancamentos, inicio, fim)
    if len(periodo) == 0:
        print("Nenhum lançamento nesse período.")
        return

    rendas, despesas, saldo = calcular_totais(periodo)
    print(f"\nPeríodo: {formatar_data(inicio)} a {formatar_data(fim)} "
          f"({len(periodo)} lançamentos)")
    print(f"  Rendas:   {formatar_moeda(rendas)}")
    print(f"  Despesas: {formatar_moeda(despesas)}")
    print(f"  Saldo:    {formatar_moeda(saldo)}")

    resumo = resumo_por_categoria(periodo, "despesa")
    if len(resumo) > 0:
        print("\n  Despesas por categoria (maior primeiro):")
        resumo = ordenar_insercao(resumo, lambda i: i["total"], True)
        for item in resumo:
            pct = item["total"] / despesas * 100
            print(f"    {item['categoria']:<12} {formatar_moeda(item['total']):>14}"
                  f"  ({pct:.1f}%, {item['qtd']} lançamento(s))")

    stats = estatisticas_despesas(periodo)
    if stats is not None:
        media, maior, menor = stats
        print(f"\n  Média por despesa: {formatar_moeda(media)}")
        print(f"  Maior despesa: {formatar_moeda(maior['valor'])} "
              f"({maior['categoria']}, {formatar_data(maior['data'])})")
        print(f"  Menor despesa: {formatar_moeda(menor['valor'])} "
              f"({menor['categoria']}, {formatar_data(menor['data'])})")


def tela_matriz(lancamentos):
    print("\n--- Despesas por categoria e mês ---")
    categorias, meses, matriz = matriz_categoria_mes(lancamentos)
    if len(meses) == 0:
        print("Sem dados.")
        return
    cabecalho = f"  {'':<12}"
    for mes in meses:
        cabecalho += f"{formatar_mes(mes):>14}"
    print(cabecalho)
    for i in range(len(categorias)):
        linha = f"  {categorias[i]:<12}"
        for j in range(len(meses)):
            linha += f"{formatar_moeda(matriz[i][j]):>14}"
        print(linha)


def tela_alertas(lancamentos, config):
    print("\n--- Alertas de gastos ---")
    mes = ler_mes("Mês (mm/aaaa): ")
    alertas = gerar_alertas(lancamentos, config, mes)
    if len(alertas) == 0:
        print(f"Nenhum alerta em {formatar_mes(mes)}.")
    for texto in alertas:
        print(texto)


def tela_limite(config):
    print("\n--- Limite mensal por categoria ---")
    categoria = ler_escolha("Categoria:", CATEGORIAS["despesa"])
    limite = ler_valor("Limite mensal (R$): ")
    config["limites"][categoria] = limite
    salvar_config(config)
    print(f"Limite de '{categoria}' definido em {formatar_moeda(limite)}.")


def tela_meta(lancamentos, config):
    print("\n--- Meta de economia ---")
    meta = config["meta"]
    if meta["valor"] > 0:
        _, _, saldo = calcular_totais(lancamentos)
        progresso = max(0.0, min(saldo / meta["valor"], 1.0))
        cheias = int(progresso * 20)
        barra = "#" * cheias + "-" * (20 - cheias)
        print(f"  Meta: {formatar_moeda(meta['valor'])}")
        print(f"  Economizado (saldo): {formatar_moeda(saldo)}")
        print(f"  [{barra}] {progresso * 100:.1f}%")
        if saldo >= meta["valor"]:
            print("  Meta atingida!")
        else:
            print(f"  Faltam {formatar_moeda(meta['valor'] - saldo)}.")
    else:
        print("  Nenhuma meta definida.")

    if ler_escolha("Definir ou alterar a meta?", ["sim", "não"]) == "sim":
        meta["valor"] = ler_valor("Valor da meta (R$): ")
        salvar_config(config)
        print("Meta salva.")


def tela_desfazer(lancamentos, historico):
    print("\n--- Desfazer último lançamento ---")
    if len(historico) == 0:
        print("Nada para desfazer.")
        return
    id_ultimo = historico.pop()
    for i in range(len(lancamentos)):
        if lancamentos[i]["id"] == id_ultimo:
            removido = lancamentos.pop(i)
            salvar_csv(lancamentos)
            print(f"Removido: {removido['tipo']} de {formatar_moeda(removido['valor'])} "
                  f"({removido['categoria']}, {formatar_data(removido['data'])}).")
            return


def mostrar_menu():
    print("\n========== CONTROLE FINANCEIRO ==========")
    print("1) Cadastrar renda/despesa")
    print("2) Listar lançamentos")
    print("3) Buscar lançamento")
    print("4) Relatório por período")
    print("5) Despesas por categoria e mês")
    print("6) Alertas de gastos")
    print("7) Limite por categoria")
    print("8) Meta de economia")
    print("9) Desfazer último lançamento")
    print("0) Sair")


def main():
    lancamentos = carregar_csv()
    config = carregar_config()
    historico = []

    if len(lancamentos) == 0:
        pedir_renda_inicial(lancamentos)

    while True:
        mostrar_menu()
        opcao = input("Opção: ").strip()
        if opcao == "1":
            tela_cadastrar(lancamentos, historico)
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
            tela_desfazer(lancamentos, historico)
        elif opcao == "0":
            break
        else:
            print("Opção inválida.")

    salvar_csv(lancamentos)
    salvar_config(config)
    print("Dados salvos. Até logo!")


if __name__ == "__main__":
    main()
