"""Write a data file whole, waiting if it is held.

On Windows the dev server's watcher can hold a file for a moment as it reads it, and opening it for writing then fails
with OSError 22 (it stopped a full rebuild on 2026-11-04). The text goes to a file beside it, which replaces it in one
step, so a reader never sees half a file and a failed write leaves the old one whole.
"""
import os
import time
from pathlib import Path


def write_text(path, text: str, tries: int = 8, wait: float = 5) -> None:
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    # text read with its line ends kept (newline='') is written as it is: translating it again doubled every CR of
    # CLAUDE.md (2026-11-05); text with plain \n keeps the platform's line ends, as the scripts' writes always had
    newline = '' if '\r' in text else None
    for attempt in range(tries):
        try:
            with open(tmp, 'w', encoding='utf-8', newline=newline) as f:
                f.write(text)
            os.replace(tmp, path)
            return
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(wait)
