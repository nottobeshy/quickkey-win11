# -*- coding: utf-8 -*-
"""
键游（Python 版）
=================

这是一份只依赖 Python 标准库的 Windows 11 快捷键教学桌面应用。

设计目标：
1. 应用平时缩成桌面右下角的悬浮球，Ctrl + Alt + K 随时呼出。
2. 用真实的全局键盘监听判断用户是否按出了当前快捷键。
3. 每个快捷键首次掌握获得 10 XP，并用音效、窗口抖动和彩纸动画反馈。
4. 提供“快捷键总览”，让用户随时查看全部课程、掌握状态并跳转练习。
5. 学习记录只保存在本机，不上传任何按键或个人数据。

为什么没有第三方依赖？
----------------------
界面由 tkinter 绘制；全局快捷键监听通过 ctypes 调用 Windows API；音效由
winsound 播放。这样源码下载后即可阅读，也更适合初学者逐段修改。
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import date, timedelta
import json
import math
import os
from pathlib import Path
import queue
import random
import struct
import sys
import threading
import tkinter as tk
import wave
import winsound

# 目录文件与本文件放在同一文件夹。显式加入路径后，从任意工作目录启动都可靠。
SOURCE_FOLDER = Path(__file__).resolve().parent
if str(SOURCE_FOLDER) not in sys.path:
    sys.path.insert(0, str(SOURCE_FOLDER))

from shortcuts_catalog import (  # noqa: E402  路径准备好后再导入本地模块
    CATEGORIES,
    SHORTCUTS,
    SOURCE_CHECKED,
    ShortcutInfo,
    validate_catalog,
)


# ---------------------------------------------------------------------------
# 1. 视觉常量：暗色机甲舱 + 明日香式炽红、橙色、黑灰与暖白
# ---------------------------------------------------------------------------

WINDOW_WIDTH = 456
WINDOW_HEIGHT = 760
BUBBLE_SIZE = 106

COLORS = {
    "transparent": "#010203",  # 用作窗口透明色，正常界面不会使用这个颜色
    "bg": "#0B080A",
    "bg_alt": "#100C0F",
    "card": "#151013",
    "card_hot": "#211317",
    "line": "#53272A",
    "line_hot": "#9C3035",
    "red": "#FF3B21",
    "red_dark": "#B91420",
    "orange": "#FF8A32",
    "yellow": "#FFD04A",
    "white": "#FFF4EC",
    "muted": "#B6A4A0",
    "dim": "#766865",
    "success": "#FFB548",
}

FONT_UI = ("Microsoft YaHei UI", 10)
FONT_SMALL = ("Microsoft YaHei UI", 9)
FONT_MONO = ("Bahnschrift", 10)
FONT_TITLE = ("Microsoft YaHei UI", 22, "bold")


# ---------------------------------------------------------------------------
# 2. 课程数据：界面与判断逻辑都从同一份数据生成
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Lesson:
    """一关快捷键课程的数据模型。"""

    lesson_id: str
    title: str
    subtitle: str
    shortcut: str
    tip: str
    steps: tuple[str, str, str]


LESSONS: tuple[Lesson, ...] = (
    Lesson(
        "desktop",
        "一秒回到桌面",
        "窗口再多，也能瞬间清场",
        "Win+D",
        "先按住 Windows 徽标键，再轻点 D；再按一次可以恢复所有窗口。",
        ("找到键盘左下角的 Win 键", "点击开始同步，保持手指放松", "按住 Win，再轻点 D 完成挑战"),
    ),
    Lesson(
        "explorer",
        "快速打开文件",
        "不用再满桌面寻找文件夹",
        "Win+E",
        "E 可以记成 Explorer（资源管理器），这个组合只用左手就能完成。",
        ("找到键盘左下角的 Win 键", "把另一根手指放到字母 E", "同时按下 Win + E，打开资源管理器"),
    ),
    Lesson(
        "switch",
        "在窗口之间穿梭",
        "多任务办公的必修动作",
        "Alt+Tab",
        "按住 Alt 不放，连续点 Tab 可以挑选你想切换的窗口。",
        ("先打开两个不同的窗口", "按住左侧 Alt 键不要松开", "轻点 Tab，看到切换器就成功了"),
    ),
    Lesson(
        "snip",
        "截取任意一块屏幕",
        "告别先截图、再裁剪",
        "Win+Shift+S",
        "按完后屏幕会变暗，用鼠标框选区域，图片会自动进入剪贴板。",
        ("左手小拇指按住 Win", "再按住 Shift，保持两个键不松", "轻点 S，看到截图工具即完成"),
    ),
    Lesson(
        "taskmanager",
        "直接打开任务管理器",
        "程序卡住时的救场组合",
        "Ctrl+Shift+Esc",
        "这比 Ctrl + Alt + Delete 更直接，会立即打开任务管理器。",
        ("左手按住 Ctrl 和 Shift", "右手找到键盘左上角 Esc", "三个键一起按下，打开任务管理器"),
    ),
    Lesson(
        "copy",
        "复制选中的内容",
        "每天都会用到的效率基石",
        "Ctrl+C",
        "C 可以记成 Copy。先选中文字或文件，再使用这个组合。",
        ("先选中一段文字或一个文件", "左手小拇指按住 Ctrl", "食指轻点 C，内容就复制好了"),
    ),
    Lesson(
        "settings",
        "直达系统设置",
        "调整 Win11 不再绕路",
        "Win+I",
        "I 可以记成 Information，按下后直接进入 Windows 设置主页。",
        ("把左手放在 Win 键上", "找到字母 I 的位置", "同时按下 Win + I，打开设置"),
    ),
    Lesson(
        "quicksettings",
        "唤出快捷设置",
        "音量、网络和蓝牙都在这里",
        "Win+A",
        "A 可以记成 Action，快捷设置会从屏幕右下角出现。",
        ("先找到左下角 Win 键", "另一根手指找到字母 A", "同时按下 Win + A，完成最后挑战"),
    ),
)


# ---------------------------------------------------------------------------
# 3. 本地进度保存：使用容易查看和修改的 JSON 文件
# ---------------------------------------------------------------------------

class ProgressStore:
    """管理积分、连续练习天数和已经掌握的课程。"""

    def __init__(self) -> None:
        local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home()))
        self.folder = Path(local_app_data) / "QuickKeyPython"
        self.path = self.folder / "progress.json"
        self.chime_path = self.folder / "success.wav"

    def load(self) -> dict:
        """读取进度；文件损坏时安全地回到初始状态。"""
        default = {"points": 0, "streak": 1, "last_practice": "", "completed": []}
        try:
            if self.path.exists():
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                default.update(saved)
        except (OSError, ValueError, TypeError):
            pass

        # 连续天数只在跨天时发生变化，同一天多次启动不会重复增加。
        try:
            last_day = date.fromisoformat(default["last_practice"])
        except (ValueError, TypeError):
            last_day = None
        if last_day == date.today() - timedelta(days=1):
            default["streak"] = max(1, int(default.get("streak", 1)) + 1)
        elif last_day and last_day < date.today() - timedelta(days=1):
            default["streak"] = 1

        default["points"] = max(0, int(default.get("points", 0)))
        default["streak"] = max(1, int(default.get("streak", 1)))
        default["completed"] = set(default.get("completed", []))
        return default

    def save(self, progress: dict) -> None:
        """将集合转换成 JSON 列表后写入磁盘。"""
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            payload = {
                "points": progress["points"],
                "streak": progress["streak"],
                "last_practice": progress["last_practice"],
                "completed": sorted(progress["completed"]),
            }
            self.path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            # 无法保存进度不应打断正在进行的训练。
            pass


# ---------------------------------------------------------------------------
# 4. 全局键盘钩子：即使焦点在资源管理器或设置中，也能识别快捷键
# ---------------------------------------------------------------------------

class KBDLLHOOKSTRUCT(ctypes.Structure):
    """Windows 传给低级键盘钩子的按键结构。"""

    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        (
            "dwExtraInfo",
            ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong,
        ),
    ]


class GlobalKeyboardHook:
    """在独立线程中安装 WH_KEYBOARD_LL，并把组合键放进线程安全队列。"""

    WH_KEYBOARD_LL = 13
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    WM_SYSKEYDOWN = 0x0104
    WM_SYSKEYUP = 0x0105
    WM_QUIT = 0x0012

    # 常用虚拟键码。Win 键分左右两个，因此判断时要同时检查。
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_MENU = 0x12  # Alt
    VK_LWIN = 0x5B
    VK_RWIN = 0x5C

    def __init__(self, output_queue: queue.Queue[str]) -> None:
        self.output_queue = output_queue
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.thread: threading.Thread | None = None
        self.thread_id = 0
        self.hook_handle = None
        self.down_keys: set[int] = set()
        self._callback_type = ctypes.WINFUNCTYPE(
            wintypes.LPARAM, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
        )
        self._callback = self._callback_type(self._hook_proc)

        # 明确声明参数类型可避免 64 位 Windows 把指针错误截断成 32 位整数。
        self.user32.SetWindowsHookExW.argtypes = (
            ctypes.c_int,
            self._callback_type,
            wintypes.HINSTANCE,
            wintypes.DWORD,
        )
        self.user32.SetWindowsHookExW.restype = wintypes.HANDLE
        self.user32.UnhookWindowsHookEx.argtypes = (wintypes.HANDLE,)
        self.user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        self.user32.CallNextHookEx.argtypes = (
            wintypes.HANDLE,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )
        self.user32.CallNextHookEx.restype = wintypes.LPARAM
        self.user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
        self.user32.GetAsyncKeyState.restype = ctypes.c_short
        self.user32.PostThreadMessageW.argtypes = (
            wintypes.DWORD,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )
        self.kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
        self.kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        self.kernel32.GetCurrentThreadId.restype = wintypes.DWORD

    def start(self) -> None:
        """启动消息循环线程；重复调用不会安装多个钩子。"""
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._message_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """向钩子线程发送 WM_QUIT，让它正常卸载并退出。"""
        if self.thread_id:
            self.user32.PostThreadMessageW(self.thread_id, self.WM_QUIT, 0, 0)

    def _message_loop(self) -> None:
        self.thread_id = self.kernel32.GetCurrentThreadId()
        module = self.kernel32.GetModuleHandleW(None)
        self.hook_handle = self.user32.SetWindowsHookExW(
            self.WH_KEYBOARD_LL, self._callback, module, 0
        )
        if not self.hook_handle:
            self.output_queue.put("__HOOK_ERROR__")
            return

        message = wintypes.MSG()
        try:
            # GetMessageW 会阻塞，但只阻塞钩子线程，不会卡住 tkinter 界面。
            while self.user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                self.user32.TranslateMessage(ctypes.byref(message))
                self.user32.DispatchMessageW(ctypes.byref(message))
        finally:
            self.user32.UnhookWindowsHookEx(self.hook_handle)
            self.hook_handle = None
            self.thread_id = 0

    def _is_down(self, virtual_key: int) -> bool:
        return bool(self.user32.GetAsyncKeyState(virtual_key) & 0x8000)

    @staticmethod
    def _is_modifier(virtual_key: int) -> bool:
        return virtual_key in {
            0x10, 0x11, 0x12, 0x5B, 0x5C,
            0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5,
        }

    @staticmethod
    def _key_name(virtual_key: int) -> str | None:
        if 0x41 <= virtual_key <= 0x5A or 0x30 <= virtual_key <= 0x39:
            return chr(virtual_key)
        if 0x70 <= virtual_key <= 0x87:
            return f"F{virtual_key - 0x6F}"
        return {
            0x09: "Tab",
            0x1B: "Esc",
            0x20: "Space",
            0x0D: "Enter",
            0x08: "Backspace",
            0x25: "Left",
            0x26: "Up",
            0x27: "Right",
            0x28: "Down",
            0x2E: "Delete",
        }.get(virtual_key)

    def _build_shortcut(self, virtual_key: int) -> str | None:
        key_name = self._key_name(virtual_key)
        if not key_name:
            return None
        parts: list[str] = []
        if self._is_down(self.VK_CONTROL):
            parts.append("Ctrl")
        if self._is_down(self.VK_MENU):
            parts.append("Alt")
        if self._is_down(self.VK_LWIN) or self._is_down(self.VK_RWIN):
            parts.append("Win")
        if self._is_down(self.VK_SHIFT):
            parts.append("Shift")
        parts.append(key_name)
        return "+".join(parts)

    def _hook_proc(self, code: int, message: int, data_pointer: int) -> int:
        """钩子回调只做轻量工作，所有界面更新交给 tkinter 主线程。"""
        if code >= 0:
            keyboard_data = ctypes.cast(
                data_pointer, ctypes.POINTER(KBDLLHOOKSTRUCT)
            ).contents
            virtual_key = int(keyboard_data.vkCode)

            if message in (self.WM_KEYUP, self.WM_SYSKEYUP):
                self.down_keys.discard(virtual_key)
            elif message in (self.WM_KEYDOWN, self.WM_SYSKEYDOWN):
                first_press = virtual_key not in self.down_keys
                self.down_keys.add(virtual_key)
                if first_press and not self._is_modifier(virtual_key):
                    shortcut = self._build_shortcut(virtual_key)
                    if shortcut == "Ctrl+Alt+K":
                        # 呼出键不应继续传给当前软件，避免输入一个多余的 K。
                        self.output_queue.put("__TOGGLE__")
                        return 1
                    if shortcut:
                        self.output_queue.put(shortcut)

        return self.user32.CallNextHookEx(
            self.hook_handle, code, message, data_pointer
        )


# ---------------------------------------------------------------------------
# 5. 小型自定义控件：统一按钮、进度条和悬停反馈
# ---------------------------------------------------------------------------

class HoverButton(tk.Button):
    """无边框按钮，鼠标经过时切换颜色。"""

    def __init__(
        self,
        master,
        *,
        normal: str,
        hover: str,
        foreground: str = COLORS["white"],
        **kwargs,
    ) -> None:
        self.normal_color = normal
        self.hover_color = hover
        super().__init__(
            master,
            bg=normal,
            fg=foreground,
            activebackground=hover,
            activeforeground=foreground,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            **kwargs,
        )
        self.bind("<Enter>", lambda _event: self.configure(bg=self.hover_color))
        self.bind("<Leave>", lambda _event: self.configure(bg=self.normal_color))

    def set_colors(self, normal: str, hover: str | None = None) -> None:
        self.normal_color = normal
        self.hover_color = hover or normal
        self.configure(bg=normal, activebackground=self.hover_color)


class HudProgress(tk.Canvas):
    """用 Canvas 绘制的细条进度条。"""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            height=8,
            bg=COLORS["bg"],
            highlightthickness=0,
            **kwargs,
        )
        self.ratio = 0.0
        self.bind("<Configure>", lambda _event: self.redraw())

    def set_ratio(self, ratio: float) -> None:
        self.ratio = max(0.0, min(1.0, ratio))
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        width = max(1, self.winfo_width())
        self.create_rectangle(0, 1, width, 7, fill="#241519", outline=COLORS["line"])
        fill_width = int(width * self.ratio)
        if fill_width:
            self.create_rectangle(0, 1, fill_width, 7, fill=COLORS["red"], outline="")
            self.create_rectangle(
                max(0, fill_width - 24), 1, fill_width, 2, fill=COLORS["orange"], outline=""
            )


# ---------------------------------------------------------------------------
# 6. 主应用：创建界面、切换页面、处理课程和游戏化反馈
# ---------------------------------------------------------------------------

class QuickKeyApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("键游 Python版 // KY-PY-02")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=COLORS["transparent"])
        self.root.resizable(False, False)
        try:
            # Windows 支持把指定颜色变成透明，因此悬浮球四角不会出现方形底色。
            self.root.wm_attributes("-transparentcolor", COLORS["transparent"])
        except tk.TclError:
            pass

        self.store = ProgressStore()
        self.progress = self.store.load()
        self.current_lesson = self._first_incomplete_lesson()
        self.listening = False
        self.expanded = True
        self.current_page = "training"
        self.last_wrong_hint_at = 0
        self.toast_after_id: str | None = None
        self.drag_offset = (0, 0)

        self.keyboard_queue: queue.Queue[str] = queue.Queue()
        self.keyboard_hook = GlobalKeyboardHook(self.keyboard_queue)

        self._build_shell()
        self._build_training_page()
        self._build_overview_page()
        self._build_achievement_page()
        self._build_bottom_navigation()
        self._build_bubble()
        self._build_success_overlay()
        self._build_context_menu()

        self._show_page("training")
        self._position_expanded()
        self._update_all()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.keyboard_hook.start()
        self.root.after(45, self._poll_keyboard)

    # ----- 窗口外壳 -------------------------------------------------------

    def _build_shell(self) -> None:
        self.panel = tk.Frame(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=COLORS["line_hot"],
        )
        self.panel.pack_propagate(False)

        self.body = tk.Frame(self.panel, bg=COLORS["bg"])
        self.body.place(x=1, y=1, width=WINDOW_WIDTH - 2, height=WINDOW_HEIGHT - 2)

        # 顶部三色警戒线是纯几何元素，没有使用任何外部图片。
        top_line = tk.Frame(self.body, bg=COLORS["red"], height=3)
        top_line.pack(fill="x")
        top_line.pack_propagate(False)
        tk.Frame(top_line, bg=COLORS["orange"]).place(relx=0.62, x=0, y=0, relwidth=0.25, height=3)

        self.header = tk.Frame(self.body, bg=COLORS["bg"], height=72)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        logo = tk.Label(
            self.header,
            text="02",
            bg=COLORS["red"],
            fg=COLORS["white"],
            font=("Bahnschrift Condensed", 18, "bold"),
            width=3,
            height=2,
            highlightbackground=COLORS["orange"],
            highlightthickness=1,
        )
        logo.pack(side="left", padx=(18, 10), pady=13)

        title_box = tk.Frame(self.header, bg=COLORS["bg"])
        title_box.pack(side="left", pady=14)
        tk.Label(
            title_box,
            text="键游 // KY-PY",
            bg=COLORS["bg"],
            fg=COLORS["white"],
            font=("Microsoft YaHei UI", 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="SHORTCUT SYNC TRAINING",
            bg=COLORS["bg"],
            fg=COLORS["orange"],
            font=("Bahnschrift", 8),
        ).pack(anchor="w", pady=(1, 0))

        self.close_button = HoverButton(
            self.header,
            text="×",
            normal=COLORS["card"],
            hover=COLORS["red_dark"],
            foreground=COLORS["orange"],
            font=("Segoe UI", 14),
            command=self.close,
            width=3,
            height=1,
        )
        self.close_button.pack(side="right", padx=(4, 12), pady=19)

        self.collapse_button = HoverButton(
            self.header,
            text="—",
            normal=COLORS["card"],
            hover=COLORS["card_hot"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 12),
            command=self.collapse,
            width=3,
            height=1,
        )
        self.collapse_button.pack(side="right", pady=19)

        self.level_label = tk.Label(
            self.header,
            text="SYNC 01",
            bg="#2C1618",
            fg=COLORS["orange"],
            font=("Bahnschrift", 9, "bold"),
            padx=8,
            pady=5,
            highlightbackground="#743033",
            highlightthickness=1,
        )
        self.level_label.pack(side="right", padx=6, pady=19)

        # 标题区域可以拖动窗口；按钮本身不绑定拖动，所以点击仍然可靠。
        for drag_widget in (self.header, logo, title_box):
            drag_widget.bind("<ButtonPress-1>", self._start_drag)
            drag_widget.bind("<B1-Motion>", self._drag_window)

        self._build_stats_card()

        self.content_host = tk.Frame(self.body, bg=COLORS["bg"])
        self.content_host.pack(fill="both", expand=True, padx=18)

        self.bottom = tk.Frame(self.body, bg=COLORS["bg_alt"], height=66)
        self.bottom.pack(fill="x", side="bottom")
        self.bottom.pack_propagate(False)

        self.toast_label = tk.Label(
            self.panel,
            text="",
            bg="#261217",
            fg=COLORS["white"],
            font=FONT_SMALL,
            padx=14,
            pady=9,
            highlightbackground=COLORS["line_hot"],
            highlightthickness=1,
        )

    def _build_stats_card(self) -> None:
        stats = tk.Frame(
            self.body,
            bg=COLORS["card"],
            height=76,
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        stats.pack(fill="x", padx=18, pady=(0, 10))
        stats.pack_propagate(False)
        stats.grid_columnconfigure(0, weight=1)
        stats.grid_columnconfigure(2, weight=1)

        left = tk.Frame(stats, bg=COLORS["card"])
        left.grid(row=0, column=0, sticky="nsew", padx=15, pady=11)
        tk.Label(
            left,
            text="◆",
            bg="#34151A",
            fg=COLORS["orange"],
            font=("Segoe UI Symbol", 15),
            width=3,
            height=2,
            highlightbackground="#7D3034",
            highlightthickness=1,
        ).pack(side="left")
        text_box = tk.Frame(left, bg=COLORS["card"])
        text_box.pack(side="left", padx=9)
        tk.Label(text_box, text="同步积分", bg=COLORS["card"], fg=COLORS["muted"], font=FONT_SMALL).pack(anchor="w")
        self.points_label = tk.Label(
            text_box, text="0 XP", bg=COLORS["card"], fg=COLORS["white"], font=("Bahnschrift", 17, "bold")
        )
        self.points_label.pack(anchor="w")

        tk.Frame(stats, bg=COLORS["line"], width=1).grid(row=0, column=1, sticky="ns", pady=15)

        right = tk.Frame(stats, bg=COLORS["card"])
        right.grid(row=0, column=2, sticky="nsew", padx=15, pady=11)
        tk.Label(
            right,
            text="▲",
            bg="#342015",
            fg=COLORS["yellow"],
            font=("Segoe UI Symbol", 14),
            width=3,
            height=2,
            highlightbackground="#7C4B28",
            highlightthickness=1,
        ).pack(side="left")
        streak_box = tk.Frame(right, bg=COLORS["card"])
        streak_box.pack(side="left", padx=9)
        tk.Label(streak_box, text="连续训练", bg=COLORS["card"], fg=COLORS["muted"], font=FONT_SMALL).pack(anchor="w")
        self.streak_label = tk.Label(
            streak_box, text="1 天", bg=COLORS["card"], fg=COLORS["white"], font=("Bahnschrift", 17, "bold")
        )
        self.streak_label.pack(anchor="w")

    # ----- 训练页 ---------------------------------------------------------

    def _build_training_page(self) -> None:
        self.training_page = tk.Frame(self.content_host, bg=COLORS["bg"])

        meta = tk.Frame(self.training_page, bg=COLORS["bg"])
        meta.pack(fill="x", pady=(1, 5))
        self.phase_label = tk.Label(
            meta,
            text="PHASE // 01",
            bg="#34151A",
            fg=COLORS["orange"],
            font=("Bahnschrift", 9, "bold"),
            padx=9,
            pady=4,
            highlightbackground="#7D3034",
            highlightthickness=1,
        )
        self.phase_label.pack(side="left")
        self.mastered_label = tk.Label(
            meta,
            text="✓ SYNCED",
            bg="#3A2515",
            fg=COLORS["yellow"],
            font=("Bahnschrift", 8, "bold"),
            padx=8,
            pady=4,
        )
        self.training_count_label = tk.Label(
            meta,
            text="00 / 08",
            bg=COLORS["bg"],
            fg=COLORS["orange"],
            font=("Bahnschrift", 9, "bold"),
        )
        self.training_count_label.pack(side="right")

        self.lesson_title_label = tk.Label(
            self.training_page,
            text="",
            bg=COLORS["bg"],
            fg=COLORS["white"],
            font=FONT_TITLE,
            anchor="w",
        )
        self.lesson_title_label.pack(fill="x")
        self.lesson_subtitle_label = tk.Label(
            self.training_page,
            text="",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=FONT_UI,
            anchor="w",
        )
        self.lesson_subtitle_label.pack(fill="x", pady=(1, 8))

        self.training_progress = HudProgress(self.training_page)
        self.training_progress.pack(fill="x", pady=(0, 10))

        key_card = tk.Frame(
            self.training_page,
            bg=COLORS["card"],
            height=168,
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        key_card.pack(fill="x")
        key_card.pack_propagate(False)
        tk.Label(
            key_card,
            text="INPUT SEQUENCE // 按键序列",
            bg=COLORS["card"],
            fg=COLORS["orange"],
            font=("Bahnschrift", 9),
        ).pack(pady=(11, 7))
        self.key_caps_frame = tk.Frame(key_card, bg=COLORS["card"], height=48)
        self.key_caps_frame.pack()
        self.key_caps_frame.pack_propagate(False)
        tk.Frame(key_card, height=1, bg=COLORS["line"]).pack(fill="x", padx=20, pady=(7, 6))
        tk.Label(
            key_card,
            text="TACTICAL NOTE // 操作提示",
            bg=COLORS["card"],
            fg=COLORS["orange"],
            font=("Microsoft YaHei UI", 9, "bold"),
        ).pack(anchor="w", padx=20)
        self.tip_label = tk.Label(
            key_card,
            text="",
            bg=COLORS["card"],
            fg=COLORS["muted"],
            font=FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=370,
        )
        self.tip_label.pack(fill="x", padx=20, pady=(3, 0))

        tk.Label(
            self.training_page,
            text="SYNC PROCEDURE // 三步完成",
            bg=COLORS["bg"],
            fg=COLORS["white"],
            font=("Microsoft YaHei UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(10, 5))

        self.step_labels: list[tk.Label] = []
        for number in range(1, 4):
            row = tk.Frame(self.training_page, bg=COLORS["bg"], height=29)
            row.pack(fill="x")
            row.pack_propagate(False)
            tk.Label(
                row,
                text=f"{number:02d}",
                bg="#34151A",
                fg=COLORS["orange"],
                font=("Bahnschrift", 8, "bold"),
                width=3,
                highlightbackground="#7D3034",
                highlightthickness=1,
            ).pack(side="left", pady=3)
            label = tk.Label(
                row,
                text="",
                bg=COLORS["bg"],
                fg=COLORS["muted"],
                font=FONT_SMALL,
                anchor="w",
            )
            label.pack(side="left", fill="x", expand=True, padx=8)
            self.step_labels.append(label)

        actions = tk.Frame(self.training_page, bg=COLORS["bg"], height=50)
        actions.pack(fill="x", pady=(8, 0))
        actions.pack_propagate(False)
        self.previous_button = HoverButton(
            actions,
            text="‹",
            normal=COLORS["card"],
            hover=COLORS["card_hot"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 18),
            width=3,
            command=self.previous_lesson,
        )
        self.previous_button.pack(side="left", fill="y")
        self.next_button = HoverButton(
            actions,
            text="›",
            normal=COLORS["card"],
            hover=COLORS["card_hot"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 18),
            width=3,
            command=self.next_lesson,
        )
        self.next_button.pack(side="right", fill="y")
        self.start_button = HoverButton(
            actions,
            text="开始同步  ·  +10 XP",
            normal=COLORS["red"],
            hover="#FF5B2B",
            foreground=COLORS["white"],
            font=("Microsoft YaHei UI", 11, "bold"),
            command=self.toggle_practice,
        )
        self.start_button.pack(side="left", fill="both", expand=True, padx=8)

    # ----- 快捷键总览页 ---------------------------------------------------

    def _build_overview_page(self) -> None:
        self.overview_page = tk.Frame(self.content_host, bg=COLORS["bg"])
        tk.Label(
            self.overview_page,
            text="SHORTCUT ARCHIVE",
            bg=COLORS["bg"],
            fg=COLORS["orange"],
            font=("Bahnschrift", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))
        tk.Label(
            self.overview_page,
            text="快捷键总览",
            bg=COLORS["bg"],
            fg=COLORS["white"],
            font=FONT_TITLE,
            anchor="w",
        ).pack(fill="x")
        self.overview_summary = tk.Label(
            self.overview_page,
            text="",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=FONT_SMALL,
            anchor="w",
        )
        self.overview_summary.pack(fill="x", pady=(2, 6))
        self.overview_progress = HudProgress(self.overview_page)
        self.overview_progress.pack(fill="x", pady=(0, 9))

        # 搜索框与类别筛选直接作用于 200+ 条官方目录，不影响核心训练关卡。
        filter_bar = tk.Frame(self.overview_page, bg=COLORS["bg"])
        filter_bar.pack(fill="x", pady=(0, 8))
        tk.Label(
            filter_bar,
            text="⌕",
            bg=COLORS["card"],
            fg=COLORS["orange"],
            font=("Segoe UI Symbol", 12),
            padx=8,
            pady=5,
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        ).pack(side="left")
        self.catalog_search = tk.StringVar()
        search_entry = tk.Entry(
            filter_bar,
            textvariable=self.catalog_search,
            bg=COLORS["card"],
            fg=COLORS["white"],
            insertbackground=COLORS["orange"],
            selectbackground=COLORS["red_dark"],
            relief="flat",
            font=FONT_SMALL,
            width=19,
        )
        search_entry.pack(side="left", fill="y", padx=(0, 7), ipady=5)
        self.catalog_search.trace_add("write", lambda *_args: self._refresh_overview())

        self.catalog_category = tk.StringVar(value="全部")
        category_menu = tk.OptionMenu(
            filter_bar,
            self.catalog_category,
            *CATEGORIES,
            command=lambda _value: self._refresh_overview(),
        )
        category_menu.configure(
            bg=COLORS["card_hot"],
            fg=COLORS["orange"],
            activebackground="#3A1A1F",
            activeforeground=COLORS["white"],
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            font=FONT_SMALL,
            cursor="hand2",
            width=10,
        )
        category_menu["menu"].configure(
            bg=COLORS["card"],
            fg=COLORS["white"],
            activebackground=COLORS["red_dark"],
            activeforeground=COLORS["white"],
            font=FONT_SMALL,
        )
        category_menu.pack(side="right", fill="y")

        list_shell = tk.Frame(
            self.overview_page,
            bg=COLORS["card"],
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        list_shell.pack(fill="both", expand=True, pady=(0, 5))

        self.overview_canvas = tk.Canvas(
            list_shell,
            bg=COLORS["card"],
            highlightthickness=0,
            bd=0,
        )
        scrollbar = tk.Scrollbar(
            list_shell,
            orient="vertical",
            command=self.overview_canvas.yview,
            troughcolor=COLORS["bg_alt"],
            bg=COLORS["line"],
            activebackground=COLORS["red"],
            relief="flat",
            width=9,
        )
        self.overview_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.overview_canvas.pack(side="left", fill="both", expand=True)
        self.overview_inner = tk.Frame(self.overview_canvas, bg=COLORS["card"])
        self.overview_window = self.overview_canvas.create_window(
            (0, 0), window=self.overview_inner, anchor="nw"
        )
        self.overview_inner.bind(
            "<Configure>",
            lambda _event: self.overview_canvas.configure(
                scrollregion=self.overview_canvas.bbox("all")
            ),
        )
        self.overview_canvas.bind(
            "<Configure>",
            lambda event: self.overview_canvas.itemconfigure(
                self.overview_window, width=event.width
            ),
        )
        tk.Label(
            self.overview_page,
            text=f"MICROSOFT SUPPORT // 核对日期 {SOURCE_CHECKED}",
            bg=COLORS["bg"],
            fg=COLORS["dim"],
            font=("Bahnschrift", 7),
            anchor="e",
        ).pack(fill="x", pady=(0, 5))
        self.overview_canvas.bind(
            "<MouseWheel>",
            lambda event: self.overview_canvas.yview_scroll(
                int(-event.delta / 120), "units"
            ),
        )

    def _refresh_overview(self) -> None:
        """按搜索词和类别重建官方目录；可训练项目支持一键跳转。"""
        for child in self.overview_inner.winfo_children():
            child.destroy()

        query = self.catalog_search.get().strip().lower()
        category = self.catalog_category.get()
        filtered = [
            item
            for item in SHORTCUTS
            if (category == "全部" or item.category == category)
            and (
                not query
                or query in item.keys.lower()
                or query in item.action.lower()
                or query in item.category.lower()
            )
        ]
        self.overview_summary.configure(
            text=f"官方目录 {len(SHORTCUTS)} 条 · 当前显示 {len(filtered)} 条 · 核心训练 {len(LESSONS)} 关"
        )

        current_id = LESSONS[self.current_lesson].lesson_id
        for index, item in enumerate(filtered):
            mastered = bool(item.lesson_id and item.lesson_id in self.progress["completed"])
            selected = item.lesson_id == current_id
            row = tk.Frame(
                self.overview_inner,
                bg=COLORS["card_hot"] if mastered else COLORS["card"],
                height=64,
                highlightbackground=COLORS["line_hot"] if selected else COLORS["line"],
                highlightthickness=1,
                cursor="hand2",
            )
            row.pack(fill="x", padx=7, pady=(7 if index == 0 else 0, 4))
            row.pack_propagate(False)

            phase = tk.Label(
                row,
                text=f"{index + 1:03d}",
                bg=COLORS["red"] if selected else "#34151A",
                fg=COLORS["white"] if selected else COLORS["orange"],
                font=("Bahnschrift", 9, "bold"),
                width=4,
            )
            phase.pack(side="left", fill="y")
            text_box = tk.Frame(row, bg=row["bg"])
            text_box.pack(side="left", fill="both", expand=True, padx=9, pady=7)
            title = tk.Label(
                text_box,
                text=item.keys,
                bg=row["bg"],
                fg=COLORS["white"],
                font=("Bahnschrift", 10, "bold"),
                anchor="w",
            )
            title.pack(anchor="w")
            action = tk.Label(
                text_box,
                text=item.action,
                bg=row["bg"],
                fg=COLORS["muted"],
                font=("Microsoft YaHei UI", 8),
                anchor="w",
                justify="left",
                wraplength=245,
            )
            action.pack(anchor="w")
            if mastered:
                status_text, status_color = "✓ 已掌握", COLORS["yellow"]
            elif item.lesson_id:
                status_text, status_color = "可训练", COLORS["orange"]
            elif item.risk == "caution":
                status_text, status_color = "⚠ 谨慎", COLORS["red"]
            elif item.risk == "context":
                status_text, status_color = "场景限定", COLORS["dim"]
            else:
                status_text, status_color = item.category, COLORS["dim"]
            status = tk.Label(
                row,
                text=status_text,
                bg=row["bg"],
                fg=status_color,
                font=("Microsoft YaHei UI", 8),
                padx=9,
            )
            status.pack(side="right")

            # 行内所有子控件共用事件，带 lesson_id 的条目会跳到分步训练。
            for widget in (row, phase, text_box, title, action, status):
                widget.bind(
                    "<Button-1>",
                    lambda _event, target=item: self.open_catalog_item(target),
                )

        if not filtered:
            tk.Label(
                self.overview_inner,
                text="没有匹配的快捷键\n试试搜索 Win、截图、窗口或文件",
                bg=COLORS["card"],
                fg=COLORS["muted"],
                font=FONT_UI,
                justify="center",
                pady=55,
            ).pack(fill="x")

    def open_catalog_item(self, item: ShortcutInfo) -> None:
        """打开目录条目；危险或场景限定项目只展示说明，不直接触发。"""
        if item.lesson_id:
            for index, lesson in enumerate(LESSONS):
                if lesson.lesson_id == item.lesson_id:
                    self.select_lesson(index)
                    return
        prefix = "谨慎操作：" if item.risk == "caution" else f"{item.category}："
        self.show_toast(prefix + item.action)

    # ----- 成就页 ---------------------------------------------------------

    def _build_achievement_page(self) -> None:
        self.achievement_page = tk.Frame(self.content_host, bg=COLORS["bg"])
        tk.Label(
            self.achievement_page,
            text="PILOT STATUS",
            bg=COLORS["bg"],
            fg=COLORS["orange"],
            font=("Bahnschrift", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))
        tk.Label(
            self.achievement_page,
            text="同步成就",
            bg=COLORS["bg"],
            fg=COLORS["white"],
            font=FONT_TITLE,
            anchor="w",
        ).pack(fill="x")

        card = tk.Frame(
            self.achievement_page,
            bg=COLORS["card"],
            highlightbackground=COLORS["line_hot"],
            highlightthickness=1,
        )
        card.pack(fill="x", pady=18)
        tk.Label(
            card,
            text="02",
            bg=COLORS["red"],
            fg=COLORS["white"],
            font=("Bahnschrift Condensed", 38, "bold"),
            width=4,
            height=2,
        ).pack(pady=(24, 12))
        self.achievement_title = tk.Label(
            card,
            text="新手同步中",
            bg=COLORS["card"],
            fg=COLORS["white"],
            font=("Microsoft YaHei UI", 16, "bold"),
        )
        self.achievement_title.pack()
        self.achievement_detail = tk.Label(
            card,
            text="",
            bg=COLORS["card"],
            fg=COLORS["muted"],
            font=FONT_UI,
        )
        self.achievement_detail.pack(pady=(5, 24))

        hint = tk.Frame(
            self.achievement_page,
            bg="#2C1719",
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        hint.pack(fill="x")
        tk.Label(
            hint,
            text="CALL SIGN",
            bg="#2C1719",
            fg=COLORS["orange"],
            font=("Bahnschrift", 9, "bold"),
        ).pack(pady=(14, 2))
        tk.Label(
            hint,
            text="Ctrl + Alt + K",
            bg="#2C1719",
            fg=COLORS["white"],
            font=("Bahnschrift", 18, "bold"),
        ).pack()
        tk.Label(
            hint,
            text="在任何程序中呼出或收起键游",
            bg="#2C1719",
            fg=COLORS["muted"],
            font=FONT_SMALL,
        ).pack(pady=(3, 14))

    # ----- 底部导航、悬浮球和菜单 -----------------------------------------

    def _build_bottom_navigation(self) -> None:
        nav_specs = (
            ("training", "⌨\n训练"),
            ("overview", "▦\n总览"),
            ("achievement", "♛\n成就"),
        )
        self.nav_buttons: dict[str, HoverButton] = {}
        for page_name, label in nav_specs:
            button = HoverButton(
                self.bottom,
                text=label,
                normal=COLORS["bg_alt"],
                hover=COLORS["card_hot"],
                foreground=COLORS["muted"],
                font=FONT_SMALL,
                command=lambda target=page_name: self._show_page(target),
            )
            button.pack(side="left", fill="both", expand=True, padx=7, pady=7)
            self.nav_buttons[page_name] = button

    def _build_bubble(self) -> None:
        self.bubble = tk.Canvas(
            self.root,
            width=BUBBLE_SIZE,
            height=BUBBLE_SIZE,
            bg=COLORS["transparent"],
            highlightthickness=0,
            cursor="hand2",
        )
        self.bubble.create_oval(10, 12, 98, 100, fill="#4B1118", outline="")
        self.bubble.create_oval(13, 8, 93, 88, fill=COLORS["red_dark"], outline=COLORS["orange"], width=2)
        self.bubble.create_oval(19, 14, 87, 82, fill=COLORS["red"], outline="#FFB45B", width=1)
        self.bubble.create_text(53, 47, text="02", fill=COLORS["white"], font=("Bahnschrift Condensed", 24, "bold"))
        self.bubble_badge = self.bubble.create_rectangle(68, 8, 100, 28, fill=COLORS["yellow"], outline="#2A1012")
        self.bubble_points = self.bubble.create_text(84, 18, text="0", fill="#241012", font=("Bahnschrift", 8, "bold"))
        self.bubble.bind("<Button-1>", lambda _event: self.expand())
        self.bubble.bind("<Button-3>", self._open_context_menu)

    def _build_context_menu(self) -> None:
        self.context_menu = tk.Menu(self.root, tearoff=False)
        self.context_menu.add_command(label="打开键游", command=self.expand)
        self.context_menu.add_command(label="快捷键总览", command=lambda: (self.expand(), self._show_page("overview")))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="退出", command=self.close)

    def _open_context_menu(self, event) -> None:
        self.context_menu.tk_popup(event.x_root, event.y_root)

    # ----- 成功反馈 -------------------------------------------------------

    def _build_success_overlay(self) -> None:
        self.success_canvas = tk.Canvas(
            self.panel,
            width=334,
            height=374,
            bg=COLORS["card"],
            highlightbackground=COLORS["line_hot"],
            highlightthickness=2,
        )
        self.success_canvas.create_text(167, 40, text="SYNC COMPLETE", fill=COLORS["orange"], font=("Bahnschrift", 10, "bold"))
        self.success_canvas.create_oval(120, 62, 214, 156, fill="#34151A", outline=COLORS["line_hot"], width=2)
        self.success_canvas.create_oval(131, 73, 203, 145, fill=COLORS["red"], outline=COLORS["orange"], width=1)
        self.success_canvas.create_text(167, 109, text="✓", fill=COLORS["white"], font=("Segoe UI", 32, "bold"))
        self.success_canvas.create_text(167, 185, text="漂亮！一次成功", fill=COLORS["white"], font=("Microsoft YaHei UI", 17, "bold"))
        self.success_message = self.success_canvas.create_text(167, 217, text="", fill=COLORS["muted"], font=FONT_UI)
        self.success_reward = self.success_canvas.create_text(167, 253, text="⚡ +10 XP", fill=COLORS["yellow"], font=("Bahnschrift", 14, "bold"))
        self.success_button = HoverButton(
            self.success_canvas,
            text="进入下一阶段",
            normal=COLORS["red"],
            hover="#FF5B2B",
            foreground=COLORS["white"],
            font=("Microsoft YaHei UI", 10, "bold"),
            command=self.continue_after_success,
            width=22,
            height=2,
        )
        self.success_canvas.create_window(167, 326, window=self.success_button)
        self.confetti: list[dict] = []

    def _show_success(self, lesson: Lesson, first_time: bool) -> None:
        self.success_canvas.itemconfigure(self.success_message, text=f"你掌握了「{lesson.title}」")
        self.success_canvas.itemconfigure(
            self.success_reward, text="⚡ +10 XP" if first_time else "✓ 复习完成"
        )
        self.success_canvas.place(x=(WINDOW_WIDTH - 334) // 2, y=186)
        self.success_canvas.lift()
        self._create_confetti()
        self._animate_confetti(0)

    def _create_confetti(self) -> None:
        for particle in self.confetti:
            self.success_canvas.delete(particle["item"])
        self.confetti.clear()
        palette = [COLORS["red"], COLORS["orange"], COLORS["yellow"], COLORS["white"], COLORS["red_dark"]]
        for _ in range(32):
            x = 167 + random.randint(-35, 35)
            y = 118 + random.randint(-12, 12)
            item = self.success_canvas.create_rectangle(
                x, y, x + random.randint(4, 8), y + random.randint(6, 11),
                fill=random.choice(palette), outline=""
            )
            self.confetti.append(
                {"item": item, "x": float(x), "y": float(y), "vx": random.uniform(-4.4, 4.4), "vy": random.uniform(-6.5, -2.0)}
            )

        # 保证文字和按钮始终位于彩纸上方。
        self.success_canvas.tag_raise(self.success_message)
        self.success_canvas.tag_raise(self.success_reward)

    def _animate_confetti(self, frame: int) -> None:
        if not self.success_canvas.winfo_ismapped() or frame > 48:
            return
        for particle in self.confetti:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] += 0.24  # 重力感
            item = particle["item"]
            box = self.success_canvas.coords(item)
            width = box[2] - box[0]
            height = box[3] - box[1]
            self.success_canvas.coords(
                item,
                particle["x"], particle["y"],
                particle["x"] + width, particle["y"] + height,
            )
        self.root.after(24, lambda: self._animate_confetti(frame + 1))

    # ----- 页面和数据更新 -------------------------------------------------

    def _show_page(self, page_name: str) -> None:
        self.current_page = page_name
        for page in (self.training_page, self.overview_page, self.achievement_page):
            page.pack_forget()
        page = {
            "training": self.training_page,
            "overview": self.overview_page,
            "achievement": self.achievement_page,
        }[page_name]
        page.pack(fill="both", expand=True)

        for name, button in self.nav_buttons.items():
            if name == page_name:
                button.configure(fg=COLORS["orange"])
                button.set_colors("#32161B", "#3E1B20")
            else:
                button.configure(fg=COLORS["muted"])
                button.set_colors(COLORS["bg_alt"], COLORS["card_hot"])

        if page_name == "overview":
            self._refresh_overview()
        self._update_header()

    def _update_all(self) -> None:
        self._update_header()
        self._update_lesson()
        self._refresh_overview()
        self._update_achievement()

    def _update_header(self) -> None:
        completed = len(self.progress["completed"])
        points = self.progress["points"]
        level = max(1, 1 + points // 30)
        self.points_label.configure(text=f"{points} XP")
        self.streak_label.configure(text=f"{self.progress['streak']} 天")
        self.level_label.configure(text=f"SYNC {level:02d}")
        self.training_count_label.configure(text=f"{completed:02d} / {len(LESSONS):02d}")
        ratio = completed / len(LESSONS)
        self.training_progress.set_ratio(ratio)
        self.overview_progress.set_ratio(ratio)
        display_points = "99+" if points > 99 else str(points)
        self.bubble.itemconfigure(self.bubble_points, text=display_points)

    def _update_lesson(self) -> None:
        self.listening = False
        lesson = LESSONS[self.current_lesson]
        mastered = lesson.lesson_id in self.progress["completed"]
        self.phase_label.configure(text=f"PHASE // {self.current_lesson + 1:02d}")
        if mastered:
            self.mastered_label.pack(side="left", padx=7)
        else:
            self.mastered_label.pack_forget()
        self.lesson_title_label.configure(text=lesson.title)
        self.lesson_subtitle_label.configure(text=lesson.subtitle)
        self.tip_label.configure(text=lesson.tip)
        for label, step in zip(self.step_labels, lesson.steps):
            label.configure(text=step)
        self._render_key_caps(lesson.shortcut)
        self.previous_button.configure(state="normal" if self.current_lesson > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_lesson < len(LESSONS) - 1 else "disabled")
        self._reset_start_button()

    def _render_key_caps(self, shortcut: str) -> None:
        """把 Win+Shift+S 拆成独立键帽，比一整段文本更容易看懂。"""
        for child in self.key_caps_frame.winfo_children():
            child.destroy()
        for index, key in enumerate(shortcut.split("+")):
            if index:
                tk.Label(
                    self.key_caps_frame,
                    text="+",
                    bg=COLORS["card"],
                    fg=COLORS["muted"],
                    font=("Bahnschrift", 14, "bold"),
                ).pack(side="left", padx=6)
            label = "⊞ Win" if key == "Win" else key
            tk.Label(
                self.key_caps_frame,
                text=label,
                bg="#241318",
                fg=COLORS["white"],
                font=("Bahnschrift", 12, "bold"),
                padx=13,
                pady=9,
                highlightbackground=COLORS["line_hot"],
                highlightthickness=1,
            ).pack(side="left")

    def _update_achievement(self) -> None:
        completed = len(self.progress["completed"])
        if completed == len(LESSONS):
            self.achievement_title.configure(text="快捷键新手毕业")
            self.achievement_detail.configure(text="全部 8 个快捷键已完成同步")
        else:
            self.achievement_title.configure(text="新手同步中")
            self.achievement_detail.configure(text=f"再掌握 {len(LESSONS) - completed} 个即可解锁毕业徽章")

    # ----- 课程控制 -------------------------------------------------------

    def _first_incomplete_lesson(self) -> int:
        for index, lesson in enumerate(LESSONS):
            if lesson.lesson_id not in self.progress["completed"]:
                return index
        return 0

    def select_lesson(self, index: int) -> None:
        self.current_lesson = index
        self._update_lesson()
        self._show_page("training")

    def previous_lesson(self) -> None:
        if self.current_lesson > 0:
            self.current_lesson -= 1
            self._update_lesson()

    def next_lesson(self) -> None:
        if self.current_lesson < len(LESSONS) - 1:
            self.current_lesson += 1
            self._update_lesson()

    def toggle_practice(self) -> None:
        self.listening = not self.listening
        if self.listening:
            lesson = LESSONS[self.current_lesson]
            self.start_button.configure(text=f"LINK ACTIVE  //  {lesson.shortcut.replace('+', ' + ')}")
            self.start_button.set_colors("#601820", "#7A2028")
            self.show_toast("同步监听已开启，可在任意窗口完成")
        else:
            self._reset_start_button()
            self.show_toast("训练已暂停")

    def _reset_start_button(self) -> None:
        lesson = LESSONS[self.current_lesson]
        mastered = lesson.lesson_id in self.progress["completed"]
        text = "再次同步  ·  巩固记忆" if mastered else "开始同步  ·  +10 XP"
        self.start_button.configure(text=text)
        self.start_button.set_colors(COLORS["red"], "#FF5B2B")

    def _complete_lesson(self) -> None:
        lesson = LESSONS[self.current_lesson]
        first_time = lesson.lesson_id not in self.progress["completed"]
        if first_time:
            self.progress["completed"].add(lesson.lesson_id)
            self.progress["points"] += 10
        self.progress["last_practice"] = date.today().isoformat()
        self.store.save(self.progress)
        self.listening = False

        # Win + D 可能把所有窗口暂时隐藏，因此完成后主动恢复并置顶。
        self.expand(activate=False)
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", False)
        self.root.attributes("-topmost", True)
        self._update_all()
        self._show_success(lesson, first_time)
        self._play_success_chime()
        self._shake_window()

    def continue_after_success(self) -> None:
        self.success_canvas.place_forget()
        if self.current_lesson < len(LESSONS) - 1:
            self.current_lesson += 1
        else:
            self.current_lesson = self._first_incomplete_lesson()
        self._update_all()
        self._show_page("training")

    # ----- 键盘事件轮询 ---------------------------------------------------

    def _poll_keyboard(self) -> None:
        """每 45ms 从线程安全队列取事件；所有 tkinter 操作都留在主线程。"""
        try:
            while True:
                shortcut = self.keyboard_queue.get_nowait()
                if shortcut == "__TOGGLE__":
                    self.collapse() if self.expanded else self.expand()
                elif shortcut == "__HOOK_ERROR__":
                    self.show_toast("全局按键监听启动失败，请重新打开应用")
                elif self.listening:
                    expected = LESSONS[self.current_lesson].shortcut
                    if shortcut.lower() == expected.lower():
                        self._complete_lesson()
                    elif "+" in shortcut:
                        self.show_toast(f"很接近！本关需要 {expected.replace('+', ' + ')}")
        except queue.Empty:
            pass
        finally:
            if self.root.winfo_exists():
                self.root.after(45, self._poll_keyboard)

    # ----- 声音、抖动和提示 -----------------------------------------------

    def _ensure_chime_file(self) -> Path:
        """用正弦波合成四音上行提示音，首次使用时生成 WAV 文件。"""
        if self.store.chime_path.exists():
            return self.store.chime_path
        self.store.folder.mkdir(parents=True, exist_ok=True)
        sample_rate = 44_100
        duration = 0.82
        frequencies = (523.25, 659.25, 783.99, 1046.50)
        starts = (0.00, 0.10, 0.20, 0.34)
        frames = bytearray()
        for index in range(int(sample_rate * duration)):
            current_time = index / sample_rate
            sample = 0.0
            for note, note_start in zip(frequencies, starts):
                local_time = current_time - note_start
                if local_time < 0:
                    continue
                envelope = min(1.0, local_time / 0.012) * math.exp(-4.8 * local_time)
                tone = math.sin(2 * math.pi * note * local_time)
                tone += 0.2 * math.sin(2 * math.pi * note * 2.01 * local_time)
                sample += envelope * tone * 0.23
            sample = max(-1.0, min(1.0, sample))
            frames.extend(struct.pack("<h", int(sample * 25_000)))
        with wave.open(str(self.store.chime_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(frames)
        return self.store.chime_path

    def _play_success_chime(self) -> None:
        try:
            path = self._ensure_chime_file()
            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
        except (OSError, RuntimeError):
            winsound.MessageBeep(winsound.MB_ICONASTERISK)

    def _shake_window(self) -> None:
        base_x, base_y = self.root.winfo_x(), self.root.winfo_y()
        offsets = (0, 12, -10, 9, -7, 6, -4, 3, -2, 1, 0)

        def apply_offset(index: int) -> None:
            if index >= len(offsets) or not self.root.winfo_exists():
                self.root.geometry(f"+{base_x}+{base_y}")
                return
            self.root.geometry(f"+{base_x + offsets[index]}+{base_y}")
            self.root.after(28, lambda: apply_offset(index + 1))

        apply_offset(0)

    def show_toast(self, message: str) -> None:
        self.toast_label.configure(text=message)
        self.toast_label.place(relx=0.5, y=78, anchor="n")
        self.toast_label.lift()
        if self.toast_after_id:
            self.root.after_cancel(self.toast_after_id)
        self.toast_after_id = self.root.after(2100, self.toast_label.place_forget)

    # ----- 悬浮、定位、拖动和退出 -----------------------------------------

    @staticmethod
    def _work_area() -> tuple[int, int, int, int]:
        """读取 Windows 工作区，避免窗口压到任务栏下面。"""
        rectangle = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rectangle), 0):
            return rectangle.left, rectangle.top, rectangle.right, rectangle.bottom
        return 0, 0, ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)

    def _position_expanded(self) -> None:
        left, top, right, bottom = self._work_area()
        x = right - WINDOW_WIDTH - 24
        y = top + max(14, (bottom - top - WINDOW_HEIGHT) // 2)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _position_bubble(self) -> None:
        left, top, right, bottom = self._work_area()
        x = right - BUBBLE_SIZE - 22
        y = bottom - BUBBLE_SIZE - 22
        self.root.geometry(f"{BUBBLE_SIZE}x{BUBBLE_SIZE}+{x}+{y}")

    def collapse(self) -> None:
        self.listening = False
        self.expanded = False
        self.success_canvas.place_forget()
        self.panel.pack_forget()
        self.bubble.pack(fill="both", expand=True)
        self._position_bubble()

    def expand(self, activate: bool = True) -> None:
        self.expanded = True
        self.bubble.pack_forget()
        self.panel.pack(fill="both", expand=True)
        self._position_expanded()
        self.root.deiconify()
        self.root.lift()
        if activate:
            self.root.focus_force()
        self._update_all()

    def _start_drag(self, event) -> None:
        self.drag_offset = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def _drag_window(self, event) -> None:
        x = event.x_root - self.drag_offset[0]
        y = event.y_root - self.drag_offset[1]
        self.root.geometry(f"+{x}+{y}")

    def close(self) -> None:
        self.keyboard_hook.stop()
        self.root.destroy()

    def run(self) -> None:
        self.panel.pack(fill="both", expand=True)
        self.root.mainloop()


# ---------------------------------------------------------------------------
# 7. 启动入口与无界面自检
# ---------------------------------------------------------------------------

def self_check() -> None:
    """供开发者在命令行快速验证课程数据是否完整。"""
    ids = [lesson.lesson_id for lesson in LESSONS]
    shortcuts = [lesson.shortcut for lesson in LESSONS]
    assert len(ids) == len(set(ids)), "课程 ID 不能重复"
    assert len(shortcuts) == len(set(shortcuts)), "快捷键不能重复"
    assert all(len(lesson.steps) == 3 for lesson in LESSONS), "每关必须恰好包含三个步骤"
    validate_catalog()
    print(
        f"QuickKey Python self-check passed: {len(LESSONS)} lessons, "
        f"{len(SHORTCUTS)} official catalog entries"
    )


def smoke_test() -> None:
    """创建真实窗口并自动走过三个页面、悬浮与展开，用于开发期回归测试。"""
    app = QuickKeyApp()
    failure: list[BaseException] = []

    def verify_ui() -> None:
        try:
            assert app.keyboard_hook.thread is not None
            assert app.keyboard_hook.thread.is_alive(), "键盘钩子线程没有运行"
            app._show_page("overview")
            app._refresh_overview()
            assert len(app.overview_inner.winfo_children()) == len(SHORTCUTS)
            app.select_lesson(3)
            assert app.lesson_title_label.cget("text") == LESSONS[3].title
            app._show_page("achievement")
            app.collapse()
            assert not app.expanded
            app.expand(activate=False)
            assert app.expanded
        except BaseException as error:  # 测试入口需要把 tkinter 回调错误传回主流程
            failure.append(error)
        finally:
            app.close()

    app.root.after(450, verify_ui)
    app.run()
    if failure:
        raise failure[0]
    print("QuickKey Python UI smoke-test passed: training, overview, achievement, bubble")


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        smoke_test()
    elif "--check" in sys.argv:
        self_check()
    else:
        QuickKeyApp().run()
