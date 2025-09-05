import sys
import subprocess
from tkinter import Tk, messagebox, ttk,Toplevel, StringVar, BooleanVar
from threading import Thread

# ================= 前置依赖检查 =================
def show_message(title, message, is_error=False):
    """通用弹窗函数"""
    root = Tk()
    root.withdraw()
    (messagebox.showerror if is_error else messagebox.showinfo)(title, message)
    root.destroy()

def check_dependencies():
    """前置依赖检查"""
    required = {
        'psutil': 'psutil', 
        'keyboard': 'keyboard', 
        'PIL': 'pillow', 
        'pystray': 'pystray', 
        'win32api': 'pywin32'  # 改为 pywin32
    }
    missing = []
    for lib, pkg in required.items():
        try: 
            __import__(lib)
        except ImportError: 
            missing.append(pkg)
    if not missing:
        return
    # 显示初始提示
    show_message("依赖安装", f"检测到缺少依赖库：{', '.join(missing)}\n点击确定开始自动安装...")
    # 创建进度窗口并置顶
    progress_root = Tk()
    progress_root.title("安装依赖")
    progress_root.geometry("400x150")
    progress_root.resizable(False, False)
    # 计算居中位置
    screen_width = progress_root.winfo_screenwidth()
    screen_height = progress_root.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 150) // 2
    progress_root.geometry(f"+{x}+{y}")
    # 确保窗口始终在最前面
    progress_root.attributes('-topmost', True)
    progress_root.lift()
    progress_root.focus_force()
    progress_label = ttk.Label(progress_root, text="准备安装依赖...")
    progress_label.pack(pady=5)
    progress_bar = ttk.Progressbar(progress_root, orient="horizontal", 
                                 length=300, mode="determinate")
    progress_bar.pack(pady=10)
    detail_label = ttk.Label(progress_root, text="")
    detail_label.pack(pady=5)
    current_pkg_label = ttk.Label(progress_root, text="")
    current_pkg_label.pack(pady=5)
    # 安装状态
    install_complete = False
    failed_packages = []
    
    def update_progress(current, total, package, message):
        """更新进度显示"""
        progress_bar['value'] = (current / total) * 100
        progress_label.config(text=f"进度: {current}/{total}")
        current_pkg_label.config(text=f"正在安装: {package}")
        detail_label.config(text=message)
        # 强制更新UI
        progress_root.update_idletasks()
    
    def on_closing():
        """处理窗口关闭事件"""
        nonlocal install_complete
        if not install_complete:
            if messagebox.askokcancel("退出", "依赖安装尚未完成，确定要退出吗？"):
                progress_root.destroy()
                sys.exit(1)
        else:
            progress_root.destroy()
    progress_root.protocol("WM_DELETE_WINDOW", on_closing)
    
    def install_dependencies():
        """安装缺失的依赖"""
        nonlocal install_complete, failed_packages
        total = len(missing)
        for i, package in enumerate(missing, 1):
            # 更新UI
            progress_root.after(0, update_progress, i-1, total, package, "准备安装...")
            try:
                # 运行pip安装命令
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # 解析输出信息
                output = result.stdout
                status_message = ""
                if "Successfully installed" in output:
                    status_message = f"{package} 安装成功"
                elif "Already satisfied" in output:
                    status_message = f"{package} 已安装"
                else:
                    status_message = output.strip()[:100] + "..." if len(output) > 100 else output.strip()  
                # 更新UI
                progress_root.after(0, update_progress, i, total, package, status_message) 
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.strip() if e.stderr else str(e)
                error_msg = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                progress_root.after(0, update_progress, i, total, package, f"{package} 安装失败: {error_msg}")
                failed_packages.append(package)
                continue
        install_complete = True
        # 安装完成后检查
        still_missing = []
        for lib in required:
            try: 
                __import__(lib)
            except ImportError:
                still_missing.append(lib)
        if failed_packages or still_missing:
            # 组合错误信息
            error_msg = ""
            if failed_packages:
                error_msg += f"以下依赖安装失败：{', '.join(failed_packages)}\n"
            if still_missing:
                error_msg += f"以下依赖仍缺失：{', '.join(still_missing)}\n"
            error_msg += f"请手动执行：\npip install {' '.join(missing)}"
            progress_root.after(0, lambda: messagebox.showerror("安装失败", error_msg))
            progress_root.after(100, progress_root.destroy)
            sys.exit(1)
    # 启动安装线程
    Thread(target=install_dependencies, daemon=True).start()
    # 主循环
    progress_root.mainloop()
# 前置执行依赖检查
check_dependencies()

try:
    import time
    import json
    import threading
    import os
    import winreg
    import platform
    import ctypes
    import keyboard
    import psutil
    from win32 import win32api # 新增导入
    from threading import Lock
    from PIL import Image, ImageDraw
    from pystray import Icon, MenuItem
except ImportError as e:
    show_message("缺少依赖", f"无法导入必要模块: {str(e)}\n请尝试手动安装依赖", True)
    sys.exit(1)
