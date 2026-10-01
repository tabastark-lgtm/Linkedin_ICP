"""Regras puras. Nunca consulta páginas do LinkedIn."""
import re
from datetime import datetime
from urllib.parse import urlsplit, unquote, quote

FIELDS = {"name": "Nome da empresa", "members": "Usuários associados", "industry": "Setor", "size": "Faixa de tamanho"}
STATUSES = ("Pendente", "Em pesquisa", "Aguardando confirmação", "Aguardando revisão", "Coleta incompleta", "Concluída", "Em dúvida", "Não encontrada", "Acesso indisponível", "Website ausente", "Website inválido")

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def domain(value):
    value = str(value or "").strip()
    if not value:
        raise ValueError("Website ausente")
    try:
        if re.search(r"\s", value) or "\\" in value:
            raise ValueError()
        u = urlsplit(value if "://" in value else "https://" + value)
        host = (u.hostname or "").encode("idna").decode("ascii").lower().rstrip(".")
        if u.scheme not in ("http", "https") or u.username or u.password or u.port:
            raise ValueError()
        if not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{1,62}", host):
            raise ValueError()
        return host.removeprefix("www.")
    except (ValueError, UnicodeError):
        raise ValueError("Website inválido: informe um domínio, como www.empresa.com.br.") from None

def company_url(value):
    try:
        u = urlsplit(str(value).strip())
        host = (u.hostname or "").lower()
        parts = u.path.strip("/").split("/")
        if u.scheme != "https" or u.username or u.password or u.port or "\\" in value:
            raise ValueError()
        if not (host == "linkedin.com" or host.endswith(".linkedin.com")):
            raise ValueError()
        if len(parts) < 2 or parts[0] != "company" or not re.fullmatch(r"[\w-]+", unquote(parts[1])):
            raise ValueError()
        return "https://www.linkedin.com/company/" + quote(unquote(parts[1]), safe="-") + "/"
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Use uma URL HTTPS de página de empresa do LinkedIn (/company/...).") from None

def initial_status(website):
    try:
        domain(website)
        return "Pendente"
    except ValueError:
        return "Website ausente" if not str(website or "").strip() else "Website inválido"

def validate_record(data):
    if data.get("status") not in STATUSES:
        raise ValueError("Status inválido.")
    for key in (*FIELDS, "website", "url", "notes"):
        if not isinstance(data.get(key, ""), str) or len(data.get(key, "")) > 10000:
            raise ValueError("Campo muito longo ou inválido.")
    unavailable = data.get("unavailable", [])
    if not isinstance(unavailable, list) or any(k not in ("members", "industry", "size") for k in unavailable):
        raise ValueError("Campos não disponíveis inválidos.")
    if any(data.get(k, "").strip() for k in unavailable):
        raise ValueError("Desmarque Não disponível nos campos que têm um valor preenchido.")
    if data.get("confirmed"):
        company_url(data.get("url", ""))
    if data.get("status") == "Concluída":
        if not data.get("confirmed") or not data.get("name", "").strip():
            raise ValueError("Para concluir, confirme a página e preencha o nome.")
        missing = [FIELDS[k] for k in ("members", "industry", "size") if not data.get(k, "").strip() and k not in unavailable]
        if missing:
            raise ValueError("Preencha ou marque Não disponível: " + ", ".join(missing))

def empty_record(website):
    return dict(website=str(website or ""), url="", confirmed=False, name="", members="", industry="", size="", notes="", unavailable=[], status=initial_status(website), consulted_at="", search_state="Não executada", searched_at="")
