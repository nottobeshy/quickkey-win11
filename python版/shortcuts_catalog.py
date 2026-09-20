# -*- coding: utf-8 -*-
"""Windows 11 官方系统快捷键目录。

数据范围
--------
本文件整理自 Microsoft Support 的“Windows 的键盘快捷方式”页面，覆盖该页
列出的 10 个主类别。动作说明采用简短中文转述，便于在桌面应用里检索和阅读。

这里特意把目录数据从主界面代码中拆开：以后微软增加快捷键时，只需更新这个
文件，不必改动 tkinter 页面或全局键盘钩子。
"""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_URL = (
    "https://support.microsoft.com/zh-cn/windows/"
    "windows-%E7%9A%84%E9%94%AE%E7%9B%98%E5%BF%AB%E6%8D%B7%E6%96%B9%E5%BC%8F-"
    "dcc61a57-8ff0-cffe-9796-cb9706c75eec"
)
SOURCE_CHECKED = "2026-07-16"


@dataclass(frozen=True)
class ShortcutInfo:
    """一条目录记录。

    risk:
        normal  - 普通快捷键。
        context - 只有在特定窗口、硬件或操作状态下才生效。
        caution - 会关闭、锁定、删除、提权或显著改变当前工作状态。
    lesson_id:
        非空时，点击总览项目可以跳转到已有的分步训练关卡。
    """

    keys: str
    action: str
    category: str
    risk: str = "normal"
    lesson_id: str | None = None


S = ShortcutInfo

CATEGORIES = (
    "全部",
    "Copilot 键",
    "文本编辑",
    "桌面与常规",
    "Windows 键",
    "命令提示符",
    "对话框",
    "文件资源管理器",
    "虚拟桌面",
    "任务栏",
    "设置",
)


