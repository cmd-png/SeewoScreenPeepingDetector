import sys
import subprocess
from tkinter import Tk, messagebox, ttk,Toplevel, StringVar
from threading import Thread

# ================= 前置依赖检查 =================
def show_message(title, message, is_error=False):
    """通用弹窗函数"""
    root = Tk()
    root.withdraw()
    (messagebox.showerror if is_error else messagebox.showinfo)(title, message)
    root.destroy()

def create_progress_window(package_count):
    """创建进度窗口"""
    root = Tk()
    root.title("安装依赖")
    root.geometry("400x150")
    root.resizable(False, False)
    
    # 计算居中位置
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - 400) // 2
    y = (screen_height - 150) // 2
    root.geometry(f"+{x}+{y}")
    
    progress_label = ttk.Label(root, text="准备安装依赖...")
    progress_label.pack(pady=5)
    
    progress_bar = ttk.Progressbar(root, orient="horizontal", 
                                 length=300, mode="determinate")
    progress_bar.pack(pady=10)
    
    detail_label = ttk.Label(root, text="")
    detail_label.pack(pady=5)
    
    current_pkg_label = ttk.Label(root, text="")
    current_pkg_label.pack(pady=5)
    
    return root, progress_bar, progress_label, detail_label, current_pkg_label

def check_dependencies():
    """前置依赖检查"""
    required = {'psutil': 'psutil', 'keyboard': 'keyboard', 'PIL': 'pillow', 'pystray': 'pystray'}
    missing = []
    
    for lib, pkg in required.items():
        try: __import__(lib)
        except ImportError: missing.append(pkg)
    
    if not missing:
        return
    
    # 显示初始提示
    show_message("依赖安装", f"检测到缺少依赖库：{', '.join(missing)}\n点击确定开始自动安装...")
    
    # 创建主窗口和进度组件
    progress_root = Tk()
    progress_root.title("安装依赖")
    progress_root.geometry("400x150")
    
    progress_label = ttk.Label(progress_root, text="准备安装依赖...")
    progress_label.pack(pady=5)
    
    progress_bar = ttk.Progressbar(progress_root, orient="horizontal", 
                                 length=300, mode="determinate")
    progress_bar.pack(pady=10)
    
    detail_label = ttk.Label(progress_root, text="")
    detail_label.pack(pady=5)
    
    current_pkg_label = ttk.Label(progress_root, text="")
    current_pkg_label.pack(pady=5)
    
    # 共享状态变量
    install_complete = False
    failed_packages = []
    check_again = False
    
    def update_progress(current, total, package, message):
        progress_bar['value'] = (current / total) * 100
        progress_label.config(text=f"进度: {current}/{total}")
        current_pkg_label.config(text=f"正在安装: {package}")
        detail_label.config(text=message)
    
    def on_closing():
        if not install_complete:
            if messagebox.askokcancel("退出", "依赖安装尚未完成，确定要退出吗？"):
                progress_root.destroy()
                sys.exit(1)
        else:
            progress_root.destroy()
    
    progress_root.protocol("WM_DELETE_WINDOW", on_closing)
    
    def install_dependencies():
        nonlocal install_complete, failed_packages, check_again
        total = len(missing)
        
        for i, package in enumerate(missing, 1):
            progress_root.after(0, lambda: update_progress(i-1, total, package, "准备安装..."))
            
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                output = result.stdout
                if "Downloading" in output:
                    progress_root.after(0, lambda: update_progress(i-1, total, package, output.strip()))
                elif "Installing" in output:
                    progress_root.after(0, lambda: update_progress(i-1, total, package, output.strip()))
                
                progress_root.after(0, lambda: update_progress(i, total, package, f"{package} 安装成功"))
                
            except subprocess.CalledProcessError as e:
                progress_root.after(0, lambda: update_progress(i, total, package, f"{package} 安装失败"))
                failed_packages.append(package)
                continue
        
        install_complete = True
        
        if failed_packages:
            progress_root.after(0, lambda: messagebox.showerror(
                "安装失败", 
                f"以下依赖安装失败：{', '.join(failed_packages)}\n请手动执行：\npip install {' '.join(failed_packages)}"
            ))
            progress_root.after(0, progress_root.destroy)
            sys.exit(1)
        
        # 安装后再次检查
        check_again = True
        for lib in required:
            try: 
                __import__(lib)
            except ImportError:
                progress_root.after(0, lambda: messagebox.showerror(
                    "严重错误", 
                    f"{lib} 仍缺失，请手动安装！"
                ))
                progress_root.after(0, progress_root.destroy)
                sys.exit(1)
        
        progress_root.after(0, lambda: messagebox.showinfo("安装成功", "所有依赖已安装！"))
        progress_root.after(0, progress_root.destroy)
    
    # 启动安装线程
    Thread(target=install_dependencies, daemon=True).start()
    progress_root.mainloop()
    
    # 确保所有依赖确实已安装
    if check_again:
        for lib in required:
            try: __import__(lib)
            except ImportError:
                show_message("严重错误", f"{lib} 仍缺失，请手动安装！", True)
                sys.exit(1)

