# Pesquisa Empresas

Aplicativo Windows que pesquisa páginas candidatas, coleta os campos da empresa confirmada no Chrome e atualiza um Excel separado.

## Começar
1. Extraia o pacote Windows inteiro para uma pasta permanente.
2. Abra **PesquisaEmpresas.exe**. Opcionalmente, dê duplo clique em **Criar atalho.vbs**.
3. Abra **GUIA.html** e faça a configuração inicial do Tavily e da extensão.
4. Importe `examples/01_empresas_ficticias.xlsx` para experimentar a importação. As empresas são fictícias; não devem produzir páginas reais.
5. Ao importar e escolher a saída, a busca começa automaticamente usando a cota Tavily. Se faltar a chave, salvar a configuração continua a pesquisa. Ao retomar, candidatas ficam disponíveis sem nova consulta; use **Pesquisar pendentes**, **Refazer pesquisa** ou **Retentar falhas de pesquisa** quando necessário.
6. Para coleta real, use uma página de empresa que você tenha confirmado no Chrome conectado.

## Desenvolvimento
Python Windows com Tkinter. Dependências: `python -m pip install -r requirements-build.txt`.
Executar: `python main.py`. Testar: `python -m unittest discover -s tests -v`.
Testes do extrator: `pnpm install --frozen-lockfile`, depois `pnpm test`.
Gerar pacote: `python scripts/build.py`. Saída em `dist/`.

## Arquitetura
`pesquisa/core.py`: regras; `excel.py`: leitura/exportação; `store.py`: SQLite e solicitações; `search.py`: Tavily; `native.py`: protocolo Chrome; `windows.py`: credenciais e registro; `ui.py`: janela; `extension/`: confirmação e extração renderizada.

Dados ficam em `%LOCALAPPDATA%\PesquisaEmpresas`. Para backup, feche o aplicativo e copie essa pasta. O Excel exportado não substitui o backup dos trabalhos.

## GitHub
Código publicado em https://github.com/tabastark-lgtm/Linkedin_ICP, na branch main, em 01/10/2026. Não há upload de dados pessoais. Consulte `docs/GITHUB.md` para o registro da publicação e das sete entregas.

## Limitações
O extrator foi projetado para rótulos português/inglês, não para todo layout possível do LinkedIn. Mudanças podem deixar campos vazios. É obrigatório revisar. O plano Tavily gratuito é sujeito às regras atuais do fornecedor. Nenhuma chave ou conta foi criada automaticamente.

## Versão 0.1.1
Fluxo guiado com próxima ação destacada, configuração com continuação da busca, progresso e tratamento distinto de falha/nenhum resultado. Para atualizar, feche a versão anterior, extraia o novo pacote em pasta permanente e abra o novo executável. Os trabalhos continuam em LOCALAPPDATA/PesquisaEmpresas. Carregue a extensão desta pasta e registre seu ID novamente para apontar ao novo bridge; teste a conexão no Chrome.

## Versão 0.1.2
Correção de coleta do rótulo português usuários associados. Atualize também a extensão no Chrome: remova a extensão antiga e carregue a pasta extension desta versão, copie o novo ID e registre-o em Configuração no aplicativo novo. Clique em Testar conexão e prepare uma nova coleta. Atualizar apenas o executável não atualiza o extrator instalado no Chrome. Os dados já salvos não são preenchidos automaticamente; revise uma nova coleta.


## Versão 0.2.0 — automação
- Buscas e posição persistentes; consultas iguais são reaproveitadas dentro do trabalho.
- Alterar website ou termos invalida candidatas anteriores; respostas antigas são descartadas.
- Concluir e próxima valida e avança pulando empresas finalizadas. Salvar e próxima permite continuar registros incompletos.
- Excel bloqueado não impede avanço. Nova tentativa a cada 15 segundos enquanto o aplicativo estiver aberto, com os dados mais recentes.
- Painel com andamento, situação do Excel e horário do backup. Backups locais diários antes da primeira alteração, com retenção de sete cópias.

### Atualizar
Feche a versão antiga, extraia todo o pacote v0.2.0 em uma pasta permanente e abra PesquisaEmpresas.exe. Não copie somente o executável. O banco existente é preservado e recebe backup antes da migração. Não abra a versão antiga depois de migrar.

A extensão 0.1.2 continua compatível, sem mudança nas permissões ou no protocolo. Se ela já funciona, mantenha sua pasta antiga e a extensão instalada. Como o novo aplicativo está em outra pasta, copie o ID da extensão no Chrome e registre-o em **Configuração** do aplicativo novo. Clique em **Testar conexão** na extensão. Não apague a pasta da extensão enquanto ela estiver carregada no Chrome.

As candidatas de sessões antigas da v0.1.2 não existiam no banco: nesses casos use Refazer pesquisa uma vez. Campos já confirmados permanecem.

### Backups e recuperação
Use **Abrir pasta de backups**. Cada ZIP contém trabalhos.sqlite, entradas/ e backup.json. A chave Tavily permanece exclusivamente no Windows. Copie backups para outro disco se desejar proteção contra falha do computador.

Para recuperar no mesmo computador: feche o aplicativo e o Chrome, guarde uma cópia de toda a pasta LOCALAPPDATA/PesquisaEmpresas atual e extraia trabalhos.sqlite e entradas/ do backup para o local original indicado em backup.json. Abra a versão 0.2.0 e confira os trabalhos antes de atualizar o Excel. A restauração substitui o estado atual pelo estado do backup; não mescla trabalhos. Para restaurar em outro local, os caminhos snapshot e output no banco precisam ser ajustados; peça assistência. Não existe botão de restauração nesta versão.
