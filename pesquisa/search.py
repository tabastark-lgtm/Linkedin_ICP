import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from .core import company_url

class SearchError(Exception):
    pass

def search(key, query, opener=urlopen):
    payload = dict(query=query, search_depth="basic", topic="general", max_results=10,
                   include_domains=["linkedin.com"], include_answer=False,
                   include_raw_content=False, include_images=False, auto_parameters=False)
    request = Request("https://api.tavily.com/search", data=json.dumps(payload).encode(),
                      headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    try:
        with opener(request, timeout=25) as response:
            data = json.loads(response.read(2_000_000))
    except HTTPError as error:
        messages = {401: "Chave inválida. Confira a configuração.", 403: "Acesso ao serviço recusado.", 429: "Limite de consultas por minuto. Aguarde antes de tentar novamente.", 432: "Cota gratuita esgotada. Aguarde a renovação; não é necessário contratar um plano.", 433: "Limite de uso atingido. A pesquisa foi interrompida."}
        raise SearchError(messages.get(error.code, f"Serviço de busca indisponível (HTTP {error.code}).")) from None
    except (URLError, TimeoutError, OSError):
        raise SearchError("Não foi possível conectar ao serviço. Confira a internet e tente novamente.") from None
    except (ValueError, TypeError):
        raise SearchError("O serviço retornou uma resposta inválida.") from None
    results, seen = [], set()
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise SearchError("O serviço retornou uma resposta inválida.")
    for item in data["results"]:
        if not isinstance(item, dict):
            continue
        try:
            url = company_url(item.get("url", ""))
        except ValueError:
            continue
        if url not in seen:
            results.append(dict(url=url, title=str(item.get("title", ""))[:300], snippet=str(item.get("content", ""))[:1000]))
            seen.add(url)
        if len(results) == 5:
            break
    return results
