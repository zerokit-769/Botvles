import asyncio
import glob
import hashlib
import json
import os
import random
import shutil
import sys
import textwrap
import time
import urllib.parse
import uuid
from datetime import datetime
from typing import Optional

import aiohttp
from telethon import TelegramClient
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

API_ID = 28752231
API_HASH = "ec1c1f2c30e2f1855c3edee7e348480b"
PAGE_ORIGIN = "https://pmtgram.vercel.app"
MAX_CAPTCHA_RETRY = 3
def get_random_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
def get_random_ua():
    android_ver = random.randint(10, 14)
    model_num = random.randint(10, 99)
    chrome_main = random.randint(100, 125)
    chrome_sub1 = random.randint(1000, 9999)
    chrome_sub2 = random.randint(10, 150)
    return f"Mozilla/5.0 (Linux; Android {android_ver}; SM-S9{model_num}B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_main}.0.{chrome_sub1}.{chrome_sub2} Mobile Safari/537.36"
def gen_hash():
    return hashlib.sha256(os.urandom(32)).hexdigest()
class TerminalUI:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    BLUE = "\033[38;5;39m"
    GREEN = "\033[38;5;118m"
    ORANGE = "\033[38;5;208m"
    CYAN = "\033[38;5;51m"
    PALETTE = (BLUE, GREEN, ORANGE, CYAN)
    def __init__(self):
        self.lock = asyncio.Lock()
        self.clear()
        size = shutil.get_terminal_size(fallback=(88, 28))
        self.width = max(48, size.columns)
        self.height = max(18, size.lines)
        self.inner_width = max(40, min(self.width - 4, 92))
        self.frames = ("◜", "◝", "◞", "◟", "◠", "◡")
        self.live_active = False
        self.palette_index = 0
        self.boot_started = time.perf_counter()
    def clear(self) -> None:
        sys.stderr.write("\033[2J\033[3J\033[H")
        sys.stderr.flush()
    def line_color(self, offset: int = 0) -> str:
        return self.PALETTE[(self.palette_index + offset) % len(self.PALETTE)]
    def paint(self, text: str, color: Optional[str] = None) -> str:
        return f"{color or self.line_color()}{text}{self.RESET}"
    def _fit(self, text: str, limit: Optional[int] = None) -> str:
        available = limit or self.inner_width
        clean = str(text).replace("\n", " ")
        if len(clean) <= available:
            return clean
        if available < 4:
            return clean[:available]
        return f"{clean[:available - 3]}..."
    def _write(self, text: str, end: str = "\n") -> None:
        sys.stderr.write(f"{text}{end}")
        sys.stderr.flush()
    def _live_clear(self) -> None:
        if self.live_active:
            self._write("\r\033[2K", end="")
            self.live_active = False
    def _progress_bar(self, progress: str, width: int = 15) -> str:
        if progress.endswith("%"):
            try:
                amount = max(0, min(100, int(progress[:-1])))
            except ValueError:
                amount = 0
            filled = int(width * amount / 100)
            return f"{self.paint('▰' * filled, self.CYAN)}{self.paint('▱' * (width - filled), self.BLUE)}"
        return self.paint(progress, self.ORANGE)
    def live(self, icon: str, message: str, progress: Optional[str] = None, color: Optional[str] = None) -> None:
        suffix = f"  {self._progress_bar(progress)}" if progress else ""
        message_limit = max(18, self.inner_width - 25)
        active_color = color or self.line_color()
        line = f"\r\033[2K  {self.paint(icon, active_color)} {self.paint(self._fit(message, message_limit), active_color)}{suffix}"
        self._write(line, end="")
        self.live_active = True
    def status(self, icon: str, message: str, detail: Optional[str] = None, color: str = CYAN) -> None:
        self._live_clear()
        message_text = self._fit(message, self.inner_width - 8)
        status_text = f"{icon} {message_text}"
        self._write(f"  {self.paint(status_text, color)}")
        if detail:
            detail_lines = textwrap.wrap(
                str(detail).replace("\n", " "),
                width=max(18, self.inner_width - 10),
                break_long_words=True,
                break_on_hyphens=False,
            ) or [""]
            for line_index, detail_line in enumerate(detail_lines):
                prefix = "↳" if line_index == 0 else " "
                detail_text = f"{prefix} {detail_line}"
                self._write(f"      {self.paint(detail_text, color)}")
        self.palette_index = (self.palette_index + 1) % len(self.PALETTE)
    def success(self, message: str, detail: Optional[str] = None) -> None:
        self.status("✦", message, detail, self.GREEN)
    def info(self, message: str, detail: Optional[str] = None) -> None:
        self.status("◆", message, detail, self.CYAN)
    def warning(self, message: str, detail: Optional[str] = None) -> None:
        self.status("◇", message, detail, self.ORANGE)
    def error(self, message: str, detail: Optional[str] = None) -> None:
        self.status("×", message, detail, self.ORANGE)
    def section(self, title: str, icon: str = "✧") -> None:
        self._live_clear()
        title_text = title.upper()
        color = self.line_color()
        section_text = f"{icon}  {title_text}"
        self._write(f"\n  {self.paint(section_text, color)}")
        self._write(f"  {self.paint('╶' * min(len(title_text) + 8, self.inner_width), color)}")
        self.palette_index = (self.palette_index + 1) % len(self.PALETTE)
    def _box_row(self, text: str, content_width: int, color: str) -> str:
        clipped = self._fit(text, content_width)
        padded = clipped + (" " * max(0, content_width - len(clipped)))
        return f"  {self.paint('│', color)} {self.paint(padded, color)} {self.paint('│', color)}"
    async def banner(self) -> None:
        self._live_clear()
        content_width = max(32, min(self.inner_width - 4, 86))
        self._write("")
        top_border = f"╭{'─' * (content_width + 2)}╮"
        self._write(f"  {self.paint(top_border, self.CYAN)}")
        rows = (
            "⚡  A U T O M A T I O N   P M T   B O T",
            "◈  Bye SyndicateBot Net",
            "⌁  SYSTEM ONLINE",
        )
        row_colors = (self.ORANGE, self.BLUE, self.GREEN)
        for row_index, row in enumerate(rows):
            self._write(self._box_row(row, content_width, row_colors[row_index]))
            await asyncio.sleep(0.12)
        bottom_border = f"╰{'─' * (content_width + 2)}╯"
        self._write(f"  {self.paint(bottom_border, self.CYAN)}")
        self._write("")
    async def loading(self, message: str, seconds: float = 1.0, color: str = CYAN) -> None:
        loop = asyncio.get_running_loop()
        end_at = loop.time() + max(0.05, seconds)
        frame_index = 0
        while loop.time() < end_at:
            remaining = max(0, end_at - loop.time())
            progress = f"{min(100, int((1 - remaining / max(seconds, 0.05)) * 100)):02d}%"
            icon = self.frames[frame_index % len(self.frames)]
            self.live(icon, message, progress, color)
            frame_index += 1
            await asyncio.sleep(0.1)
        self._live_clear()
        self.success(message, "ready")
    async def wait_with_status(self, message: str, seconds: float, color: str = CYAN) -> None:
        await self.loading(message, seconds, color)
    async def countdown(self, seconds: int, message: str) -> None:
        loop = asyncio.get_running_loop()
        end_at = loop.time() + seconds
        color = self.line_color()
        while True:
            now = loop.time()
            if now >= end_at:
                break
            remaining = int(end_at - now)
            line = f"\r\033[2K  {self.paint('⧖', self.ORANGE)} {self.paint(message, color)} {self.paint(f'{remaining}s', self.CYAN)}..."
            self._write(line, end="")
            await asyncio.sleep(0.5)
        self._write("\r\033[2K", end="")
    def prompt(self, label: str, hint: str) -> str:
        self._live_clear()
        color = self.line_color()
        prompt_text = f"\n  {self.paint(f'◈  {label}', color)}\n  {self.paint(f'⌁ {hint}', color)}\n  {self.paint('➜', color)} "
        return input(prompt_text).strip()
    def measure(self) -> None:
        self._write(f"  {self.paint('◈  TERMINAL VIEWPORT LOCKED', self.CYAN)}")
        dimensions = f"╰─ {self.width} columns × {self.height} rows"
        self._write(f"      {self.paint(dimensions, self.BLUE)}")
    def finish(self) -> None:
        self._live_clear()
        elapsed = time.perf_counter() - self.boot_started
        self._write(f"\n  {self.paint('╰─ SESSION COMPLETE', self.GREEN)}")
        self._write(f"      {self.paint(f'runtime {elapsed:.1f}s  •  terminal channel closed', self.CYAN)}")
        self._write(f"  {self.paint('═' * self.inner_width, self.BLUE)}")
