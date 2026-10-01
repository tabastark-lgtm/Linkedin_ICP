const host = 'br.com.pesquisaempresas.bridge';
const status = document.getElementById('status');
const capture = document.getElementById('capture');
const checkbox = document.getElementById('confirmed');
let context = null;
let targetTab = null;
function company(url) {
  try { const u = new URL(url); return u.protocol === 'https:' && !u.username && !u.password && !u.port && (u.hostname === 'linkedin.com' || u.hostname.endsWith('.linkedin.com')) && /^\/company\/[^/]+\//.test(u.pathname + '/'); } catch { return false; }
}
async function send(message) {
  try {
    const result = await chrome.runtime.sendNativeMessage(host, message);
    if (!result?.ok) throw new Error(result?.error || 'Sem resposta do aplicativo.');
    return result;
  } catch (error) {
    if (/host|native messaging|specified/i.test(error.message)) throw new Error('Conexão não configurada. No aplicativo, abra Configuração e registre o ID desta extensão.');
    throw error;
  }
}
async function init() {
  try {
    const result = await send({action:'context'});
    context = result.context;
    [targetTab] = await chrome.tabs.query({active:true, currentWindow:true});
    document.getElementById('destination').textContent = `Linha ${context.row_num} do Excel\nWebsite original: ${context.website || '(vazio)'}${context.name ? '\nNome: ' + context.name : ''}`;
    document.getElementById('page').textContent = targetTab?.url || '';
    if (!company(targetTab?.url)) throw new Error('Abra uma página de empresa do LinkedIn, na seção Sobre.');
    status.textContent = 'Confira a empresa e marque a confirmação.';
  } catch(error) { context = null; status.textContent = error.message; document.getElementById('destination').textContent = 'Coleta ainda não preparada.'; }
}
checkbox.addEventListener('change', () => { capture.disabled = !(checkbox.checked && context); });
document.getElementById('ping').addEventListener('click', async () => {
  try { status.textContent = (await send({action:'ping'})).message; } catch(error) { status.textContent = error.message; }
});
capture.addEventListener('click', async () => {
  capture.disabled = true;
  try {
    const current = await chrome.tabs.get(targetTab.id);
    if (current.url !== targetTab.url || !company(current.url)) throw new Error('A página mudou. Feche e reabra a extensão.');
    const results = await chrome.scripting.executeScript({target:{tabId:targetTab.id}, func:extractCompany});
    const after = await chrome.tabs.get(targetTab.id);
    if (after.url !== targetTab.url) throw new Error('A página mudou durante a coleta. Tente novamente.');
    const result = results[0]?.result;
    if (!result?.fields) throw new Error('Não foi possível ler os campos desta página.');
    const response = await send({action:'capture', ...context, confirmed:true, url:current.url, ...result});
    status.textContent = response.message;
    context = null;
  } catch(error) { status.textContent = error.message; capture.disabled = false; }
});
init();
