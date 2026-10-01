# Estado da implementação

## Implementado
- Importação, validação, prévia, preservação da entrada e oito exemplos fictícios.
- Janela Windows, formulário, revisão, status, salvamento e retomada SQLite.
- Busca Tavily e tratamento de erros/cota; candidatas nunca são confirmações.
- Extensão Chrome e Native Messaging com vínculo de linha, token e revisão.
- Exportação atômica com falha recuperável quando o arquivo estiver aberto.
- Guia ilustrado, documentação e scripts de pacote Windows.

## Verificação realizada
- 15 testes Python passaram: URLs, planilhas, fórmulas, limites, retomada, mensagens de coleta, busca simulada e exportação.
- 5 cenários de extração em DOM simulado passaram: português, inglês, campos parciais, login e membros/tamanho no mesmo bloco.
- Smoke de controles Tk passou: edição, navegação, salvamento, retomada, confirmação/invalidação de URL, exportação e vínculo de coleta.
- Pacote Windows compilado com PyInstaller. Autoteste do executável passou em pasta isolada, incluindo inicialização Tk, formulário e Excel.
- Bridge compilado passou nos testes via subprocesso: conexão, contexto de linha, recebimento de coleta, revisão obrigatória e rejeição de mensagem repetida.
- Exemplo principal inspecionado por valores e renderização.
- A automação de desktop retornou acesso negado ao abrir o executável. Não foi concluída inspeção visual na área de trabalho do usuário; o autoteste de controles não substitui essa inspeção.

## Pendências externas
- Configurar chave Tavily do usuário e executar busca real.
- Carregar extensão no Chrome, registrar ID e validar uma coleta na conta do usuário.
- Usuário solicitou trocar a conta GitHub. Não publicar até identificar a conta correta.

## Git local
- Sete entregas registradas em commits e branches entrega-01-base até entrega-07-windows; integradas localmente na main.
- Autor técnico local: Codex. Nenhuma identidade da conta GitHub anterior foi usada para publicação.
- Tag local v0.1.0. Repositório remoto, issues, PRs e release no GitHub ainda não criados.

## Retomar
Leia PRD.md e AGENTS.md. Execute testes antes de alterar. Nenhum dado real foi coletado. Use apenas examples/ para testes locais. Não considere testes simulados prova de compatibilidade com o LinkedIn atual.

## Revisão v0.1.1 — 30/09/2026
- Implementado painel Próximo passo após importar/retomar, com próxima ação destacada.
- Salvar chave em configuração aberta pela busca continua a pesquisa solicitada; cancelar não consulta o serviço.
- Progresso imediato; falha permanece visível e não vira empresa não encontrada.
- Candidata abre Sobre com coleta preparada; orientação de instalação/teste de conexão e revisão.
- Concluir e próxima valida os dados, exporta e avança; falha de exportação mantém a linha.
- Esquemas de planilha, SQLite e protocolo Native Messaging preservados.
- 26 testes Python passaram, incluindo dez integrações Tk/SQLite e um cenário de orientação de acesso indisponível. 5 cenários de DOM simulado passaram. Rede, Chrome e credenciais foram simulados nos testes da janela.
- Testes Tk no runtime desta sessão exigem caminhos Tcl/Tk relativos à pasta 2026-09-29/p; com caminhos absolutos o Tcl não localiza init.tcl. O pacote usa caminhos relativos próprios.
- Busca Tavily real e coleta LinkedIn no Chrome ainda pendentes; não considerar os testes simulados validação de integração real.
- Corrigido build para usar Tcl/Tk relativo durante a análise do PyInstaller. O primeiro pacote de teste falhou por exclusão de tkinter; não foi entregue.
- Pacote recompilado passou em autoteste do executável: Tkinter, importação, formulário, persistência, navegação, exportação, preparação de coleta e orientação inicial.
- Bridge empacotado passou em ping, contexto, recebimento para revisão e rejeição de mensagem repetida via subprocesso. Isso não comprova conexão em um Chrome real.
- Nenhuma chave Tavily configurada foi encontrada nesta sessão. Não executada busca real nem coleta real no LinkedIn. A pasta de dados do usuário não foi modificada pelos testes; todos usaram diretórios isolados com exemplos fictícios.
- Verificação do pacote final: houve WinError 4551 (Controle de Aplicativo) na primeira tentativa. Repetir exatamente o mesmo executável, sem alterar o arquivo nem políticas, abriu normalmente. Autoteste final e testes do bridge passaram. O executável permanece sem assinatura digital.

## Correção v0.1.2 — 30/09/2026
- Causa confirmada: o extrator não aceitava o rótulo usuários associados visto na captura do usuário.
- Acrescentado suporte a usuários associados com/sem acento, mantendo membros associados e associated members.
- Nome exibido e cabeçalho Excel alterados para Usuários associados. A chave members e os esquemas de banco/protocolo foram preservados.
- 10 cenários de DOM simulado passaram, incluindo 57.744 usuários associados separado de 5.001-10.000 funcionários, mesmo bloco, texto sem acento, informação oculta e contagem sem faixa de tamanho. Não foi copiado HTML real de nenhuma empresa.
- 26 testes Python passaram, incluindo exportação com o novo cabeçalho. Nenhum dado real foi modificado.
- É necessário atualizar a extensão no Chrome e fazer nova coleta. Leitura da página real atualizada ainda depende da confirmação do usuário.
- Pacote Windows v0.1.2 passou em autoteste Tk/formulário/exportação, bridge por subprocesso, novo cabeçalho Excel e igualdade do extrator empacotado com o código testado.