class StealthPatch:
    UA_POOL = [
    "Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; SM-S938B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; SM-S938B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; SM-S938B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; SM-S938B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Redmi Note 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Redmi Note 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; M2007J20CG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; M2007J20CG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; M2101K6G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; M2101K6G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; M2102J20SG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; M2102J20SG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; 23021RAAEG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; 23021RAAEG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; CPH2249) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; CPH2249) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; CPH2581) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; CPH2581) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; LE2113) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; LE2113) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; CPH2449) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; CPH2449) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; moto g54 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; moto g54 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; moto g84 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; moto g84 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Nokia G50) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Nokia G50) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Nokia X30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Nokia X30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; vivo V23 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; vivo V23 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; vivo V27) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; vivo V27) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; V2145) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; V2250) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Infinix X6816) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Infinix X6816) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Infinix X6831) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Infinix X6831) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; TECNO KI5q) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; TECNO KI5q) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; TECNO CK8n) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; TECNO CK8n) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G780F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-G990B2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; SM-A556B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-F721B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-F731B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; SM-F741B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; RMX3478) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; RMX3830) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; RMX3999) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; 2201117TY) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; 22101316G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; 22111317G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; 2312DRA50G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; 2109119DG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; 23078PND5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; 24090RA29G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36",
]
    def __init__(self, ui: TerminalUI):
        self.ui = ui
        self.user_agent = random.choice(self.UA_POOL)
        self.profile_dir = f"/data/data/com.termux/files/usr/tmp/stealth_{random.randint(1000, 9999)}"
        os.makedirs(self.profile_dir, exist_ok=True)
        self.browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--no-zygote",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-ipc-flooding-protection",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-first-run",
            "--no-default-browser-check",
            "--password-store=basic",
            "--use-mock-keychain",
            f"--user-agent={self.user_agent}",
            "--disable-blink-features=AutomationControlled",
            "--disable-automation",
            "--lang=en-US",
            "--window-size=1280,800",
        ]
    async def apply(self, page):
        try:
            await page.evaluate("""
                (() => {
                    if (window.__stealth__) return;
                    window.__stealth__ = true;
                    const ua = navigator.userAgent.replace('HeadlessChrome', 'Chrome');
                    Object.defineProperty(navigator, 'userAgent', { get: () => ua });
                    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
                    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
                    Object.defineProperty(navigator, 'webdriver', { get: () => false });
                    Object.defineProperty(navigator, 'platform', { get: () => 'Linux armv8l' });
                    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

                    const origGetContext = HTMLCanvasElement.prototype.getContext;
                    HTMLCanvasElement.prototype.getContext = function(...a) {
                        const c = origGetContext.apply(this, a);
                        if (c && (a[0] === 'webgl' || a[0] === 'webgl2')) {
                            const p = c.getParameter.bind(c);
                            c.getParameter = function(x) {
                                if (x === 37445) return 'Google Inc. (Qualcomm)';
                                if (x === 37446) return 'Adreno (TM) 640';
                                return p(x);
                            };
                        }
                        return c;
                    };

                    if (!window.chrome) window.chrome = {};
                    if (!window.chrome.runtime) window.chrome.runtime = {};
                })();
            """)
        except Exception as error:
            self.ui.warning("Stealth patch warning", str(error))
    async def start_browser(self):
        chrome_path = self._find_chrome()
        self.ui.info("Browser executable located", chrome_path)
        try:
            import zendriver as uc
        except ImportError:
            raise RuntimeError(
                "zendriver is not installed.\n"
                "Install it with: pip install zendriver"
            )
        try:
            await self.ui.wait_with_status("Preparing browser engine", 0.9, self.ui.BLUE)
            browser = await uc.start(
                headless=True,
                no_sandbox=True,
                browser_executable_path=chrome_path,
                browser_args=self.browser_args,
                user_data_dir=self.profile_dir,
            )
            return browser, "zendriver"
        except Exception as error:
            raise RuntimeError(f"zendriver failed to start: {error}")
    @staticmethod
    def _find_chrome():
        if os.environ.get("CHROME_PATH"):
            return os.environ["CHROME_PATH"]
        candidates = [
            "/data/data/com.termux/files/usr/bin/chromium-browser",
            "/data/data/com.termux/files/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        raise FileNotFoundError(
            "Chrome or Chromium was not found. Set CHROME_PATH.\n"
            "Termux users can install it with: pkg install chromium"
        )
    async def solve(self, page, sitekey: str) -> Optional[str]:
        self.ui.clear()
        await self.ui.banner()
        self.ui.section("Widget handshake", "◈")
        self.ui.info("Injecting Turnstile widget", "waiting for challenge surface")
        await page.evaluate(f"""
            (() => {{
                if (document.getElementById('_ts')) return;
                window._tok = null;
                const d = document.createElement('div');
                d.id = '_ts';
                d.style = 'position:fixed;top:20px;left:20px;z-index:2147483647;background:#111;padding:12px;border-radius:8px;';
                document.body.appendChild(d);
                window._ld = function() {{
                    turnstile.render('#_ts', {{
                        sitekey: '{sitekey}',
                        theme: 'dark',
                        callback: t => {{ window._tok = t; }}
                    }});
                }};
                const s = document.createElement('script');
                s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=_ld&render=explicit';
                document.head.appendChild(s);
            }})();
        """)
        await self.ui.wait_with_status("Waiting for Turnstile to render", 8.0, self.ui.ORANGE)

        async def token_value():
            try:
                return await page.evaluate("window._tok || null")
            except Exception:
                return None
        async def find_iframe():
            try:
                result = await page.evaluate("""
                    JSON.stringify((() => {
                        for (const frame of document.querySelectorAll('iframe')) {
                            const src = frame.src || '';
                            if (src.includes('challenges.cloudflare.com') || src.includes('turnstile')) {
                                const bounds = frame.getBoundingClientRect();
                                if (bounds.width > 30) return {x:bounds.x, y:bounds.y, w:bounds.width, h:bounds.height};
                            }
                        }
                        return null;
                    })())
                """)
                return json.loads(result) if result and result != "null" else None
            except Exception:
                return None
        token = await token_value()
        if token:
            self.ui.success("Token received before interaction", "challenge completed")
            return token
        rect = None
        for attempt in range(20):
            rect = await find_iframe()
            if rect:
                self.ui.success("Challenge surface detected", f"position {rect}")
                break
            self.ui.live("◌", "Scanning for challenge surface", f"{attempt + 1:02d}/20")
            await asyncio.sleep(0.5)
        self.ui._live_clear()
        if not rect:
            self.ui.warning("Challenge frame was not detected", "continuing with fallback coordinates")
        for click_number in range(5):
            token = await token_value()
            if token:
                return token
            center_x = (rect["x"] if rect else 20) + (rect["w"] / 2 if rect else 150) + random.uniform(-5, 5)
            center_y = (rect["y"] if rect else 20) + (rect["h"] / 2 if rect else 32) + random.uniform(-3, 3)

            self.ui.info(
                f"Interaction cycle {click_number + 1}/5",
                f"target {center_x:.0f},{center_y:.0f}",
            )
            try:
                await page.mouse_move(center_x - random.randint(40, 80), center_y - random.randint(10, 30))
                await asyncio.sleep(random.uniform(0.15, 0.3))
                await page.mouse_move(center_x, center_y)
                await asyncio.sleep(random.uniform(0.08, 0.15))
                await page.mouse_click(center_x, center_y)
            except Exception as error:
                self.ui.warning("Interaction cycle failed", str(error))
                await asyncio.sleep(2)
                continue
            for wait_number in range(20):
                token = await token_value()
                if token:
                    return token
                self.ui.live("◒", "Waiting for challenge response", f"{wait_number + 1:02d}/20")
                await asyncio.sleep(0.5)
            self.ui._live_clear()

            new_rect = await find_iframe()
            if new_rect:
                rect = new_rect
        self.ui.info("Entering final token wait", "last verification window")
        for wait_number in range(20):
            token = await token_value()
            if token:
                return token
            self.ui.live("◓", "Finalizing token handshake", f"{wait_number + 1:02d}/20")
            await asyncio.sleep(1)
        self.ui._live_clear()
        return None
