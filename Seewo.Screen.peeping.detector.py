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

def check_dependencies():
    """前置依赖检查"""
    required = {'psutil': 'psutil', 'keyboard': 'keyboard', 'PIL': 'pillow', 'pystray': 'pystray'}
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
    from threading import Lock
    from PIL import Image, ImageDraw
    from pystray import Icon, MenuItem
except ImportError as e:
    show_message("缺少依赖", f"无法导入必要模块: {str(e)}\n请尝试手动安装依赖", True)
    sys.exit(1)
# ================= 全局配置 =================
PROCESS_CONFIG = {
    "rtcRemoteDesktop.exe": ["ctrl+windows+d", "ctrl+windows+f4"],
    "screenCapture.exe": ["ctrl+windows+d", "ctrl+windows+f4"],
    "notepad.exe": ["ctrl+windows+d", "ctrl+windows+f4"]
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
    "alert_duration": 3  # 默认弹窗显示5秒
}

settings_lock = Lock()

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
        self.last_update_time = 0 # 添加进程ID缓存
        self.process_cache = {p: set() for p in PROCESS_CONFIG}  # {进程名: 进程ID集合}# 添加图标缓存
        self.icon_cache = {}
        self.last_icon_state = None
        
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
            MenuItem("🌐 项目地址", self.open_project_url),
            MenuItem("⛔ 退出程序", self.clean_exit)
        ]
        return menu_items
    
    
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
        """生成托盘图标（带缓存）"""
        # 生成状态标识
        current_state = (
            self.global_settings['show_alert'],
            self.global_settings['enable_hotkey'],
            self.global_settings['alert_on_top'],
            self.global_settings['enable_sleep'],
            self._get_center_status_color()  # 中心状态颜色
        )
        
        # 如果状态未变化且缓存存在，直接返回缓存
        if current_state == self.last_icon_state and current_state in self.icon_cache:
            return self.icon_cache[current_state]
            
        try:
            img = Image.new('RGB', (64, 64), (40, 40, 40))
            draw = ImageDraw.Draw(img)
            
            # 绘制状态环
            self._draw_status_rings(draw)
            
            # 绘制中心状态
            self._draw_center_status(draw)
            
            # 更新缓存
            self.icon_cache[current_state] = img
            self.last_icon_state = current_state
            return img
        except Exception as e:
            show_message(f"生成图标失败: {str(e)}")
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
        """优化后的监控循环"""
        self.last_process_states = self.process_states.copy()
        
        while self.running:
            try:
                # 使用事件等待代替固定sleep
                time.sleep(self.global_settings["check_interval"])
                self._check_processes()
            except Exception as e:
                show_message(f"监控循环错误: {str(e)}")
            finally:
                time.sleep(0.02)  #减少CPU占用

    def _check_processes(self):
        """优化后的进程检查方法"""
        # 使用缓存检查进程状态
        current_states = {}
        any_running = False
        
        # 获取所有进程列表（减少调用次数）
        all_processes = list(psutil.process_iter(['pid', 'name']))
        
        for proc_name in PROCESS_CONFIG:
            # 首先检查缓存中的进程是否还存在
            running = False
            invalid_pids = set()
            
            for pid in self.process_cache[proc_name]:
                try:
                    p = psutil.Process(pid)
                    if p.name().lower() == proc_name.lower() and p.is_running():
                        running = True
                    else:
                        invalid_pids.add(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    invalid_pids.add(pid)
            
            # 移除无效的PID
            self.process_cache[proc_name] -= invalid_pids
            
            # 如果缓存中没有运行中的进程，扫描新进程
            if not running:
                for p in all_processes:
                    try:
                        if p.info['name'].lower() == proc_name.lower():
                            self.process_cache[proc_name].add(p.info['pid'])
                            running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    except Exception:
                        continue
            
            current_states[proc_name] = running
            if running:
                any_running = True
        
        # 处理状态变化
        for proc_name, running in current_states.items():
            if running != self.process_states[proc_name]:
                self._handle_state_change(proc_name, running)
                self.process_states[proc_name] = running
        
        # 处理睡眠功能
        self._handle_sleep_function(any_running)
        
        # 仅在状态变化时更新托盘
        if any(self.process_states.values()) != any(self.last_process_states.values()):
            self._update_tray()
        
        self.last_process_states = self.process_states.copy()

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

if __name__ == "__main__":
    try:
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
