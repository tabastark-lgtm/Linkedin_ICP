# Pesquisa Empresas

Aplicativo Windows que pesquisa páginas candidatas, coleta os campos da empresa confirmada no Chrome e atualiza um Excel separado.

## Começar
1. Extraia o pacote Windows inteiro para uma pasta permanente.
2. Abra **PesquisaEmpresas.exe**. Opcionalmente, dê duplo clique em **Criar atalho.vbs**.
3. Abra **GUIA.html** e faça a configuração inicial do Tavily e da extensão.
4. Importe `examples/01_empresas_ficticias.xlsx` para experimentar a importação. As empresas são fictícias; não devem produzir páginas reais.
5. Após importar ou retomar, siga o painel **Próximo passo** e clique em **Iniciar pesquisa das empresas**. A importação não inicia a busca; se faltar a chave, salvar a configuração continua a busca solicitada.
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