async def stop_browser(browser, ui: TerminalUI):
    if not browser:
        return
    try:
        result = browser.stop()
        if asyncio.iscoroutine(result):
            await result
        ui.success("Browser session closed", "resources released")
    except Exception as error:
        ui.warning("Browser close warning", str(error))
CAPTCHA_LOCK = asyncio.Lock()
async def get_turnstile_token(ui: TerminalUI, sitekey: str, origin: str = PAGE_ORIGIN) -> Optional[str]:
    if not sitekey:
        ui.error("CAPTCHA aborted", "SiteKey tidak tersedia dari response /getState")
        return None
    async with CAPTCHA_LOCK:
        for path in glob.glob("ss_page_*.png"):
            try:
                os.remove(path)
            except Exception:
                pass
        sp = StealthPatch(ui)
        browser = None
        token = None
        try:
            browser, engine = await sp.start_browser()
            ui.success("Browser engine online", engine)
            ui.info("Opening page origin", origin)
            page = await browser.get(origin)
            await ui.wait_with_status("Waiting for page surface", 3.0, ui.BLUE)
            await sp.apply(page)
            ui.success("Page surface synchronized", "browser context ready")
            timestamp = datetime.now().strftime("%H%M%S")
            screenshot_path = f"ss_page_{timestamp}.png"
            try:
                await page.save_screenshot(screenshot_path)
                ui.success("Page snapshot captured", screenshot_path)
            except Exception as error:
                ui.warning("Page snapshot skipped", str(error))
            token = await sp.solve(page, sitekey)
            if token:
                ui.success("CAPTCHA solved", "token obtained")
                for path in glob.glob("ss_page_*.png"):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
                ui.success("Temporary snapshots removed", "session cleanup complete")
            else:
                ui.error("Verification did not complete", "snapshots kept for debugging")
        except Exception as error:
            ui.error("CAPTCHA session error", str(error))
            token = None
        finally:
            await stop_browser(browser, ui)
            try:
                if os.path.isdir(sp.profile_dir):
                    shutil.rmtree(sp.profile_dir, ignore_errors=True)
            except Exception as error:
                ui.warning("Profile cleanup warning", str(error))
            await asyncio.sleep(0.2)
        return token
