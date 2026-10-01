# Orientações para manutenção

- Interface e documentação em português simples. Manter uso diário sem terminal.
- Preservar entradas e identidade por trabalho/aba/linha. Nunca usar domínio como chave única.
- Não coletar LinkedIn sem confirmação explícita da empresa na extensão. Não acessar cookies, credenciais, APIs internas nem contornar bloqueios.
- Extrator deve ler somente elementos renderizados e manter membros associados separados de tamanho.
- Não inferir URLs, identidade, dados faltantes ou zeros. Não tratar erro da busca como página não encontrada.
- Não registrar chaves, HTML de páginas reais, cookies, planilhas pessoais ou dados de produção no Git.
- Código de rede apenas no serviço Tavily. DOM do LinkedIn só na extensão, após ação do usuário.
- Manter validação de token, linha, trabalho, revisão, prazo e uso único em Native Messaging.
- Toda gravação de saída é atômica e recusa arquivos de entrada. Banco é fonte de retomada.
- Testes: `python -m unittest discover -s tests -v`; `pnpm install --frozen-lockfile` e `pnpm test` para DOM simulado.
- Exemplos: `python scripts/create_examples.py`. Build Windows: `python scripts/build.py` após instalar requirements-build.txt.
- Atualizar PRD.md quando comportamento mudar e STATUS.md com evidências e pendências reais.
- Busca persistida é candidata, nunca confirmação. Mudanças de website/consulta invalidam gerações e respostas antigas; preservar cache somente por trabalho/consulta.
- Migração exige backup consistente anterior. Backup diário pode falhar sem bloquear salvamento, mas a falha deve ficar visível. Usar SQLite backup e fechar conexões explicitamente no Windows.
- Excel bloqueado não impede avanço. Repetir somente bloqueios de compartilhamento, a cada 15 segundos e com dados recentes; outros erros exigem ação explícita.
- Não declarar validação em LinkedIn real, Chrome ou Tavily sem executar esse teste. Não publicar na conta GitHub anterior; confirmar a conta de destino informada pelo usuário.
