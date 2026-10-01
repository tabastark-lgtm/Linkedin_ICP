"""Orientação do fluxo; não altera dados nem confirma candidatas."""
from .core import domain


def next_step(data, candidates, searching=False, armed=False):
    if searching:
        return ("1. Pesquisa em andamento", "Aguarde os resultados. Você pode interromper pelo botão acima.", "Aguarde…", "wait")
    if data["status"] == "Concluída":
        return ("4. Empresa concluída", "Salve o Excel e continue para a próxima empresa.", "Salvar Excel e próxima", "next")
    if data["status"] == "Não encontrada":
        return ("Empresa marcada como não encontrada", "Salve e continue, ou use Pesquisar esta empresa para tentar novamente.", "Salvar Excel e próxima", "next")
    if data["status"] == "Acesso indisponível" and data["url"].strip():
        return ("2. Verificar o acesso no Chrome", "A página não pôde ser lida. Confira o acesso à seção Sobre no Chrome e tente coletar novamente.", "Preparar coleta e abrir Chrome", "collect")
    if data["confirmed"]:
        return ("3. Revisar os dados", "Confira os campos. Preencha os ausentes ou marque Não disponível. Depois conclua esta empresa.", "Concluir e próxima empresa", "complete")
    if armed:
        return ("2. Confirmar e coletar no Chrome", "Na página Sobre, abra a extensão Pesquisa Empresas, confirme que é a empresa correta e clique em coletar. Volte aqui para revisar. Se expirar, prepare novamente.", "Preparar e abrir novamente", "collect")
    if data["url"].strip():
        return ("2. Confirmar e coletar no Chrome", "Abra a página, confira a empresa e use a extensão para coletar os dados. Precisa instalar a extensão? Abra Configuração e o guia.", "Preparar coleta e abrir Chrome", "collect")
    try:
        domain(data["website"])
    except ValueError:
        return ("Corrigir website", "Preencha Website de pesquisa com um endereço válido. A entrada original será preservada.", "Validar website e pesquisar", "search_one")
    if candidates:
        return ("2. Escolher a página da empresa", "Selecione uma candidata na lista abaixo. A seleção não confirma a identidade da empresa.", "Abrir candidata selecionada", "candidate")
    if data["search_state"] == "Falha na busca":
        return ("1. Pesquisa interrompida", "A busca falhou; isso não significa que a empresa não existe. Confira a mensagem, a conexão e a chave em Configuração.", "Tentar esta empresa novamente", "search_one")
    if data["search_state"] == "Sem candidatas":
        return ("1. Nenhuma candidata encontrada", "A busca terminou sem páginas candidatas. Ajuste a consulta abaixo e tente novamente, ou informe uma URL que você verificou.", "Pesquisar esta empresa novamente", "search_one")
    return ("1. Pesquisar páginas no LinkedIn", "A planilha foi carregada. Clique no botão para localizar as páginas das empresas. Se faltar a chave Tavily, vamos orientar a configuração.", "Iniciar pesquisa das empresas", "search_batch")
