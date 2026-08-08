# -*- mode: python ; coding: utf-8 -*-
"""
LosPrice - empacotamento com PyInstaller

Gera uma pasta autocontida em dist/LosPrice/ que roda em qualquer
Windows, sem Python instalado.

    python -m PyInstaller LosPrice.spec --clean

Banco, backups e relatorios NAO ficam dentro da pasta do programa:
sao gravados ao lado do LosPrice.exe (ver database/conexao.py), para
que atualizar o sistema nao apague os dados do usuario.
"""

from PyInstaller.utils.hooks import collect_all

datas = [('assets', 'assets')]
binaries = []
hiddenimports = []

# customtkinter carrega temas por caminho de arquivo, entao precisa
# vir inteiro; reportlab traz fontes e o openpyxl seus escritores.
for pacote in ('customtkinter', 'reportlab', 'openpyxl'):
    pacote_datas, pacote_binaries, pacote_hidden = collect_all(pacote)
    datas += pacote_datas
    binaries += pacote_binaries
    hiddenimports += pacote_hidden

# As telas sao carregadas por importlib em main.py, entao o PyInstaller
# nao consegue descobri-las sozinho analisando os imports.
hiddenimports += [
    'screens.dashboard',
    'screens.ingredientes',
    'screens.embalagens',
    'screens.receitas',
    'screens.precificacao',
    'screens.simulador',
    'screens.fornecedores',
    'screens.relatorios',
    'screens.configuracoes',
]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'pytest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LosPrice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icone.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LosPrice',
)
