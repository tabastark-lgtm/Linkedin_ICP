"""Integração Tk/SQLite com rede, credenciais e Chrome simulados."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from pesquisa.ui import App
from pesquisa.store import Store
from pesquisa.core import empty_record
from pesquisa.workflow import next_step
from pesquisa.search import SearchError

BASE = Path(__file__).resolve().parents[1]
CANDIDATE = dict(url="https://www.linkedin.com/company/ficticia/", title="Fictícia", snippet="Teste")

class GuidedUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "dados")
        self.job = self.store.import_job(BASE / "examples/01_empresas_ficticias.xlsx", "Empresas", self.root / "saida.xlsx")
        self.app = App(self.store); self.app.withdraw(); self.app.open_job(self.job); self.app.update()
        self.info = patch("pesquisa.ui.messagebox.showinfo").start()
        self.error = patch("pesquisa.ui.messagebox.showerror").start()

    def tearDown(self):
        self.app.close()
        patch.stopall()
        self.temp.cleanup()

    def drain(self):
        deadline = time.monotonic() + 5
        while self.app.searching and time.monotonic() < deadline:
            time.sleep(.02)
            self.app.after_cancel(self.app.poll_job); self.app.poll()
        self.assertFalse(self.app.searching)

    def test_import_and_resume_guidance_and_invalid_website(self):
        self.assertEqual(self.app.step_action, "search_batch")
        self.app.vars["website"].set("inválido"); self.assertTrue(self.app.save())
        self.assertEqual(self.app.step_action, "search_one")
        self.assertIn("Corrigir", self.app.step_title.get())
        self.app.vars["website"].set("example.com"); self.app.save()
        self.app.open_job(self.job)
        self.assertEqual(self.app.step_action, "search_batch")

    def test_returning_home_removes_progress_resize_callback(self):
        with patch.object(self.app, "report_callback_exception") as error:
            self.app.home()
            self.app.container.event_generate("<Configure>", width=1000)
            self.app.update()
            error.assert_not_called()
        self.app.open_job(self.job)
        self.assertEqual(self.app.step_action, "search_batch")

    def test_invalid_website_does_not_request_key_or_call_service(self):
        self.app.vars["website"].set("inválido"); self.app.save()
        with patch("pesquisa.ui.read_key") as read_key, patch("pesquisa.ui.search") as search:
            self.app.search_one()
            read_key.assert_not_called(); search.assert_not_called()
        self.assertFalse(self.app.searching)
        self.info.assert_called()

    def test_missing_key_saving_resumes_requested_search(self):
        with patch("pesquisa.ui.read_key", side_effect=["", "dummy"]), patch("pesquisa.ui.save_key") as save_key, patch("pesquisa.ui.search", return_value=[CANDIDATE]):
            self.app.search_one()
            win = next(w for w in self.app.winfo_children() if w.winfo_class() == "Toplevel")
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            widgets = list(descendants(win))
            entry = next(w for w in widgets if w.winfo_class() == "TEntry")
            entry.insert(0, "dummy")
            next(w for w in widgets if w.winfo_class() == "TButton" and w.cget("text") == "Salvar chave e iniciar pesquisa").invoke()
            self.drain()
            save_key.assert_called_once_with("dummy")
            self.assertEqual(self.app.step_action, "candidate")

    def test_cancel_configuration_does_not_start_search(self):
        with patch("pesquisa.ui.read_key", return_value=""), patch("pesquisa.ui.search") as search:
            self.app.search_one()
            next(w for w in self.app.winfo_children() if w.winfo_class() == "Toplevel").destroy()
            self.assertFalse(self.app.searching); search.assert_not_called()

    def test_empty_results_and_failure_are_distinct_and_retryable(self):
        with patch("pesquisa.ui.read_key", return_value="dummy"), patch("pesquisa.ui.search", return_value=[]):
            self.app.search_one(); self.drain()
        self.assertEqual(self.app.current["data"]["search_state"], "Sem candidatas")
        self.assertNotEqual(self.app.current["data"]["status"], "Não encontrada")
        with patch("pesquisa.ui.read_key", return_value="dummy"), patch("pesquisa.ui.search", side_effect=SearchError("Chave inválida")):
            self.app.search_one(); self.drain()
        self.assertEqual(self.app.current["data"]["search_state"], "Falha na busca")
        self.assertIn("Chave inválida", self.app.progress.get())
        self.assertEqual(self.app.step_action, "search_one")

    def test_duplicate_queries_share_search_but_keep_separate_rows(self):
        rows = self.store.records(self.job)[:2]
        for r in rows:
            d = r["data"]; d["website"] = "example.com"; self.store.save(r["id"], d)
        self.app.load_record(rows[0]["id"])
        with patch("pesquisa.ui.read_key", return_value="dummy"), patch("pesquisa.ui.search", return_value=[CANDIDATE]) as search:
            self.app.start_search([self.store.record(r["id"]) for r in rows]); self.drain()
            self.assertEqual(search.call_count, 1)
        self.assertEqual(len(self.app.results), 2)
        self.assertFalse(any(self.store.record(r["id"])["data"]["confirmed"] for r in rows))

    def test_candidate_opens_about_with_correct_capture_context(self):
        self.app.results[self.app.current["id"]] = [CANDIDATE]
        self.app.show_candidates(); self.app.candidates.selection_set(0)
        with patch("pesquisa.ui.open_chrome") as chrome:
            self.app.open_candidate()
            chrome.assert_called_once_with(CANDIDATE["url"] + "about/")
        self.assertEqual(self.store.capture_context()["record_id"], self.app.current["id"])
        self.assertFalse(self.app.current["data"]["confirmed"])
        self.app.armed_until = time.time() - 1; self.app.update_step()
        self.assertEqual(self.app.step_button.cget("text"), "Preparar coleta e abrir Chrome")

    def test_partial_capture_requires_review_before_completion(self):
        self.app.arm()
        self.store.accept_capture(dict(**self.store.capture_context(), confirmed=True, url=CANDIDATE["url"], fields=dict(name="Fictícia")))
        capture = self.store.pending_captures()[0]
        self.app.review_capture(capture)
        self.assertEqual(self.store.record(self.app.current["id"])["data"]["name"], "")
        win = next(w for w in self.app.winfo_children() if w.winfo_class() == "Toplevel")
        frame = win.winfo_children()[0]
        bar = frame.winfo_children()[-1]
        next(w for w in bar.winfo_children() if w.cget("text") == "Aplicar campos coletados").invoke()
        self.assertEqual(self.app.current["data"]["status"], "Coleta incompleta")
        self.assertEqual(self.app.step_action, "complete")
        self.app.complete_next()
        self.assertEqual(self.app.current["data"]["status"], "Coleta incompleta")
        self.error.assert_called()

    def test_completion_exports_and_advances_and_export_failure_stays(self):
        rid = self.app.current["id"]
        self.app.vars["url"].set(CANDIDATE["url"])
        self.app.current["data"]["confirmed"] = True
        for key, value in dict(name="Fictícia", members="10", industry="Teste", size="1–10").items():
            self.app.vars[key].set(value)
        self.app.complete_next()
        self.assertEqual(self.store.record(rid)["data"]["status"], "Concluída")
        self.assertNotEqual(self.app.current["id"], rid)
        self.assertTrue((self.root / "saida.xlsx").exists())
        rid = self.app.current["id"]
        with patch("pesquisa.ui.write_output", side_effect=PermissionError("Excel aberto")):
            self.app.save_next()
        self.assertEqual(self.app.current["id"], rid)
        self.assertTrue(self.store.job(self.job)["excel_pending"] or self.error.called)

class GuidedStateTests(unittest.TestCase):
    def test_access_issue_offers_new_collection_instead_of_completion(self):
        d = empty_record("example.com")
        d.update(url=CANDIDATE["url"], confirmed=True, status="Acesso indisponível")
        self.assertEqual(next_step(d, [])[3], "collect")
