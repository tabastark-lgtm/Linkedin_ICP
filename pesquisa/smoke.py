"""Diagnóstico opcional do pacote, isolado em PESQUISA_DATA_DIR."""
import json
import os
import sys
from pathlib import Path

def run():
    if not os.environ.get("PESQUISA_DATA_DIR"):
        raise ValueError("O diagnóstico exige PESQUISA_DATA_DIR em pasta de teste.")
    root = Path(os.environ["PESQUISA_DATA_DIR"]); root.mkdir(parents=True, exist_ok=True)
    report = root / "smoke-report.json"
    app = None
    try:
        from .ui import App
        from .store import Store
        store = Store(root)
        base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
        jid = store.import_job(base / "examples/01_empresas_ficticias.xlsx", "Empresas", root / "saida.xlsx")
        app = App(store); app.open_job(jid); app.update()
        assert app.step_action == "search_batch"
        assert "Pesquisar" in app.step_title.get()
        app.vars["name"].set("TESTE FICTÍCIO DO PACOTE")
        assert app.save()
        app.navigate(1); app.navigate(-1)
        assert app.vars["name"].get() == "TESTE FICTÍCIO DO PACOTE"
        assert app.export()
        app.arm(); assert store.capture_context()["record_id"] == app.current["id"]
        report.write_text(json.dumps({"ok":True,"frozen":bool(getattr(sys,"frozen",False)),"checks":["Tkinter","importação","formulário","SQLite","navegação","exportação","preparar coleta","orientação após importação"]},ensure_ascii=False,indent=2),encoding="utf-8")
    except Exception as error:
        report.write_text(json.dumps({"ok":False,"error":str(error)},ensure_ascii=False,indent=2),encoding="utf-8")
        raise
    finally:
        if app: app.close()
