import json
import os
import secrets
import shutil
import sqlite3
import time
import uuid
from contextlib import contextmanager, closing
from pathlib import Path
from .core import empty_record, validate_record, company_url, now, FIELDS, domain
from .backups import create_backup
from .excel import inspect_book

def data_dir():
    return Path(os.environ.get("PESQUISA_DATA_DIR", str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "PesquisaEmpresas")))

class Store:
    def __init__(self, root=None):
        self.root = Path(root) if root else data_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.backup_error = ""
        database = self.root / "trabalhos.sqlite"
        if database.exists():
            with closing(sqlite3.connect(database)) as connection:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version < 2:
                # Migração só prossegue com uma cópia completa e verificável.
                create_backup(self.root, migration=True)
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, name TEXT, source TEXT, snapshot TEXT, sheet TEXT, output TEXT, updated TEXT, excel_pending INTEGER DEFAULT 1);
            CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, job_id TEXT, row_num INTEGER, original TEXT, data TEXT, revision INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS captures(token TEXT PRIMARY KEY, record_id TEXT, revision INTEGER, expires REAL, state TEXT, payload TEXT);
            CREATE TABLE IF NOT EXISTS searches(record_id TEXT PRIMARY KEY, query TEXT, generation INTEGER DEFAULT 0, state TEXT, candidates TEXT, searched_at TEXT, error TEXT);
            CREATE TABLE IF NOT EXISTS search_cache(job_id TEXT, query TEXT, candidates TEXT, searched_at TEXT, PRIMARY KEY(job_id,query));
            PRAGMA user_version=2;
            ''')

    def before_change(self):
        try:
            create_backup(self.root)
            self.backup_error = ""
        except Exception as error:
            self.backup_error = "Backup não realizado: " + str(error)

    @staticmethod
    def default_query(website):
        try:
            return f'site:linkedin.com/company/ "{domain(website)}"'
        except ValueError:
            return ""

    def search_info(self, record_id):
        with self.db() as db:
            row = db.execute("SELECT * FROM searches WHERE record_id=?", (record_id,)).fetchone()
        if row:
            result = dict(row)
            result["candidates"] = json.loads(result["candidates"])
            return result
        record = self.record(record_id)
        # Versões antigas não guardavam candidatas. Exigem refazer explicitamente.
        state = record["data"].get("search_state", "Não executada")
        return dict(record_id=record_id, query=self.default_query(record["data"]["website"]), generation=0,
                    state=state, candidates=[], searched_at=record["data"].get("searched_at", ""), error="")

    def set_query(self, record_id, query):
        query = query.strip()
        info = self.search_info(record_id)
        if info["query"] == query:
            return
        self.before_change()
        with self.db() as db:
            self._invalidate_search(db, record_id, query)

    def _invalidate_search(self, db, record_id, query):
        row = db.execute("SELECT generation FROM searches WHERE record_id=?", (record_id,)).fetchone()
        generation = row[0] + 1 if row else 1
        db.execute("INSERT OR REPLACE INTO searches VALUES (?,?,?,'Não executada','[]','','')", (record_id, query, generation))
        record = self.decode(db.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone())
        data = record["data"]
        data.update(search_state="Não executada", searched_at="")
        db.execute("UPDATE records SET data=?,revision=revision+1 WHERE id=?", (json.dumps(data, ensure_ascii=False), record_id))

    def begin_search(self, record_id):
        self.before_change()
        info = self.search_info(record_id)
        generation = info["generation"] + 1
        with self.db() as db:
            db.execute("INSERT OR REPLACE INTO searches VALUES (?,?,?,?,?,?,?)", (record_id, info["query"], generation, info["state"], json.dumps(info["candidates"]), info["searched_at"], ""))
        return (record_id, info["query"], generation)

    def cached_search(self, job_id, query):
        with self.db() as db:
            row = db.execute("SELECT candidates,searched_at FROM search_cache WHERE job_id=? AND query=?", (job_id, query)).fetchone()
        return (json.loads(row[0]), row[1]) if row else None

    def finish_search(self, request, candidates, searched_at, error=""):
        record_id, query, generation = request
        self.before_change()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            active = db.execute("SELECT query,generation FROM searches WHERE record_id=?", (record_id,)).fetchone()
            if not active or tuple(active) != (query, generation):
                return False
            record = self.decode(db.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone())
            state = "Falha na busca" if error else ("Candidatas disponíveis" if candidates else "Sem candidatas")
            db.execute("UPDATE searches SET state=?,candidates=?,searched_at=?,error=? WHERE record_id=?", (state, json.dumps(candidates), searched_at, error, record_id))
            if not error:
                db.execute("INSERT OR REPLACE INTO search_cache VALUES (?,?,?,?)", (record["job_id"], query, json.dumps(candidates), searched_at))
            data = record["data"]
            data.update(search_state=state, searched_at=searched_at)
            if data["status"] in ("Pendente", "Em pesquisa", "Aguardando confirmação") and not error:
                data["status"] = "Aguardando confirmação" if candidates else "Em pesquisa"
            db.execute("UPDATE records SET data=?,revision=revision+1 WHERE id=?", (json.dumps(data, ensure_ascii=False), record_id))
            db.execute("UPDATE jobs SET updated=?,excel_pending=1 WHERE id=?", (now(), record["job_id"]))
        return True

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.root / "trabalhos.sqlite", timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def setting(self, key, value=None):
        with self.db() as db:
            if value is not None:
                db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, json.dumps(value)))
                return value
            row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else None

    def import_job(self, source, sheet, output):
        parsed = inspect_book(source, sheet)
        from .excel import same_path
        if same_path(source, output) or any(same_path(output, p) for p in self.protected_paths()):
            raise ValueError("Escolha um destino diferente de todas as entradas.")
        job_id = uuid.uuid4().hex
        self.before_change()
        folder = self.root / "entradas"
        folder.mkdir(exist_ok=True)
        snapshot = folder / (job_id + ".xlsx")
        shutil.copy2(source, snapshot)
        try:
            with self.db() as db:
                db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,1)", (job_id, Path(source).name, str(Path(source).resolve()), str(snapshot), sheet, str(Path(output).resolve()), now()))
                for row_num, website in parsed["records"]:
                    db.execute("INSERT INTO records VALUES (?,?,?,?,?,0)", (uuid.uuid4().hex, job_id, row_num, str(website or ""), json.dumps(empty_record(website), ensure_ascii=False)))
        except Exception:
            snapshot.unlink(missing_ok=True)
            raise
        return job_id

    def jobs(self):
        with self.db() as db:
            return [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY updated DESC")]

    def job(self, job_id):
        with self.db() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                raise ValueError("Trabalho não encontrado.")
            return dict(row)

    def protected_paths(self):
        return [j[k] for j in self.jobs() for k in ("source", "snapshot")]

    @staticmethod
    def decode(row):
        if not row:
            raise ValueError("Linha não encontrada.")
        result = dict(row)
        result["data"] = json.loads(result["data"])
        return result

    def records(self, job_id):
        with self.db() as db:
            return [self.decode(r) for r in db.execute("SELECT * FROM records WHERE job_id=? ORDER BY row_num", (job_id,))]

    def record(self, record_id):
        with self.db() as db:
            return self.decode(db.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone())

    def save(self, record_id, data, revision=None):
        validate_record(data)
        self.before_change()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            old = self.decode(db.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone())
            if revision is not None and old["revision"] != revision:
                raise ValueError("A linha mudou. Reabra a empresa antes de salvar.")
            db.execute("UPDATE records SET data=?, revision=revision+1 WHERE id=?", (json.dumps(data, ensure_ascii=False), record_id))
            db.execute("UPDATE jobs SET updated=?, excel_pending=1 WHERE id=?", (now(), old["job_id"]))
            if old["data"]["website"] != data["website"]:
                self._invalidate_search(db, record_id, self.default_query(data["website"]))

    def output_saved(self, job_id, path):
        with self.db() as db:
            db.execute("UPDATE jobs SET output=?, excel_pending=0 WHERE id=?", (str(path), job_id))

    def mark_output_pending(self, job_id):
        with self.db() as db:
            db.execute("UPDATE jobs SET excel_pending=1 WHERE id=?", (job_id,))

    def arm(self, record_id):
        self.before_change()
        token = secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            record = self.decode(db.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone())
            db.execute("UPDATE captures SET state='cancelled' WHERE state='armed'")
            db.execute("INSERT INTO captures VALUES (?,?,?,?,?,NULL)", (token, record_id, record["revision"], time.time() + 900, "armed"))
        return token

    def cancel_capture(self):
        with self.db() as db:
            db.execute("UPDATE captures SET state='cancelled' WHERE state='armed'")

    def capture_context(self):
        if time.time() - (self.setting("heartbeat") or 0) > 12:
            raise ValueError("Abra o aplicativo e selecione Preparar coleta.")
        with self.db() as db:
            c = db.execute("SELECT * FROM captures WHERE state='armed' AND expires>? ORDER BY expires DESC LIMIT 1", (time.time(),)).fetchone()
            if not c:
                raise ValueError("No aplicativo, selecione a empresa e clique em Preparar coleta.")
            r = self.decode(db.execute("SELECT * FROM records WHERE id=?", (c["record_id"],)).fetchone())
            return dict(token=c["token"], record_id=r["id"], job_id=r["job_id"], row_num=r["row_num"], website=r["original"], name=r["data"]["name"])

    def accept_capture(self, message):
        self.before_change()
        if time.time() - (self.setting("heartbeat") or 0) > 12:
            raise ValueError("O aplicativo não está aberto.")
        url = company_url(message.get("url", ""))
        if message.get("confirmed") is not True:
            raise ValueError("Confirme a empresa antes de coletar.")
        fields = message.get("fields", {})
        if not isinstance(fields, dict) or any(not isinstance(fields.get(k, ""), str) or len(fields.get(k, "")) > 2000 for k in FIELDS):
            raise ValueError("Dados de coleta inválidos.")
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            capture = db.execute("SELECT * FROM captures WHERE token=?", (message.get("token"),)).fetchone()
            if not capture or capture["state"] != "armed" or capture["expires"] < time.time():
                raise ValueError("Coleta expirada ou já utilizada. Prepare outra no aplicativo.")
            record = self.decode(db.execute("SELECT * FROM records WHERE id=?", (capture["record_id"],)).fetchone())
            if message.get("record_id") != record["id"] or message.get("job_id") != record["job_id"] or record["revision"] != capture["revision"]:
                raise ValueError("A linha foi alterada. Prepare uma nova coleta.")
            payload = dict(url=url, fields={k: fields.get(k, "").strip() for k in FIELDS}, consulted_at=now(), error=str(message.get("error", ""))[:500], access_issue=message.get("access_issue") is True)
            db.execute("UPDATE captures SET state='received', payload=? WHERE token=?", (json.dumps(payload, ensure_ascii=False), capture["token"]))
        return {"ok": True, "message": "Coleta enviada. Revise os campos no aplicativo."}

    def pending_captures(self):
        with self.db() as db:
            return [dict(r) for r in db.execute("SELECT * FROM captures WHERE state='received'")]

    def finish_capture(self, token):
        with self.db() as db:
            db.execute("UPDATE captures SET state='reviewed',payload=NULL WHERE token=?", (token,))
