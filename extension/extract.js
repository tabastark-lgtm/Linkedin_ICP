/* A função é autocontida para chrome.scripting.executeScript. Não faz requests. */
function extractCompany() {
  const clean = s => String(s || '').replace(/\s+/g, ' ').trim();
  const norm = s => clean(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/:$/, '');
  const visible = el => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden' && getComputedStyle(el).display !== 'none';
  const text = el => visible(el) ? clean(el.innerText) : '';
  const fields = {name:'', members:'', industry:'', size:''};
  const root = document.querySelector('main');
  const pageText = clean(document.body?.innerText);
  if (/\/(login|authwall|checkpoint|uas\/login)(\/|\?|$)/i.test(location.href) || (!root && /sign in|entrar|security verification|verificacao de seguranca/i.test(norm(pageText)))) {
    return {fields, access_issue:true, error:'Login expirado ou acesso interrompido. Resolva no Chrome e tente novamente.'};
  }
  if (!root) return {fields, error:'Não foi possível identificar o conteúdo da empresa. Abra a seção Sobre.'};
  const title = [...root.querySelectorAll('h1')].find(visible);
  fields.name = text(title);
  for (const dt of root.querySelectorAll('dt')) {
    const label = norm(text(dt));
    let dd = dt.nextElementSibling;
    if (!dd || dd.tagName !== 'DD') continue;
    const value = text(dd);
    if (label === 'setor' || label === 'industry') fields.industry = value;
    if (label === 'tamanho da empresa' || label === 'company size') {
      // O primeiro dd é a faixa. Um dd seguinte pode conter usuários/membros associados.
      const range = value.match(/^(?:[\d.,]+\s*[–—-]\s*[\d.,]+|[\d.,]+\+|[\d.,]+)\s*(?:funcion[aá]rios|employees)\b/i);
      fields.size = range ? range[0] : (/associated members|membros associados|usu[aá]rios associados/i.test(value) ? '' : value);
    }
  }
  const memberPatterns = [
    /([\d][\d.,\s]*\+?)\s+(?:membros? associados?|usu[aá]rios? associados?|associated members?)/i,
    /(?:ver|veja|visualizar|see|view)(?:\s+todos(?:\s+os)?|\s+all)?\s+([\d][\d.,\s]*\+?)\s+(?:funcion[aá]rios|employees)\b/i
  ];
  for (const el of root.querySelectorAll('dd,a,span,p')) {
    const value = text(el);
    if (!value || value.length > 240) continue;
    for (const pattern of memberPatterns) {
      const match = value.match(pattern);
      if (match) { fields.members = clean(match[1]); break; }
    }
    if (fields.members) break;
  }
  return {fields, error:Object.values(fields).some(v => !v) ? 'Há campos não identificados. Confira a seção Sobre e revise no aplicativo.' : ''};
}
if (typeof module !== 'undefined') module.exports = {extractCompany};
