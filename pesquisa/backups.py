"""Cópias consistentes locais; nunca incluem a chave do Windows."""
import json
import os
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime
from pathlib import Path


def create_backup(root, migration=False):
    root = Path(root)
    folder = root / "backups"
    folder.mkdir(exist_ok=True)
    stamp = datetime.now()
    daily = folder / (stamp.strftime("%Y-%m-%d") + "-diario.zip")
    if not migration and daily.exists():
        return daily
    target = folder / (stamp.strftime("%Y-%m-%d-%H%M%S-%f") + "-migracao.zip") if migration else daily
    with tempfile.TemporaryDirectory(prefix=".backup-", dir=folder) as temporary:
        temporary = Path(temporary)
        database = temporary / "trabalhos.sqlite"
        with closing(sqlite3.connect(root / "trabalhos.sqlite")) as source:
            with closing(sqlite3.connect(database)) as destination:
                source.backup(destination)
        archive = temporary / "copia.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as out:
            out.write(database, "trabalhos.sqlite")
            with closing(sqlite3.connect(database)) as db:
                entries = list(db.execute("SELECT id,snapshot FROM jobs"))
            for job_id, snapshot in entries:
                out.write(snapshot, "entradas/" + job_id + ".xlsx")
            out.writestr("backup.json", json.dumps({"created_at": stamp.isoformat(timespec="seconds"), "original_root": str(root), "migration": migration}))
        os.replace(archive, target)
    for old in sorted(folder.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)[7:]:
        old.unlink()
    return target


def last_backup(root):
    copies = list((Path(root) / "backups").glob("*.zip"))
    if not copies:
        return "Ainda não criado"
    return datetime.fromtimestamp(max(p.stat().st_mtime for p in copies)).strftime("%d/%m/%Y %H:%M")
