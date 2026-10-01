"""Smoke de controles Tk com dados fictícios; não acessa Chrome ou serviços."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pesquisa.ui import App
from pesquisa.store import Store
from openpyxl import load_workbook

def main():
    with tempfile.TemporaryDirectory() as temp:
        store = Store(Path(temp) / "dados")
        source = Path(__file__).resolve().parents[1] / "examples/01_empresas_ficticias.xlsx"
        output = Path(temp) / "saida.xlsx"
        job = store.import_job(source, "Empresas", output)
        app = App(store)
        app.open_job(job)
        app.update()
        app.vars["name"].set("Aurora — teste de interface")
        app.vars["members"].set("27")
        app.vars["size"].set("11–50 funcionários")
        assert app.save()
        app.navigate(1); app.navigate(-1)
        assert app.vars["name"].get() == "Aurora — teste de interface"
        assert app.export()
        wb = load_workbook(output)
        assert wb.active["G2"].value == "Aurora — teste de interface"
        assert wb.active["H2"].value == "27"
        wb.close()
        app.update_idletasks()
        app.form_canvas.yview_moveto(1)
        app.update_idletasks()
        root_bottom = app.winfo_rooty() + app.winfo_height()
        assert app.candidates.winfo_height() >= 50, "Lista de candidatas sem espaço"
        assert app.candidates.winfo_rooty() + app.candidates.winfo_height() <= root_bottom
        app.arm()
        assert store.capture_context()["record_id"] == app.current["id"]
        app.close()
        app = App(Store(Path(temp) / "dados")); app.open_job(job); app.update()
        assert app.vars["name"].get() == "Aurora — teste de interface"
        with patch("pesquisa.ui.messagebox.askyesno", return_value=True):
            app.vars["url"].set("https://www.linkedin.com/company/teste/")
            app.confirm_url()
        assert app.current["data"]["confirmed"]
        app.vars["url"].set("https://www.linkedin.com/company/outro/")
        assert not app.current["data"]["confirmed"]
        assert app.save()
        app.close()
    print("UI_SMOKE_OK: edição, salvamento, navegação, exportação, retomada, URL e vínculo de coleta")

if __name__ == "__main__": main()
