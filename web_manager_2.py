import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import json
import os
import functools
import subprocess  # 新增：用于启动外部浏览器进程

# === 全局配置 ===
COLORS = {
    "primary": "#4A90E2",
    "primary_hover": "#357ABD",
    "bg_light": "#FFFFFF",
    "bg_gray": "#F5F7FA",
    "text_dark": "#333333",
    "text_light": "#FFFFFF",
}

FONTS = {
    "h1": ("Microsoft YaHei UI", 12, "bold"),
    "body": ("Microsoft YaHei UI", 10),
    "body_bold": ("Microsoft YaHei UI", 10, "bold"),
    "small": ("Microsoft YaHei UI", 9)
}

# === 浏览器路径配置 (Windows 常用路径) ===
# 程序启动时会自动检测这些路径是否存在
POTENTIAL_BROWSERS = {
    "Chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ],
    "Edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ],
    "Firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
    ],
    "Brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    ]
}


# === 防崩溃安全网 ===
def safe_action(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            print(f"⚠️ 操作异常 [{func.__name__}]: {e}")
            self.refresh_group_list()
            if self.current_active_group:
                self.refresh_site_list(self.current_active_group)

    return wrapper


class ModernButton(tk.Button):
    def __init__(self, master, text, command, bg=COLORS["primary"], fg=COLORS["text_light"], **kwargs):
        super().__init__(master, text=text, command=command, bg=bg, fg=fg,
                         font=FONTS["body"], relief="flat", activebackground=COLORS["primary_hover"],
                         activeforeground=fg, cursor="hand2", **kwargs)
        self.default_bg = bg
        self.hover_bg = COLORS["primary_hover"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e): self["bg"] = self.hover_bg

    def on_leave(self, e): self["bg"] = self.default_bg


class WebManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ 网站收藏管理器 (多浏览器版)")
        self.root.geometry("900x600")
        self.root.configure(bg=COLORS["bg_light"])

        # 状态变量
        self.current_active_group = None
        self.context_item_site = None
        self.context_item_group = None

        # === 检测已安装的浏览器 ===
        self.available_browsers = self.detect_browsers()

        self.configure_styles()
        self.data_file = "bookmarks.json"
        self.data = self.load_data()

        if self.data:
            self.current_active_group = list(self.data.keys())[0]

        self.setup_ui()

    def detect_browsers(self):
        """检测系统中实际存在的浏览器"""
        found = {}
        for name, paths in POTENTIAL_BROWSERS.items():
            for path in paths:
                if os.path.exists(path):
                    found[name] = path
                    break  # 找到一个路径即可
        return found

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLORS["bg_light"], foreground=COLORS["text_dark"],
                        rowheight=38, fieldbackground=COLORS["bg_light"], font=FONTS["body"], borderwidth=0)
        style.configure("Treeview.Heading", background=COLORS["bg_gray"], foreground=COLORS["text_dark"],
                        font=FONTS["h1"], relief="flat")
        style.map("Treeview", background=[('selected', COLORS["primary"])],
                  foreground=[('selected', COLORS["text_light"])])

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"常用工具": [{"name": "Google", "url": "https://www.google.com"}], "学习资料": [], "娱乐": []}

    def save_data(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        # === 左侧布局 ===
        left_frame = tk.Frame(self.root, width=240, bg=COLORS["bg_gray"])
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        left_frame.pack_propagate(False)

        tk.Label(left_frame, text="📁 分组列表", bg=COLORS["bg_gray"], fg=COLORS["text_dark"], font=FONTS["h1"]).pack(
            fill=tk.X, pady=(20, 10), padx=15)

        self.group_tree = ttk.Treeview(left_frame, show="tree", selectmode="browse")
        self.group_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.group_tree.bind("<Motion>", self.on_group_hover)
        self.group_tree.bind("<Leave>", self.on_group_leave)
        self.group_tree.bind("<Button-1>", self.handle_group_click)
        self.group_tree.bind("<Button-3>", self.show_group_menu)

        self.group_tree.tag_configure("active_group", font=FONTS["body_bold"], foreground=COLORS["primary"])
        self.group_tree.tag_configure("normal_group", font=FONTS["body"])

        btn_frame_left = tk.Frame(left_frame, bg=COLORS["bg_gray"])
        btn_frame_left.pack(fill=tk.X, padx=15, pady=20)
        ModernButton(btn_frame_left, text="+ 新建分组", command=self.add_group).pack(fill=tk.X)

        # === 右侧布局 ===
        right_frame = tk.Frame(self.root, bg=COLORS["bg_light"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(right_frame, bg=COLORS["bg_light"])
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        tk.Label(header_frame, text="🌐 网站列表", bg=COLORS["bg_light"], fg=COLORS["text_dark"], font=FONTS["h1"]).pack(
            side=tk.LEFT)
        tk.Label(header_frame, text="(右键选择打开方式)", bg=COLORS["bg_light"], fg="#999999",
                 font=FONTS["small"]).pack(side=tk.LEFT, padx=10, pady=5)
        ModernButton(header_frame, text="+ 添加网站", command=self.add_website, width=12).pack(side=tk.RIGHT)

        tree_frame = tk.Frame(right_frame, bg=COLORS["bg_light"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("name", "url")
        self.site_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.site_tree.heading("name", text="网站名称")
        self.site_tree.heading("url", text="网址 URL")
        self.site_tree.column("name", width=200)
        self.site_tree.column("url", width=400)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.site_tree.yview)
        self.site_tree.configure(yscroll=scrollbar.set)
        self.site_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.site_tree.bind("<Motion>", self.on_site_hover)
        self.site_tree.bind("<Leave>", self.on_site_leave)
        self.site_tree.bind("<Button-1>", self.handle_site_click)
        self.site_tree.bind("<Button-3>", self.show_site_menu)

        self.site_tree.tag_configure("even", background="#FAFAFA")
        self.site_tree.tag_configure("odd", background=COLORS["bg_light"])

        self.create_context_menus()
        self.refresh_group_list()
        if self.current_active_group:
            self.refresh_site_list(self.current_active_group)

    # === 【关键更新】 上下文菜单 ===

    def create_context_menus(self):
        # 分组菜单
        self.group_menu = tk.Menu(self.root, tearoff=0, font=FONTS["body"])
        self.group_menu.add_command(label="✏️ 重命名", command=self.rename_group)
        self.group_menu.add_command(label="🗑️ 删除分组", command=self.delete_group)
        self.group_menu.add_separator()
        self.group_menu.add_command(label="⬆️ 上移", command=lambda: self.move_item(self.group_tree, True, "up"))
        self.group_menu.add_command(label="⬇️ 下移", command=lambda: self.move_item(self.group_tree, True, "down"))

        # 网站菜单
        self.site_menu = tk.Menu(self.root, tearoff=0, font=FONTS["body"])

        # --- 子菜单：打开方式 ---
        # 如果检测到了任何浏览器，就创建子菜单
        if self.available_browsers:
            self.browser_submenu = tk.Menu(self.site_menu, tearoff=0, font=FONTS["body"])
            self.site_menu.add_cascade(label="🚀 打开方式 (Open With)", menu=self.browser_submenu)

            # 添加“默认浏览器”选项
            self.browser_submenu.add_command(label="💻 系统默认", command=lambda: self.open_with_browser("Default"))
            self.browser_submenu.add_separator()

            # 动态添加检测到的浏览器
            for b_name, b_path in self.available_browsers.items():
                # 使用 lambda 闭包捕获参数
                self.browser_submenu.add_command(label=f"🌐 {b_name}",
                                                 command=lambda p=b_path: self.open_with_browser(p))

            self.site_menu.add_separator()
        # ---------------------

        self.site_menu.add_command(label="✏️ 编辑", command=self.edit_website)
        self.site_menu.add_command(label="🗑️ 删除", command=self.delete_website)
        self.site_menu.add_separator()
        self.site_menu.add_command(label="⬆️ 上移", command=lambda: self.move_item(self.site_tree, False, "up"))
        self.site_menu.add_command(label="⬇️ 下移", command=lambda: self.move_item(self.site_tree, False, "down"))
        self.site_menu.add_command(label="🔝 置顶", command=lambda: self.move_item(self.site_tree, False, "top"))
        self.site_menu.add_command(label="BOTTOM 置底", command=lambda: self.move_item(self.site_tree, False, "bottom"))

    # === 【新功能】 浏览器启动逻辑 ===

    @safe_action
    def open_with_browser(self, browser_path):
        """使用指定浏览器打开当前选中的网站"""
        # 获取当前选中的 URL
        # 注意：这里我们使用 context_item_site (右键时的行)
        item_id = self.context_item_site
        if not item_id:
            # 容错：如果右键没抓到，尝试取 selection
            sel = self.site_tree.selection()
            if sel: item_id = sel[0]

        if not item_id: return

        item = self.site_tree.item(item_id)
        url = item['values'][1]

        if browser_path == "Default":
            webbrowser.open(url)
        else:
            # 使用 subprocess 调用外部 exe 打开 url
            try:
                subprocess.Popen([browser_path, url])
            except Exception as e:
                messagebox.showerror("启动失败", f"无法启动浏览器：\n{e}")

    # === 移动逻辑 ===

    @safe_action
    def move_item(self, tree, is_group, direction):
        item = self.context_item_group if is_group else self.context_item_site
        if not item:
            sel = tree.selection()
            if sel: item = sel[0]

        if not item: return

        parent = tree.parent(item)
        current_idx = tree.index(item)
        total_items = len(tree.get_children(parent))
        target_idx = current_idx

        if direction == "up":
            if current_idx > 0: target_idx = current_idx - 1
        elif direction == "down":
            if current_idx < total_items - 1: target_idx = current_idx + 1
        elif direction == "top":
            target_idx = 0
        elif direction == "bottom":
            target_idx = total_items

        if target_idx != current_idx:
            tree.move(item, parent, target_idx)
            self.sync_data_order(is_group)

    def sync_data_order(self, is_group):
        if is_group:
            new_keys = self.group_tree.get_children()
            new_data = {}
            for key in new_keys:
                if key in self.data:
                    new_data[key] = self.data[key]
            self.data = new_data
            self.save_data()
            self.refresh_group_list()
        else:
            if not self.current_active_group: return
            new_order_ids = self.site_tree.get_children()
            old_site_list = self.data[self.current_active_group]
            new_site_list = []
            for iid in new_order_ids:
                try:
                    original_index = int(iid)
                    if original_index < len(old_site_list):
                        new_site_list.append(old_site_list[original_index])
                except:
                    pass
            self.data[self.current_active_group] = new_site_list
            self.save_data()
            self.refresh_site_list(self.current_active_group)

    # === 基础交互 ===

    @safe_action
    def on_group_hover(self, event):
        item_id = self.group_tree.identify_row(event.y)
        if item_id and item_id not in self.group_tree.selection():
            self.group_tree.selection_set(item_id)

    @safe_action
    def on_group_leave(self, event):
        if self.group_tree.selection():
            self.group_tree.selection_remove(self.group_tree.selection())

    @safe_action
    def handle_group_click(self, event):
        item_id = self.group_tree.identify_row(event.y)
        if item_id:
            self.current_active_group = item_id
            self.refresh_group_list()
            self.refresh_site_list(self.current_active_group)

    @safe_action
    def show_group_menu(self, event):
        item_id = self.group_tree.identify_row(event.y)
        if item_id:
            self.context_item_group = item_id
            self.group_tree.selection_set(item_id)
            self.group_menu.post(event.x_root, event.y_root)

    @safe_action
    def on_site_hover(self, event):
        item_id = self.site_tree.identify_row(event.y)
        if item_id and item_id not in self.site_tree.selection():
            self.site_tree.selection_set(item_id)

    @safe_action
    def on_site_leave(self, event):
        if self.site_tree.selection():
            self.site_tree.selection_remove(self.site_tree.selection())

    @safe_action
    def handle_site_click(self, event):
        item_id = self.site_tree.identify_row(event.y)
        if item_id:
            item = self.site_tree.item(item_id)
            url = item['values'][1]
            # 默认点击仍然使用系统默认浏览器
            webbrowser.open(url)

    @safe_action
    def show_site_menu(self, event):
        item_id = self.site_tree.identify_row(event.y)
        if item_id:
            self.context_item_site = item_id
            self.site_tree.selection_set(item_id)
            self.site_menu.post(event.x_root, event.y_root)

    # === 界面刷新与增删改 ===

    def refresh_group_list(self):
        sel = self.group_tree.selection()
        for item in self.group_tree.get_children(): self.group_tree.delete(item)
        for group in self.data.keys():
            tag = "active_group" if group == self.current_active_group else "normal_group"
            text = f"👉 {group}" if group == self.current_active_group else f"   {group}"
            self.group_tree.insert("", tk.END, iid=group, text=text, tags=(tag,))
        try:
            if sel and self.group_tree.exists(sel[0]): self.group_tree.selection_set(sel)
        except:
            pass

    def refresh_site_list(self, group_name):
        for item in self.site_tree.get_children(): self.site_tree.delete(item)
        sites = self.data.get(group_name, [])
        for i, site in enumerate(sites):
            tag = "even" if i % 2 == 0 else "odd"
            self.site_tree.insert("", tk.END, iid=str(i), values=(site["name"], site["url"]), tags=(tag,))

    @safe_action
    def add_group(self):
        name = simpledialog.askstring("新建分组", "请输入分组名称：")
        if name and name not in self.data:
            self.data[name] = []
            self.save_data()
            self.current_active_group = name
            self.refresh_group_list()
            self.refresh_site_list(name)

    @safe_action
    def add_website(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("添加新网站")
        add_window.configure(bg=COLORS["bg_light"])
        self.center_window(add_window, 420, 300)

        current_selection = self.group_tree.selection()
        if current_selection:
            default_group = current_selection[0]
        else:
            default_group = self.current_active_group if self.current_active_group else ""
        existing_groups = list(self.data.keys())

        def create_input(label_text, y_pos):
            tk.Label(add_window, text=label_text, bg=COLORS["bg_light"], font=FONTS["body"]).place(x=40, y=y_pos)
            entry = tk.Entry(add_window, width=30, font=FONTS["body"], relief="solid", bd=1)
            entry.place(x=130, y=y_pos)
            return entry

        entry_name = create_input("网站名称:", 40)
        entry_name.focus_set()
        entry_url = create_input("网址 URL:", 90)
        entry_url.insert(0, "https://")

        tk.Label(add_window, text="选择分组:", bg=COLORS["bg_light"], font=FONTS["body"]).place(x=40, y=140)
        combo_group = ttk.Combobox(add_window, values=existing_groups, width=28, font=FONTS["body"])
        combo_group.place(x=130, y=140)
        if default_group in existing_groups:
            combo_group.set(default_group)
        elif existing_groups:
            combo_group.current(0)

        def confirm_add():
            name = entry_name.get().strip()
            url = entry_url.get().strip()
            group = combo_group.get().strip()
            if not name or not url or not group: return
            if group not in self.data:
                self.data[group] = []
                self.refresh_group_list()
            self.data[group].append({"name": name, "url": url})
            self.save_data()
            if group == self.current_active_group:
                self.refresh_site_list(group)
            add_window.destroy()

        ModernButton(add_window, text="确认添加", command=confirm_add, width=12).place(x=80, y=220)
        ModernButton(add_window, text="取消", command=add_window.destroy, width=12, bg="#E0E0E0",
                     fg=COLORS["text_dark"]).place(x=220, y=220)

    def center_window(self, win, width, height):
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        win.geometry(f"{width}x{height}+{x}+{y}")

    @safe_action
    def rename_group(self):
        t = self.context_item_group or self.current_active_group
        if not t: return
        n = simpledialog.askstring("重命名", "新名称:", initialvalue=t)
        if n and n != t:
            keys = list(self.data.keys())
            idx = keys.index(t)
            new_data = {}
            for k in keys: new_data[n if k == t else k] = self.data[k]
            self.data = new_data
            if self.current_active_group == t: self.current_active_group = n
            self.save_data()
            self.refresh_group_list()
            self.refresh_site_list(self.current_active_group)

    @safe_action
    def delete_group(self):
        t = self.context_item_group or self.current_active_group
        if t and messagebox.askyesno("确认", "删除?"):
            del self.data[t]
            if self.current_active_group == t: self.current_active_group = list(self.data.keys())[
                0] if self.data else None
            self.save_data()
            self.refresh_group_list()
            if self.current_active_group:
                self.refresh_site_list(self.current_active_group)
            else:
                [self.site_tree.delete(i) for i in self.site_tree.get_children()]

    @safe_action
    def edit_website(self):
        item_id = self.context_item_site if self.context_item_site else self.site_tree.selection()
        if not item_id: return
        if isinstance(item_id, tuple): item_id = item_id[0]
        group_name = self.current_active_group
        index = int(item_id)
        site_data = self.data[group_name][index]
        new_name = simpledialog.askstring("编辑", "名称：", initialvalue=site_data["name"])
        new_url = simpledialog.askstring("编辑", "网址：", initialvalue=site_data["url"])
        if new_name and new_url:
            self.data[group_name][index] = {"name": new_name, "url": new_url}
            self.save_data()
            self.refresh_site_list(group_name)

    @safe_action
    def delete_website(self):
        item_id = self.context_item_site if self.context_item_site else self.site_tree.selection()
        if not item_id: return
        if isinstance(item_id, tuple): item_id = item_id[0]
        group_name = self.current_active_group
        index = int(item_id)
        if messagebox.askyesno("确认", "确定删除该网站吗？"):
            self.data[group_name].pop(index)
            self.save_data()
            self.refresh_site_list(group_name)


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = WebManagerApp(root)
    root.mainloop()