def _response_needs_captcha(resp: dict) -> bool:
    if not isinstance(resp, dict):
        return False
    if resp.get("requiresCaptcha") is True:
        return True
    err_msg = str(resp.get("error", "") or "")
    return "captcha" in err_msg.lower() or "security check" in err_msg.lower()
async def _raw_call_api(endpoint: str, init_data: str, user_agent: str, ip_addr: str, device_data: dict, extra_payload: Optional[dict] = None) -> dict:
    url = f"https://captivating-gentleness-production-3932.up.railway.app/{endpoint}"
    headers = {
        'User-Agent': user_agent,
        'Content-Type': "application/json",
        'sec-ch-ua-platform': "\"Android\"",
        'authorization': f"tma {init_data}",
        'sec-ch-ua': f"\"Chromium\";v=\"{user_agent.split('Chrome/')[1].split('.')[0]}\", \"Not?A_Brand\";v=\"24\", \"Android WebView\";v=\"{user_agent.split('Chrome/')[1].split('.')[0]}\"",
        'sec-ch-ua-mobile': "?1",
        'origin': PAGE_ORIGIN,
        'x-requested-with': "org.telegram.messenger.web",
        'sec-fetch-site': "cross-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': f"{PAGE_ORIGIN}/",
        'accept-language': "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        'priority': "u=1, i",
        'X-Forwarded-For': ip_addr
    }
    payload = {
        "_initData": init_data,
        "_startParam": "0376WPTZXJ",
        "_deviceFingerprint": device_data['fp'],
        "_deviceId": device_data['id'],
        "_suspiciousFlags": {
            "headless": False,
            "emulator": False,
            "devtools": False
        },
        "_signals": device_data['signals']
    }
    if extra_payload:
        payload.update(extra_payload)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            try:
                return await response.json()
            except Exception:
                return {}
