"""Execute com Python Windows que tenha Tcl/Tk, openpyxl e PyInstaller."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    os.chdir(ROOT)
    dist = Path(os.environ.get("PESQUISA_DIST", str(ROOT / "dist"))).resolve()
    build = Path(os.environ.get("PESQUISA_BUILD", str(ROOT / "build"))).resolve()
    tcl = Path(os.environ.get("PESQUISA_TCL", str(Path(sys.base_prefix) / "tcl"))).resolve()
    # Tcl desta instalação precisa de caminhos relativos também durante a análise.
    os.environ["TCL_LIBRARY"] = os.path.relpath(tcl / "tcl8.6", ROOT).replace("\\", "/")
    os.environ["TK_LIBRARY"] = os.path.relpath(tcl / "tk8.6", ROOT).replace("\\", "/")
    package = dist / "PesquisaEmpresas"
    os.environ.setdefault("PYINSTALLER_CONFIG_DIR", str(build / "cache"))
    common = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(dist), "--workpath", str(build), "--specpath", str(build), "--exclude-module", "numpy", "--exclude-module", "pandas", "--exclude-module", "matplotlib", "--exclude-module", "scipy", "--exclude-module", "IPython", "--exclude-module", "PIL"]
    subprocess.run([*common, "--name", "PesquisaEmpresas", "--windowed", "--onedir", "--add-data", str(tcl / "tcl8.6") + os.pathsep + "_tcl_data", "--add-data", str(tcl / "tk8.6") + os.pathsep + "_tk_data", "main.py"], check=True)
    subprocess.run([*common, "--name", "PesquisaBridge", "--console", "--onedir", "bridge.py"], check=True)
    # O bridge usa os mesmos arquivos do runtime e acrescenta apenas dependências faltantes.
    bridge = dist / "PesquisaBridge"
    shutil.copy2(bridge / "PesquisaBridge.exe", package)
    for source in (bridge / "_internal").rglob("*"):
        target = package / "_internal" / source.relative_to(bridge / "_internal")
        if source.is_file() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for directory in ("extension", "examples"):
        shutil.copytree(ROOT / directory, package / directory, dirs_exist_ok=True)
    for name in ("GUIA.html", "README.md", "PRD.md", "STATUS.md", "Criar atalho.vbs"):
        shutil.copy2(ROOT / name, package / name)
    shutil.make_archive(str(dist / "PesquisaEmpresas-v0.1.2-Windows"), "zip", dist, "PesquisaEmpresas")
    print("Pacote criado:", package)

if __name__ == "__main__": main()
