import copy
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from .core import FIELDS, STATUSES, domain, company_url, now
from .store import Store
from .excel import inspect_book, write_output
from .search import search, SearchError
from .workflow import next_step
from .windows import read_key, save_key, install_bridge, open_chrome

class App(tk.Tk):
    def __init__(self, store=None):
        super().__init__()
        self.title("Pesquisa Empresas — v0.1.2")
        self.geometry("1190x820")
        self.minsize(1000, 720)
        self.store = store or Store()
        self.store.setting("heartbeat", time.time())
        self.current = None
        self.job_id = None
        self.loading = False
        self.dirty = False
        self.scheduled = None
        self.results = {}
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.searching = False
        self.reviews_open = set()
        self.armed_record = None
        self.armed_until = 0
        self.search_failure = ""
        self.protocol("WM_DELETE_WINDOW", self.close)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10))
        style.configure("TButton", padding=(10, 6))
        style.configure("Primary.TButton", background="#245a80", foreground="white", font=("Segoe UI", 11, "bold"))
        style.map("Primary.TButton", background=[("active", "#194360")])
        style.configure("Title.TLabel", font=("Segoe UI", 23, "bold"), foreground="#24415b")
        style.configure("Treeview", rowheight=29)
        self.container = ttk.Frame(self, padding=20)
        self.container.pack(fill="both", expand=True)
        self.home()
        self.poll_job = self.after(500, self.poll)

    def clear(self):
        self.container.unbind("<Configure>")
        for child in self.container.winfo_children(): child.destroy()

    def header(self, title, subtitle):
        ttk.Label(self.container, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.container, text=subtitle, foreground="#607387").pack(anchor="w", pady=(4, 16))

    def home(self):
        if self.current and not self.save(): return
        self.store.cancel_capture()
        self.current = None
        self.job_id = None
        self.clear()
        self.header("Pesquisa Empresas", "Pesquise páginas, confirme a empresa e leve os dados para o Excel.")
        bar = ttk.Frame(self.container); bar.pack(fill="x", pady=(0, 18))
        for label, cmd in [("Importar Excel", self.import_dialog), ("Configuração", self.config), ("Abrir guia", self.guide)]:
            ttk.Button(bar, text=label, command=cmd).pack(side="left", padx=(0, 8))
        ttk.Label(self.container, text="Seus trabalhos", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=8)
        tree = ttk.Treeview(self.container, columns=("file", "sheet", "progress", "updated"), show="headings")
        for key, label, width in [("file", "Arquivo", 330), ("sheet", "Aba", 180), ("progress", "Concluídas", 100), ("updated", "Última alteração", 230)]:
            tree.heading(key, text=label); tree.column(key, width=width)
        tree.pack(fill="both", expand=True)
        for job in self.store.jobs():
            records = self.store.records(job["id"])
            progress = f"{sum(r['data']['status'] == 'Concluída' for r in records)} / {len(records)}"
            tree.insert("", "end", iid=job["id"], values=(job["name"], job["sheet"], progress, job["updated"].replace("T", " ")[:19]))
        def resume():
            if tree.selection(): self.open_job(tree.selection()[0])
        tree.bind("<Double-1>", lambda e: resume())
        ttk.Button(self.container, text="Continuar trabalho selecionado", command=resume).pack(anchor="e", pady=12)

    def guide(self):
        base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
        os.startfile(base / "GUIA.html")

    def config(self, on_key_saved=None):
        win = tk.Toplevel(self); win.title("Configuração inicial"); win.geometry("760x590"); win.transient(self); win.grab_set()
        frame = ttk.Frame(win, padding=22); frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="1. Serviço gratuito de pesquisa", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Abra o painel Tavily e obtenha uma chave de pesquisa.\nAs condições de uso e a cota dependem da sua conta.\nCole a chave abaixo; ela ficará no Gerenciador de Credenciais do Windows.").pack(anchor="w", pady=10)
        ttk.Button(frame, text="Abrir cadastro do Tavily", command=lambda: open_chrome("https://app.tavily.com/")).pack(anchor="w")
        key = ttk.Entry(frame, show="•", width=65); key.pack(fill="x", pady=8)
        def save_credential():
            try:
                save_key(key.get()); key.delete(0, "end")
            except Exception as e:
                messagebox.showerror("Configuração", str(e), parent=win); return
            if on_key_saved:
                win.destroy()
                on_key_saved()
            else:
                messagebox.showinfo("Configuração", "Chave salva no Windows. Volte ao trabalho e clique em Iniciar pesquisa.", parent=win)
        ttk.Button(frame, text="Salvar chave e iniciar pesquisa" if on_key_saved else "Salvar chave", command=save_credential).pack(anchor="w")
        ttk.Separator(frame).pack(fill="x", pady=16)
        ttk.Label(frame, text="2. Conectar a extensão do Chrome", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Abra o guia, carregue a pasta extension em chrome://extensions\ne cole aqui o ID da extensão (32 letras).").pack(anchor="w", pady=8)
        ttk.Label(frame, text="Depois de registrar, abra a extensão no Chrome e clique em Testar conexão.\nMantenha o aplicativo aberto. Se mover esta pasta, registre novamente.", wraplength=700).pack(anchor="w", pady=6)
        ttk.Button(frame, text="Abrir extensões do Chrome", command=lambda: open_chrome("chrome://extensions/")).pack(anchor="w", pady=4)
        extension = ttk.Entry(frame); extension.pack(fill="x")
        def register():
            try: install_bridge(extension.get().strip(), self.store.root); messagebox.showinfo("Extensão", "Registrada. Na extensão, clique em Testar conexão.", parent=win)
            except Exception as e: messagebox.showerror("Extensão", str(e), parent=win)
        buttons = ttk.Frame(frame); buttons.pack(fill="x", pady=10)
        ttk.Button(buttons, text="Registrar extensão", command=register).pack(side="left")
        ttk.Button(buttons, text="Abrir guia ilustrado", command=self.guide).pack(side="left", padx=8)

    def import_dialog(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not path: return
        try: sheets = inspect_book(path)
        except Exception as e: messagebox.showerror("Importação", str(e)); return
        win = tk.Toplevel(self); win.title("Conferir a lista"); win.geometry("950x570")
        frame = ttk.Frame(win, padding=18); frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Escolha a aba e confira todas as colunas antes de importar.").pack(anchor="w")
        selected = tk.StringVar(value=sheets[0])
        combo = ttk.Combobox(frame, textvariable=selected, values=sheets, state="readonly"); combo.pack(anchor="w", pady=10)
        tree = ttk.Treeview(frame, show="headings"); tree.pack(fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview); scroll.pack(fill="x"); tree.configure(xscrollcommand=scroll.set)
        warning = tk.StringVar(); ttk.Label(frame, textvariable=warning, wraplength=890).pack(anchor="w", pady=8)
        valid = [False]
        def preview(*_):
            valid[0] = False
            tree.delete(*tree.get_children())
            try:
                data = inspect_book(path, selected.get())
                cols = [f"c{i}" for i in range(len(data["headers"]) + 1)]
                tree.configure(columns=cols)
                for k, label in zip(cols, ["Linha", *data["headers"]]): tree.heading(k, text=str(label or "")); tree.column(k, width=180)
                for n, row in enumerate(data["rows"][1:], 2): tree.insert("", "end", values=[n, *["" if v is None else str(v) for v in row]])
                seen, warnings = {}, []
                for n, value in data["records"]:
                    try:
                        d = domain(value)
                        if d in seen: warnings.append(f"Linhas {seen[d]} e {n}: website repetido")
                        else: seen[d] = n
                    except ValueError: warnings.append(f"Linha {n}: website ausente ou inválido")
                warning.set(f"{len(data['records'])} empresas. " + ("; ".join(warnings) if warnings else "Lista válida."))
                valid[0] = True
            except Exception as e: warning.set(str(e))
        combo.bind("<<ComboboxSelected>>", preview)
        def start():
            if not valid[0]: return
            output = filedialog.asksaveasfilename(parent=win, initialfile=Path(path).stem + "_enriquecidas.xlsx", defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
            if not output: return
            try:
                job = self.store.import_job(path, selected.get(), output)
                win.destroy(); self.open_job(job); self.export()
            except Exception as e: messagebox.showerror("Importação", str(e), parent=self)
        ttk.Button(frame, text="Escolher Excel de saída e iniciar", command=start).pack(anchor="e", pady=8)
        preview()

    def open_job(self, job_id):
        if self.current and not self.save(): return
        self.store.cancel_capture()
        self.current = None
        self.job_id = job_id
        self.clear()
        job = self.store.job(job_id)
        self.header(job["name"], "Importar → pesquisar → confirmar e coletar no Chrome → revisar → salvar Excel")
        bar = ttk.Frame(self.container); bar.pack(fill="x", pady=(0, 10))
        for i, (label, cmd) in enumerate([("Seus trabalhos", self.home), ("Pesquisar empresas", self.search_batch), ("Interromper", self.stop_search), ("Configuração", self.config), ("Atualizar Excel agora", self.export), ("Exportar como", lambda:self.export(True))]):
            ttk.Button(bar, text=label, command=cmd).grid(row=i//3, column=i%3, sticky="ew", padx=(0, 5), pady=2)
        self.progress = tk.StringVar(value="Planilha carregada. Siga o Próximo passo abaixo para começar.")
        progress_label = ttk.Label(self.container, textvariable=self.progress, foreground="#45617a", wraplength=1050)
        progress_label.pack(anchor="w", pady=4)
        self.container.bind("<Configure>", lambda e: progress_label.configure(wraplength=max(200, e.width - 20)))
        guidance = ttk.LabelFrame(self.container, text="Próximo passo", padding=12)
        guidance.pack(fill="x", pady=(6, 10))
        self.step_title = tk.StringVar(); self.step_hint = tk.StringVar()
        ttk.Label(guidance, textvariable=self.step_title, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        hint_label = ttk.Label(guidance, textvariable=self.step_hint, wraplength=1050)
        hint_label.pack(anchor="w", pady=5)
        guidance.bind("<Configure>", lambda e: hint_label.configure(wraplength=max(200, e.width - 40)))
        self.step_button = ttk.Button(guidance, style="Primary.TButton", command=self.advance_step)
        self.step_button.pack(anchor="w")
        panes = ttk.Panedwindow(self.container, orient="horizontal"); panes.pack(fill="both", expand=True)
        left = ttk.Frame(panes, width=310); panel = ttk.Frame(panes, padding=(12, 0, 0, 0)); panes.add(left, weight=1); panes.add(panel, weight=3)
        self.form_canvas = tk.Canvas(panel, highlightthickness=0, background="#dcdad5")
        form_scroll = ttk.Scrollbar(panel, orient="vertical", command=self.form_canvas.yview)
        form_scroll.pack(side="right", fill="y")
        self.form_canvas.pack(side="left", fill="both", expand=True)
        self.form_canvas.configure(yscrollcommand=form_scroll.set)
        right = ttk.Frame(self.form_canvas, padding=(0, 0, 8, 12))
        window = self.form_canvas.create_window((0, 0), window=right, anchor="nw")
        right.bind("<Configure>", lambda e:self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all")))
        self.form_canvas.bind("<Configure>", lambda e:self.form_canvas.itemconfigure(window, width=e.width))
        self.filter = tk.StringVar(value="Todos")
        filterbox = ttk.Combobox(left, values=["Todos", *STATUSES], textvariable=self.filter, state="readonly"); filterbox.pack(fill="x", pady=(0, 8)); filterbox.bind("<<ComboboxSelected>>", lambda e:self.refresh_list())
        self.tree = ttk.Treeview(left, columns=("website", "status"), show="headings", selectmode="browse")
        self.tree.heading("website", text="Website / linha"); self.tree.heading("status", text="Status")
        self.tree.column("website", width=190); self.tree.column("status", width=155)
        self.tree.pack(fill="both", expand=True); self.tree.bind("<<TreeviewSelect>>", self.select_record)
        self.titlevar = tk.StringVar(); ttk.Label(right, textvariable=self.titlevar, font=("Segoe UI", 14, "bold"), wraplength=650).pack(anchor="w")
        self.originalvar = tk.StringVar(); ttk.Label(right, textvariable=self.originalvar, wraplength=650, foreground="#607387").pack(anchor="w", pady=6)
        ttk.Button(right, text="Ver demais colunas originais", command=self.original_details).pack(anchor="w")
        form = ttk.Frame(right); form.pack(fill="x", pady=8); form.columnconfigure(1, weight=1)
        self.vars = {}
        self.unavailable = {}
        for i, (key, label) in enumerate([("website", "Website de pesquisa"), ("url", "URL LinkedIn"), *FIELDS.items(), ("notes", "Observações")]):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", padx=(0, 10), pady=3)
            var = tk.StringVar(); self.vars[key] = var
            ttk.Entry(form, textvariable=var).grid(row=i, column=1, sticky="ew", pady=3)
            var.trace_add("write", lambda *a, k=key:self.changed(k))
            if key in ("members", "industry", "size"):
                missing = tk.BooleanVar(); self.unavailable[key] = missing
                ttk.Checkbutton(form, text="Não disponível", variable=missing, command=lambda:self.changed("unavailable")).grid(row=i, column=2, padx=5)
        buttons = ttk.Frame(right); buttons.pack(fill="x", pady=3)
        ttk.Button(buttons, text="Abrir página", command=self.open_url).pack(side="left")
        ttk.Button(buttons, text="Preparar coleta na extensão", command=self.arm).pack(side="left", padx=5)
        ttk.Button(buttons, text="Confirmar URL manualmente", command=self.confirm_url).pack(side="left")
        self.confirmvar = tk.StringVar(); ttk.Label(right, textvariable=self.confirmvar, wraplength=660).pack(anchor="w", pady=3)
        statebar = ttk.Frame(right); statebar.pack(fill="x", pady=6)
        ttk.Label(statebar, text="Status").pack(side="left", padx=(0, 12))
        self.statusvar = tk.StringVar(); statusbox = ttk.Combobox(statebar, textvariable=self.statusvar, values=STATUSES, state="readonly", width=24); statusbox.pack(side="left"); statusbox.bind("<<ComboboxSelected>>", lambda e:self.changed("status"))
        ttk.Button(statebar, text="Concluir", command=self.complete).pack(side="left", padx=8)
        querybar = ttk.Frame(right); querybar.pack(fill="x", pady=4)
        self.queryvar = tk.StringVar(); ttk.Entry(querybar, textvariable=self.queryvar).pack(side="left", fill="x", expand=True)
        ttk.Button(querybar, text="Pesquisar esta empresa", command=self.search_one).pack(side="left", padx=5)
        self.candidates = tk.Listbox(right, height=5, font=("Segoe UI", 10)); self.candidates.pack(fill="x")
        self.candidates.bind("<Double-1>", lambda e:self.open_candidate())
        self.snippet = tk.StringVar()
        ttk.Label(right, textvariable=self.snippet, wraplength=650, foreground="#607387").pack(anchor="w")
        self.candidates.bind("<<ListboxSelect>>", self.show_snippet)
        ttk.Button(right, text="Abrir candidata selecionada", command=self.open_candidate).pack(anchor="w", pady=4)
        footer = ttk.Frame(right); footer.pack(fill="x", pady=(8, 0))
        ttk.Button(footer, text="Anterior", command=lambda:self.navigate(-1)).pack(side="left")
        ttk.Button(footer, text="Salvar e próxima", command=self.save_next).pack(side="right")
        self.savedvar = tk.StringVar(); ttk.Label(self.container, textvariable=self.savedvar).pack(anchor="w", pady=(12, 0))
        self.refresh_list()
        records = self.store.records(job_id)
        active = next((r for r in records if r["data"]["status"] != "Concluída"), records[0])
        self.load_record(active["id"])

    def refresh_list(self):
        if not self.job_id: return
        selected = self.current["id"] if self.current else None
        self.tree.delete(*self.tree.get_children())
        for r in self.store.records(self.job_id):
            if self.filter.get() in ("Todos", r["data"]["status"]):
                self.tree.insert("", "end", iid=r["id"], values=(f"{r['row_num']}: {r['original'] or '(vazio)'}", r["data"]["status"]))
        if selected and self.tree.exists(selected): self.tree.selection_set(selected)

    def select_record(self, _=None):
        selection = self.tree.selection()
        if selection and (not self.current or selection[0] != self.current["id"]):
            if self.save(): self.load_record(selection[0])
            elif self.current and self.tree.exists(self.current["id"]): self.tree.selection_set(self.current["id"])

    def load_record(self, record_id):
        self.store.cancel_capture()
        self.current = self.store.record(record_id)
        self.loading = True
        d = self.current["data"]
        for k, v in self.vars.items(): v.set(d[k])
        for k, v in self.unavailable.items(): v.set(k in d["unavailable"])
        self.statusvar.set(d["status"])
        self.titlevar.set(d["name"] or self.current["original"] or "Website não informado")
        rows = self.store.records(self.job_id)
        index = next(i for i, r in enumerate(rows) if r["id"] == record_id)
        duplicate = []
        try:
            current_domain = domain(d["website"])
            for r in rows:
                try:
                    if r["id"] != record_id and domain(r["data"]["website"]) == current_domain: duplicate.append(str(r["row_num"]))
                except ValueError: pass
            self.queryvar.set(f'site:linkedin.com/company/ "{current_domain}"')
        except ValueError: self.queryvar.set("")
        self.originalvar.set(f"Empresa {index+1} de {len(rows)} · Linha {self.current['row_num']} · Original: {self.current['original'] or '(vazio)'}" + ("\nWebsite repetido nas linhas: " + ", ".join(duplicate) if duplicate else ""))
        self.confirmvar.set(("Página confirmada" if d["confirmed"] else "Página ainda não confirmada") + (" · Consulta: " + d["consulted_at"].replace("T", " ")[:19] if d["consulted_at"] else ""))
        self.loading = False; self.dirty = False
        if self.tree.exists(record_id): self.tree.selection_set(record_id); self.tree.see(record_id)
        self.armed_record = None
        self.show_candidates()
        self.savedvar.set("Salvo localmente" + (" · Excel aguardando atualização" if self.store.job(self.job_id)["excel_pending"] else " · Excel atualizado"))

    def original_details(self):
        if not self.current: return
        job = self.store.job(self.job_id); parsed = inspect_book(job["snapshot"], job["sheet"])
        row = parsed["rows"][self.current["row_num"] - 1]
        messagebox.showinfo("Dados originais", "\n".join(f"{h or '(sem título)'}: {v if v is not None else ''}" for h, v in zip(parsed["headers"], row)))

    def changed(self, key):
        if self.loading or not self.current: return
        self.dirty = True
        if key == "url":
            self.current["data"]["confirmed"] = False
            self.confirmvar.set("URL alterada: confirme novamente antes de concluir.")
            if self.statusvar.get() == "Concluída": self.statusvar.set("Aguardando confirmação")
        if self.scheduled: self.after_cancel(self.scheduled)
        self.savedvar.set("Alterações ainda não salvas…")
        self.scheduled = self.after(1000, lambda:self.save(quiet=True))

    def save(self, quiet=False):
        if self.scheduled: self.after_cancel(self.scheduled); self.scheduled = None
        if not self.current or not self.dirty: return True
        d = copy.deepcopy(self.current["data"])
        d.update({k:v.get() for k,v in self.vars.items()})
        d["unavailable"] = [k for k,v in self.unavailable.items() if v.get()]
        d["status"] = self.statusvar.get()
        if not d.get("consulted_at") and d["status"] in ("Concluída", "Não encontrada", "Em dúvida", "Acesso indisponível"):
            d["consulted_at"] = now()
        if d["status"] in ("Website ausente", "Website inválido"):
            try: domain(d["website"]); d["status"] = "Pendente"
            except ValueError: pass
        try:
            self.store.save(self.current["id"], d, self.current["revision"])
            self.current = self.store.record(self.current["id"])
            self.dirty = False
            self.statusvar.set(d["status"])
            self.savedvar.set("Salvo localmente · Excel aguardando atualização")
            if self.tree.exists(self.current["id"]): self.tree.set(self.current["id"], "status", d["status"])
            self.update_step()
            return True
        except Exception as e:
            self.savedvar.set("Não salvo: " + str(e))
            if not quiet: messagebox.showerror("Não foi possível salvar", str(e))
            return False

    def confirm_url(self):
        try: url = company_url(self.vars["url"].get())
        except ValueError as e: messagebox.showerror("URL", str(e)); return
        if messagebox.askyesno("Confirmar empresa", f"Você verificou que esta página corresponde à linha {self.current['row_num']}?\n\n{url}"):
            self.vars["url"].set(url)
            self.current["data"]["confirmed"] = True
            self.confirmvar.set("Página confirmada por você.")
            self.dirty = True; self.save()

    def arm(self):
        if not self.current or not self.save(): return
        self.store.arm(self.current["id"])
        self.armed_record = self.current["id"]; self.armed_until = time.time() + 900
        self.confirmvar.set("Coleta preparada por 15 minutos. No Chrome, abra Sobre e clique na extensão.")
        self.update_step()
        return True

    def update_step(self):
        if not self.current or not self.job_id: return
        title, hint, label, action = next_step(self.current["data"], self.results.get(self.current["id"], []), self.searching,
            self.armed_record == self.current["id"] and time.time() < self.armed_until)
        self.step_title.set(title); self.step_hint.set(hint); self.step_action = action
        self.step_button.configure(text=label, state="disabled" if action == "wait" else "normal")

    def advance_step(self):
        if not self.save(): return
        self.update_step()
        actions = {"search_batch": self.search_batch, "search_one": self.search_one, "candidate": self.open_candidate,
                   "collect": self.collect_current, "complete": self.complete_next, "next": self.save_next}
        if self.step_action in actions: actions[self.step_action]()

    def collect_current(self):
        try: url = company_url(self.vars["url"].get())
        except ValueError as e: messagebox.showerror("Página", str(e)); return
        if self.arm():
            open_chrome(url + "about/")
            self.progress.set("No Chrome: abra a extensão, confirme a empresa e clique em coletar. Depois volte para revisar. Instalação e teste de conexão: Configuração → Abrir guia.")

    def complete_next(self):
        if self.complete(): self.save_next()

    def open_url(self):
        try: open_chrome(company_url(self.vars["url"].get()) + "about/")
        except ValueError as e: messagebox.showerror("Página", str(e))

    def show_candidates(self):
        self.candidates.delete(0, "end")
        self.snippet.set("")
        results = self.results.get(self.current["id"], [])
        for r in results: self.candidates.insert("end", r["title"] + " — " + r["url"])
        if not results:
            state = self.current["data"]["search_state"]
            messages = {"Sem candidatas": "Busca concluída sem candidatas. Ajuste a consulta e tente novamente.",
                        "Falha na busca": "Falha na busca. Confira a conexão e a configuração; tente novamente.",
                        "Candidatas disponíveis": "Resultados da sessão anterior: pesquise novamente para exibir a lista."}
            self.candidates.insert("end", messages.get(state, "Pesquisa ainda não iniciada nesta sessão. Use o Próximo passo acima."))
        self.update_step()

    def show_snippet(self, _=None):
        items = self.results.get(self.current["id"], [])
        selected = self.candidates.curselection()
        self.snippet.set(items[selected[0]]["snippet"][:220] if selected and selected[0] < len(items) else "")

    def open_candidate(self):
        items = self.results.get(self.current["id"], [])
        selection = self.candidates.curselection()
        if not selection or selection[0] >= len(items):
            self.form_canvas.yview_moveto(1)
            self.candidates.focus_set()
            messagebox.showinfo("Escolher página", "Selecione uma candidata na lista de resultados e clique em Abrir candidata selecionada."); return
        selected = items[selection[0]]
        self.vars["url"].set(selected["url"])
        if not self.save(): return
        self.collect_current()

    def search_batch(self):
        if not self.save(): return
        rows = [r for r in self.store.records(self.job_id) if r["data"]["search_state"] == "Não executada" or (r["data"]["status"] not in ("Concluída", "Não encontrada") and r["id"] not in self.results)]
        self.start_search(rows)

    def search_one(self):
        if self.current and self.save(): self.start_search([self.current], self.queryvar.get().strip())

    def start_search(self, records, override=None):
        if self.searching: messagebox.showinfo("Pesquisa", "Há uma pesquisa em andamento."); return
        jobs = []
        for r in records:
            try: d = domain(r["data"]["website"])
            except ValueError: continue
            jobs.append((r["id"], override or f'site:linkedin.com/company/ "{d}"'))
        if not jobs: messagebox.showinfo("Pesquisa", "Não há websites válidos para pesquisar."); return
        try: key = read_key()
        except Exception as e: messagebox.showerror("Chave", str(e)); return
        if not key:
            job_id = self.job_id
            ids = [r["id"] for r in records]
            def resume_search():
                if self.job_id == job_id and self.save():
                    self.start_search([self.store.record(rid) for rid in ids], override)
            self.progress.set("Para pesquisar, configure a chave Tavily. Ao salvar, a pesquisa será iniciada.")
            self.config(on_key_saved=resume_search); return
        self.searching = True; self.stop.clear(); self.search_failure = ""
        self.progress.set(f"Pesquisando 1 de {len(jobs)} empresas… Aguarde a resposta do serviço.")
        self.update_step()
        def worker():
            cache = {}
            for i, (rid, query) in enumerate(jobs, 1):
                if self.stop.is_set(): break
                try:
                    if query not in cache:
                        self.store.setting("search_count", (self.store.setting("search_count") or 0) + 1)
                        cache[query] = search(key, query)
                    self.events.put(("search", rid, cache[query], f"Pesquisa {i} de {len(jobs)}"))
                except SearchError as e:
                    self.events.put(("search_error", rid, str(e))); break
                except Exception:
                    self.events.put(("search_error", rid, "Erro local ao executar a pesquisa.")); break
            self.events.put(("done", len(jobs)))
        threading.Thread(target=worker, daemon=True).start()

    def stop_search(self):
        self.stop.set()
        if self.job_id: self.progress.set("Interrompendo após a consulta em andamento…")

    def complete(self):
        self.statusvar.set("Concluída"); self.dirty = True
        if not self.save():
            self.statusvar.set(self.current["data"]["status"])
            self.dirty = True
            return False
        return True

    def navigate(self, offset):
        if not self.current or not self.save(): return
        records = self.store.records(self.job_id)
        index = next(i for i,r in enumerate(records) if r["id"] == self.current["id"])
        self.load_record(records[max(0, min(len(records)-1, index+offset))]["id"])

    def save_next(self):
        if not self.save() or not self.export(): return
        records = self.store.records(self.job_id)
        index = next(i for i, r in enumerate(records) if r["id"] == self.current["id"])
        if index + 1 < len(records): self.navigate(1)
        else:
            pending = next((r for r in records if r["data"]["status"] not in ("Concluída", "Não encontrada")), None)
            if pending and pending["id"] != self.current["id"]: self.load_record(pending["id"])
            self.progress.set("Excel atualizado. " + ("Ainda há empresas para revisar." if pending else "Você chegou ao fim da lista."))

    def export(self, choose=False):
        if not self.job_id or not self.save(): return False
        job = self.store.job(self.job_id); target = job["output"]
        if choose:
            target = filedialog.asksaveasfilename(initialfile=Path(target).name, defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
            if not target: return False
        try:
            write_output(job, self.store.records(self.job_id), target, self.store.protected_paths())
            self.store.output_saved(self.job_id, target)
            self.savedvar.set("Salvo · Excel atualizado: " + target)
            self.update_step()
            return True
        except Exception as e:
            self.savedvar.set("Salvo localmente · Excel aguardando atualização")
            messagebox.showerror("Excel aguardando atualização", "Se o arquivo estiver aberto no Excel, feche-o e tente novamente.\nSeu preenchimento continua salvo no aplicativo.\n\n" + str(e))
            return False

    def review_capture(self, capture):
        self.reviews_open.add(capture["token"])
        record = self.store.record(capture["record_id"])
        payload = json.loads(capture["payload"])
        win = tk.Toplevel(self); win.title("Revisar coleta recebida"); win.geometry("780x430")
        frame = ttk.Frame(win, padding=20); frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=f"Linha {record['row_num']} · {record['original']}", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(frame, text=payload["url"], wraplength=730).pack(anchor="w", pady=8)
        table = ttk.Treeview(frame, columns=("field", "old", "new"), show="headings", height=4)
        for key, label in [("field", "Campo"), ("old", "Valor atual"), ("new", "Valor coletado")]: table.heading(key, text=label); table.column(key, width=230)
        for k, label in FIELDS.items(): table.insert("", "end", values=(label, record["data"][k], payload["fields"][k] or "Não identificado"))
        table.pack(fill="x", pady=8)
        ttk.Label(frame, text=payload["error"] or "Confira os valores antes de aplicar.", wraplength=730).pack(anchor="w")
        ttk.Label(frame, text="Campos não identificados ficam vazios. Aplicar substitui os quatro campos mostrados acima.", wraplength=730).pack(anchor="w", pady=8)
        def close():
            self.store.finish_capture(capture["token"]); self.reviews_open.discard(capture["token"]); win.destroy()
        def apply():
            if self.current and not self.save(): return
            latest = self.store.record(record["id"])
            if latest["revision"] != capture["revision"]:
                messagebox.showerror("Coleta antiga", "A linha mudou após a coleta. Descarte esta coleta e prepare uma nova.", parent=win); return
            d = copy.deepcopy(latest["data"])
            d.update(payload["fields"]); d.update(url=payload["url"], confirmed=True, consulted_at=payload["consulted_at"], unavailable=[])
            d["status"] = "Aguardando revisão" if all(payload["fields"].values()) else "Coleta incompleta"
            if payload.get("access_issue"): d["status"] = "Acesso indisponível"
            self.store.save(record["id"], d, latest["revision"])
            close()
            if self.job_id == record["job_id"]:
                self.refresh_list()
                if self.current and self.current["id"] == record["id"]: self.load_record(record["id"])
        bar = ttk.Frame(frame); bar.pack(fill="x", pady=12)
        ttk.Button(bar, text="Aplicar campos coletados", command=apply).pack(side="right")
        ttk.Button(bar, text="Descartar coleta", command=close).pack(side="right", padx=8)
        win.protocol("WM_DELETE_WINDOW", close)

    def poll(self):
        try:
            self.store.setting("heartbeat", time.time())
            while not self.events.empty():
                event = self.events.get_nowait()
                if event[0] == "done":
                    self.searching = False
                    if self.job_id:
                        self.progress.set(self.search_failure or ("Pesquisa interrompida por você. Os resultados recebidos foram preservados." if self.stop.is_set() else "Pesquisa encerrada. Selecione uma empresa e siga o Próximo passo para abrir uma candidata."))
                        self.update_step()
                    continue
                rid = event[1]
                if self.current and self.current["id"] == rid and not self.save(quiet=True):
                    self.events.put(event); break
                r = self.store.record(rid); d = r["data"]
                if event[0] == "search":
                    self.results[rid] = event[2]
                    d["search_state"] = "Candidatas disponíveis" if event[2] else "Sem candidatas"
                    d["searched_at"] = now()
                    if d["status"] in ("Pendente", "Em pesquisa", "Aguardando confirmação"):
                        d["status"] = "Aguardando confirmação" if event[2] else "Em pesquisa"
                else:
                    self.results.pop(rid, None)
                    d["search_state"] = "Falha na busca"
                    self.search_failure = "Pesquisa interrompida: " + event[2]
                    if self.job_id: self.progress.set(self.search_failure)
                    messagebox.showerror("Pesquisa interrompida", event[2])
                self.store.save(rid, d, r["revision"])
                if self.current and self.current["id"] == rid:
                    self.current = self.store.record(rid); self.statusvar.set(d["status"]); self.show_candidates()
                if self.job_id == r["job_id"]:
                    if self.tree.exists(rid): self.tree.set(rid, "status", d["status"])
                    if event[0] == "search": self.progress.set(event[3] + f" · {len(event[2])} candidata(s) para a linha {r['row_num']}.")
            if self.job_id: self.update_step()
            for capture in self.store.pending_captures():
                if capture["token"] not in self.reviews_open: self.review_capture(capture)
        except Exception as e:
            if self.job_id: self.savedvar.set("Atenção: " + str(e))
        self.poll_job = self.after(700, self.poll)

    def close(self):
        if not self.save(): return
        self.after_cancel(self.poll_job)
        self.stop.set(); self.store.cancel_capture(); self.store.setting("heartbeat", 0)
        self.destroy()