# ================= 全局配置 =================
PROCESS_CONFIG = {
    "rtcRemoteDesktop.exe": ["ctrl+windows+d", "ctrl+windows+f4"],
    "screenCapture.exe": ["ctrl+windows+d", "ctrl+windows+f4"]
}
DEFAULT_CHECK_INTERVAL = 0.05  # 默认监测间隔(秒)
SETTINGS_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'GlobalProcessWatcher')
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')
DEFAULT_SETTINGS = {
    "auto_start": False, 
    "show_alert": False, 
    "alert_on_top": False,
    "enable_hotkey": False,
    "enable_sleep": False,
    "auto_pause": False,  # 新增自动暂停设置
    "auto_mute": False,  # 自动静音设置
    "auto_kill": False,  # 新增：自动结束进程
    "check_interval": DEFAULT_CHECK_INTERVAL,
    "alert_duration": 1,  # 默认弹窗显示1秒
    "only_rtc_effective": False  # 新增：仅对rtcRemoteDesktop.exe生效
}

settings_lock = Lock()

# ================= 免责声明 =================
def show_disclaimer():
    """显示免责声明并获取用户同意"""
    disclaimer_file = os.path.join(SETTINGS_DIR, 'disclaimer_accepted')
    # 如果已经同意过，直接返回
    if os.path.exists(disclaimer_file):
        return True
    disclaimer_text = """
    免责声明&用户协议

    本程序为开源技术研究工具，开发者不承担用户使用、传播本程序引发的任何直接或间接责任。使用本程序即视为同意以下条款：

    一、责任豁免
    1. 您将独自承担使用本程序的所有风险及后果
    2. 开发者不对程序的完整性、准确性、适用性作任何担保
    3. 因程序漏洞、数据丢失导致的损失，开发者不承担责任
    4. 开发者保留随时修改、终止服务的权利，无需提前通知

    二、使用限制
    1. 禁止用于非法监控、商业间谍等侵犯隐私行为
    2. 不得违反《网络安全法》《个人信息保护法》等法律法规
    3. 禁止通过本程序干扰、破坏他人计算机系统
    4. 不得将本程序用于任何网络攻击行为

    三、知识产权
    1. 程序涉及的第三方库版权归属原开发者
    2. 未经许可不得将本程序用于商业用途

    四、法律管辖
    1. 本声明适用中华人民共和国法律解释
    2. 争议应提交开发者所在地有管辖权的法院解决

    五、用户承诺
    1. 已充分理解使用本程序可能存在的法律风险
    2. 保证使用行为符合所在国家/地区的法律法规
    3. 若将本程序用于他人设备，已获得合法授权

    继续使用表示您同意承担所有相关责任 请确认您已理解并同意上述条款
    如果您不同意上述条款，请点击"拒绝"按钮退出程序。
    """
    root = Tk()
    root.title("免责声明&用户协议")
    root.geometry("800x650")
    root.resizable(False, False)
    # 计算居中位置
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - 800) // 2
    y = (screen_height - 650) // 2
    root.geometry(f"+{x}+{y}")
    # 创建文本区域
    text = ttk.Label(root, text=disclaimer_text, justify="left", padding=10)
    text.pack(fill="both", expand=True)
    # 创建按钮框架
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)
    accepted = False
    
    def on_accept():
        # 确保配置目录存在
        ensure_settings_dir()
        nonlocal accepted
        accepted = True
        try:
            with open(disclaimer_file, 'w') as f:
                f.write("1")  # 创建标记文件
        except Exception as e:
            show_message("错误", f"无法保存同意状态: {str(e)}", True)
        root.destroy()

    def on_reject():
        root.destroy()
    # 创建按钮
    accept_btn = ttk.Button(button_frame, text="同意并继续", command=on_accept)
    accept_btn.pack(side="left", padx=10)
    reject_btn = ttk.Button(button_frame, text="拒绝并退出", command=on_reject)
    reject_btn.pack(side="right", padx=10)
    # 绑定窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", on_reject)
    root.mainloop()
    return accepted

# ================= 系统控制API =================
def system_sleep():
    """使系统进入睡眠状态"""
    if platform.system() == 'Windows':
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
            ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
        except Exception as e:
            show_message("睡眠失败", f"无法进入睡眠状态：{str(e)}", True)
    else:
        show_message("不支持", "该功能仅支持Windows系统", True)

# ================= 权限管理 =================
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def request_admin():
    if os.name == 'nt' and not is_admin():
        try:
            # 重新以管理员权限运行程序
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
            )
            return True
        except Exception as e:
            show_message("权限错误", f"权限请求失败：{str(e)}", True)
    return False

# ================= 注册表操作 =================
def get_registry_auto_start():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "GlobalProcessWatcher")
            return value == sys.executable
    except: return False

def set_registry_auto_start(enable):
    """设置开机自启动注册表项"""
    try:
        # 先检查当前状态，避免重复写入
        current_state = get_registry_auto_start()
        if current_state == enable:
            return  # 如果状态相同，无需重复写入
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
            if enable:
                winreg.SetValueEx(key, "GlobalProcessWatcher", 0, winreg.REG_SZ, f'"{sys.executable}"')
            else:
                try: 
                    winreg.DeleteValue(key, "GlobalProcessWatcher")
                except FileNotFoundError: 
                    pass  # 如果键不存在则忽略
    except Exception as e: 
        raise RuntimeError(f"注册表操作失败：{str(e)}")