check_dependencies()  # 前置执行依赖检查
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
    from threading import Lock
    from PIL import Image, ImageDraw
    from pystray import Icon, MenuItem
except:
    show_message("缺少依赖", "无法自动安装依赖，请尝试手动安装依赖")
# ================= 全局配置 =================
PROCESS_CONFIG = {
    "rtcRemoteDesktop.exe": ["ctrl+windows+d", "ctrl+windows+f4"],
    "screenCapture.exe": ["ctrl+windows+d", "ctrl+windows+f4"]
}
DEFAULT_CHECK_INTERVAL = 0.25  # 默认监测间隔(秒)
SETTINGS_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'GlobalProcessWatcher')
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')
DEFAULT_SETTINGS = {
    "auto_start": False, 
    "show_alert": False, 
    "alert_on_top": False,
    "enable_hotkey": False,
    "enable_sleep": False,
    "check_interval": DEFAULT_CHECK_INTERVAL,
    "alert_duration": 1  # 默认弹窗显示1秒
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
    免责声明

    本程序仅供技术研究和学习使用，开发者不承担用户因使用此程序而造成的一切责任。

    使用本程序即表示您同意以下条款：
    1. 您将自行承担使用本程序的所有风险和责任
    2. 开发者不对程序的适用性、安全性或可靠性作任何保证
    3. 开发者不承担因使用本程序导致的任何直接或间接损失

    如果您不同意上述条款，请点击"拒绝"按钮退出程序。
    """
    
    root = Tk()
    root.title("免责声明")
    root.geometry("600x400")
    root.resizable(False, False)
    
    # 计算居中位置
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - 600) // 2
    y = (screen_height - 400) // 2
    root.geometry(f"+{x}+{y}")
    
    # 创建文本区域
    text = ttk.Label(root, text=disclaimer_text, justify="left", padding=10)
    text.pack(fill="both", expand=True)
    
    # 创建按钮框架
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)
    
    accepted = False
    
    def on_accept():
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
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
            )
            sys.exit(0)
        except Exception as e:
            show_message("权限错误", f"权限请求失败：{str(e)}", True)
            sys.exit(1)

# ================= 注册表操作 =================
def get_registry_auto_start():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "GlobalProcessWatcher")
            return value == sys.executable
    except: return False

def set_registry_auto_start(enable):
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
            if enable:
                winreg.SetValueEx(key, "GlobalProcessWatcher", 0, winreg.REG_SZ, f'"{sys.executable}"')
            else:
                try: winreg.DeleteValue(key, "GlobalProcessWatcher")
                except FileNotFoundError: pass
    except Exception as e: raise RuntimeError(f"注册表操作失败：{str(e)}")

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
    """配置保存"""
    ensure_settings_dir()
    try:
        with settings_lock:
            temp_file = f"{SETTINGS_FILE}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            if os.path.exists(SETTINGS_FILE):
                os.remove(SETTINGS_FILE)
            os.rename(temp_file, SETTINGS_FILE)
    except Exception as e:
        show_message("配置错误", f"保存设置失败：{str(e)}", True)

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
            "check_interval": max(0.02, min(10, float(self.settings.get("check_interval", DEFAULT_CHECK_INTERVAL)))),
            "alert_on_top": self.settings.get("alert_on_top", True),
            "alert_duration": self.settings.get("alert_duration", 5)
        }
        self.process_states = {p: False for p in PROCESS_CONFIG}
        self.sleep_triggered = False
        self.last_update_time = 0
        
        self._initialize_components()
        
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
            MenuItem(lambda _: f"🔝 弹窗置顶：{'✔' if self.global_settings['alert_on_top'] else '❌'}", self.toggle_alert_on_top),
            MenuItem(lambda _: f"⌨️ 全局热键：{'✔' if self.global_settings['enable_hotkey'] else '❌'}", self.toggle_hotkey),
            MenuItem(lambda _: f"💤 睡眠功能：{'✔' if self.global_settings['enable_sleep'] else '❌'}", self.toggle_sleep),
            MenuItem("✏️ 更多设置", self.show_settings_dialog),
            MenuItem("📊 当前状态", self.show_status),
            MenuItem("⛔ 退出程序", self.clean_exit)
        ]
        return menu_items

    def show_settings_dialog(self, _=None):
        """显示设置对话框"""
        try:
            if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
                self.settings_window.lift()
                return

            self.settings_window = Toplevel(self.root)
            self.settings_window.title("更多设置")
            self.settings_window.geometry("400x200")
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
        
        # 保存按钮
        save_button = ttk.Button(
            self.settings_window, 
            text="保存设置", 
            command=self._save_settings
        )
        save_button.grid(row=2, column=0, columnspan=2, pady=20)
        
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
                "alert_duration": alert_duration
            })
            self.save_current_settings()
            
            self._close_settings_window()
            show_message("设置成功", 
                        f"监测间隔已设置为 {interval} 秒\n"
                        f"弹窗显示时间已设置为 {alert_duration} 秒")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def _generate_icon(self):
        """生成托盘图标"""
        try:
            img = Image.new('RGB', (64, 64), (40, 40, 40))
            draw = ImageDraw.Draw(img)
            
            # 绘制状态环
            self._draw_status_rings(draw)
            
            # 绘制中心状态
            self._draw_center_status(draw)
            
            return img
        except Exception as e:
            print(f"生成图标失败: {str(e)}")
            return Image.new('RGB', (64, 64), (255, 0, 0))

    def _draw_status_rings(self, draw):
        """绘制状态环"""
        # 外环状态 - 表示弹窗提醒和全局热键
        if self.global_settings['show_alert'] and self.global_settings['enable_hotkey']:
            # 两个功能都开启 - 绘制双色环
            draw.arc((8, 8, 56, 56), 0, 180, (0, 191, 255), 3)  # 上半环蓝色(弹窗提醒)
            draw.arc((8, 8, 56, 56), 180, 360, (255, 204, 0), 3)  # 下半环黄色(全局热键)
        elif self.global_settings['show_alert']:
            # 只有弹窗提醒开启 - 全环亮蓝色
            draw.arc((8, 8, 56, 56), 0, 360, (0, 191, 255), 3)
        elif self.global_settings['enable_hotkey']:
            # 只有全局热键开启 - 全环黄色
            draw.arc((8, 8, 56, 56), 0, 360, (255, 204, 0), 3)
        else:
            # 两个功能都关闭 - 灰色环
            draw.arc((8, 8, 56, 56), 0, 360, (100, 100, 100), 3)
        
        # 内环状态(16-48像素直径) - 表示弹窗置顶和睡眠功能
        if self.global_settings['alert_on_top'] and self.global_settings['enable_sleep']:
            # 两个功能都开启 - 绘制双色环
            draw.arc((16, 16, 48, 48), 180, 360, (0, 255, 255), 3)  # 上半环亮绿色(弹窗置顶)
            draw.arc((16, 16, 48, 48), 0, 180, (255, 119, 0), 3)  # 下半环橙色(睡眠功能)
        elif self.global_settings['alert_on_top']:
            # 只有弹窗置顶开启 - 全环亮绿色
            draw.arc((16, 16, 48, 48), 0, 360, (0, 255, 255), 3)
        elif self.global_settings['enable_sleep']:
            # 只有睡眠功能开启 - 全环橙色
            draw.arc((16, 16, 48, 48), 0, 360, (255, 119, 0), 3)
        else:
            # 两个功能都关闭 - 灰色环
            draw.arc((16, 16, 48, 48), 0, 360, (100, 100, 100), 3)

    def _get_outer_ring_color(self):
        """获取外环颜色"""
        if self.global_settings['show_alert'] and self.global_settings['enable_hotkey']:
            return (0, 191, 255)  # 蓝色
        elif self.global_settings['show_alert']:
            return (0, 191, 255)  # 蓝色
        elif self.global_settings['enable_hotkey']:
            return (255, 204, 0)  # 黄色
        return (100, 100, 100)  # 灰色

    def _get_inner_ring_color(self):
        """获取内环颜色"""
        if self.global_settings['alert_on_top'] and self.global_settings['enable_sleep']:
            return (0, 255, 255)  # 亮绿色
        elif self.global_settings['alert_on_top']:
            return (0, 255, 255)  # 亮绿色
        elif self.global_settings['enable_sleep']:
            return (255, 119, 0)  # 橙色
        return (100, 100, 100)  # 灰色

    def _draw_center_status(self, draw):
        """绘制中心状态"""
        status_color = self._get_center_status_color()
        draw.ellipse((22, 22, 42, 42), fill=status_color)

    def _get_center_status_color(self):
        """获取中心状态颜色"""
        if self.process_states.get("rtcRemoteDesktop.exe", False):
            return (255, 0, 0)  # 红色
        elif self.process_states.get("screenCapture.exe", False):
            return (255, 255, 0)  # 黄色
        elif any(self.process_states.values()):
            return (255, 0, 0)  # 红色
        return (0, 255, 0)  # 绿色

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

    def _keep_alive(self):
        """保持主循环运行"""
        if self.running:
            self.root.after(100, self._keep_alive)

    def _monitoring_loop(self):
        """主监控循环"""
        while self.running:
            try:
                current_time = time.time()
                if current_time - self.last_update_time >= self.global_settings["check_interval"]:
                    self.last_update_time = current_time
                    self._check_processes()
            except Exception as e:
                show_message(f"监控循环错误: {str(e)}")
            finally:
                time.sleep(0.02)  #减少CPU占用

    def _check_processes(self):
        """检查进程状态"""
        current_states = {p: self._is_process_running(p) for p in PROCESS_CONFIG}
        any_running = any(current_states.values())
        
        self._handle_sleep_function(any_running)
        
        for proc in PROCESS_CONFIG:
            if current_states[proc] != self.process_states[proc]:
                self._handle_state_change(proc, current_states[proc])
                self.process_states[proc] = current_states[proc]
        
        self._update_tray()

    def _handle_sleep_function(self, any_running):
        """睡眠功能逻辑"""
        if self.global_settings["enable_sleep"] and any_running and not self.sleep_triggered:
            try:
                system_sleep()
                self.sleep_triggered = True
                self.global_settings["enable_sleep"] = False
                self.save_current_settings()
                self._update_tray()
                show_message("睡眠模式", "系统已进入过睡眠状态，睡眠功能已自动禁用")
            except Exception as e:
                show_message("睡眠失败", f"无法进入睡眠状态：{str(e)}", True)
        elif not any_running and self.sleep_triggered:
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
        
        message = f"{process_name} 已 {'启动' if new_state else '终止'}！"
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
                "check_interval": self.global_settings["check_interval"],
                "alert_duration": self.global_settings["alert_duration"]
            }
            save_settings(settings)
        except Exception as e:
            show_message(f"保存设置错误: {str(e)}")

    def toggle_auto_start(self, _=None):
        """切换开机自启设置"""
        try:
            set_registry_auto_start(not self.auto_start)
            self.auto_start = not self.auto_start
            self.save_current_settings()
            self._update_tray()
            show_message("设置成功", f"开机自启已{'启用' if self.auto_start else '禁用'}！")
        except Exception as e:
            show_message("设置失败", f"操作失败: {str(e)}\n请以管理员权限运行！", True)

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
                f"⏱️ 监测间隔：{self.global_settings['check_interval']} 秒",
                f"🕒 弹窗显示时间：{self.global_settings['alert_duration']} 秒",
                "",
                "进程状态："
            ]
            
            for proc, state in self.process_states.items():
                status_lines.append(f"• {proc}: {'🟢 运行中' if state else '🔴 已停止'}")
                
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

# ================= 主程序入口 =================
if __name__ == "__main__":
    try:
        # 确保配置目录存在
        ensure_settings_dir()
        
        # 显示免责声明
        if not show_disclaimer():
            sys.exit(0)
            
        if os.name == 'nt' and not is_admin():
            request_admin()
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