async def call_api(
    endpoint: str,
    init_data: str,
    user_agent: str,
    ip_addr: str,
    device_data: dict,
    extra_payload: Optional[dict] = None,
    ui: Optional[TerminalUI] = None,
    site_key: str = "",
) -> dict:
    payload_extra = dict(extra_payload) if extra_payload else {}
    response = await _raw_call_api(endpoint, init_data, user_agent, ip_addr, device_data, payload_extra or None)
    attempt = 0
    while _response_needs_captcha(response) and attempt < MAX_CAPTCHA_RETRY:
        attempt += 1
        if ui:
            ui.warning(f"CAPTCHA required on [{endpoint}]", f"auto solving ({attempt}/{MAX_CAPTCHA_RETRY})")
        token = await get_turnstile_token(ui or TerminalUI(), site_key, PAGE_ORIGIN)
        if not token:
            if ui:
                ui.error(f"CAPTCHA failed on [{endpoint}]", "token tidak diperoleh, request tidak diulang dengan token kosong")
            if attempt >= MAX_CAPTCHA_RETRY:
                break
            await asyncio.sleep(3)
            continue
        payload_extra["turnstileToken"] = token
        if ui:
            ui.success("Token obtained", "injecting into payload")
            ui.info(f"Retrying request [{endpoint}]", "with turnstileToken")
        response = await _raw_call_api(endpoint, init_data, user_agent, ip_addr, device_data, payload_extra)
    if _response_needs_captcha(response) and ui:
        ui.error(f"CAPTCHA still required on [{endpoint}]", "retry limit reached, request dianggap gagal")
    return response
