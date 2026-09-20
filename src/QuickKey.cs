using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Media;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Markup;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Threading;

namespace QuickKey
{
    internal sealed class Lesson
    {
        public string Id;
        public string Title;
        public string Subtitle;
        public string Shortcut;
        public string Tip;
        public string[] Steps;
    }

    internal sealed class ShortcutInfo
    {
        public string Category;
        public string Keys;
        public string Action;
        public string Risk;
        public string LessonId;
    }

    internal sealed class ProgressData
    {
        public int Points;
        public int Streak;
        public DateTime LastPractice;
        public HashSet<string> Completed = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    }

    internal static class ProgressStore
    {
        private static readonly string Folder = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "QuickKey");
        private static readonly string FilePath = Path.Combine(Folder, "progress.dat");

        public static ProgressData Load()
        {
            ProgressData data = new ProgressData();
            data.Streak = 1;
            if (File.Exists(FilePath))
            {
                try
                {
                    string[] lines = File.ReadAllLines(FilePath, Encoding.UTF8);
                    foreach (string line in lines)
                    {
                        int equals = line.IndexOf('=');
                        if (equals <= 0) continue;
                        string key = line.Substring(0, equals).Trim();
                        string value = line.Substring(equals + 1).Trim();
                        int number;
                        DateTime date;
                        if (key == "points" && int.TryParse(value, out number)) data.Points = number;
                        if (key == "streak" && int.TryParse(value, out number)) data.Streak = Math.Max(1, number);
                        if (key == "lastPractice" && DateTime.TryParseExact(value, "yyyy-MM-dd", CultureInfo.InvariantCulture,
                            DateTimeStyles.None, out date)) data.LastPractice = date;
                        if (key == "completed")
                        {
                            string[] ids = value.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);
                            foreach (string id in ids) data.Completed.Add(id.Trim());
                        }
                    }
                }
                catch
                {
                    data = new ProgressData();
                    data.Streak = 1;
                }
            }