# 注意：同一组合键可能在不同上下文中执行不同操作，因此目录允许跨类别重复。
SHORTCUTS: tuple[ShortcutInfo, ...] = (
    # ------------------------------------------------------------------
    # Copilot 键
    # ------------------------------------------------------------------
    S("Copilot 键", "打开或关闭 Windows 搜索；可在设置中自定义", "Copilot 键", "context"),

    # ------------------------------------------------------------------
    # 文本编辑
    # ------------------------------------------------------------------
    S("Backspace", "删除光标左侧的字符", "文本编辑"),
    S("Ctrl + A", "选择全部文本", "文本编辑"),
    S("Ctrl + B", "为选中文本应用粗体", "文本编辑", "context"),
    S("Ctrl + Backspace", "删除光标左侧的整个单词", "文本编辑"),
    S("Ctrl + C / Ctrl + Insert", "复制选中的文本", "文本编辑", "normal", "copy"),
    S("Ctrl + Delete", "删除光标右侧的整个单词", "文本编辑"),
    S("Ctrl + Down", "移动到下一段开头", "文本编辑"),
    S("Ctrl + End", "移动到文档结尾", "文本编辑"),
    S("Ctrl + F", "查找文本", "文本编辑"),
    S("Ctrl + H", "查找并替换文本", "文本编辑", "context"),
    S("Ctrl + Home", "移动到文档开头", "文本编辑"),
    S("Ctrl + I", "为选中文本应用斜体", "文本编辑", "context"),
    S("Ctrl + Left", "移动到上一个单词开头", "文本编辑"),
    S("Ctrl + Right", "移动到下一个单词开头", "文本编辑"),
    S("Ctrl + Shift + V", "粘贴为纯文本", "文本编辑", "context"),
    S("Ctrl + U", "为选中文本添加下划线", "文本编辑", "context"),
    S("Ctrl + Up", "移动到上一段开头", "文本编辑"),
    S("Ctrl + V / Shift + Insert", "粘贴剪贴板中的内容", "文本编辑"),
    S("Ctrl + X", "剪切选中的文本", "文本编辑"),
    S("Ctrl + Y", "重做上一次撤销的输入", "文本编辑", "context"),
    S("Ctrl + Z", "撤销上一次输入", "文本编辑"),
    S("Delete", "删除光标右侧的字符", "文本编辑"),
    S("Down", "将光标移动到下一行", "文本编辑"),
    S("End", "将光标移动到当前行末尾", "文本编辑"),
    S("Home", "将光标移动到当前行开头", "文本编辑"),
    S("Left", "向左移动一个字符", "文本编辑"),
    S("Page Down", "向后移动一页", "文本编辑"),
    S("Page Up", "向前移动一页", "文本编辑"),
    S("Right", "向右移动一个字符", "文本编辑"),
    S("Ctrl + Shift + Down", "从光标向后选择一个段落", "文本编辑"),
    S("Ctrl + Shift + End", "选择到文档结尾", "文本编辑"),
    S("Ctrl + Shift + Home", "选择到文档开头", "文本编辑"),
    S("Ctrl + Shift + Left", "向左按单词选择", "文本编辑"),
    S("Ctrl + Shift + Right", "向右按单词选择", "文本编辑"),
    S("Ctrl + Shift + Up", "从光标向前选择一个段落", "文本编辑"),
    S("Shift + Down", "向下选择一行", "文本编辑"),
    S("Shift + End", "选择到当前行末尾", "文本编辑"),
    S("Shift + Home", "选择到当前行开头", "文本编辑"),
    S("Shift + Left", "向左选择一个字符", "文本编辑"),
    S("Shift + Page Down", "向后选择一页文本", "文本编辑"),
    S("Shift + Page Up", "向前选择一页文本", "文本编辑"),
    S("Shift + Right", "向右选择一个字符", "文本编辑"),
    S("Shift + Up", "向上选择一行", "文本编辑"),
    S("Tab", "将光标缩进一个制表位", "文本编辑", "context"),
    S("Up", "将光标移动到上一行", "文本编辑"),

    # ------------------------------------------------------------------
    # 桌面与其他常规快捷键
    # ------------------------------------------------------------------
    S("Alt + A", "聚焦建议操作菜单的第一个图标", "桌面与常规", "context"),
    S("Alt + Esc", "按打开顺序循环浏览窗口", "桌面与常规"),
    S("Alt + F4", "关闭活动窗口；桌面上会显示关机提示", "桌面与常规", "caution"),
    S("Alt + F8", "在登录屏幕显示密码", "桌面与常规", "context"),
    S("Alt + Left", "返回上一位置", "桌面与常规", "context"),
    S("Alt + Page Down", "向下移动一个屏幕", "桌面与常规", "context"),
    S("Alt + Page Up", "向上移动一个屏幕", "桌面与常规", "context"),
    S("Alt + PrtScn", "把活动窗口截图复制到剪贴板", "桌面与常规"),
    S("Alt + Right", "前进到下一位置", "桌面与常规", "context"),
    S("Alt + Shift + 箭头", "移动开始菜单中聚焦的组或磁贴", "桌面与常规", "context"),
    S("Alt + Space", "打开活动窗口的系统菜单", "桌面与常规"),
    S("Alt + Tab", "在打开的窗口之间切换", "桌面与常规", "normal", "switch"),
    S("Alt + 带下划线字母", "执行菜单中对应的命令", "桌面与常规", "context"),
    S("Ctrl + A", "选择当前窗口中的全部项目", "桌面与常规", "context"),
    S("Ctrl + Alt + Delete", "打开 Windows 安全屏幕", "桌面与常规", "caution"),
    S("Ctrl + Alt + Tab", "固定显示窗口切换器，再用方向键选择", "桌面与常规"),
    S("Ctrl + Esc", "打开开始菜单", "桌面与常规"),
    S("Ctrl + F4", "关闭支持多文档应用中的当前文档", "桌面与常规", "caution"),
    S("Ctrl + F5 / Ctrl + R", "刷新当前窗口", "桌面与常规", "context"),
    S("Ctrl + Shift", "在可用键盘布局之间切换", "桌面与常规", "context"),
    S("Ctrl + Shift + 箭头", "在开始菜单中移动磁贴并创建文件夹", "桌面与常规", "context"),
    S("Ctrl + Shift + Esc", "打开任务管理器", "桌面与常规", "normal", "taskmanager"),
    S("Ctrl + Space", "启用或禁用中文输入法", "桌面与常规", "context"),
    S("Ctrl + Y", "重做上一次撤销的操作", "桌面与常规", "context"),
    S("Ctrl + Z", "撤销上一个操作", "桌面与常规", "context"),
    S("Esc", "停止当前任务或关闭对话框", "桌面与常规"),
    S("F5", "刷新活动窗口", "桌面与常规"),
    S("F6", "循环浏览窗口或桌面的元素", "桌面与常规"),
    S("F10", "激活活动窗口的菜单栏", "桌面与常规", "context"),
    S("PrtScn", "打开区域截图并复制到剪贴板", "桌面与常规", "context"),

    # ------------------------------------------------------------------
    # Windows 键组合
    # ------------------------------------------------------------------
    S("Win", "打开或关闭开始菜单", "Windows 键"),
    S("Win + A", "打开快速设置", "Windows 键", "normal", "quicksettings"),
    S("Win + Shift + A", "聚焦可用的 Windows 提示", "Windows 键", "context"),
    S("Win + Alt + B", "打开或关闭 HDR", "Windows 键", "context"),
    S("Win + C", "打开或关闭 Windows 搜索", "Windows 键"),
    S("Win + Alt + D", "显示或隐藏桌面日期和时间", "Windows 键"),
    S("Win + Alt + Down", "把活动窗口贴靠到屏幕下半部", "Windows 键"),
    S("Win + Alt + H", "语音输入开启时聚焦其键盘", "Windows 键", "context"),
    S("Win + Alt + K", "在支持的应用中静音或取消静音麦克风", "Windows 键", "context"),
    S("Win + Alt + Up", "把活动窗口贴靠到屏幕上半部", "Windows 键"),
    S("Win + Comma", "按住时临时预览桌面", "Windows 键"),
    S("Win + Ctrl + C", "打开或关闭颜色筛选器", "Windows 键", "context"),
    S("Win + Ctrl + Enter", "打开讲述人", "Windows 键", "context"),
    S("Win + Ctrl + F", "搜索网络中的设备", "Windows 键", "context"),
    S("Win + Ctrl + Q", "打开快速助手", "Windows 键"),
    S("Win + Ctrl + Shift + B", "从黑屏状态唤醒显示设备", "Windows 键", "caution"),
    S("Win + Ctrl + Space", "切回先前选定的输入法", "Windows 键", "context"),
    S("Win + Ctrl + V", "打开快速设置的声音输出页面", "Windows 键"),
    S("Win + D", "显示或隐藏桌面", "Windows 键", "normal", "desktop"),
    S("Win + Down", "最小化或还原活动窗口", "Windows 键"),
    S("Win + E", "打开文件资源管理器", "Windows 键", "normal", "explorer"),
    S("Win + Esc", "关闭放大镜", "Windows 键", "context"),
    S("Win + F", "打开反馈中心", "Windows 键"),
    S("Win + /", "启动输入法重新转换", "Windows 键", "context"),
    S("Win + G", "打开 Game Bar", "Windows 键", "context"),
    S("Win + H", "打开语音输入", "Windows 键"),
    S("Win + Home", "最小化除活动窗口外的所有窗口", "Windows 键"),
    S("Win + I", "打开 Windows 设置", "Windows 键", "normal", "settings"),
    S("Win + J", "在支持的设备上打开召回", "Windows 键", "context"),
    S("Win + K", "打开投放面板以连接显示器", "Windows 键", "context"),
    S("Win + L", "锁定计算机", "Windows 键", "caution"),
    S("Win + Left", "把窗口贴靠到屏幕左侧", "Windows 键"),
    S("Win + M", "最小化所有窗口", "Windows 键"),
    S("Win + Minus", "缩小放大镜", "Windows 键", "context"),
    S("Win + N", "打开通知中心和日历", "Windows 键"),
    S("Win + O", "锁定设备方向", "Windows 键", "context"),
    S("Win + P", "选择投影显示模式", "Windows 键", "context"),
    S("Win + Pause", "打开设置中的系统关于页面", "Windows 键"),
    S("Win + Period / Win + Semicolon", "打开表情符号面板", "Windows 键"),
    S("Win + Plus", "打开放大镜并放大", "Windows 键", "context"),
    S("Win + PrtScn", "截取全屏并保存到图片/屏幕截图", "Windows 键"),
    S("Win + Q", "打开 Windows 搜索", "Windows 键"),
    S("Win + R", "打开运行对话框", "Windows 键"),
    S("Win + Right", "把窗口贴靠到屏幕右侧", "Windows 键"),
    S("Win + S", "打开 Windows 搜索", "Windows 键"),
    S("Win + Shift + Down", "还原已贴靠或最大化的窗口", "Windows 键"),
    S("Win + Shift + Enter", "把活动 UWP 应用切换为全屏", "Windows 键", "context"),
    S("Win + Shift + Left", "把活动窗口移到左侧显示器", "Windows 键", "context"),
    S("Win + Shift + M", "还原已最小化的窗口", "Windows 键"),
    S("Win + Shift + R", "选择屏幕区域并用截图工具录制", "Windows 键"),
    S("Win + Shift + Right", "把活动窗口移到右侧显示器", "Windows 键", "context"),
    S("Win + Shift + S", "选择区域并把截图复制到剪贴板", "Windows 键", "normal", "snip"),
    S("Win + Shift + Space", "向后切换输入语言和键盘布局", "Windows 键", "context"),
    S("Win + Shift + Up", "垂直拉伸活动窗口", "Windows 键"),
    S("Win + Shift + V", "循环浏览通知", "Windows 键"),
    S("Win + Space", "向前切换输入语言和键盘布局", "Windows 键", "context"),
    S("Win + Tab", "打开任务视图", "Windows 键"),
    S("Win + U", "打开辅助功能设置", "Windows 键"),
    S("Win + Up", "最大化活动窗口", "Windows 键"),
    S("Win + V", "打开剪贴板历史记录", "Windows 键", "context"),
    S("Win + W", "打开小组件", "Windows 键"),
    S("Win + X", "打开快速链接菜单", "Windows 键"),
    S("Win + Y", "在混合现实与桌面间切换输入", "Windows 键", "context"),
    S("Win + Z", "打开贴靠布局", "Windows 键"),

    # ------------------------------------------------------------------
    # 命令提示符
    # ------------------------------------------------------------------
    S("Ctrl + C / Ctrl + Insert", "复制选中的命令行文本", "命令提示符", "context"),
    S("Ctrl + V / Shift + Insert", "粘贴命令行文本", "命令提示符", "context"),
    S("Ctrl + M", "进入标记模式", "命令提示符", "context"),
    S("Alt + 选择键", "开始块模式选择", "命令提示符", "context"),
    S("箭头键", "按方向移动命令行光标", "命令提示符", "context"),
    S("Page Up", "向上移动一个输出页面", "命令提示符", "context"),
    S("Page Down", "向下移动一个输出页面", "命令提示符", "context"),
    S("Ctrl + Home（标记模式）", "移动到缓冲区开头", "命令提示符", "context"),
    S("Ctrl + End（标记模式）", "移动到缓冲区结尾", "命令提示符", "context"),
    S("Ctrl + Up", "在输出历史中上移一行", "命令提示符", "context"),
    S("Ctrl + Down", "在输出历史中下移一行", "命令提示符", "context"),
    S("Ctrl + Home（历史导航）", "移到缓冲区顶部或删除光标左侧字符", "命令提示符", "context"),
    S("Ctrl + End（历史导航）", "移到命令行或删除光标右侧字符", "命令提示符", "context"),

    # ------------------------------------------------------------------
    # 对话框
    # ------------------------------------------------------------------
    S("F4", "显示活动列表中的项目", "对话框", "context"),
    S("Ctrl + Tab", "向前切换选项卡", "对话框", "context"),
    S("Ctrl + Shift + Tab", "向后切换选项卡", "对话框", "context"),
    S("Ctrl + 数字 1-9", "跳到指定编号的选项卡", "对话框", "context"),
    S("Tab", "在选项间向前移动", "对话框", "context"),
    S("Shift + Tab", "在选项间向后移动", "对话框", "context"),
    S("Alt + 带下划线字母", "执行对应命令或选择对应选项", "对话框", "context"),
    S("Space", "选择或清除当前复选框", "对话框", "context"),
    S("Backspace", "在打开或另存为对话框中返回上级文件夹", "对话框", "context"),
    S("箭头键", "在选项按钮组中选择按钮", "对话框", "context"),

    # ------------------------------------------------------------------
    # 文件资源管理器
    # ------------------------------------------------------------------
    S("Alt + D", "选择地址栏", "文件资源管理器"),
    S("Alt + Enter", "显示所选项目的属性", "文件资源管理器"),
    S("Alt + Left / Backspace", "返回上一个文件夹", "文件资源管理器"),
    S("Alt + 拖动文件", "在放下位置创建原文件的快捷方式", "文件资源管理器", "context"),
    S("Alt + P", "显示或隐藏预览窗格", "文件资源管理器"),
    S("Alt + Right", "前往下一个文件夹", "文件资源管理器"),
    S("Alt + Shift + P", "显示或隐藏详细信息窗格", "文件资源管理器"),
    S("Alt + Up", "在文件夹路径中向上一级", "文件资源管理器"),
    S("Ctrl + 箭头后按 Space", "选择多个不连续项目", "文件资源管理器", "context"),
    S("Ctrl + D / Delete", "把所选项目移到回收站", "文件资源管理器", "caution"),
    S("Ctrl + E / Ctrl + F", "选择搜索框", "文件资源管理器"),
    S("Ctrl + L", "聚焦地址栏", "文件资源管理器"),
    S("Ctrl + 拖动文件", "在放下位置复制文件", "文件资源管理器", "context"),
    S("Ctrl + 鼠标滚轮", "更改文件和文件夹图标大小", "文件资源管理器", "context"),
    S("Ctrl + N", "打开新的资源管理器窗口", "文件资源管理器"),
    S("Ctrl + 数字 1-9", "切换到指定编号的选项卡", "文件资源管理器", "context"),
    S("Ctrl + 小键盘加号", "调整所有列宽以适应文本", "文件资源管理器", "context"),
    S("Ctrl + Shift + E", "展开导航窗格中的全部文件夹树", "文件资源管理器"),
    S("Ctrl + Shift + N", "新建文件夹", "文件资源管理器"),
    S("Ctrl + Shift + 数字 1-9", "切换资源管理器视图样式", "文件资源管理器", "context"),
    S("Ctrl + Shift + Tab", "切换到上一个选项卡", "文件资源管理器"),
    S("Ctrl + T", "打开并切换到新选项卡", "文件资源管理器"),
    S("Ctrl + W", "关闭当前选项卡或窗口", "文件资源管理器", "caution"),
    S("Ctrl + Tab", "切换到下一个选项卡", "文件资源管理器"),
    S("End", "滚动到活动窗口底部", "文件资源管理器"),
    S("F2", "重命名所选项目", "文件资源管理器"),
    S("F3", "搜索文件或文件夹", "文件资源管理器"),
    S("F4", "选择地址栏并更改路径", "文件资源管理器"),
    S("F5", "刷新窗口", "文件资源管理器"),
    S("F6", "循环浏览窗口中的元素", "文件资源管理器"),
    S("F11", "最大化或还原资源管理器窗口", "文件资源管理器"),
    S("Home", "滚动到活动窗口顶部", "文件资源管理器"),
    S("Left", "折叠目录树选择项或选择其父文件夹", "文件资源管理器", "context"),
    S("Right", "展开目录树选择项或选择首个子文件夹", "文件资源管理器", "context"),
    S("Shift + 箭头", "选择多个项目", "文件资源管理器", "context"),
    S("Shift + Delete", "永久删除所选项目，不经过回收站", "文件资源管理器", "caution"),
    S("Shift + F10", "显示所选项目的上下文菜单", "文件资源管理器"),
    S("Shift + 拖动文件", "把文件移动到放下位置", "文件资源管理器", "caution"),
    S("Shift + 鼠标右键", "显示更多选项上下文菜单", "文件资源管理器", "context"),

    # ------------------------------------------------------------------
    # 多个桌面
    # ------------------------------------------------------------------
    S("Win + Tab", "打开任务视图", "虚拟桌面"),
    S("Win + Ctrl + D", "创建新的虚拟桌面", "虚拟桌面"),
    S("Win + Ctrl + Right", "切换到右侧虚拟桌面", "虚拟桌面", "context"),
    S("Win + Ctrl + Left", "切换到左侧虚拟桌面", "虚拟桌面", "context"),
    S("Win + Ctrl + F4", "关闭当前虚拟桌面", "虚拟桌面", "caution"),

    # ------------------------------------------------------------------
    # 任务栏
    # ------------------------------------------------------------------
    S("Alt + Shift + 箭头", "移动当前聚焦的任务栏应用图标", "任务栏", "context"),
    S("Ctrl + 单击分组应用", "在同一应用的窗口组中循环切换", "任务栏", "context"),
    S("Ctrl + Shift + 单击应用", "以管理员身份打开任务栏应用", "任务栏", "caution"),
    S("Shift + 右键单击应用", "显示应用窗口菜单", "任务栏", "context"),
    S("Shift + 右键单击分组按钮", "显示应用组窗口菜单", "任务栏", "context"),
    S("Shift + 单击应用", "打开任务栏应用的新实例", "任务栏", "context"),
    S("Win + Alt + Enter（任务栏项聚焦）", "打开任务栏设置", "任务栏", "context"),
    S("Win + Alt + 数字 0-9", "打开对应固定应用的跳转列表", "任务栏", "context"),
    S("Win + B", "聚焦任务栏通知区域的第一个图标", "任务栏"),
    S("Win + Ctrl + 数字 0-9", "切换到对应应用最后活动的窗口", "任务栏", "context"),
    S("Win + Ctrl + Shift + 数字 0-9", "以管理员身份打开对应应用的新实例", "任务栏", "caution"),
    S("Win + 数字 0-9", "打开或切换到对应位置的固定应用", "任务栏", "context"),
    S("Win + Shift + 数字 0-9", "打开对应固定应用的新实例", "任务栏", "context"),
    S("Win + T", "向前循环浏览任务栏应用", "任务栏"),
    S("Win + Shift + T", "向后循环浏览任务栏应用", "任务栏"),

    # ------------------------------------------------------------------
    # 设置应用
    # ------------------------------------------------------------------
    S("箭头键", "在当前区域移动焦点并滚动页面", "设置", "context"),
    S("Backspace", "返回上一个设置页面", "设置", "context"),
    S("Enter / Space", "选择当前聚焦的设置项", "设置", "context"),
    S("Shift + Tab", "向后浏览设置区域", "设置", "context"),
    S("Tab", "向前浏览设置区域", "设置", "context"),
    S("Win + I", "打开 Windows 设置", "设置", "normal", "settings"),
)


def validate_catalog() -> None:
    """开发期数据检查：类别合法、字段非空，并确保目录规模没有意外缩水。"""
    valid_categories = set(CATEGORIES) - {"全部"}
    assert len(SHORTCUTS) >= 190, "Windows 快捷键目录条目异常减少"
    assert all(item.keys and item.action for item in SHORTCUTS)
    assert all(item.category in valid_categories for item in SHORTCUTS)
    assert all(item.risk in {"normal", "context", "caution"} for item in SHORTCUTS)


if __name__ == "__main__":
    validate_catalog()
    print(f"Windows shortcut catalog: {len(SHORTCUTS)} entries, {len(CATEGORIES) - 1} categories")

