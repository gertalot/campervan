"""Development-only CAD change notifications; no initial regeneration."""

import asyncio
from pathlib import Path

from campervan.coordinator import Coordinator


async def watch_cad(directory: Path, coordinator: Coordinator, stop_event: asyncio.Event) -> None:
    # Production installations do not need the development-only watchfiles package.
    from watchfiles import awatch

    directory = directory.resolve()
    async for changes in awatch(directory, debounce=250, stop_event=stop_event):
        if stop_event.is_set():
            return
        if any(Path(path).suffix == ".py" and Path(path).resolve().is_relative_to(directory) for _, path in changes):
            await coordinator.accept()