# ================= 配置管理 =================
def ensure_settings_dir():
    """确保配置目录存在"""
    if not os.path.exists(SETTINGS_DIR):
        try:
            os.makedirs(SETTINGS_DIR, exist_ok=True)
        except Exception as e:
            show_message("配置错误", f"无法创建配置目录：{str(e)}", True)
            sys.exit(1)

def load_settings():
    """配置加载，兼容旧版本"""
    ensure_settings_dir()
    try:
        merged_settings = DEFAULT_SETTINGS.copy()
        if os.path.exists(SETTINGS_FILE):
            with settings_lock, open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                merged_settings.update(loaded)
        # 版本兼容处理
        if 'enable_sleep' not in merged_settings:
            merged_settings['enable_sleep'] = DEFAULT_SETTINGS['enable_sleep']
            save_settings(merged_settings)
        return merged_settings
    except Exception as e:
        show_message("配置错误", f"加载设置失败：{str(e)}", True)
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """配置保存(原子写入)"""
    ensure_settings_dir()
    temp_file = f"{SETTINGS_FILE}.tmp"
    backup_file = f"{SETTINGS_FILE}.bak"
    try:
        with settings_lock:
            # 1. 先写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            # 2. 如果有原文件，创建备份
            if os.path.exists(SETTINGS_FILE):
                try:
                    os.replace(SETTINGS_FILE, backup_file)
                except Exception:
                    pass  # 备份失败不影响继续
            # 3. 临时文件重命名为正式文件
            try:
                os.replace(temp_file, SETTINGS_FILE)
            except Exception as e:
                # 4. 如果重命名失败，尝试恢复备份
                if os.path.exists(backup_file):
                    os.replace(backup_file, SETTINGS_FILE)
                raise e
            # 5. 成功后删除备份
            if os.path.exists(backup_file):
                try:
                    os.remove(backup_file)
                except Exception:
                    pass  # 删除备份失败不影响结果     
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        show_message("配置错误", f"保存设置失败：{str(e)}", True)

# ================= 进程操作 =================
def terminate_process_by_name(process_name):
    """根据进程名终止进程"""
    try:
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                    killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    try:
                        proc.kill()
                        killed_count += 1
                    except:
                        pass
        return killed_count > 0
    except Exception as e:
        show_message("进程终止错误", f"无法终止进程 {process_name}: {str(e)}", True)
        return False

