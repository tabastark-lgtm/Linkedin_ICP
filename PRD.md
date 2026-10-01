# Pesquisa Empresas — v0.2.0

## Objetivo e fluxo
Aplicativo Windows para um usuário iniciante pesquisar e enriquecer até 50 empresas por trabalho. Importar .xlsx → selecionar aba e saída → pesquisar automaticamente → escolher candidata → confirmar e coletar no Chrome → revisar → concluir e próxima.

Ao importar, o aviso informa uso da cota Tavily. Interromper termina após a consulta atual, preservando resultados recebidos. Se faltar a chave, salvar a configuração continua a busca. Retomar abre a última empresa selecionada e não inicia rede automaticamente.

## Busca e identidade
- Candidatas, termos, horário e resultado persistem em SQLite. Cache por trabalho/consulta, inclusive resultados vazios; sem prazo de expiração automático. Refazer pesquisa ignora o cache.
- Pesquisar pendentes consulta somente registros não finalizados, válidos e ainda não pesquisados. Falhas e ausência de resultados exigem ação explícita. Retentar falhas refaz só registros com falha.
- Consultas iguais podem compartilhar resultados, mas cada linha conserva confirmação e dados independentes.
- Alterar website ou termos invalida candidatas; geração por solicitação impede aplicar respostas antigas, mesmo ao voltar aos termos originais.
- Migração preserva campos antigos. Candidatas não armazenadas pela v0.1.2 exigem Refazer pesquisa; nunca são reconstruídas a partir de dados confirmados.
- Não inferir URL ou dados. URLs candidatas vêm do Tavily e devem ser páginas HTTPS /company/ em domínio LinkedIn legítimo. Perfil pessoal é recusado.

## Confirmação e revisão
Extensão 0.1.2 inalterada: activeTab, scripting, nativeMessaging; apenas DOM renderizado após confirmação humana. Sem APIs internas, cookies, senha, pessoas, navegação autônoma ou contorno de bloqueios. Protocolo mantém token de uso único, registro, trabalho, revisão e validade de 15 minutos.

Usuários associados e faixa de tamanho são campos distintos. Concluir exige URL confirmada, nome, demais campos ou marcação explícita Não disponível. Coleta recebida é rascunho e requer revisão para substituir valores.

Status: Pendente, Em pesquisa, Aguardando confirmação, Aguardando revisão, Coleta incompleta, Concluída, Em dúvida, Não encontrada, Acesso indisponível, Website ausente e Website inválido.

Concluir e próxima valida, salva e solicita exportação. Salvar e próxima permite registros incompletos. Ambos avançam na ordem original pulando Concluída e Não encontrada, voltando ao início se necessário, sem selecionar a mesma linha imediatamente. Pendências restantes são resumidas.

## Persistência, Excel e backup
- Uma coluna Website da empresa na primeira linha, até 50 linhas com conteúdo; lacunas intermediárias não são tarefas. Preservar entrada, demais colunas, ordem e valores; exportar somente a aba escolhida, sem gráficos/formatação/outras abas. Fórmulas exigem resultado salvo. Strings não executam fórmulas.
- SQLite em LOCALAPPDATA/PesquisaEmpresas com cópia da entrada. Schema user_version=2 acrescenta searches e search_cache; posição por trabalho em settings. Banco antigo recebe backup completo antes da migração; se esse backup falhar, a abertura é interrompida com mensagem.
- Exportação atômica para destino diferente de todas as entradas. Colunas e datas de consulta permanecem no formato da v0.1.2.
- Arquivo bloqueado permite continuar e dispara nova tentativa a cada 15 segundos enquanto aberto o aplicativo, inclusive ao mudar de trabalho. Tentativa usa registros mais recentes. Ao retomar trabalho pendente, exportar novamente.
- Erros diferentes de bloqueio exigem Atualizar Excel agora ou Exportar como; mensagem exibe a causa sem loop de alertas.
- Backup diário antes da primeira alteração, usando SQLite backup e cópias das entradas em ZIP. Manter sete cópias mais recentes, incluindo backups de migração. Falha diária é informada, mas não impede salvamento local. Não inclui chave Windows. Recuperação manual documentada.
- Painel informa total, concluídas, não encontradas, restantes, dúvidas, falhas de pesquisa, websites inválidos/ausentes, coletas incompletas, estado do Excel e último backup.

## Aceitação e limites
Testar 50/51 registros, cabeçalhos, zeros à esquerda, texto como fórmula, hash da entrada, retomada, cache sem rede, invalidar resposta atrasada, interrupção/cota, validação de conclusão, exportação bloqueada com dados recentes, restauração e retenção de backup, migração e protocolo da extensão.

Validação de controles Tk e bloqueio Windows não substitui conferência visual no desktop nem teste na conta real do LinkedIn/Tavily. Gratuidade e cota dependem do fornecedor. Publicação desta entrega remota não é automática.

## Entrega v0.2.0 e manutenção
- Publicação do código e documentação autorizada pelo usuário em tabastark-lgtm/Linkedin_ICP, branch main. Preservar o histórico remoto, sem forçar atualização.
- Evidências da versão: 40 testes Python, 10 cenários DOM simulados, smoke Tk e testes do executável/bridge empacotados. A conferência manual na conta real continua pendente e não pode ser declarada concluída.
- Aplicativo 0.2.0, extensão compatível 0.1.2 e banco user_version=2. Atualização exige fechar a versão anterior, abrir a pasta nova e registrar o ID da extensão no novo aplicativo.
- O pacote Windows e SHA-256 permanecem na entrega local. Publicação de código não equivale à criação de uma release com executáveis.
