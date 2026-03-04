# Sistema de Chamados Local

Sistema desktop local, sem web, com duas interfaces:

- `Chamados Usuario`: abertura e acompanhamento de chamados pela maquina do colaborador.
- `Chamados TI`: fila geral para atendimento e atualizacao de status.

## Arquitetura

- Aplicacao: Python + `tkinter` (GUI nativa Windows).
- Banco: SQLite (arquivo unico), com suporte a acesso concorrente via `WAL`.
- Multiusuario por maquina: cada estacao instala seu executavel e aponta para o mesmo banco compartilhado.

## Requisitos

- Windows 10/11
- Python 3.11+ (para executar via codigo-fonte)
- Opcional para build: Inno Setup 6

## Configuracao do banco

1. Copie `config.example.json` para `config.json`.
2. Defina `database_path` com um caminho compartilhado usado por todos, por exemplo:
   - `S:\\Comum\\TI\\Agents\\chamados.db`
   - `\\\\SERVIDOR\\Chamados\\chamados.db`

Tambem e possivel sobrescrever via variavel de ambiente:

- `CHAMADOS_DB_PATH=\\\\SERVIDOR\\Chamados\\chamados.db`

## Atualizacao automatica (Usuario)

O app `Chamados Usuario` pode detectar versao nova e perguntar se deseja atualizar.

No `config.json`, configure:

- `update_manifest_path`: caminho para o manifesto JSON de atualizacao.
- `update_check_interval_seconds`: intervalo de checagem (minimo 60 segundos).

Exemplo de manifesto: `update_manifest.example.json`

Campos do manifesto:

- `latest_version`: versao mais nova disponivel.
- `installer_path`: caminho para `ChamadosUsuarioSetup.exe`.
- `notes`: texto opcional mostrado no aviso de atualizacao.

Variaveis de ambiente opcionais:

- `CHAMADOS_UPDATE_MANIFEST`
- `CHAMADOS_UPDATE_INTERVAL`

## Instalador do Usuario sem admin

O instalador do `Chamados Usuario` foi configurado para instalacao por usuario (`AppData`),
com inicio automatico no Windows.

O app de Usuario permite apenas uma instancia por maquina.

Na primeira instalacao em uma maquina limpa, nao deve pedir senha de administrador.

## Execucao local

```powershell
python -m pip install -r requirements.txt
python run_usuario.py
python run_ti.py
```

## Build de executaveis

```powershell
.\scripts\build_usuario.ps1
.\scripts\build_ti.ps1
```

Saida esperada:

- `dist\ChamadosUsuario\ChamadosUsuario.exe`
- `dist\ChamadosTI\ChamadosTI.exe`

## Instaladores por maquina

```powershell
.\scripts\create_installers.ps1
```

Observacao: a versao do instalador de Usuario e lida automaticamente de
`src\chamados\version.py` durante a geracao.

Saida esperada:

- `dist_installers\ChamadosUsuarioSetup.exe`
- `dist_installers\ChamadosTISetup.exe`

## Fluxo de uso

1. Usuario abre chamado no app `Chamados Usuario`.
2. Time TI enxerga e trata no app `Chamados TI`.
3. Status possiveis:
   - `ABERTO`
   - `EM_ATENDIMENTO`
   - `AGUARDANDO_USUARIO`
   - `RESOLVIDO`
   - `CANCELADO`