# ================= 核心功能类 =================
class GlobalProcessWatcher:
    def __init__(self):
        """初始化监控器"""
        self.settings = load_settings()
        self.running = True
        self.auto_start = self.settings.get("auto_start", False)
        self.global_settings = {
            "show_alert": self.settings.get("show_alert", False),
            "enable_hotkey": self.settings.get("enable_hotkey", False),
            "enable_sleep": self.settings.get("enable_sleep", False),
            "auto_pause": self.settings.get("auto_pause", False),  # 新增自动暂停设置
            "auto_kill": self.settings.get("auto_kill", False),  # 新增自动结束进程设置
            "check_interval": max(0.02, min(10, float(self.settings.get("check_interval", DEFAULT_CHECK_INTERVAL)))),
            "alert_on_top": self.settings.get("alert_on_top", True),
            "alert_duration": self.settings.get("alert_duration", 5),
            "only_rtc_effective": self.settings.get("only_rtc_effective", False)  # 新增：仅对rtcRemoteDesktop.exe生效
        }
        self.media_paused = False  # 新增媒体暂停状态标记
        self.process_states = {p: False for p in PROCESS_CONFIG}
        self.sleep_triggered = False
        self.last_update_time = 0 # 添加进程ID缓存
        self.process_cache = {p: set() for p in PROCESS_CONFIG}  # {进程名: 进程ID集合}# 添加图标缓存
        self.icon_cache = {}
        self.last_icon_state = None
        
        self._initialize_components()
        
        # 初始化时检查是否需要暂停媒体
        if self.global_settings["auto_pause"]:
            for proc_name in PROCESS_CONFIG:
                if self._is_process_running(proc_name):
                    self._send_media_key()
                    self.media_paused = True
                    break

    def _initialize_components(self):
        """初始化所有组件"""
        self.sync_registry_state()
        self._init_ui()
        self.start_monitoring()
        self.save_current_settings()

    def sync_registry_state(self):
        """同步注册表状态"""
        try:
            if get_registry_auto_start() != self.auto_start:
                set_registry_auto_start(self.auto_start)
        except Exception as e:
            show_message("注册表错误", f"无法同步注册表状态: {str(e)}", True)

    def _init_ui(self):
        """初始化用户界面"""
        self._hide_console()
        self.root = Tk()
        self.root.withdraw()
        self._init_tray_icon()

    def _hide_console(self):
        """隐藏控制台窗口"""
        if os.name == 'nt':
            try:
                ctypes.windll.user32.ShowWindow(
                    ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except Exception as e:
                show_message(f"无法隐藏控制台: {str(e)}")

    def _init_tray_icon(self):
        """初始化系统托盘图标"""
        try:
            self.tray_icon = Icon(
                "global_watcher",
                self._generate_icon(),
                "进程监控器",
                self._create_menu()
            )
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            show_message("初始化失败", f"无法创建托盘图标: {str(e)}", True)
            sys.exit(1)


    def _create_menu(self):
        """创建托盘菜单"""
        menu_items = [
            MenuItem(lambda _: f"🚀 开机自启：{'✔' if self.auto_start else '❌'}", self.toggle_auto_start),
            MenuItem(lambda _: f"📢 弹窗提醒：{'✔' if self.global_settings['show_alert'] else '❌'}", self.toggle_alert),
            MenuItem(lambda _: f"⌨️ 全局热键：{'✔' if self.global_settings['enable_hotkey'] else '❌'}", self.toggle_hotkey),
            MenuItem(lambda _: f"💤 睡眠功能：{'✔' if self.global_settings['enable_sleep'] else '❌'}", self.toggle_sleep),
            MenuItem(lambda _: f"⏸️ 自动暂停：{'✔' if self.global_settings['auto_pause'] else '❌'}", self.toggle_auto_pause),  # 新增菜单项
            MenuItem(lambda _: f"🔴 结束进程：{'✔' if self.global_settings['auto_kill'] else '❌'}", self.toggle_auto_kill),  # 新增菜单项
            MenuItem("📊 当前状态", self.show_status),
            MenuItem("✏️ 更多设置", self.show_settings_dialog),
            MenuItem("📖 使用方法", self.show_usage),
            MenuItem("🌐 项目地址", self.open_project_url),
            MenuItem("⛔ 退出程序", self.clean_exit)
        ]
        return menu_items
    
    def show_usage(self, _=None):
        """显示程序使用方法"""
        usage_text = """
📢 弹窗提醒：在老师监视你屏幕的时候弹出提示弹窗，弹窗显示的时间可以在更多设置中修改，默认1秒。
当提示"screenCapture.exe已启动"时，代表老师可能正在观察你的屏幕，同时程序创建的托盘图标中心会变成黄色。
当提示"rtcRemoteDesktop.exe已启动"时，说明你已经被老师远程控制，此时程序的托盘图标会显示红色。
⌨️ 全局热键：当上述任意一个程序启动时，自动新建桌面，程序退出时删除新建的桌面
💤 睡眠功能：当上述任意一个程序启动时，自动使电脑进入睡眠状态
⏸️ 自动暂停：当上述任意一个程序启动时自动暂停正在播放的音/视频
🔴 结束进程：当上述任意一个程序启动时自动结束该进程
⚠️ 警告：使用此功能可能导致被管理员线下真实!作者不对因使用本软件带来的任何后果及连带后果负责！

✏️ 更多设置：你可以在这里修改程序的其他设置
⏱️ 监测间隔：控制程序的扫描间隔，值越小检测越灵敏，性能要求越高
🕒 弹窗显示时间：控制"弹窗提醒"功能弹出的提醒弹窗显示的时长
🔝 弹窗置顶：设置"弹窗提醒"功能的弹窗是否置顶显示
🎯 仅对rtcRemoteDesktop.exe生效：选中时，除了弹窗提醒和弹窗置顶以外的功能将只在"rtcRemoteDesktop.exe"运行时才触发
⚠️ 注意：使用此功能前请注意观察学校的行动方式，确认学校在观察你屏幕的时候会启用远程桌面（rtcRemoteDesktop.exe）再打开此功能
若经常先提示"screenCapture.exe已启动"后提示"rtcRemoteDesktop.exe已启动"则大概率学校在观察你屏幕的时候会启用远程桌面

图标颜色说明：
外环：
        只有弹窗提醒开启 - 全环亮蓝色
        只有全局热键开启 - 全环黄色
        上述功能都开启：
        下半环蓝色(弹窗提醒)
        上半环黄色(全局热键)
内环：
        只有自动暂停开启 - 全环紫色
        只有睡眠功能开启 - 全环橙色
        上述功能都开启：
        上半环紫色(自动暂停)
        下半环橙色(睡眠功能)
        """
        messagebox.showinfo("使用方法", usage_text.strip())
    
    def open_project_url(self, _=None):
        """打开项目GitHub地址"""
        import webbrowser
        try:
            webbrowser.open("https://github.com/cmd-png/SeewoScreenPeepingDetector")
        except Exception as e:
            show_message("打开失败", f"无法打开项目地址: {str(e)}", True)

    def show_settings_dialog(self, _=None):
        """显示设置对话框"""
        try:
            if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
                self.settings_window.lift()
                return

            self.settings_window = Toplevel(self.root)
            self.settings_window.title("更多设置")
            self.settings_window.geometry("400x300")  # 增加窗口高度以容纳新控件
            self.settings_window.resizable(False, False)
            self._center_window(self.settings_window)
            
            self.settings_window.protocol("WM_DELETE_WINDOW", self._close_settings_window)
            
            # 创建控件
            self._create_settings_controls()
            
            # 绑定回车键
            self.settings_window.bind('<Return>', self._save_settings)
            
        except Exception as e:
            show_message("错误", f"无法创建设置窗口: {str(e)}", True)

    def _center_window(self, window):
        """居中显示窗口"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')

    def _create_settings_controls(self):
        """创建设置对话框控件"""
        # 监测间隔设置
        ttk.Label(self.settings_window, text="监测间隔(0.02-10秒):").grid(
            row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.interval_var = StringVar(value=str(self.global_settings["check_interval"]))
        interval_entry = ttk.Entry(self.settings_window, textvariable=self.interval_var, width=10)
        interval_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # 弹窗显示时间设置
        ttk.Label(self.settings_window, text="弹窗显示时间(1-30秒):").grid(
            row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.alert_duration_var = StringVar(value=str(self.global_settings["alert_duration"]))
        alert_duration_entry = ttk.Entry(self.settings_window, 
                                       textvariable=self.alert_duration_var, 
                                       width=10)
        alert_duration_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # 弹窗置顶设置
        self.alert_on_top_var = BooleanVar(value=self.global_settings["alert_on_top"])
        alert_on_top_cb = ttk.Checkbutton(self.settings_window, 
                                         text="弹窗置顶显示", 
                                         variable=self.alert_on_top_var)
        alert_on_top_cb.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # 自动暂停后静音设置
        self.auto_mute_var = BooleanVar(value=self.global_settings.get("auto_mute", False))
        auto_mute_cb = ttk.Checkbutton(self.settings_window,
                                      text="自动暂停执行后使电脑静音",
                                      variable=self.auto_mute_var)
        auto_mute_cb.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # 仅对rtcRemoteDesktop.exe生效设置
        self.only_rtc_effective_var = BooleanVar(value=self.global_settings.get("only_rtc_effective", False))
        only_rtc_effective_cb = ttk.Checkbutton(self.settings_window,
                                               text="仅对rtcRemoteDesktop.exe生效",
                                               variable=self.only_rtc_effective_var)
        only_rtc_effective_cb.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        ttk.Label(self.settings_window, text="注：请查看使用方法后再启用此功能！").grid(
            row=5, column=0, padx=10, pady=5, sticky="w")
        
        # 保存按钮
        save_button = ttk.Button(
            self.settings_window, 
            text="保存设置", 
            command=self._save_settings
        )
        save_button.grid(row=6, column=0, columnspan=2, pady=10)
        
        interval_entry.focus_set()

    def _close_settings_window(self):
        """安全关闭设置窗口"""
        if hasattr(self, 'settings_window'):
            try:
                self.settings_window.destroy()
                del self.settings_window
            except:
                pass

    def _save_settings(self, _=None):
        """保存设置"""
        try:
            # 验证输入
            interval = float(self.interval_var.get())
            alert_duration = int(self.alert_duration_var.get())
            
            if not 0.02 <= interval <= 10:
                messagebox.showerror("错误", "监测间隔必须在0.02秒到10秒之间")
                return
                
            if not 1 <= alert_duration <= 30:
                messagebox.showerror("错误", "弹窗显示时间必须在1秒到30秒之间")
                return
            
            # 更新设置
            self.global_settings.update({
                "check_interval": interval,
                "alert_duration": alert_duration,
                "alert_on_top": self.alert_on_top_var.get(),
                "auto_mute": self.auto_mute_var.get(),
                "only_rtc_effective": self.only_rtc_effective_var.get()
            })
            self.save_current_settings()
            
            self._close_settings_window()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def _generate_icon(self):
        """生成托盘图标（带缓存）- 使用透明背景"""
        # 生成状态标识
        current_state = (
            self.global_settings['show_alert'],
            self.global_settings['enable_hotkey'],
            self.global_settings['auto_pause'],  # 改为自动暂停
            self.global_settings['enable_sleep'],
            self.global_settings['auto_kill'],
            self._get_center_status_color(),  # 中心状态颜色
            self.global_settings['only_rtc_effective'],  # 仅对远程生效状态
            self.global_settings['auto_kill']  # 结束进程状态
        )
        
        # 如果状态未变化且缓存存在，直接返回缓存
        if current_state == self.last_icon_state and current_state in self.icon_cache:
            return self.icon_cache[current_state]
            
        try:
            # 使用RGBA模式创建透明背景图像
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))  # 完全透明背景
            draw = ImageDraw.Draw(img)
            
            # 绘制状态环
            self._draw_status_rings(draw)
            
            # 绘制中心状态
            self._draw_center_status(draw)
            
            # 如果启用了结束进程功能，绘制红色正方形边框
            if self.global_settings['auto_kill']:
                draw.rectangle([2, 2, 62, 62], outline=(255, 0, 0, 255), width=3)  # 添加Alpha通道
            
            # 更新缓存
            self.icon_cache[current_state] = img
            self.last_icon_state = current_state
            return img
        except Exception as e:
            show_message(f"生成图标失败: {str(e)}")
            # 创建透明背景的红色错误图标
            error_img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(error_img)
            draw.ellipse((16, 16, 48, 48), fill=(255, 0, 0, 255))
            return error_img

    def _draw_status_rings(self, draw):
        """绘制状态环 - 使用RGBA颜色"""
        # 外环状态 - 表示弹窗提醒和全局热键
        if self.global_settings['show_alert'] and self.global_settings['enable_hotkey']:
            # 两个功能都开启 - 绘制双色环
            draw.arc((8, 8, 56, 56), 0, 180, (0, 191, 255, 255), 3)  # 上半环蓝色(弹窗提醒)
            draw.arc((8, 8, 56, 56), 180, 360, (215, 194, 70, 255), 3)  # 下半环黄色(全局热键)
        elif self.global_settings['show_alert']:
            # 只有弹窗提醒开启 - 全环亮蓝色
            draw.arc((8, 8, 56, 56), 0, 360, (0, 191, 255, 255), 3)
        elif self.global_settings['enable_hotkey']:
            # 只有全局热键开启 - 全环黄色
            draw.arc((8, 8, 56, 56), 0, 360, (215, 194, 70, 255), 3)
        else:
            # 两个功能都关闭 - 灰色环
            draw.arc((8, 8, 56, 56), 0, 360, (100, 100, 100, 255), 3)
        
        # 内环状态(16-48像素直径) - 表示自动暂停和睡眠功能
        if self.global_settings['auto_pause'] and self.global_settings['enable_sleep']:
            # 两个功能都开启 - 绘制双色环
            draw.arc((16, 16, 48, 48), 180, 360, (128, 0, 255, 255), 3)  # 上半环绿色(自动暂停)
            draw.arc((16, 16, 48, 48), 0, 180, (255, 119, 0, 255), 3)  # 下半环橙色(睡眠功能)
        elif self.global_settings['auto_pause']:
            # 只有自动暂停开启 - 全环绿色
            draw.arc((16, 16, 48, 48), 0, 360, (128, 0, 255, 255), 3)
        elif self.global_settings['enable_sleep']:
            # 只有睡眠功能开启 - 全环橙色
            draw.arc((16, 16, 48, 48), 0, 360, (255, 119, 0, 255), 3)
        else:
            # 两个功能都关闭 - 灰色环
            draw.arc((16, 16, 48, 48), 0, 360, (100, 100, 100, 255), 3)

    def _draw_center_status(self, draw):
        """绘制中心状态 - 使用RGBA颜色"""
        status_color = self._get_center_status_color()
        # 确保颜色有Alpha通道
        if len(status_color) == 3:
            status_color = (*status_color, 255)
        draw.ellipse((22, 22, 42, 42), fill=status_color)

    def _get_center_status_color(self):
        """获取中心状态颜色 - 返回RGBA颜色"""
        if self.process_states.get("rtcRemoteDesktop.exe", False):
            return (255, 0, 0, 255)  # 红色
        elif self.process_states.get("screenCapture.exe", False):
            return (255, 255, 0, 255)  # 黄色
        elif any(self.process_states.values()):
            return (255, 0, 0, 255)  # 红色
        return (0, 255, 0, 255)  # 绿色

    def start_monitoring(self):
        """启动监控线程"""
        try:
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop, 
                name="ProcessMonitorThread",
                daemon=True
            )
            self.monitor_thread.start()
            self.root.after(100, self._keep_alive)
        except Exception as e:
            show_message("监控错误", f"无法启动监控线程: {str(e)}", True)
        self._update_tray()

    def _keep_alive(self):
        """保持主循环运行"""
        if self.running:
            self.root.after(100, self._keep_alive)

    def _send_media_key(self):
        """模拟发送媒体播放/暂停键"""
        try:
            # Windows多媒体键代码 - VK_MEDIA_PLAY_PAUSE (0xB3)
            win32api.keybd_event(0xB3, 0, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(0xB3, 0, 2, 0)  # KEYEVENTF_KEYUP = 2
        except Exception as e:
            show_message("媒体控制", f"无法控制媒体播放状态: {str(e)}", True)
            
    def _mute_system(self):
        """使系统静音"""
        try:
            # Windows多媒体键代码 - VK_VOLUME_MUTE (0xAD)
            win32api.keybd_event(0xAD, 0, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(0xAD, 0, 2, 0)  # KEYEVENTF_KEYUP = 2
        except Exception as e:
            show_message("静音控制", f"无法控制系统音量: {str(e)}", True)

    def _monitoring_loop(self):
        """优化后的监控循环"""
        self.last_process_states = self.process_states.copy()
        
        while self.running:
            try:
                time.sleep(self.global_settings["check_interval"])
                self._check_processes()
            except Exception as e:
                show_message("监控错误", f"监控循环错误: {str(e)}", True)
            finally:
                time.sleep(0.02)  # 减少CPU占用

    def _check_processes(self):
        """优化后的进程检查方法"""
        current_states = {}
        any_running = False
        
        all_processes = list(psutil.process_iter(['pid', 'name']))
        
        # 检查每个监控进程的状态
        for proc_name in PROCESS_CONFIG:
            running = False
            invalid_pids = set()
            
            # 先检查缓存
            for pid in self.process_cache[proc_name]:
                try:
                    p = psutil.Process(pid)
                    if p.name().lower() == proc_name.lower() and p.is_running():
                        running = True
                        break
                    else:
                        invalid_pids.add(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    invalid_pids.add(pid)
            
            # 清理无效的PID
            self.process_cache[proc_name] -= invalid_pids
            
            # 如果缓存中没有找到,则扫描所有进程
            if not running:
                for p in all_processes:
                    try:
                        if p.info['name'].lower() == proc_name.lower():
                            self.process_cache[proc_name].add(p.info['pid'])
                            running = True
                            break
                    except:
                        continue
            
            current_states[proc_name] = running
            if running:
                any_running = True
        
        # 处理状态变化
        state_changed = False
        for proc_name, running in current_states.items():
            if running != self.process_states[proc_name]:
                self._handle_state_change(proc_name, running)
                self.process_states[proc_name] = running
                state_changed = True
        
        # 处理自动结束进程逻辑
        if self.global_settings["auto_kill"]:
            for proc_name, running in current_states.items():
                # 如果启用了"仅对远程生效"，则只检查rtcRemoteDesktop.exe
                if self.global_settings["only_rtc_effective"] and proc_name != "rtcRemoteDesktop.exe":
                    continue
                    
                if running:
                    # 尝试结束进程
                    if terminate_process_by_name(proc_name):
                        self.process_states[proc_name] = False
                        state_changed = True
        
        # 处理媒体暂停和静音逻辑
        if self.global_settings["auto_pause"]:
            # 如果启用了"仅对远程生效"，则只检查rtcRemoteDesktop.exe
            if self.global_settings["only_rtc_effective"]:
                should_pause = current_states.get("rtcRemoteDesktop.exe", False)
            else:
                should_pause = any_running
                
            if should_pause and not self.media_paused:
                self._send_media_key()
                self.media_paused = True
                # 如果启用了自动静音，在暂停后执行静音
                if self.global_settings.get("auto_mute", False):
                    self._mute_system()
            elif not should_pause and self.media_paused:
                self._send_media_key()
                self.media_paused = False
        
        # 处理睡眠功能
        self._handle_sleep_function(any_running)
        
        # 只有在状态发生变化时才更新托盘图标
        if state_changed:
            self._update_tray()
        
        self.last_process_states = self.process_states.copy()

    def _handle_sleep_function(self, any_running):
        """睡眠功能逻辑"""
        # 如果启用了"仅对远程生效"，则只检查rtcRemoteDesktop.exe
        if self.global_settings["only_rtc_effective"]:
            should_sleep = self.process_states.get("rtcRemoteDesktop.exe", False)
        else:
            should_sleep = any_running
            
        if self.global_settings["enable_sleep"] and should_sleep and not self.sleep_triggered:
            try:
                system_sleep()
                self.sleep_triggered = True
                self.global_settings["enable_sleep"] = False
                self.save_current_settings()
                self._update_tray()
                show_message("睡眠模式", "系统已进入过睡眠状态，睡眠功能已自动禁用")
            except Exception as e:
                show_message("睡眠失败", f"无法进入睡眠状态：{str(e)}", True)
        elif not should_sleep and self.sleep_triggered:
            self.sleep_triggered = False

    def _is_process_running(self, process_name):
        """检查指定进程是否在运行"""
        try:
            return any(proc.info['name'].lower() == process_name.lower()
                     for proc in psutil.process_iter(['name']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        except Exception as e:
            show_message(f"检查进程运行状态错误: {str(e)}")
            return False

    def _handle_state_change(self, process_name, new_state):
        """处理进程状态变化"""
        try:
            if self.global_settings["show_alert"]:
                self._show_alert_window(process_name, new_state)
            
            if self.global_settings["enable_hotkey"] and process_name in PROCESS_CONFIG:
                # 如果启用了"仅对远程生效"，则只对rtcRemoteDesktop.exe触发热键
                if self.global_settings["only_rtc_effective"] and process_name != "rtcRemoteDesktop.exe":
                    return
                self._trigger_hotkeys(process_name, new_state)
        except Exception as e:
            show_message(f"处理状态变化错误: {str(e)}")

    def _show_alert_window(self, process_name, new_state):
        """显示状态变化弹窗"""
        alert_window = Toplevel(self.root)
        alert_window.title("状态变化")
        alert_window.geometry("300x100")
        alert_window.resizable(False, False)
        self._center_window(alert_window)
        message = f"{process_name} 已{'启动' if new_state else '终止'}！"
        ttk.Label(alert_window, text=message).pack(pady=20)
        duration = self.global_settings["alert_duration"] * 1000
        alert_window.after(duration, alert_window.destroy)
        if self.global_settings["alert_on_top"]:
            alert_window.lift()
            alert_window.attributes('-topmost', True)
            alert_window.after(100, lambda: alert_window.attributes('-topmost', False))

    def _trigger_hotkeys(self, process_name, new_state):
        """触发热键操作"""
        try:
            key = PROCESS_CONFIG[process_name][0 if new_state else 1]
            keyboard.press_and_release(key)
            
            if not new_state:
                time.sleep(0.2)
                keyboard.press_and_release('ctrl+windows+left')
        except Exception as e:
            show_message(f"热键模拟错误: {str(e)}")

    def _update_tray(self):
        """更新托盘图标和菜单"""
        try:
            self.tray_icon.icon = self._generate_icon()
            self.tray_icon.update_menu()
        except Exception as e:
            show_message(f"更新托盘图标错误: {str(e)}")

    def save_current_settings(self):
        """保存当前设置"""
        try:
            settings = {
                "auto_start": self.auto_start,
                "show_alert": self.global_settings["show_alert"],
                "alert_on_top": self.global_settings["alert_on_top"],
                "enable_hotkey": self.global_settings["enable_hotkey"],
                "enable_sleep": self.global_settings["enable_sleep"],
                "auto_pause": self.global_settings["auto_pause"],  # 新增自动暂停设置保存
                "auto_kill": self.global_settings["auto_kill"],  # 新增自动结束进程设置保存
                "check_interval": self.global_settings["check_interval"],
                "alert_duration": self.global_settings["alert_duration"],
                "only_rtc_effective": self.global_settings["only_rtc_effective"]  # 新增设置保存
            }
            save_settings(settings)
        except Exception as e:
            show_message(f"保存设置错误: {str(e)}")

    def toggle_auto_start(self, _=None):
        """切换开机自启设置"""
        try:
            # 尝试修改注册表
            set_registry_auto_start(not self.auto_start)
            self.auto_start = not self.auto_start
            self.save_current_settings()
            self._update_tray()
        except Exception as e:
            # 如果权限不足，请求管理员权限
            if "拒绝访问" in str(e) or "access denied" in str(e).lower():
                if request_admin():
                    # 管理员权限请求成功，退出当前实例
                    self.clean_exit()
            else:
                show_message("设置失败", f"操作失败: {str(e)}", True)

    def toggle_alert(self, _=None):
        """切换弹窗提醒设置"""
        self.global_settings["show_alert"] = not self.global_settings["show_alert"]
        self.save_current_settings()
        self._update_tray()

    def toggle_hotkey(self, _=None):
        """切换热键功能设置"""
        self.global_settings["enable_hotkey"] = not self.global_settings["enable_hotkey"]
        self.save_current_settings()
        self._update_tray()
    
    def toggle_sleep(self, _=None):
        """切换睡眠功能设置"""
        self.global_settings["enable_sleep"] = not self.global_settings["enable_sleep"]
        self.sleep_triggered = False
        self.save_current_settings()
        self._update_tray()
    
    def toggle_auto_pause(self, _=None):
        """切换自动暂停设置"""
        self.global_settings["auto_pause"] = not self.global_settings["auto_pause"]
        self.save_current_settings()
        self._update_tray()
    
    def toggle_auto_kill(self, _=None):
        """切换自动结束进程设置"""
        # 移除了管理员权限检查
        self.global_settings["auto_kill"] = not self.global_settings["auto_kill"]
        self.save_current_settings()
        self._update_tray()
    
    def toggle_only_rtc_effective(self, _=None):
        """切换仅对远程生效设置"""
        if not ["only_rtc_effective"]:
            show_message("警告","使用此功能可能导致被管理员线下真实/n作者不对因使用本软件带来的任何后果及连带后果负责")
        self.global_settings["only_rtc_effective"] = not self.global_settings["only_rtc_effective"]
        self.save_current_settings()
        self._update_tray()
    
    def toggle_alert_on_top(self, _=None):
        """切换弹窗置顶设置"""
        self.global_settings["alert_on_top"] = not self.global_settings["alert_on_top"]
        self.save_current_settings()
        self._update_tray()

    def show_status(self, _=None):
        """显示当前状态"""
        try:
            status_lines = [
                "全局监控状态：",
                f"🚀 开机自启：{'✔ 启用' if self.auto_start else '❌ 禁用'}",
                f"📢 弹窗提醒：{'✔ 启用' if self.global_settings['show_alert'] else '❌ 禁用'}",
                f"🔝 弹窗置顶：{'✔ 启用' if self.global_settings['alert_on_top'] else '❌ 禁用'}",
                f"⌨️ 全局热键：{'✔ 启用' if self.global_settings['enable_hotkey'] else '❌ 禁用'}",
                f"💤 睡眠功能：{'✔ 启用' if self.global_settings['enable_sleep'] else '❌ 禁用'}",
                f"⏸️ 自动暂停：{'✔ 启用' if self.global_settings['auto_pause'] else '❌ 禁用'}",
                f"🔴 结束进程：{'✔ 启用' if self.global_settings['auto_kill'] else '❌ 禁用'}",
                f"🎯 仅对rtcRemoteDesktop.exe生效：{'✔ 启用' if self.global_settings['only_rtc_effective'] else '❌ 禁用'}",
                f"⏱️ 监测间隔：{self.global_settings['check_interval']} 秒",
                f"🕒 弹窗显示时间：{self.global_settings['alert_duration']} 秒",
                "V1.1.2"
                "",
                "进程状态："
            ]
            
            for proc, state in self.process_states.items():
                status_lines.append(f"• {proc}: {'🔴运行中' if state else '🟢已停止'}")
                
            messagebox.showinfo("系统状态", "\n".join(status_lines))
        except Exception as e:
            show_message("错误", f"无法显示状态: {str(e)}", True)
    
    def clean_exit(self, _=None):
        """安全退出程序"""
        try:
            self.running = False
            if hasattr(self, 'tray_icon'):
                self.tray_icon.stop()
            if hasattr(self, 'root'):
                self.root.after(100, self.root.destroy)
        except Exception as e:
            show_message(f"退出错误: {str(e)}")
        finally:
            os._exit(0)

if __name__ == "__main__":
    try:
        # 显示免责声明
        if not show_disclaimer():
            sys.exit(0)

        # 确保只有一个实例运行
        if platform.system() == 'Windows':
            mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "GlobalProcessWatcherMutex")
            if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                show_message("错误", "程序已经在运行中", True)
                sys.exit(1)
                
        app = GlobalProcessWatcher()
        app.root.mainloop()
    except Exception as e:
        show_message("启动失败", f"初始化错误: {str(e)}", True)
        sys.exit(1)