async def process_session(session_path: str, ui: TerminalUI, is_multi: bool):
    session_file = session_path.replace(".session", "")
    async with ui.lock:
        ui.info(f"Starting session", session_file)
    client = TelegramClient(session_file, API_ID, API_HASH)
    try:
        await client.start()
        bot_peer = await client.get_input_entity("@Pmt_Gram_Bot")
        app_req = RequestAppWebViewRequest(
            peer=bot_peer,
            app=InputBotAppShortName(bot_id=bot_peer, short_name="app"),
            platform="android",
            start_param="0376WPTZXJ",
            write_allowed=True
        )
        result = await client(app_req)
        raw_data = result.url.split("tgWebAppData=")[1].split("&tgWebAppVersion")[0]
        init_data = urllib.parse.unquote(raw_data)
        async with ui.lock:
            ui.success(f"InitData Retrieved", f"\n{init_data}...")
        device_data = {
            'fp': gen_hash(),
            'id': str(uuid.uuid4()),
            'signals': {
                "canvasHash": gen_hash(),
                "webglHash": gen_hash(),
                "hardwareHash": gen_hash(),
                "fontsHash": gen_hash(),
                "audioHash": gen_hash()
            }
        }
        random_ua = get_random_ua()
        random_ip = get_random_ip()
        state_resp = await call_api("getState", init_data, random_ua, random_ip, device_data, ui=ui)
        if not state_resp.get("success"):
            async with ui.lock:
                ui.error(f"Failed to get state for {session_file}")
            return
        data = state_resp.get("data", {})
        user_info = data.get("user", {})
        config_info = data.get("config", {})
        daily_info = data.get("daily", {})
        mining_info = data.get("mining", {})
        game_plays = data.get("gamePlays", {})
        ads_watched_by_company = data.get("adsWatchedByCompany", {})
        ad_companies_config = data.get("adCompanies", {})
        first_name = user_info.get("firstName", "")
        balance = user_info.get("balance", 0)
        site_key = config_info.get("turnstileSiteKey", "")
        daily_claimed = daily_info.get("claimed", True)
        mining_started_at = mining_info.get("startedAt")
        need_daily = not daily_claimed
        need_mining_start = False
        need_mining_claim = False
        current_time_ms = int(time.time() * 1000)
        async with ui.lock:
            if need_daily:
                ui.warning("Daily Claim", "Belum di claim")
            if mining_started_at is None:
                ui.warning("Mining", "Belum mulai")
                need_mining_start = True
            else:
                if current_time_ms >= (mining_started_at + 3660000):
                    ui.warning("Mining", "Belum di claim")
                    need_mining_claim = True
            await asyncio.sleep(1)
            ui.clear()
            await ui.banner()
            ui._write(f"  {ui.paint('Account', ui.CYAN)} : {session_file}")
            ui._write(f"  {ui.paint('Name', ui.CYAN)}    : {first_name}")
            ui._write(f"  {ui.paint('Balance', ui.CYAN)} : {balance}")
            ui._write(f"  {ui.paint('SiteKey', ui.CYAN)} : {site_key}")
            ui._write(f"  {ui.paint('Proxy IP', ui.CYAN)} : {random_ip}")
            ui._write("")
        if need_daily:
            async with ui.lock:
                await ui.loading("Claim Daily Check In", 1.5, ui.ORANGE)
            daily_resp = await call_api("claimDailyBonus", init_data, random_ua, random_ip, device_data, ui=ui, site_key=site_key)
            async with ui.lock:
                if daily_resp.get("success"):
                    d_data = daily_resp.get("data", {})
                    ui.success(f"Success Claim : {d_data.get('shibaAdded')}")
                    ui.info(f"Balance Point now : {d_data.get('shibaBalance')}")
                else:
                    ui.error("Daily claim failed")
        if need_mining_claim:
            async with ui.lock:
                await ui.loading("Claiming Mining", 1.5, ui.ORANGE)
            claim_resp = await call_api("claimMining", init_data, random_ua, random_ip, device_data, ui=ui, site_key=site_key)
            async with ui.lock:
                if claim_resp.get("success"):
                    c_data = claim_resp.get("data", {})
                    ui.success(f"Mining Claim : {c_data.get('shibaAdded')}")
                    ui.info(f"Point Balance now : {c_data.get('shibaBalance')}")
                    need_mining_start = True
                else:
                    ui.error("Mining claim failed")
        if need_mining_start:
            async with ui.lock:
                await ui.loading("Starting Mining", 1.5, ui.ORANGE)
            start_resp = await call_api("startMining", init_data, random_ua, random_ip, device_data, ui=ui, site_key=site_key)
            async with ui.lock:
                if start_resp.get("success"):
                    ui.success("Mining", "Start For 1 Hour")
                else:
                    ui.error("Mining start failed")
        games = ["gem", "wheel", "xo", "fruit"]
        async with ui.lock:
            ui.section("Playing Mini Games", "🎮")
        for game_name in games:
            plays_count = game_plays.get(game_name, 0)
            if plays_count >= 3:
                async with ui.lock:
                    ui.info(f"Game [{game_name}]", f"Sudah {plays_count}/3 (Skip)")
                continue
            while plays_count < 3:
                async with ui.lock:
                    await ui.loading(f"Playing {game_name} ({plays_count + 1}/3)", 1.2, ui.CYAN)
                game_payload = {"game": game_name, "score": 50}
                game_resp = await call_api(
                    "playGame", init_data, random_ua, random_ip, device_data, game_payload,
                    ui=ui, site_key=site_key
                )
                if game_resp.get("success"):
                    g_data = game_resp.get("data", {})
                    new_game_plays = g_data.get("gamePlays", {})
                    plays_count = new_game_plays.get(game_name, plays_count + 1)
                    async with ui.lock:
                        ui.success(
                            f"Game [{game_name}] Success ({plays_count}/3)",
                            f"Added: +{g_data.get('shibaAdded')} | Balance now: {g_data.get('shibaBalance')}"
                        )
                    await asyncio.sleep(1)
                else:
                    err_msg = game_resp.get("error", "Unknown Error")
                    async with ui.lock:
                        ui.error(f"Game [{game_name}] Failed", err_msg)
                    break
        ad_companies = ["monetag", "adsgram", "gigapub", "monetix"]
        async with ui.lock:
            ui.section("Watching Ads", "📺")
        for company in ad_companies:
            limit_init = ad_companies_config.get(company, {}).get("dailyLimit", 15)
            watched_init = ads_watched_by_company.get(company, 0)
            if watched_init >= limit_init:
                async with ui.lock:
                    ui.info(f"Ad [{company}]", f"Already Maxed {watched_init}/{limit_init} (Skip)")
                continue
            while True:
                async with ui.lock:
                    await ui.loading(f"Claiming Ad: {company}", 1.2, ui.CYAN)
                payload = {"company": company}
                ad_resp = await call_api(
                    "claimAdReward", init_data, random_ua, random_ip, device_data, payload,
                    ui=ui, site_key=site_key
                )
                if ad_resp.get("success"):
                    a_data = ad_resp.get("data", {})
                    added = a_data.get("shibaAdded", 0)
                    balance = a_data.get("shibaBalance", 0)
                    ads_watched = a_data.get("adsWatchedByCompany", {}).get(company, 0)
                    daily_limit = a_data.get("adCompanies", {}).get(company, {}).get("dailyLimit", limit_init)
                    async with ui.lock:
                        ui.success(f"Ad [{company}] Success ({ads_watched}/{daily_limit})", f"Added: +{added} | Balance now: {balance}")
                    if ads_watched >= daily_limit:
                        async with ui.lock:
                            ui.info(f"Ad [{company}]", "Hit daily limit, Next Company...")
                        break
                    if is_multi:
                        async with ui.lock:
                            ui.info(f"Ad [{company}]", "Cooldown 20s...")
                        await asyncio.sleep(20)
                    else:
                        await ui.countdown(20, f"Cooldown Ad {company}")

                else:
                    err_msg = ad_resp.get("error", "Unknown Error")
                    if "limit" in err_msg.lower() or "exceeded" in err_msg.lower() or "maximum" in err_msg.lower():
                        async with ui.lock:
                            ui.info(f"Ad [{company}]", f"Limit Reached: {err_msg}")
                        break
                    async with ui.lock:
                        ui.error(f"Ad [{company}] Failed", err_msg)
                    break 
    except Exception as e:
        async with ui.lock:
            ui.error(f"Error in {session_file}", str(e))
    finally:
        await client.disconnect()
