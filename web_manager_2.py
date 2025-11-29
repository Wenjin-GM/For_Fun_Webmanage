import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import json
import os
import functools
import subprocess

# === 🎨 全局配置 (Modern Clean - 现代极简风) ===
COLORS = {
    "bg_main": "#F3F4F6",  # 整体背景 - 极浅灰蓝
    "bg_card": "#FFFFFF",  # 卡片背景 - 纯白
    "primary": "#3B82F6",  # 主色调 - 科技蓝
    "primary_hover": "#2563EB",  # 主色调悬停 - 深蓝
    "text_main": "#1F2937",  # 主要文字 - 深灰
    "text_sub": "#6B7280",  # 次要文字 - 中灰
    "text_on_bg": "#1F2937",  # 背景文字
    "border": "#E5E7EB",  # 边框线
    "white": "#FFFFFF",
    "success": "#10B981",  # 成功色
    "danger": "#EF4444",  # 危险色
    "item_hover": "#F9FAFB",  # 列表项悬停
    "item_selected": "#EFF6FF",  # 列表项选中 - 淡蓝
}

FONTS = {
    "h1": ("Microsoft YaHei UI", 16, "bold"),
    "h2": ("Microsoft YaHei UI", 11, "bold"),
    "body": ("Microsoft YaHei UI", 10),
    "body_bold": ("Microsoft YaHei UI", 10, "bold"),
    "small": ("Microsoft YaHei UI", 9),
}

# === 浏览器路径配置 ===
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


# === 视觉工具 ===

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*[int(x) for x in rgb])


