Option Explicit
Dim shell, fs, folder, shortcut
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
folder = fs.GetParentFolderName(WScript.ScriptFullName)
If Not fs.FileExists(folder & "\PesquisaEmpresas.exe") Then
  MsgBox "Extraia todo o pacote Windows antes de criar o atalho.", 48, "Pesquisa Empresas"
  WScript.Quit 1
End If
Set shortcut = shell.CreateShortcut(shell.SpecialFolders("Desktop") & "\Pesquisa Empresas.lnk")
shortcut.TargetPath = folder & "\PesquisaEmpresas.exe"
shortcut.WorkingDirectory = folder
shortcut.Description = "Pesquisar e enriquecer empresas"
shortcut.Save
MsgBox "Atalho criado na Área de Trabalho.", 64, "Pesquisa Empresas"
