import json
import aiofiles
import asyncio
from pathlib import Path
from typing import Any, Optional

_lock = asyncio.Lock()

async def safe_load_json(path: Path, default: Optional[Any] = None) -> Any:
    if not path.exists():
        return default or {}
    try:
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            text = await f.read()
            if not text.strip():
                return default or {}
            return json.loads(text)
    except (json.JSONDecodeError, FileNotFoundError):
        return default or {}
    except Exception:
        return default or {}

async def safe_save_json(path: Path, data: Any) -> None:
    async with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