async def main():
    ui = TerminalUI()
    ui.clear()
    await ui.banner()
    ui.section("Session Configuration", "⚙")
    exec_all = ""
    while exec_all.upper() not in ['Y', 'N']:
        exec_all = ui.prompt("Do you want execute all sess.?", "Y / N")
    mode = ""
    while mode not in ['1', '2']:
        mode = ui.prompt("Select a Number Below", "1. run simultaneously  |  2. run in turns")
    ui.clear()
    await ui.banner()
    ui.section("Initialization", "🚀")
    sessions = glob.glob("sess*.session")
    if not sessions:
        ui.error("No session files found!", "Please ensure sess*.session exists.")
        sys.exit(1)
    if exec_all.upper() == 'N':
        sessions = sessions[:1]
        ui.info("Mode single session activated", f"Target: {sessions[0]}")
    else:
        ui.info("Mode multi session activated", f"Total targets: {len(sessions)}")
    await ui.loading("Connecting to Telegram API", 1.5, ui.BLUE)
    if mode == '1':
        ui.info("Execution mode", "Simultaneously (Async/Multi-worker)")
        tasks = [process_session(sess, ui, True) for sess in sessions]
        await asyncio.gather(*tasks)
    else:
        ui.info("Execution mode", "In turns (Sequential)")
        for sess in sessions:
            await process_session(sess, ui, False)
            if sess != sessions[-1]:
                await asyncio.sleep(2)

    ui.finish()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.stderr.write(f"\n{TerminalUI.ORANGE}◇ Session interrupted by user{TerminalUI.RESET}\n")
        sys.exit(130)