            DateTime today = DateTime.Today;
            if (data.LastPractice == DateTime.MinValue)
            {
                data.Streak = 1;
            }
            else if (data.LastPractice.Date == today.AddDays(-1))
            {
                data.Streak = Math.Max(1, data.Streak + 1);
            }
            else if (data.LastPractice.Date < today.AddDays(-1))
            {
                data.Streak = 1;
            }
            return data;
        }

        public static void Save(ProgressData data)
        {
            try
            {
                Directory.CreateDirectory(Folder);
                string[] lines =
                {
                    "points=" + data.Points.ToString(CultureInfo.InvariantCulture),
                    "streak=" + data.Streak.ToString(CultureInfo.InvariantCulture),
                    "lastPractice=" + data.LastPractice.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture),
                    "completed=" + string.Join(",", data.Completed)
                };
                File.WriteAllLines(FilePath, lines, new UTF8Encoding(false));
            }
            catch
            {
                // Progress persistence should never interrupt a lesson.
            }
        }
    }

    internal static class KeyboardHook
    {
        private const int WhKeyboardLl = 13;
        private const int WmKeyDown = 0x0100;
        private const int WmKeyUp = 0x0101;
        private const int WmSysKeyDown = 0x0104;
        private const int WmSysKeyUp = 0x0105;

        private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);
        private static readonly LowLevelKeyboardProc Proc = HookCallback;
        private static readonly ConcurrentQueue<string> Shortcuts = new ConcurrentQueue<string>();
        private static readonly HashSet<int> DownKeys = new HashSet<int>();
        private static IntPtr hookId = IntPtr.Zero;

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn, IntPtr hMod, uint threadId);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool UnhookWindowsHookEx(IntPtr hhk);

        [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern IntPtr GetModuleHandle(string moduleName);

        [DllImport("user32.dll")]
        private static extern short GetAsyncKeyState(int virtualKeyCode);

        public static bool Start()
        {
            if (hookId != IntPtr.Zero) return true;
            hookId = SetWindowsHookEx(WhKeyboardLl, Proc, GetModuleHandle(null), 0);
            return hookId != IntPtr.Zero;
        }

        public static void Stop()
        {
            if (hookId == IntPtr.Zero) return;
            UnhookWindowsHookEx(hookId);
            hookId = IntPtr.Zero;
            DownKeys.Clear();
        }

        public static bool TryGetShortcut(out string shortcut)
        {
            return Shortcuts.TryDequeue(out shortcut);
        }

        private static bool IsDown(int key)
        {
            return (GetAsyncKeyState(key) & 0x8000) != 0;
        }

        private static bool IsModifier(int vk)
        {
            return vk == 0x10 || vk == 0x11 || vk == 0x12 || vk == 0x5B || vk == 0x5C ||
                   vk == 0xA0 || vk == 0xA1 || vk == 0xA2 || vk == 0xA3 || vk == 0xA4 || vk == 0xA5;
        }

        private static string KeyName(int vk)
        {
            if (vk >= 0x41 && vk <= 0x5A) return ((char)vk).ToString();
            if (vk >= 0x30 && vk <= 0x39) return ((char)vk).ToString();
            if (vk >= 0x70 && vk <= 0x87) return "F" + (vk - 0x6F).ToString(CultureInfo.InvariantCulture);
            switch (vk)
            {
                case 0x09: return "Tab";
                case 0x1B: return "Esc";
                case 0x20: return "Space";
                case 0x0D: return "Enter";
                case 0x08: return "Backspace";
                case 0x25: return "Left";
                case 0x26: return "Up";
                case 0x27: return "Right";
                case 0x28: return "Down";
                case 0x2E: return "Delete";
                default: return null;
            }
        }

        private static string BuildShortcut(int vk)
        {
            string key = KeyName(vk);
            if (key == null) return null;
            List<string> parts = new List<string>();
            if (IsDown(0x11) || IsDown(0xA2) || IsDown(0xA3)) parts.Add("Ctrl");
            if (IsDown(0x12) || IsDown(0xA4) || IsDown(0xA5)) parts.Add("Alt");
            if (IsDown(0x5B) || IsDown(0x5C)) parts.Add("Win");
            if (IsDown(0x10) || IsDown(0xA0) || IsDown(0xA1)) parts.Add("Shift");
            parts.Add(key);
            return string.Join("+", parts.ToArray());
        }

        private static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0)
            {
                int message = wParam.ToInt32();
                int vk = Marshal.ReadInt32(lParam);
                if (message == WmKeyUp || message == WmSysKeyUp)
                {
                    DownKeys.Remove(vk);
                }
                else if (message == WmKeyDown || message == WmSysKeyDown)
                {
                    bool firstPress = DownKeys.Add(vk);
                    if (firstPress && !IsModifier(vk))
                    {
                        string shortcut = BuildShortcut(vk);
                        if (!string.IsNullOrEmpty(shortcut))
                        {
                            if (shortcut == "Ctrl+Alt+K")
                            {
                                Shortcuts.Enqueue("__TOGGLE__");
                                return new IntPtr(1);
                            }
                            Shortcuts.Enqueue(shortcut);
                        }
                    }
                }
            }
            return CallNextHookEx(hookId, nCode, wParam, lParam);
        }
    }

    internal static class ChimePlayer
    {
        private static MemoryStream chimeStream;
        private static SoundPlayer player;

        public static void PlaySuccess()
        {
            try
            {
                if (player == null)
                {
                    chimeStream = BuildChime();
                    player = new SoundPlayer(chimeStream);
                    player.Load();
                }
                chimeStream.Position = 0;
                player.Play();
            }
            catch
            {
                SystemSounds.Asterisk.Play();
            }
        }

        private static MemoryStream BuildChime()
        {
            const int sampleRate = 44100;
            const double duration = 0.82;
            int sampleCount = (int)(sampleRate * duration);
            MemoryStream stream = new MemoryStream();
            BinaryWriter writer = new BinaryWriter(stream, Encoding.ASCII);
            int dataSize = sampleCount * 2;

            writer.Write(Encoding.ASCII.GetBytes("RIFF"));
            writer.Write(36 + dataSize);
            writer.Write(Encoding.ASCII.GetBytes("WAVE"));
            writer.Write(Encoding.ASCII.GetBytes("fmt "));
            writer.Write(16);
            writer.Write((short)1);
            writer.Write((short)1);
            writer.Write(sampleRate);
            writer.Write(sampleRate * 2);
            writer.Write((short)2);
            writer.Write((short)16);
            writer.Write(Encoding.ASCII.GetBytes("data"));
            writer.Write(dataSize);

            double[] frequencies = { 523.25, 659.25, 783.99, 1046.50 };
            double[] starts = { 0.00, 0.10, 0.20, 0.34 };
            for (int i = 0; i < sampleCount; i++)
            {
                double t = (double)i / sampleRate;
                double sample = 0;
                for (int n = 0; n < frequencies.Length; n++)
                {
                    double local = t - starts[n];
                    if (local < 0) continue;
                    double envelope = Math.Min(1.0, local / 0.012) * Math.Exp(-4.8 * local);
                    double tone = Math.Sin(2 * Math.PI * frequencies[n] * local);
                    tone += 0.20 * Math.Sin(2 * Math.PI * frequencies[n] * 2.01 * local);
                    tone += 0.08 * Math.Sin(2 * Math.PI * frequencies[n] * 3.98 * local);
                    sample += envelope * tone * (n == 3 ? 0.32 : 0.24);
                }
                double fade = Math.Min(1.0, Math.Min(t / 0.008, (duration - t) / 0.03));
                sample = Math.Max(-1.0, Math.Min(1.0, sample * fade));
                writer.Write((short)(sample * short.MaxValue * 0.82));
            }
            writer.Flush();
            stream.Position = 0;
            return stream;
        }
    }

    internal sealed class QuickKeyApplication
    {
        private readonly Window window;
        private readonly Grid bubbleView;
        private readonly Border appShell;
        private readonly Button bubbleButton;
        private readonly Button startButton;
        private readonly Button previousButton;
        private readonly Button nextButton;
        private readonly Grid successOverlay;
        private readonly Canvas confettiCanvas;
        private readonly Border toast;
        private readonly TextBlock toastText;
        private readonly TextBlock lessonNumberText;
        private readonly TextBlock lessonTitle;
        private readonly TextBlock lessonSubtitle;
        private readonly TextBlock tipText;
        private readonly TextBlock stepOne;
        private readonly TextBlock stepTwo;
        private readonly TextBlock stepThree;
        private readonly TextBlock pointsText;
        private readonly TextBlock streakText;
        private readonly TextBlock levelText;
        private readonly TextBlock progressCount;
        private readonly TextBlock bubblePoints;
        private readonly TextBlock masteredBadge;
        private readonly TextBlock successText;
        private readonly TextBlock rewardText;
        private readonly WrapPanel keyCaps;
        private readonly Border progressFill;
        private readonly Grid trainingView;
        private readonly Grid overviewView;
        private readonly Grid achievementView;
        private readonly TextBox overviewSearchBox;
        private readonly ComboBox categoryCombo;
        private readonly StackPanel overviewList;
        private readonly TextBlock overviewSummary;
        private readonly Border overviewProgressFill;
        private readonly TextBlock achievementTitle;
        private readonly TextBlock achievementDetail;
        private readonly TextBlock achievementCatalog;
        private readonly Button learnNav;
        private readonly Button libraryNav;
        private readonly Button awardNav;
        private readonly DispatcherTimer keyboardTimer;
        private readonly DispatcherTimer toastTimer;
        private readonly List<Lesson> lessons;
        private readonly List<ShortcutInfo> catalog;
        private readonly ProgressData progress;
        private readonly Random random = new Random();
        private int lessonIndex;
        private bool listening;
        private bool expanded = true;
        private string currentPage = "training";
        private DateTime lastWrongHint = DateTime.MinValue;

        public QuickKeyApplication(Window mainWindow)
        {
            window = mainWindow;
            bubbleView = Find<Grid>("BubbleView");
            appShell = Find<Border>("AppShell");
            bubbleButton = Find<Button>("BubbleButton");
            startButton = Find<Button>("StartButton");
            previousButton = Find<Button>("PreviousButton");
            nextButton = Find<Button>("NextButton");
            successOverlay = Find<Grid>("SuccessOverlay");
            confettiCanvas = Find<Canvas>("ConfettiCanvas");
            toast = Find<Border>("Toast");
            toastText = Find<TextBlock>("ToastText");
            lessonNumberText = Find<TextBlock>("LessonNumberText");
            lessonTitle = Find<TextBlock>("LessonTitle");
            lessonSubtitle = Find<TextBlock>("LessonSubtitle");
            tipText = Find<TextBlock>("TipText");
            stepOne = Find<TextBlock>("StepOne");
            stepTwo = Find<TextBlock>("StepTwo");
            stepThree = Find<TextBlock>("StepThree");
            pointsText = Find<TextBlock>("PointsText");
            streakText = Find<TextBlock>("StreakText");
            levelText = Find<TextBlock>("LevelText");
            progressCount = Find<TextBlock>("ProgressCount");
            bubblePoints = Find<TextBlock>("BubblePoints");
            masteredBadge = Find<TextBlock>("MasteredBadge");
            successText = Find<TextBlock>("SuccessText");
            rewardText = Find<TextBlock>("RewardText");
            keyCaps = Find<WrapPanel>("KeyCaps");
            progressFill = Find<Border>("ProgressFill");
            trainingView = Find<Grid>("TrainingView");
            overviewView = Find<Grid>("OverviewView");
            achievementView = Find<Grid>("AchievementView");
            overviewSearchBox = Find<TextBox>("OverviewSearchBox");
            categoryCombo = Find<ComboBox>("CategoryCombo");
            overviewList = Find<StackPanel>("OverviewList");
            overviewSummary = Find<TextBlock>("OverviewSummary");
            overviewProgressFill = Find<Border>("OverviewProgressFill");
            achievementTitle = Find<TextBlock>("AchievementTitle");
            achievementDetail = Find<TextBlock>("AchievementDetail");
            achievementCatalog = Find<TextBlock>("AchievementCatalog");
            learnNav = Find<Button>("LearnNav");
            libraryNav = Find<Button>("LibraryNav");
            awardNav = Find<Button>("AwardNav");

            lessons = BuildLessons();
            catalog = LoadShortcutCatalog();
            progress = ProgressStore.Load();
            lessonIndex = FirstIncompleteLesson();

            string[] categories = { "全部", "Copilot 键", "文本编辑", "桌面与常规", "Windows 键", "命令提示符", "对话框", "文件资源管理器", "虚拟桌面", "任务栏", "设置" };
            foreach (string category in categories) categoryCombo.Items.Add(category);
            categoryCombo.SelectedIndex = 0;

            WireEvents();

            keyboardTimer = new DispatcherTimer(DispatcherPriority.Input);
            keyboardTimer.Interval = TimeSpan.FromMilliseconds(45);
            keyboardTimer.Tick += PollKeyboard;

            toastTimer = new DispatcherTimer();
            toastTimer.Interval = TimeSpan.FromSeconds(2.1);
            toastTimer.Tick += delegate
            {
                toastTimer.Stop();
                toast.Visibility = Visibility.Collapsed;
            };

            window.Loaded += delegate
            {
                PositionExpanded();
                UpdateLesson();
                ShowPage("training");
                bool hookReady = KeyboardHook.Start();
                keyboardTimer.Start();
                if (!hookReady) ShowToast("全局按键监听未启动，请重新打开应用");
            };
            window.Closing += delegate
            {
                keyboardTimer.Stop();
                KeyboardHook.Stop();
            };
        }

        private T Find<T>(string name) where T : class
        {
            T element = window.FindName(name) as T;
            if (element == null) throw new InvalidOperationException("找不到界面元素：" + name);
            return element;
        }

        private static List<Lesson> BuildLessons()
        {
            return new List<Lesson>
            {
                new Lesson { Id = "desktop", Title = "一秒回到桌面", Subtitle = "窗口再多，也能瞬间清场", Shortcut = "Win+D",
                    Tip = "先按住 Windows 徽标键，再轻点 D；再按一次可以恢复所有窗口。",
                    Steps = new[] { "看清 Win 与 D 两个键的位置", "点击开始练习，保持手指放松", "按住 Win，再轻点 D 完成挑战" } },
                new Lesson { Id = "explorer", Title = "快速打开文件", Subtitle = "不用再满桌面寻找文件夹", Shortcut = "Win+E",
                    Tip = "E 可以记成 Explorer（资源管理器），用左手即可完成。",
                    Steps = new[] { "找到键盘左下角的 Win 键", "把另一根手指放到字母 E", "同时按下 Win + E，打开资源管理器" } },
                new Lesson { Id = "switch", Title = "在窗口之间穿梭", Subtitle = "多任务办公的必修动作", Shortcut = "Alt+Tab",
                    Tip = "按住 Alt 不放，连续点 Tab 可以挑选你想切换的窗口。",
                    Steps = new[] { "先打开两个不同的窗口", "按住左侧 Alt 键不要松开", "轻点 Tab，看到切换器就成功了" } },
                new Lesson { Id = "snip", Title = "截取任意一块屏幕", Subtitle = "告别先截图、再裁剪", Shortcut = "Win+Shift+S",
                    Tip = "按完后屏幕会变暗，用鼠标框选区域，图片会自动进入剪贴板。",
                    Steps = new[] { "左手小拇指按住 Win", "再按住 Shift，保持两个键不松", "轻点 S，看到截图工具即完成" } },
                new Lesson { Id = "taskmanager", Title = "直接打开任务管理器", Subtitle = "程序卡住时的救场组合", Shortcut = "Ctrl+Shift+Esc",
                    Tip = "这是比 Ctrl + Alt + Delete 更直接的路径，会立即打开任务管理器。",
                    Steps = new[] { "左手按住 Ctrl 和 Shift", "右手找到键盘左上角 Esc", "三个键一起按下，打开任务管理器" } },
                new Lesson { Id = "copy", Title = "复制选中的内容", Subtitle = "每天都会用到的效率基石", Shortcut = "Ctrl+C",
                    Tip = "C 可以记成 Copy。先选中文字或文件，再使用这个组合。",
                    Steps = new[] { "先选中一段文字或一个文件", "左手小拇指按住 Ctrl", "食指轻点 C，内容就复制好了" } },
                new Lesson { Id = "settings", Title = "直达系统设置", Subtitle = "调整 Win11 不再绕路", Shortcut = "Win+I",
                    Tip = "I 可以记成 Information，按下后直接进入 Windows 设置主页。",
                    Steps = new[] { "把左手放在 Win 键上", "找到字母 I 的位置", "同时按下 Win + I，打开设置" } },
                new Lesson { Id = "quicksettings", Title = "唤出快捷设置", Subtitle = "音量、网络和蓝牙都在这里", Shortcut = "Win+A",
                    Tip = "A 可以记成 Action，快捷设置会从屏幕右下角出现。",
                    Steps = new[] { "先找到左下角 Win 键", "另一根手指找到字母 A", "同时按下 Win + A，完成最后挑战" } }
            };
        }

        private static List<ShortcutInfo> LoadShortcutCatalog()
        {
            List<ShortcutInfo> items = new List<ShortcutInfo>();
            string path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data", "windows_shortcuts.tsv");
            if (!File.Exists(path)) return items;

            try
            {
                string[] lines = File.ReadAllLines(path, Encoding.UTF8);
                for (int i = 1; i < lines.Length; i++)
                {
                    if (string.IsNullOrWhiteSpace(lines[i])) continue;
                    string[] columns = lines[i].Split('\t');
                    if (columns.Length < 5) continue;
                    items.Add(new ShortcutInfo
                    {
                        Category = columns[0],
                        Keys = columns[1],
                        Action = columns[2],
                        Risk = columns[3],
                        LessonId = columns[4]
                    });
                }
            }
            catch
            {
                items.Clear();
            }
            return items;
        }

        private int FirstIncompleteLesson()
        {
            for (int i = 0; i < lessons.Count; i++)
            {
                if (!progress.Completed.Contains(lessons[i].Id)) return i;
            }
            return 0;
        }

        private void WireEvents()
        {
            Find<Button>("CollapseButton").Click += delegate { Collapse(); };
            Find<Button>("CloseButton").Click += delegate { Application.Current.Shutdown(); };
            bubbleButton.Click += delegate { Expand(); };
            MenuItem openItem = bubbleButton.ContextMenu.Items[0] as MenuItem;
            MenuItem exitItem = bubbleButton.ContextMenu.Items[2] as MenuItem;
            if (openItem != null) openItem.Click += delegate { Expand(); };
            if (exitItem != null) exitItem.Click += delegate { Application.Current.Shutdown(); };
            startButton.Click += StartPractice;
            previousButton.Click += delegate
            {
                if (lessonIndex > 0) { lessonIndex--; UpdateLesson(); }
            };
            nextButton.Click += delegate
            {
                if (lessonIndex < lessons.Count - 1) { lessonIndex++; UpdateLesson(); }
            };
            Find<Button>("ContinueButton").Click += delegate
            {
                successOverlay.Visibility = Visibility.Collapsed;
                confettiCanvas.Children.Clear();
                if (lessonIndex < lessons.Count - 1) lessonIndex++;
                else lessonIndex = FirstIncompleteLesson();
                UpdateLesson();
            };
            libraryNav.Click += delegate { ShowPage("overview"); };
            awardNav.Click += delegate { ShowPage("achievement"); };
            learnNav.Click += delegate { ShowPage("training"); };
            overviewSearchBox.TextChanged += delegate { RefreshOverview(); };
            categoryCombo.SelectionChanged += delegate { RefreshOverview(); };

            Grid dragArea = Find<Grid>("DragArea");
            dragArea.MouseLeftButtonDown += delegate(object sender, MouseButtonEventArgs args)
            {
                if (args.ButtonState == MouseButtonState.Pressed && !HasButtonAncestor(args.OriginalSource as DependencyObject))
                {
                    try { window.DragMove(); } catch { }
                }
            };
        }

        private void ShowPage(string page)
        {
            currentPage = page;
            trainingView.Visibility = page == "training" ? Visibility.Visible : Visibility.Collapsed;
            overviewView.Visibility = page == "overview" ? Visibility.Visible : Visibility.Collapsed;
            achievementView.Visibility = page == "achievement" ? Visibility.Visible : Visibility.Collapsed;

            SetNavigationState(learnNav, page == "training");
            SetNavigationState(libraryNav, page == "overview");
            SetNavigationState(awardNav, page == "achievement");

            if (page == "training") UpdateLesson();
            if (page == "overview") RefreshOverview();
            if (page == "achievement") UpdateAchievement();
        }

        private static void SetNavigationState(Button button, bool active)
        {
            button.Background = new SolidColorBrush(active ? Color.FromRgb(50, 22, 27) : Color.FromRgb(16, 12, 15));
            button.Foreground = new SolidColorBrush(active ? Color.FromRgb(255, 112, 66) : Color.FromRgb(174, 159, 155));
        }

        private void RefreshOverview()
        {
            overviewList.Children.Clear();
            string query = (overviewSearchBox.Text ?? string.Empty).Trim();
            string category = categoryCombo.SelectedItem as string ?? "全部";
            List<ShortcutInfo> filtered = new List<ShortcutInfo>();

            foreach (ShortcutInfo item in catalog)
            {
                bool categoryMatches = category == "全部" || item.Category == category;
                bool queryMatches = query.Length == 0 ||
                    item.Keys.IndexOf(query, StringComparison.OrdinalIgnoreCase) >= 0 ||
                    item.Action.IndexOf(query, StringComparison.OrdinalIgnoreCase) >= 0 ||
                    item.Category.IndexOf(query, StringComparison.OrdinalIgnoreCase) >= 0;
                if (categoryMatches && queryMatches) filtered.Add(item);
            }

            overviewSummary.Text = "官方目录 " + catalog.Count + " 条  ·  当前显示 " + filtered.Count + " 条  ·  核心训练 " + lessons.Count + " 关";
            string currentLessonId = lessons[lessonIndex].Id;
            for (int i = 0; i < filtered.Count; i++)
            {
                overviewList.Children.Add(CreateOverviewRow(filtered[i], i + 1, currentLessonId));
            }

            if (filtered.Count == 0)
            {
                TextBlock empty = new TextBlock();
                empty.Text = "没有匹配的快捷键\n试试搜索 Win、截图、窗口或文件";
                empty.Foreground = new SolidColorBrush(Color.FromRgb(174, 159, 155));
                empty.FontSize = 12;
                empty.TextAlignment = TextAlignment.Center;
                empty.Margin = new Thickness(20, 60, 20, 60);
                overviewList.Children.Add(empty);
            }

            window.Dispatcher.BeginInvoke(new Action(UpdateOverviewProgress), DispatcherPriority.Loaded);
        }

        private UIElement CreateOverviewRow(ShortcutInfo item, int displayIndex, string currentLessonId)
        {
            bool mastered = !string.IsNullOrEmpty(item.LessonId) && progress.Completed.Contains(item.LessonId);
            bool selected = !string.IsNullOrEmpty(item.LessonId) && item.LessonId == currentLessonId;
            Color normalColor = mastered ? Color.FromRgb(33, 19, 23) : Color.FromRgb(21, 16, 19);

            Border row = new Border();
            row.Height = 64;
            row.Margin = new Thickness(0, 0, 0, 5);
            row.Background = new SolidColorBrush(normalColor);
            row.BorderBrush = new SolidColorBrush(selected ? Color.FromRgb(156, 48, 53) : Color.FromRgb(83, 39, 42));
            row.BorderThickness = new Thickness(1);
            row.CornerRadius = new CornerRadius(3);
            row.Cursor = Cursors.Hand;

            Grid grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(45) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            Border numberBox = new Border();
            numberBox.Background = new SolidColorBrush(selected ? Color.FromRgb(255, 59, 33) : Color.FromRgb(52, 21, 26));
            TextBlock number = new TextBlock();
            number.Text = displayIndex.ToString("000", CultureInfo.InvariantCulture);
            number.Foreground = new SolidColorBrush(selected ? Color.FromRgb(255, 244, 236) : Color.FromRgb(255, 138, 50));
            number.FontFamily = new FontFamily("Bahnschrift");
            number.FontSize = 10;
            number.FontWeight = FontWeights.Bold;
            number.HorizontalAlignment = HorizontalAlignment.Center;
            number.VerticalAlignment = VerticalAlignment.Center;
            numberBox.Child = number;
            Grid.SetColumn(numberBox, 0);
            grid.Children.Add(numberBox);

            StackPanel textBox = new StackPanel();
            textBox.Margin = new Thickness(10, 7, 6, 6);
            TextBlock keys = new TextBlock();
            keys.Text = item.Keys;
            keys.Foreground = new SolidColorBrush(Color.FromRgb(255, 244, 236));
            keys.FontFamily = new FontFamily("Bahnschrift");
            keys.FontSize = 11.5;
            keys.FontWeight = FontWeights.Bold;
            keys.TextTrimming = TextTrimming.CharacterEllipsis;
            TextBlock action = new TextBlock();
            action.Text = item.Action;
            action.Foreground = new SolidColorBrush(Color.FromRgb(182, 164, 160));
            action.FontSize = 9.5;
            action.Margin = new Thickness(0, 3, 0, 0);
            action.TextTrimming = TextTrimming.CharacterEllipsis;
            textBox.Children.Add(keys);
            textBox.Children.Add(action);
            Grid.SetColumn(textBox, 1);
            grid.Children.Add(textBox);

            string statusText;
            Color statusColor;
            if (mastered)
            {
                statusText = "✓ 已掌握";
                statusColor = Color.FromRgb(255, 208, 74);
            }
            else if (!string.IsNullOrEmpty(item.LessonId))
            {
                statusText = "可训练";
                statusColor = Color.FromRgb(255, 138, 50);
            }
            else if (item.Risk == "caution")
            {
                statusText = "⚠ 谨慎";
                statusColor = Color.FromRgb(255, 59, 33);
            }
            else if (item.Risk == "context")
            {
                statusText = "场景限定";
                statusColor = Color.FromRgb(118, 104, 101);
            }
            else
            {
                statusText = item.Category;
                statusColor = Color.FromRgb(118, 104, 101);
            }

            TextBlock status = new TextBlock();
            status.Text = statusText;
            status.Foreground = new SolidColorBrush(statusColor);
            status.FontSize = 9;
            status.VerticalAlignment = VerticalAlignment.Center;
            status.Margin = new Thickness(6, 0, 10, 0);
            Grid.SetColumn(status, 2);
            grid.Children.Add(status);

            row.Child = grid;
            row.MouseEnter += delegate { row.Background = new SolidColorBrush(Color.FromRgb(48, 24, 29)); };
            row.MouseLeave += delegate { row.Background = new SolidColorBrush(normalColor); };
            row.MouseLeftButtonUp += delegate { OpenCatalogItem(item); };
            return row;
        }

        private void OpenCatalogItem(ShortcutInfo item)
        {
            if (!string.IsNullOrEmpty(item.LessonId))
            {
                for (int i = 0; i < lessons.Count; i++)
                {
                    if (lessons[i].Id == item.LessonId)
                    {
                        lessonIndex = i;
                        ShowPage("training");
                        return;
                    }
                }
            }
            ShowToast((item.Risk == "caution" ? "谨慎操作：" : item.Category + "：") + item.Action);
        }

        private void UpdateAchievement()
        {
            int remaining = lessons.Count - progress.Completed.Count;
            if (remaining <= 0)
            {
                achievementTitle.Text = "快捷键新手毕业";
                achievementDetail.Text = "全部 " + lessons.Count + " 个核心快捷键已完成同步";
            }
            else
            {
                achievementTitle.Text = "新手同步中";
                achievementDetail.Text = "再掌握 " + remaining + " 个即可解锁毕业徽章";
            }
            achievementCatalog.Text = "官方快捷键目录：" + catalog.Count + " 条";
        }

        private void UpdateOverviewProgress()
        {
            FrameworkElement parent = overviewProgressFill.Parent as FrameworkElement;
            double available = parent == null ? 0 : parent.ActualWidth;
            if (available > 0) overviewProgressFill.Width = available * progress.Completed.Count / lessons.Count;
        }

        private static bool HasButtonAncestor(DependencyObject source)
        {
            DependencyObject current = source;
            while (current != null)
            {
                if (current is Button) return true;
                current = VisualTreeHelper.GetParent(current);
            }
            return false;
        }

        private void StartPractice(object sender, RoutedEventArgs e)
        {
            listening = !listening;
            if (listening)
            {
                startButton.Content = "LINK ACTIVE  //  请按 " + DisplayShortcut(lessons[lessonIndex].Shortcut);
                startButton.Background = new SolidColorBrush(Color.FromRgb(92, 24, 30));
                ShowToast("同步监听已开启，可在任意窗口完成");
            }
            else
            {
                ResetStartButton();
                ShowToast("练习已暂停");
            }
        }

        private void PollKeyboard(object sender, EventArgs e)
        {
            string shortcut;
            while (KeyboardHook.TryGetShortcut(out shortcut))
            {
                if (shortcut == "__TOGGLE__")
                {
                    if (expanded) Collapse(); else Expand();
                    continue;
                }
                if (!listening || successOverlay.Visibility == Visibility.Visible) continue;
                if (string.Equals(shortcut, lessons[lessonIndex].Shortcut, StringComparison.OrdinalIgnoreCase))
                {
                    CompleteLesson();
                }
                else if (shortcut.IndexOf('+') >= 0 && DateTime.Now - lastWrongHint > TimeSpan.FromSeconds(1.8))
                {
                    lastWrongHint = DateTime.Now;
                    ShowToast("很接近！本关需要 " + DisplayShortcut(lessons[lessonIndex].Shortcut));
                }
            }
        }

        private void CompleteLesson()
        {
            listening = false;
            Lesson lesson = lessons[lessonIndex];
            bool firstTime = progress.Completed.Add(lesson.Id);
            if (firstTime) progress.Points += 10;
            progress.LastPractice = DateTime.Today;
            ProgressStore.Save(progress);

            window.WindowState = WindowState.Normal;
            window.Show();
            window.Topmost = false;
            window.Topmost = true;
            expanded = true;
            bubbleView.Visibility = Visibility.Collapsed;
            appShell.Visibility = Visibility.Visible;
            window.Width = 432;
            window.Height = 724;
            PositionExpanded();

            successText.Text = "你掌握了「" + lesson.Title + "」";
            if (rewardText != null) rewardText.Text = firstTime ? "⚡ +10 XP" : "✓ 复习完成";
            successOverlay.Visibility = Visibility.Visible;
            UpdateHeaderStats();
            UpdateAchievement();
            CreateConfetti();
            ChimePlayer.PlaySuccess();
            ShakeWindow();
        }

        private void UpdateLesson()
        {
            listening = false;
            ResetStartButton();
            Lesson lesson = lessons[lessonIndex];
            bool mastered = progress.Completed.Contains(lesson.Id);

            lessonNumberText.Text = "PHASE // " + (lessonIndex + 1).ToString("00", CultureInfo.InvariantCulture);
            lessonTitle.Text = lesson.Title;
            lessonSubtitle.Text = lesson.Subtitle;
            tipText.Text = lesson.Tip;
            stepOne.Text = lesson.Steps[0];
            stepTwo.Text = lesson.Steps[1];
            stepThree.Text = lesson.Steps[2];
            masteredBadge.Visibility = mastered ? Visibility.Visible : Visibility.Collapsed;
            previousButton.IsEnabled = lessonIndex > 0;
            nextButton.IsEnabled = lessonIndex < lessons.Count - 1;

            keyCaps.Children.Clear();
            string[] keys = lesson.Shortcut.Split('+');
            for (int i = 0; i < keys.Length; i++)
            {
                if (i > 0)
                {
                    TextBlock plus = new TextBlock();
                    plus.Text = "+";
                    plus.FontSize = 15;
                    plus.FontWeight = FontWeights.SemiBold;
                    plus.Foreground = new SolidColorBrush(Color.FromRgb(190, 156, 150));
                    plus.VerticalAlignment = VerticalAlignment.Center;
                    plus.Margin = new Thickness(7, 0, 7, 0);
                    keyCaps.Children.Add(plus);
                }
                keyCaps.Children.Add(CreateKeyCap(keys[i]));
            }

            UpdateHeaderStats();
            window.Dispatcher.BeginInvoke(new Action(UpdateProgressBar), DispatcherPriority.Loaded);
        }

        private UIElement CreateKeyCap(string key)
        {
            string label = key == "Win" ? "⊞  Win" : key;
            TextBlock text = new TextBlock();
            text.Text = label;
            text.FontSize = 13;
            text.FontWeight = FontWeights.SemiBold;
            text.Foreground = new SolidColorBrush(Color.FromRgb(255, 240, 232));
            text.HorizontalAlignment = HorizontalAlignment.Center;
            text.VerticalAlignment = VerticalAlignment.Center;

            Border cap = new Border();
            cap.MinWidth = key == "Shift" ? 64 : (key == "Win" ? 67 : 47);
            cap.Height = 43;
            cap.Padding = new Thickness(11, 0, 11, 0);
            cap.Background = new LinearGradientBrush(Color.FromRgb(48, 20, 25), Color.FromRgb(18, 12, 15), 90);
            cap.BorderBrush = new SolidColorBrush(Color.FromRgb(142, 47, 51));
            cap.BorderThickness = new Thickness(1);
            cap.CornerRadius = new CornerRadius(11);
            cap.Child = text;
            cap.Effect = new System.Windows.Media.Effects.DropShadowEffect
            {
                Color = Color.FromRgb(255, 55, 32),
                Opacity = 0.28,
                BlurRadius = 5,
                ShadowDepth = 2,
                Direction = 270
            };
            return cap;
        }

        private void UpdateHeaderStats()
        {
            pointsText.Text = progress.Points.ToString(CultureInfo.InvariantCulture);
            streakText.Text = progress.Streak.ToString(CultureInfo.InvariantCulture);
            levelText.Text = "SYNC " + Math.Max(1, 1 + progress.Points / 30).ToString("00", CultureInfo.InvariantCulture);
            bubblePoints.Text = progress.Points > 99 ? "99+" : progress.Points.ToString(CultureInfo.InvariantCulture);
            progressCount.Text = progress.Completed.Count.ToString("00", CultureInfo.InvariantCulture) + " / " + lessons.Count.ToString("00", CultureInfo.InvariantCulture);
            UpdateAchievement();
            window.Dispatcher.BeginInvoke(new Action(UpdateOverviewProgress), DispatcherPriority.Loaded);
        }

        private void UpdateProgressBar()
        {
            FrameworkElement parent = progressFill.Parent as FrameworkElement;
            double available = parent == null ? 0 : parent.ActualWidth;
            if (available > 0) progressFill.Width = available * progress.Completed.Count / lessons.Count;
        }

        private void ResetStartButton()
        {
            bool mastered = progress.Completed.Contains(lessons[lessonIndex].Id);
            startButton.Content = mastered ? "再次同步  ·  巩固记忆" : "开始同步  ·  +10 XP";
            startButton.Background = new SolidColorBrush(Color.FromRgb(255, 59, 33));
        }

        private static string DisplayShortcut(string shortcut)
        {
            return shortcut.Replace("+", " + ").Replace("Win", "Win");
        }

        private void Collapse()
        {
            successOverlay.Visibility = Visibility.Collapsed;
            confettiCanvas.Children.Clear();
            listening = false;
            expanded = false;
            appShell.Visibility = Visibility.Collapsed;
            bubbleView.Visibility = Visibility.Visible;
            window.Width = 104;
            window.Height = 104;
            PositionBubble();
        }

        private void Expand()
        {
            expanded = true;
            bubbleView.Visibility = Visibility.Collapsed;
            appShell.Visibility = Visibility.Visible;
            window.Width = 432;
            window.Height = 724;
            PositionExpanded();
            window.Show();
            window.Topmost = true;
            window.Activate();
            ShowPage(currentPage);
        }

        private void PositionExpanded()
        {
            Rect area = SystemParameters.WorkArea;
            window.Left = Math.Max(area.Left + 14, area.Right - window.Width - 24);
            window.Top = Math.Max(area.Top + 14, area.Top + (area.Height - window.Height) / 2);
        }

        private void PositionBubble()
        {
            Rect area = SystemParameters.WorkArea;
            window.Left = area.Right - window.Width - 22;
            window.Top = area.Bottom - window.Height - 22;
        }

        private void ShowToast(string message)
        {
            toastText.Text = message;
            toast.Visibility = Visibility.Visible;
            toastTimer.Stop();
            toastTimer.Start();
        }

        private void ShakeWindow()
        {
            double originLeft = window.Left;
            double originTop = window.Top;
            Stopwatch watch = Stopwatch.StartNew();
            DispatcherTimer timer = new DispatcherTimer(DispatcherPriority.Render);
            timer.Interval = TimeSpan.FromMilliseconds(15);
            timer.Tick += delegate
            {
                double elapsed = watch.Elapsed.TotalMilliseconds;
                double progressValue = elapsed / 430.0;
                if (progressValue >= 1)
                {
                    window.Left = originLeft;
                    window.Top = originTop;
                    timer.Stop();
                    return;
                }
                double power = 1.0 - progressValue;
                window.Left = originLeft + Math.Sin(elapsed * 0.105) * 13.0 * power;
                window.Top = originTop + Math.Sin(elapsed * 0.071) * 2.5 * power;
            };
            timer.Start();
        }

        private void CreateConfetti()
        {
            confettiCanvas.Children.Clear();
            Color[] colors =
            {
                Color.FromRgb(255, 59, 33), Color.FromRgb(255, 154, 50), Color.FromRgb(255, 208, 74),
                Color.FromRgb(189, 19, 28), Color.FromRgb(255, 245, 238)
            };
            double width = window.Width;
            double height = window.Height;
            for (int i = 0; i < 42; i++)
            {
                Border piece = new Border();
                piece.Width = random.Next(5, 10);
                piece.Height = random.Next(8, 15);
                piece.CornerRadius = new CornerRadius(2);
                piece.Background = new SolidColorBrush(colors[random.Next(colors.Length)]);
                RotateTransform rotate = new RotateTransform(random.Next(0, 180));
                piece.RenderTransform = rotate;

                double startX = width / 2 + random.Next(-45, 46);
                double endX = random.Next(12, (int)width - 12);
                double startY = height / 2 - 80 + random.Next(-15, 16);
                Canvas.SetLeft(piece, startX);
                Canvas.SetTop(piece, startY);
                confettiCanvas.Children.Add(piece);

                double duration = 0.85 + random.NextDouble() * 0.65;
                DoubleAnimation xAnimation = new DoubleAnimation(startX, endX, TimeSpan.FromSeconds(duration));
                xAnimation.EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseOut };
                DoubleAnimation yAnimation = new DoubleAnimation(startY, height + 20, TimeSpan.FromSeconds(duration));
                yAnimation.EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn };
                DoubleAnimation spinAnimation = new DoubleAnimation(rotate.Angle, rotate.Angle + random.Next(180, 720), TimeSpan.FromSeconds(duration));

                piece.BeginAnimation(Canvas.LeftProperty, xAnimation);
                piece.BeginAnimation(Canvas.TopProperty, yAnimation);
                rotate.BeginAnimation(RotateTransform.AngleProperty, spinAnimation);
            }
        }
    }

    internal static class Program
    {
        [STAThread]
        public static void Main()
        {
            Application application = new Application();
            application.ShutdownMode = ShutdownMode.OnExplicitShutdown;
            application.DispatcherUnhandledException += delegate(object sender, DispatcherUnhandledExceptionEventArgs args)
            {
                MessageBox.Show("键游遇到问题：\n" + args.Exception.Message, "键游", MessageBoxButton.OK, MessageBoxImage.Information);
                args.Handled = true;
            };

            try
            {
                string xamlPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "src", "MainWindow.xaml");
                if (!File.Exists(xamlPath))
                {
                    MessageBox.Show("找不到界面文件：\n" + xamlPath, "键游", MessageBoxButton.OK, MessageBoxImage.Error);
                    return;
                }
                Window window;
                using (FileStream stream = File.OpenRead(xamlPath))
                {
                    window = (Window)XamlReader.Load(stream);
                }
                QuickKeyApplication controller = new QuickKeyApplication(window);
                GC.KeepAlive(controller);
                application.Run(window);
            }
            catch (Exception ex)
            {
                try
                {
                    File.WriteAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "startup-error.log"),
                        ex.ToString(), new UTF8Encoding(false));
                }
                catch { }
                MessageBox.Show("键游启动失败：\n" + ex, "键游", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
