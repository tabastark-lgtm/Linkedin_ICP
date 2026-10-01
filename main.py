import os
import sys

def main():
    if getattr(sys, "frozen", False):
        # Caminhos relativos também funcionam em pastas Windows redirecionadas.
        os.chdir(sys._MEIPASS)
        os.environ["TCL_LIBRARY"] = "_tcl_data"
        os.environ["TK_LIBRARY"] = "_tk_data"
    if "--self-test" in sys.argv:
        from pesquisa.smoke import run
        run()
        return
    # Uma instância evita duas janelas editarem a mesma linha simultaneamente.
    import ctypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel.CreateMutexW(None, False, "Local\\PesquisaEmpresasApp")
    if ctypes.get_last_error() == 183:
        ctypes.windll.user32.MessageBoxW(None, "O aplicativo já está aberto. Procure a janela Pesquisa Empresas.", "Pesquisa Empresas", 0)
        return
    from pesquisa.ui import App
    try:
        app = App()
    except Exception as error:
        ctypes.windll.user32.MessageBoxW(None, "Não foi possível abrir o aplicativo. Seus trabalhos não foram apagados.\n\n" + str(error), "Pesquisa Empresas", 16)
        return
    app.mainloop()
    if handle:
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle(handle)

if __name__ == "__main__":
    main()
