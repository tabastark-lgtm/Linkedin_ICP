import json
import struct
import sys
from .store import Store

MAX_MESSAGE = 64000

def read_exact(stream, size):
    chunks = bytearray()
    while len(chunks) < size:
        part = stream.read(size - len(chunks))
        if not part:
            raise EOFError()
        chunks.extend(part)
    return bytes(chunks)

def read_message(stream):
    length = struct.unpack("<I", read_exact(stream, 4))[0]
    if length > MAX_MESSAGE:
        raise ValueError("Mensagem excessiva.")
    message = json.loads(read_exact(stream, length))
    if not isinstance(message, dict):
        raise ValueError("Mensagem inválida.")
    return message

def write_message(stream, data):
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    stream.write(struct.pack("<I", len(raw)) + raw)
    stream.flush()

def handle(store, message):
    if message.get("action") == "context":
        return {"ok": True, "context": store.capture_context()}
    if message.get("action") == "capture":
        return store.accept_capture(message)
    if message.get("action") == "ping":
        store.setting("last_bridge_ping", __import__("time").time())
        return {"ok": True, "message": "Extensão conectada ao aplicativo."}
    raise ValueError("Comando desconhecido.")

def main():
    import os
    if os.name == "nt":
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    store = Store()
    while True:
        try:
            message = read_message(sys.stdin.buffer)
        except EOFError:
            break
        except (ValueError, struct.error):
            write_message(sys.stdout.buffer, {"ok": False, "error": "Mensagem inválida."})
            break
        try:
            result = handle(store, message)
        except (ValueError, OSError) as error:
            result = {"ok": False, "error": str(error)}
        except Exception:
            result = {"ok": False, "error": "Não foi possível salvar a coleta. Abra o aplicativo e tente novamente."}
        write_message(sys.stdout.buffer, result)
