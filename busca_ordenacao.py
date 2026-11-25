"""Algoritmos feitos à mão: ordenação por inserção, busca sequencial e busca binária."""


def fora_de_ordem(a, b, decrescente):
    """Diz se 'a' deveria vir depois de 'b'."""
    if decrescente:
        return a < b
    return a > b


def ordenar_insercao(registros, chave, decrescente=False):
    """
    Ordenação por INSERÇÃO. Devolve uma cópia ordenada.
    'chave' é uma função que diz por qual campo comparar cada item.
    """
    lista = registros[:]
    for i in range(1, len(lista)):
        atual = lista[i]
        j = i - 1
        while j >= 0 and fora_de_ordem(chave(lista[j]), chave(atual), decrescente):
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = atual
    return lista


def busca_sequencial(lista, valor):
    """Percorre item a item. Devolve (posição ou -1, comparações)."""
    comparacoes = 0
    for i in range(len(lista)):
        comparacoes += 1
        if lista[i] == valor:
            return i, comparacoes
    return -1, comparacoes


def busca_binaria(ordenada, chave, alvo):
    """
    Busca BINÁRIA do PRIMEIRO item cuja chave é igual ao alvo.
    A lista precisa estar ordenada pela mesma chave.
    Devolve (posição ou -1, comparações).
    """
    inicio = 0
    fim = len(ordenada) - 1
    achado = -1
    comparacoes = 0
    while inicio <= fim:
        meio = (inicio + fim) // 2
        comparacoes += 1
        if chave(ordenada[meio]) == alvo:
            achado = meio
            fim = meio - 1  # pode haver outro igual mais à esquerda
        elif chave(ordenada[meio]) < alvo:
            inicio = meio + 1
        else:
            fim = meio - 1
    return achado, comparacoes
