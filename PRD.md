# Pesquisa Empresas — v0.1.2

## Objetivo e público
Aplicativo local para uma pessoa iniciante no Windows enriquecer até 50 empresas por trabalho. Busca candidatas, coleta campos da página confirmada no Chrome e atualiza outro Excel. Não exige terminal no uso diário.

## Fluxo
Configurar chave Tavily e extensão → importar .xlsx e escolher aba → conferir prévia → escolher saída → pesquisar → abrir candidata no Chrome → abrir Sobre → confirmar empresa e coletar na extensão → revisar valores atuais/coletados → aplicar → salvar e próxima → retomar quando necessário.

## Dados e regras
- Cabeçalho na primeira linha: uma única coluna Website da empresa, ignorando espaços externos.
- Até 50 linhas com conteúdo. Linhas totalmente vazias intermediárias são preservadas sem virar tarefas.
- Campos: website usado, URL confirmada, nome, membros associados, setor, faixa de tamanho, campos não disponíveis, observações, status, data da consulta.
- Membros e tamanho são distintos. Ausência nunca vira zero ou estimativa.
- Websites inválidos/ausentes exigem correção em campo separado. Original imutável.
- Repetições mantêm identidade por trabalho/aba/linha. Só consultas iguais dentro do lote são reaproveitadas, não confirmações.
- URL LinkedIn deve ser HTTPS, domínio legítimo e /company/identificador. Nenhuma URL é inferida do domínio.
- Status: Pendente, Em pesquisa, Aguardando confirmação, Aguardando revisão, Coleta incompleta, Concluída, Em dúvida, Não encontrada, Acesso indisponível, Website ausente, Website inválido.
- Conclusão exige URL confirmada, nome e os demais campos preenchidos ou explicitamente não disponíveis.

## Integrações e limites
Tavily Search básico, sem resposta gerada ou conteúdo integral. A chave fica no Gerenciador de Credenciais do Windows. Nenhuma contratação automática. A cota e gratuidade são condições do fornecedor, não garantia do programa.

Extensão Chrome local: activeTab, scripting, nativeMessaging. Coleta apenas após gesto e confirmação. Não lê cookies/senhas, não consulta APIs internas e não contorna login, CAPTCHA ou bloqueio. Campos são identificados no DOM renderizado em português/inglês. Layouts diferentes podem requerer manutenção.

Mensagens vinculam token, trabalho e registro. Token de uso único, validade de 15 minutos, revisão otimista e sinal de aplicativo aberto. Alteração de linha ou do registro invalida a solicitação. Candidatas são temporárias; dados confirmados são locais.

## Persistência e Excel
SQLite em LOCALAPPDATA/PesquisaEmpresas. Cópia da entrada, registros por linha, salvamento após pausa e ao navegar/fechar. O banco é a fonte do trabalho; exportação não altera data de coleta.

Saída nova com dados e colunas da aba escolhida, em ordem, sem gráficos/estilos/abas extras. Fórmulas usam resultado em cache; ausência de cache bloqueia importação. Strings são texto, inclusive iniciadas por =. Colisões de cabeçalho recebem sufixo. Salvar e próxima atualiza saída atomicamente; arquivo aberto/sem permissão deixa atualização pendente, sem perder o banco.

## Aceitação
1. Importação aceita 50, recusa 51 e cabeçalho ausente/duplicado.
2. Original tem hash idêntico antes/depois; duplicatas, lacunas e demais colunas permanecem.
3. Busca distingue falha e ausência de candidatas; nenhuma seleção automática.
4. Coleta fica em rascunho e apresenta comparação antes de substituir valores.
5. Mensagens antigas/de outra linha são rejeitadas.
6. Fechar/reabrir mantém registros, status e data; Excel bloqueado não perde dados.
7. Pacote abre sem Python instalado; configuração Chrome/Tavily é guiada.

## Fora da v0.1
Sincronização, múltiplos usuários, armazenamento de senha LinkedIn, coleta de perfis/pessoas, navegação autônoma pelo LinkedIn, garantia contra mudanças de layout e reprodução integral de formatação Excel.

## Fluxo guiado v0.1.1
- Painel Próximo passo acompanha pesquisa, escolha, coleta, revisão e conclusão ao importar ou retomar.
- A pesquisa exige ação do usuário; se faltar a chave, salvar a configuração continua a pesquisa solicitada. Fechar a configuração não inicia consultas.
- Progresso aparece imediatamente, falhas permanecem visíveis e resultados vazios orientam uma nova consulta.
- Preparar coleta e abrir Chrome é uma ação guiada; confirmação permanece na extensão.
- Concluir e próxima valida, exporta e avança. Falha de exportação não avança e mantém o banco salvo.
- Compatibilidade: nenhuma mudança em esquema SQLite, planilha ou protocolo Native Messaging.

## Correção v0.1.2
Extrator aceita usuários associados (com/sem acento), membros associados e associated members. Aplicativo e cabeçalho de saída usam Usuários associados. A chave interna members e o banco/protocolo permanecem compatíveis. Usuários associados nunca são usados como faixa de tamanho.