def interpolate_color(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return rgb_to_hex((r, g, b))


class ToastNotification:
    def __init__(self, master, message, kind="info"):
        self.top = tk.Toplevel(master)
        self.top.overrideredirect(True)
        bg_color = COLORS["text_main"]
        fg_color = COLORS["white"]
        if kind == "success": bg_color = COLORS["success"]
        if kind == "error": bg_color = COLORS["danger"]
        self.top.configure(bg=bg_color)
        lbl = tk.Label(self.top, text=message, fg=fg_color, bg=bg_color, font=FONTS["body_bold"], padx=20, pady=10)
        lbl.pack()
        master.update_idletasks()
        try:
            x = master.winfo_rootx() + (master.winfo_width() // 2) - (lbl.winfo_reqwidth() // 2)
            y = master.winfo_rooty() + master.winfo_height() - 100
            self.top.geometry(f"+{x}+{y}")
        except:
            self.top.geometry("+100+100")
        self.alpha = 0.0
        self.top.attributes("-alpha", self.alpha)
        self.fade_in()

    def fade_in(self):
        if self.alpha < 0.9:
            self.alpha += 0.1
            self.top.attributes("-alpha", self.alpha)
            self.top.after(20, self.fade_in)
        else:
            self.top.after(2000, self.fade_out)

    def fade_out(self):
        if self.alpha > 0:
            self.alpha -= 0.1
            self.top.attributes("-alpha", self.alpha)
            self.top.after(30, self.fade_out)
        else:
            self.top.destroy()


class AnimatedButton(tk.Button):
    def __init__(self, master, text, command, bg=COLORS["primary"], fg=COLORS["white"], width=None, **kwargs):
        font = kwargs.pop("font", FONTS["body_bold"])
        super().__init__(master, text=text, command=command, bg=bg, fg=fg,
                         font=font, relief="flat", activebackground=bg,
                         activeforeground=fg, cursor="hand2", width=width, bd=0, **kwargs)
        self.default_bg = bg
        self.hover_bg = COLORS["primary_hover"]
        self.current_bg = bg
        self.target_bg = bg
        self.animation_running = False
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.target_bg = self.hover_bg
        if not self.animation_running:
            self.animate()

    def on_leave(self, e):
        self.target_bg = self.default_bg
        if not self.animation_running:
            self.animate()

    def animate(self):
        self.animation_running = True
        c1 = self.current_bg
        c2 = self.target_bg
        if c1 == c2:
            self.animation_running = False
            return
        new_color = interpolate_color(c1, c2, 0.2)
        self.configure(bg=new_color, activebackground=new_color)
        self.current_bg = new_color
        if self.current_bg == self.target_bg:
            self.animation_running = False
        else:
            self.after(20, self.animate)


# === 防崩溃安全网 ===
def safe_action(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            print(f"⚠️ 操作异常 [{func.__name__}]: {e}")
            try:
                self.refresh_group_list()
                if self.current_active_group:
                    self.refresh_site_list(self.current_active_group)
            except:
                pass

    return wrapper


class WebManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Manager Pro")
        self.root.geometry("1100x700")  # 稍微加宽一点以容纳备注列
        self.root.configure(bg=COLORS["bg_main"])

        self.current_active_group = None
        self.context_item_site = None
        self.context_item_group = None

        self.available_browsers = self.detect_browsers()
        self.configure_styles()
        self.data_file = "bookmarks.json"
        self.data = self.load_data()

        if self.data:
            self.current_active_group = list(self.data.keys())[0]

        self.root.attributes("-alpha", 0.0)
        self.setup_ui()
        self.fade_in_window()

    def fade_in_window(self):
        alpha = self.root.attributes("-alpha")
        if alpha < 1.0:
            alpha += 0.05
            self.root.attributes("-alpha", alpha)
            self.root.after(15, self.fade_in_window)

    def detect_browsers(self):
        found = {}
        for name, paths in POTENTIAL_BROWSERS.items():
            for path in paths:
                if os.path.exists(path):
                    found[name] = path
                    break
        return found

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLORS["bg_card"], foreground=COLORS["text_main"],
                        rowheight=40, fieldbackground=COLORS["bg_card"], font=FONTS["body"], borderwidth=0)
        style.configure("Treeview.Heading", background=COLORS["bg_card"], foreground=COLORS["text_sub"],
                        font=FONTS["h2"], relief="flat")
        style.map("Treeview", background=[('selected', COLORS["item_selected"])],
                  foreground=[('selected', COLORS["primary"])])

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"常用工具": [{"name": "Google", "url": "https://www.google.com", "note": ""}], "学习资料": [],
                "娱乐": []}

    def save_data(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        top_bar = tk.Frame(self.root, bg=COLORS["bg_main"], height=60)
        top_bar.pack(fill=tk.X, padx=30, pady=(20, 10))
        top_bar.pack_propagate(False)
        tk.Label(top_bar, text="🌏 我的网站收藏", bg=COLORS["bg_main"], fg=COLORS["text_on_bg"], font=FONTS["h1"]).pack(
            side=tk.LEFT, anchor="w")

        content_area = tk.Frame(self.root, bg=COLORS["bg_main"])
        content_area.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))

        # === 左侧分组 ===
        left_card = tk.Frame(content_area, bg=COLORS["bg_card"], width=260)
        left_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left_card.pack_propagate(False)

        left_header = tk.Frame(left_card, bg=COLORS["bg_card"], height=60)
        left_header.pack(fill=tk.X, padx=20)
        left_header.pack_propagate(False)
        tk.Label(left_header, text="分组", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["h2"]).pack(
            side=tk.LEFT, pady=15)
        AnimatedButton(left_header, text="+", command=self.add_group, width=3, height=1, font=FONTS["body_bold"]).pack(
            side=tk.RIGHT, pady=15)
        tk.Frame(left_card, bg=COLORS["border"], height=1).pack(fill=tk.X, padx=20)

        self.group_tree = ttk.Treeview(left_card, show="tree", selectmode="browse")
        self.group_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.group_tree.bind("<Motion>", self.on_group_hover)
        self.group_tree.bind("<Leave>", self.on_group_leave)
        self.group_tree.bind("<Button-1>", self.handle_group_click)
        self.group_tree.bind("<Button-3>", self.show_group_menu)
        self.group_tree.tag_configure("active_group", font=FONTS["body_bold"], foreground=COLORS["primary"])
        self.group_tree.tag_configure("normal_group", font=FONTS["body"], foreground=COLORS["text_main"])

        # === 右侧列表 ===
        right_card = tk.Frame(content_area, bg=COLORS["bg_card"])
        right_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        right_header = tk.Frame(right_card, bg=COLORS["bg_card"], height=60)
        right_header.pack(fill=tk.X, padx=20)
        right_header.pack_propagate(False)
        tk.Label(right_header, text="网站列表", bg=COLORS["bg_card"], fg=COLORS["text_main"], font=FONTS["h2"]).pack(
            side=tk.LEFT, pady=15)
        AnimatedButton(right_header, text="+ 添加网站", command=self.add_website, width=12).pack(side=tk.RIGHT, pady=12)
        tk.Frame(right_card, bg=COLORS["border"], height=1).pack(fill=tk.X, padx=20)

        # 修改：增加“备注”列
        columns = ("name", "url", "note")
        self.site_tree = ttk.Treeview(right_card, columns=columns, show="headings", selectmode="browse")

        self.site_tree.heading("name", text="网站名称", anchor="w")
        self.site_tree.heading("url", text="网址 URL", anchor="w")
        self.site_tree.heading("note", text="备注", anchor="w")  # 新增表头

        self.site_tree.column("name", width=200, anchor="w")
        self.site_tree.column("url", width=350, anchor="w")
        self.site_tree.column("note", width=200, anchor="w")  # 新增列宽

        scrollbar = ttk.Scrollbar(right_card, orient=tk.VERTICAL, command=self.site_tree.yview)
        self.site_tree.configure(yscroll=scrollbar.set)
        self.site_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 5))

        self.site_tree.bind("<Motion>", self.on_site_hover)
        self.site_tree.bind("<Leave>", self.on_site_leave)
        self.site_tree.bind("<Button-1>", self.handle_site_click)
        self.site_tree.bind("<Button-3>", self.show_site_menu)
        self.site_tree.tag_configure("even", background=COLORS["bg_card"])
        self.site_tree.tag_configure("odd", background="#FAFAFA")

        self.create_context_menus()
        self.refresh_group_list()
        if self.current_active_group:
            self.refresh_site_list(self.current_active_group)

    def create_context_menus(self):
        self.group_menu = tk.Menu(self.root, tearoff=0, font=FONTS["body"])
        self.group_menu.add_command(label="重命名", command=self.rename_group)
        self.group_menu.add_command(label="删除分组", command=self.delete_group)
        self.group_menu.add_separator()
        self.group_menu.add_command(label="上移", command=lambda: self.move_item(self.group_tree, True, "up"))
        self.group_menu.add_command(label="下移", command=lambda: self.move_item(self.group_tree, True, "down"))

        self.site_menu = tk.Menu(self.root, tearoff=0, font=FONTS["body"])
        if self.available_browsers:
            self.browser_submenu = tk.Menu(self.site_menu, tearoff=0, font=FONTS["body"])
            self.site_menu.add_cascade(label="打开方式 (Open With)", menu=self.browser_submenu)
            self.browser_submenu.add_command(label="系统默认", command=lambda: self.open_with_browser("Default"))
            self.browser_submenu.add_separator()
            for b_name, b_path in self.available_browsers.items():
                self.browser_submenu.add_command(label=f"{b_name}", command=lambda p=b_path: self.open_with_browser(p))
            self.site_menu.add_separator()
        self.site_menu.add_command(label="编辑", command=self.edit_website)
        self.site_menu.add_command(label="删除", command=self.delete_website)
        self.site_menu.add_separator()
        self.site_menu.add_command(label="上移", command=lambda: self.move_item(self.site_tree, False, "up"))
        self.site_menu.add_command(label="下移", command=lambda: self.move_item(self.site_tree, False, "down"))
        self.site_menu.add_command(label="置顶", command=lambda: self.move_item(self.site_tree, False, "top"))
        self.site_menu.add_command(label="置底", command=lambda: self.move_item(self.site_tree, False, "bottom"))

    @safe_action
    def open_with_browser(self, browser_path):
        item_id = self.context_item_site
        if not item_id:
            sel = self.site_tree.selection()
            if sel: item_id = sel[0]
        if not item_id: return
        item = self.site_tree.item(item_id)
        url = item['values'][1]
        if browser_path == "Default":
            webbrowser.open(url)
        else:
            try:
                subprocess.Popen([browser_path, url])
            except Exception as e:
                messagebox.showerror("启动失败", f"无法启动浏览器：\n{e}")

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
        if item_id:
            if item_id not in self.site_tree.selection():
                self.site_tree.selection_set(item_id)
            # 移除了 Tooltip 显示逻辑

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
            webbrowser.open(url)

    @safe_action
    def show_site_menu(self, event):
        item_id = self.site_tree.identify_row(event.y)
        if item_id:
            self.context_item_site = item_id
            self.site_tree.selection_set(item_id)
            self.site_menu.post(event.x_root, event.y_root)

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
            note = site.get("note", "")  # 获取备注
            # 插入数据包含 note
            self.site_tree.insert("", tk.END, iid=str(i), values=(site["name"], site["url"], note), tags=(tag,))

    @safe_action
    def add_group(self):
        # 创建自定义弹窗，而不是使用 simpledialog
        add_window = tk.Toplevel(self.root)
        add_window.title("新建分组")
        add_window.configure(bg=COLORS["bg_card"])

        # 设定窗口大小：宽 380，高 200，确保标题能完整显示
        self.center_window(add_window, 380, 200)

        # 标签
        tk.Label(add_window, text="请输入分组名称:", bg=COLORS["bg_card"], font=FONTS["body"]).place(x=40, y=30)

        # 输入框
        entry_name = tk.Entry(add_window, width=32, font=FONTS["body"], relief="solid", bd=1)
        entry_name.place(x=40, y=65)
        entry_name.focus_set()  # 自动聚焦，方便直接输入

        # 确认逻辑
        def confirm_add(event=None):  # 支持回车键确认
            name = entry_name.get().strip()
            if not name:
                return
            if name in self.data:
                messagebox.showerror("错误", "该分组已存在", parent=add_window)
                return

            self.data[name] = []
            self.save_data()
            self.current_active_group = name
            self.refresh_group_list()
            self.refresh_site_list(name)
            add_window.destroy()
            ToastNotification(self.root, f"分组 '{name}' 已创建", "success")

        # 绑定回车键
        add_window.bind('<Return>', confirm_add)

        # 按钮 (使用我们自定义的 AnimatedButton)
        btn_confirm = AnimatedButton(add_window, text="确认", command=confirm_add, width=12)
        btn_confirm.place(x=40, y=120)

        btn_cancel = AnimatedButton(add_window, text="取消", command=add_window.destroy, width=12, bg="#E0E0E0",
                                    fg=COLORS["text_main"])
        btn_cancel.place(x=200, y=120)

    @safe_action
    def add_website(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("添加新网站")
        add_window.configure(bg=COLORS["bg_card"])
        self.center_window(add_window, 420, 350)

        current_selection = self.group_tree.selection()
        if current_selection:
            default_group = current_selection[0]
        else:
            default_group = self.current_active_group if self.current_active_group else ""
        existing_groups = list(self.data.keys())

        def create_input(label_text, y_pos):
            tk.Label(add_window, text=label_text, bg=COLORS["bg_card"], font=FONTS["body"]).place(x=40, y=y_pos)
            entry = tk.Entry(add_window, width=30, font=FONTS["body"], relief="solid", bd=1)
            entry.place(x=130, y=y_pos)
            return entry

        entry_name = create_input("网站名称:", 40)
        entry_name.focus_set()
        entry_url = create_input("网址 URL:", 90)
        entry_url.insert(0, "https://")

        entry_note = create_input("备注 (选填):", 140)

        tk.Label(add_window, text="选择分组:", bg=COLORS["bg_card"], font=FONTS["body"]).place(x=40, y=190)
        combo_group = ttk.Combobox(add_window, values=existing_groups, width=28, font=FONTS["body"])
        combo_group.place(x=130, y=190)
        if default_group in existing_groups:
            combo_group.set(default_group)
        elif existing_groups:
            combo_group.current(0)

        def confirm_add():
            name = entry_name.get().strip()
            url = entry_url.get().strip()
            note = entry_note.get().strip()
            group = combo_group.get().strip()
            if not name or not url or not group: return
            if group not in self.data:
                self.data[group] = []
                self.refresh_group_list()
            self.data[group].append({"name": name, "url": url, "note": note})
            self.save_data()
            if group == self.current_active_group:
                self.refresh_site_list(group)
            add_window.destroy()
            ToastNotification(self.root, "网站添加成功", "success")

        AnimatedButton(add_window, text="确认添加", command=confirm_add, width=12).place(x=80, y=270)
        AnimatedButton(add_window, text="取消", command=add_window.destroy, width=12, bg="#E0E0E0",
                       fg=COLORS["text_main"]).place(x=220, y=270)

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
            ToastNotification(self.root, "重命名成功")

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
            ToastNotification(self.root, "分组已删除", "error")

    @safe_action
    def edit_website(self):
        item_id = self.context_item_site if self.context_item_site else self.site_tree.selection()
        if not item_id: return
        if isinstance(item_id, tuple): item_id = item_id[0]
        group_name = self.current_active_group
        index = int(item_id)
        site_data = self.data[group_name][index]

        edit_window = tk.Toplevel(self.root)
        edit_window.title("编辑网站")
        edit_window.configure(bg=COLORS["bg_card"])
        self.center_window(edit_window, 420, 300)

        def create_input(label_text, y_pos, val):
            tk.Label(edit_window, text=label_text, bg=COLORS["bg_card"], font=FONTS["body"]).place(x=40, y=y_pos)
            entry = tk.Entry(edit_window, width=30, font=FONTS["body"], relief="solid", bd=1)
            entry.place(x=130, y=y_pos)
            entry.insert(0, val)
            return entry

        e_name = create_input("名称:", 40, site_data["name"])
        e_url = create_input("网址:", 90, site_data["url"])
        e_note = create_input("备注:", 140, site_data.get("note", ""))

        def confirm_edit():
            new_name = e_name.get().strip()
            new_url = e_url.get().strip()
            new_note = e_note.get().strip()
            if new_name and new_url:
                self.data[group_name][index] = {"name": new_name, "url": new_url, "note": new_note}
                self.save_data()
                self.refresh_site_list(group_name)
                edit_window.destroy()
                ToastNotification(self.root, "修改已保存")

        AnimatedButton(edit_window, text="保存", command=confirm_edit, width=12).place(x=80, y=220)
        AnimatedButton(edit_window, text="取消", command=edit_window.destroy, width=12, bg="#E0E0E0",
                       fg=COLORS["text_main"]).place(x=220, y=220)

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
            ToastNotification(self.root, "网站已删除", "error")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = WebManagerApp(root)
    root.mainloop()