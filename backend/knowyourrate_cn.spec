# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for KnowYourRate CN Edition."""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect litellm data files (model cost maps, etc.)
litellm_datas = collect_data_files("litellm")
litellm_hiddenimports = collect_submodules("litellm")

# Collect python-youtube submodules (pip: python-youtube, import: pyyoutube)
youtube_hiddenimports = collect_submodules("pyyoutube")

# Frontend dist directory (built before packaging)
frontend_dist = os.path.join("..", "frontend", "dist")

datas = [
    (frontend_dist, "frontend_dist"),
] + litellm_datas

a = Analysis(
    ["run_cn.py"],
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
        "app.utils.pricing_tables",
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
        "pyyoutube",
        # CN Edition specific imports
        "app.edition",
        "app.agents.creator_profile_cn",
        "app.agents.market_data_cn",
        "app.agents.report_cn",
        "app.utils.pricing_tables_cn",
        "app.utils.prompts_cn",
        "app.services.bilibili",
        "app.services.douyin",
        "app.services.kuaishou",
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
    name="KnowYourRate-CN",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)
