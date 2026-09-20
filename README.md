# 键游 · Win11 快捷键训练

一款面向 Windows 11 新手的桌面悬浮教学应用。它把常用快捷键拆成小关卡，通过真实的全局按键检测、积分、悦耳提示音、彩纸和窗口抖动，让练习像闯关一样有反馈。

界面采用暗色机甲驾驶舱风格，以明日香式炽红、橙色、黑灰和暖白为核心配色，加入 `02` 识别、HUD 编号、警戒线与切角面板。所有图形均为原创界面元素，不依赖外部图片素材。

## 直接体验

双击 `启动键游.cmd`。项目已经包含构建好的 `QuickKey.exe`；如果可执行文件不存在，启动脚本会使用 Windows 自带的 .NET Framework 编译器自动构建。

- 点击右上角 `—`，应用会缩成桌面右下角的悬浮球。
- 在任意软件中按 `Ctrl + Alt + K`，可以快速展开或收起。
- 点击“开始练习”后，在任意窗口按出本关快捷键即可过关。
- 点击底部“总览”可搜索和筛选 228 条微软官方 Windows 快捷键；危险操作会显示警告。
- 点击总览中的核心快捷键会直接跳转到对应的分步训练。
- 点击“成就”可查看毕业徽章进度、官方目录规模和全局呼出键。
- 每个快捷键首次掌握获得 `10 XP`；进度保存在 `%LOCALAPPDATA%\QuickKey\progress.dat`。
- 右键悬浮球可以打开或退出应用。

## 已内置的 8 个关卡

1. `Win + D` 显示桌面
2. `Win + E` 打开资源管理器
3. `Alt + Tab` 切换窗口
4. `Win + Shift + S` 区域截图
5. `Ctrl + Shift + Esc` 任务管理器
6. `Ctrl + C` 复制
7. `Win + I` 系统设置
8. `Win + A` 快捷设置

## 可选：开机自动悬浮

右键 `设置开机启动.ps1`，选择“使用 PowerShell 运行”。脚本只会在当前用户的启动文件夹创建一个快捷方式，不需要管理员权限。

## 重新构建

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

应用使用原生 WPF 和 Windows 低级键盘钩子，无第三方依赖，也不上传任何按键或学习数据。

WPF 版从 [`data/windows_shortcuts.tsv`](./data/windows_shortcuts.tsv) 读取官方目录。Python 数据有更新时，可运行 [`python版/export_catalog_tsv.py`](./python版/export_catalog_tsv.py) 同步到原生版。

## Python 源码版

项目同时提供了功能相同的纯 Python 版本，并新增“快捷键总览”页面。总览收录微软官方 Windows 11 主目录中的 228 条记录，支持搜索、分类筛选和风险提示。它只使用 Python 标准库，界面源码位于 [`python版/quickkey.pyw`](./python版/quickkey.pyw)，目录数据位于 [`python版/shortcuts_catalog.py`](./python版/shortcuts_catalog.py)，双击 [`python版/启动Python版.cmd`](./python版/启动Python版.cmd) 即可体验。
