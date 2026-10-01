"""Credencial genérica no Windows; nenhuma senha/cookie do LinkedIn é lida."""
import ctypes
import json
import os
import re
import sys
import webbrowser
from pathlib import Path
from ctypes import wintypes

TARGET = "PesquisaEmpresas/Tavily"
HOST = "br.com.pesquisaempresas.bridge"

class CREDENTIAL(ctypes.Structure):
    _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]

def credential_api():
    api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    api.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
    api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
    api.CredFree.argtypes = [ctypes.c_void_p]
    return api

def save_key(key):
    if not key.strip() or len(key) > 1000:
        raise ValueError("Informe uma chave válida.")
    raw = key.strip().encode("utf-16-le")
    buf = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    cred = CREDENTIAL(Type=1, TargetName=TARGET, CredentialBlobSize=len(raw), CredentialBlob=buf, Persist=2, UserName="Tavily")
    if not credential_api().CredWriteW(ctypes.byref(cred), 0):
        raise ctypes.WinError(ctypes.get_last_error())

def read_key():
    api = credential_api()
    ptr = ctypes.POINTER(CREDENTIAL)()
    if not api.CredReadW(TARGET, 1, 0, ctypes.byref(ptr)):
        if ctypes.get_last_error() == 1168:
            return ""
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(ptr.contents.CredentialBlob, ptr.contents.CredentialBlobSize).decode("utf-16-le")
    finally:
        api.CredFree(ptr)

def install_bridge(extension_id, root):
    import winreg
    if not re.fullmatch(r"[a-p]{32}", extension_id):
        raise ValueError("Cole o ID de 32 letras exibido em chrome://extensions.")
    executable = Path(sys.executable).parent / "PesquisaBridge.exe"
    if not getattr(sys, "frozen", False) or not executable.exists():
        raise ValueError("Abra o executável empacotado para registrar a extensão.")
    manifest = Path(root) / "native-host.json"
    manifest.write_text(json.dumps(dict(name=HOST, description="Pesquisa Empresas: coleta confirmada", path=str(executable), type="stdio", allowed_origins=[f"chrome-extension://{extension_id}/"]), indent=2), encoding="utf-8")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Google\\Chrome\\NativeMessagingHosts\\" + HOST) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest))

def file_locked(path):
    """Distingue bloqueio de compartilhamento de falta de permissão no destino."""
    if os.name != "nt" or not Path(path).exists():
        return False
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    # Solicita somente um handle com permissão de substituição; não altera o arquivo.
    handle = kernel.CreateFileW(str(path), 0x10000, 7, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        return ctypes.get_last_error() in (32, 33)
    kernel.CloseHandle(handle)
    return False


def open_chrome(url):
    import subprocess
    candidates = [Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe", Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Google/Chrome/Application/chrome.exe", Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe"]
    for exe in candidates:
        if exe.exists():
            subprocess.Popen([str(exe), url])
            return
    webbrowser.open(url)
