# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for KnowYourRate."""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect litellm data files (model cost maps, etc.)
litellm_datas = collect_data_files("litellm")
litellm_hiddenimports = collect_submodules("litellm")

# Collect python-youtube submodules (import name is "youtube")
youtube_hiddenimports = collect_submodules("youtube")

# Frontend dist directory (built before packaging)
frontend_dist = os.path.join("..", "frontend", "dist")

datas = [
    (frontend_dist, "frontend_dist"),
] + litellm_datas

a = Analysis(
    ["run.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "aiosqlite",
        "sqlalchemy.dialects.sqlite",
        "sqlalchemy.dialects.sqlite.aiosqlite",
        "app",
        "app.main",
        "app.config",
        "app.database",
        "app.api",
        "app.api.router",
        "app.api.deps",
        "app.api.routes.health",
        "app.api.routes.settings",
        "app.api.routes.creators",
        "app.api.routes.analysis",
        "app.api.routes.reports",
        "app.agents",
        "app.agents.base",
        "app.agents.orchestrator",
        "app.agents.market_data",
        "app.agents.creator_profile",
        "app.agents.brand_strategy",
        "app.agents.debate",
        "app.agents.report",
        "app.llm",
        "app.llm.provider",
        "app.llm.registry",
        "app.models",
        "app.models.settings",
        "app.models.creator",
        "app.models.analysis_run",
        "app.models.report",
        "app.schemas",
        "app.schemas.settings",
        "app.schemas.creator",
        "app.schemas.analysis",
        "app.schemas.report",
        "app.services",
        "app.services.encryption",
        "app.services.youtube",
        "app.services.tiktok",
        "app.utils",
        "app.utils.prompts",
        "youtube",
    ] + litellm_hiddenimports + youtube_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="KnowYourRate",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)
