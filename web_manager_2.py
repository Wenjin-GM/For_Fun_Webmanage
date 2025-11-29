import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import json
import os

# === 全局配置 ===
COLORS = {
    "primary": "#4A90E2",
    "primary_hover": "#357ABD",
    "bg_light": "#FFFFFF",
    "bg_gray": "#F5F7FA",
    "text_dark": "#333333",
    "text_light": "#FFFFFF",
    "ghost_bg": "#4A90E2",
    "ghost_alpha": 0.8,
    "indicator": "#4A90E2"
}

FONTS = {
    "h1": ("Microsoft YaHei UI", 12, "bold"),
    "body": ("Microsoft YaHei UI", 10),
    "body_bold": ("Microsoft YaHei UI", 10, "bold"),
    "small": ("Microsoft YaHei UI", 9)
}


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
        self.root.title("✨ 网站收藏管理器 (稳定版)")
        self.root.geometry("900x600")
        self.root.configure(bg=COLORS["bg_light"])

        # 状态变量
        self.current_active_group = None
        self.context_item_site = None
        self.context_item_group = None

        # === 拖拽核心变量 ===
        self.drag_data = {
            "item": None,  # 被拖拽的 item ID
            "parent": "",  # 原始父节点 (用于恢复)
            "index": 0,  # 原始索引 (用于恢复)
            "y": 0,  # 初始 Y 坐标
            "ghost": None,  # 幽灵窗口
            "indicator": None,  # 插入指示线
            "tree": None,  # 当前操作的 Treeview
            "is_group": False,  # 是否是分组
            "drop_target": None,  # 放置目标 ID
            "drop_pos": "after"  # 放置位置
        }

        self.configure_styles()
        self.data_file = "bookmarks.json"
        self.data = self.load_data()

        if self.data:
            self.current_active_group = list(self.data.keys())[0]

        self.setup_ui()

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
        self.group_tree.bind("<Button-3>", self.show_group_menu)

        self.group_tree.bind("<ButtonPress-1>", lambda e: self.on_press(e, self.group_tree, is_group=True))
        self.group_tree.bind("<B1-Motion>", self.on_motion)
        self.group_tree.bind("<ButtonRelease-1>", self.on_release)

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
        tk.Label(header_frame, text="(按住拖拽，松手插入)", bg=COLORS["bg_light"], fg="#999999",
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
        self.site_tree.bind("<Button-3>", self.show_site_menu)

        self.site_tree.bind("<ButtonPress-1>", lambda e: self.on_press(e, self.site_tree, is_group=False))
        self.site_tree.bind("<B1-Motion>", self.on_motion)
        self.site_tree.bind("<ButtonRelease-1>", self.on_release)

        self.site_tree.tag_configure("even", background="#FAFAFA")
        self.site_tree.tag_configure("odd", background=COLORS["bg_light"])

        self.create_context_menus()
        self.refresh_group_list()
        if self.current_active_group:
            self.refresh_site_list(self.current_active_group)

    # === 拖拽视觉逻辑 ===

    def create_ghost_window(self, text):
        if self.drag_data["ghost"]: self.drag_data["ghost"].destroy()
        ghost = tk.Toplevel(self.root)
        ghost.overrideredirect(True)
        ghost.attributes("-alpha", COLORS["ghost_alpha"])
        ghost.attributes("-topmost", True)
        label = tk.Label(ghost, text=text, bg=COLORS["ghost_bg"], fg="white",
                         font=FONTS["body"], padx=10, pady=5, relief="solid", bd=1)
        label.pack()
        self.drag_data["ghost"] = ghost

    def create_indicator(self):
        if self.drag_data["indicator"]: self.drag_data["indicator"].destroy()
        indicator = tk.Toplevel(self.root)
        indicator.overrideredirect(True)
        indicator.attributes("-topmost", True)
        indicator.configure(bg=COLORS["indicator"])
        indicator.geometry("100x2+0+0")
        self.drag_data["indicator"] = indicator

    def update_ghost_position(self, x_root, y_root):
        if self.drag_data["ghost"]:
            self.drag_data["ghost"].geometry(f"+{x_root + 15}+{y_root + 15}")

    def on_press(self, event, tree, is_group):
        item = tree.identify_row(event.y)
        if item:
            self.drag_data["item"] = item
            self.drag_data["parent"] = tree.parent(item)
            self.drag_data["index"] = tree.index(item)
            self.drag_data["y"] = event.y
            self.drag_data["tree"] = tree
            self.drag_data["is_group"] = is_group
            # 每次按下前，重置这些状态，防止污染
            self.drag_data["ghost"] = None
            self.drag_data["indicator"] = None
            self.drag_data["drop_target"] = None

    def on_motion(self, event):
        if not self.drag_data["item"]: return

        # 1. 触发拖拽 (Detach)
        if not self.drag_data["ghost"] and abs(event.y - self.drag_data["y"]) > 5:
            tree = self.drag_data["tree"]
            item = self.drag_data["item"]

            # 安全检查：确保 item 存在
            if not tree.exists(item): return

            item_text = ""
            if self.drag_data["is_group"]:
                item_text = tree.item(item, "text")
            else:
                vals = tree.item(item, "values")
                if vals: item_text = f"{vals[0]} - {vals[1]}"

            self.create_ghost_window(item_text)
            self.create_indicator()
            tree.configure(cursor="fleur")

            # 【Detach】 将行从视图中暂时移除
            tree.detach(item)

        # 2. 拖拽过程中
        if self.drag_data["ghost"]:
            tree = self.drag_data["tree"]
            self.update_ghost_position(event.x_root, event.y_root)

            target_id = tree.identify_row(event.y)

            # 只有当 target_id 存在且有效时才显示指示线
            if target_id:
                bbox = tree.bbox(target_id)
                if bbox:
                    row_y = bbox[1]
                    row_h = bbox[3]
                    mouse_y_in_row = event.y - row_y

                    line_x = tree.winfo_rootx() + bbox[0]
                    line_w = bbox[2]
                    line_h = 2

                    if mouse_y_in_row < row_h / 2:
                        line_y = tree.winfo_rooty() + row_y
                        self.drag_data["drop_target"] = target_id
                        self.drag_data["drop_pos"] = "before"
                    else:
                        line_y = tree.winfo_rooty() + row_y + row_h
                        self.drag_data["drop_target"] = target_id
                        self.drag_data["drop_pos"] = "after"

                    if self.drag_data["indicator"]:
                        self.drag_data["indicator"].geometry(f"{line_w}x{line_h}+{line_x}+{line_y}")
                        self.drag_data["indicator"].deiconify()
            else:
                # 鼠标在空白处，隐藏指示线，target 设为 None
                if self.drag_data["indicator"]:
                    self.drag_data["indicator"].withdraw()
                    self.drag_data["drop_target"] = None

    # === 【关键修复】 释放与异常恢复逻辑 ===
    def on_release(self, event):
        # 1. 清理视觉元素
        if self.drag_data["ghost"]:
            self.drag_data["ghost"].destroy()
            self.drag_data["ghost"] = None
        if self.drag_data["indicator"]:
            self.drag_data["indicator"].destroy()
            self.drag_data["indicator"] = None

        if self.drag_data["tree"]:
            self.drag_data["tree"].configure(cursor="")

        # 2. 判断是否发生了拖拽
        tree = self.drag_data["tree"]
        item = self.drag_data["item"]

        # 简单判定：如果有位移，说明触发了拖拽逻辑
        was_dragged = abs(event.y - self.drag_data["y"]) > 5

        if was_dragged and item:
            # === 尝试执行移动 ===
            try:
                target = self.drag_data["drop_target"]
                pos = self.drag_data["drop_pos"]

                # 如果有有效目标，移动到新位置
                if target:
                    if pos == "before":
                        tree.move(item, tree.parent(target), tree.index(target))
                    else:
                        tree.move(item, tree.parent(target), tree.index(target) + 1)

                    # 同步数据
                    self.sync_order_after_drag(item)
                else:
                    # 【无有效目标】：恢复原位 (Restore)
                    # print("Drop target invalid, restoring...")
                    tree.move(item, self.drag_data["parent"], self.drag_data["index"])

            except Exception as e:
                # 【发生任何错误】：强制恢复原位，防止程序崩溃或 item 消失
                print(f"Drag Error: {e}")  # 调试用
                try:
                    tree.move(item, self.drag_data["parent"], self.drag_data["index"])
                except:
                    pass  # 如果恢复也失败（极少见），不做处理防止弹窗报错

        else:
            # === 只是点击 (未触发拖拽) ===
            # 注意：因为没有 detach，所以不需要 restore
            if self.drag_data["is_group"]:
                self.handle_group_click(event)
            else:
                self.handle_site_click(event)

        self.drag_data["item"] = None

    def sync_order_after_drag(self, moved_item_id):
        if self.drag_data["is_group"]:
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

            # 根据 iid 映射回原始数据
            for iid in new_order_ids:
                try:
                    original_index = int(iid)
                    if original_index < len(old_site_list):
                        new_site_list.append(old_site_list[original_index])
                except:
                    pass

            self.data[self.current_active_group] = new_site_list
            self.save_data()
            # 刷新以重置 iid，确保下次拖拽逻辑正确
            self.refresh_site_list(self.current_active_group)

    # === 原有的辅助逻辑 ===

    def create_context_menus(self):
        self.group_menu = tk.Menu(self.root, tearoff=0, font=FONTS["body"])
        self.group_menu.add_command(label="✏️ 重命名", command=self.rename_group)
        self.group_menu.add_separator()
        self.group_menu.add_command(label="🗑️ 删除分组", command=self.delete_group)

        self.site_menu = tk.Menu(self.root, tearoff=0, font=FONTS["body"])
        self.site_menu.add_command(label="✏️ 编辑", command=self.edit_website)
        self.site_menu.add_separator()
        self.site_menu.add_command(label="🗑️ 删除", command=self.delete_website)

    def on_group_hover(self, event):
        if self.drag_data["ghost"]: return
        item_id = self.group_tree.identify_row(event.y)
        if item_id and item_id not in self.group_tree.selection():
            self.group_tree.selection_set(item_id)

    def on_group_leave(self, event):
        if not self.drag_data["ghost"] and self.group_tree.selection():
            self.group_tree.selection_remove(self.group_tree.selection())

    def show_group_menu(self, event):
        item_id = self.group_tree.identify_row(event.y)
        if item_id:
            self.context_item_group = item_id
            self.group_tree.selection_set(item_id)
            self.group_menu.post(event.x_root, event.y_root)

    def on_site_hover(self, event):
        if self.drag_data["ghost"]: return
        item_id = self.site_tree.identify_row(event.y)
        if item_id and item_id not in self.site_tree.selection():
            self.site_tree.selection_set(item_id)

    def on_site_leave(self, event):
        if not self.drag_data["ghost"] and self.site_tree.selection():
            self.site_tree.selection_remove(self.site_tree.selection())

    def show_site_menu(self, event):
        item_id = self.site_tree.identify_row(event.y)
        if item_id:
            self.context_item_site = item_id
            self.site_tree.selection_set(item_id)
            self.site_menu.post(event.x_root, event.y_root)

    def handle_group_click(self, event):
        item_id = self.group_tree.identify_row(event.y)
        if item_id:
            self.current_active_group = item_id
            self.refresh_group_list()
            self.refresh_site_list(self.current_active_group)

    def handle_site_click(self, event):
        item_id = self.site_tree.identify_row(event.y)
        if item_id:
            item = self.site_tree.item(item_id)
            url = item['values'][1]
            webbrowser.open(url)

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

    def add_group(self):
        name = simpledialog.askstring("新建分组", "请输入分组名称：")
        if name and name not in self.data:
            self.data[name] = []
            self.save_data()
            self.current_active_group = name
            self.refresh_group_list()
            self.refresh_site_list(name)

    def add_website(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("添加新网站")
        add_window.configure(bg=COLORS["bg_light"])
        self.center_window(add_window, 420, 300)

        current_selection = self.group_tree.selection()
        # 这里需要处理 selection 为空或为 tuple 的情况
        if current_selection:
            # Treeview selection is tuple
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
            if not name or not url or not group:
                messagebox.showwarning("提示", "请填写完整信息", parent=add_window)
                return
            if group not in self.data:
                self.data[group] = []
                self.refresh_group_list()
            self.data[group].append({"name": name, "url": url})
            self.save_data()
            if group == self.current_active_group:
                self.refresh_site_list(group)
            add_window.destroy()

        btn_confirm = ModernButton(add_window, text="确认添加", command=confirm_add, width=12)
        btn_confirm.place(x=80, y=220)
        btn_cancel = ModernButton(add_window, text="取消", command=add_window.destroy, width=12, bg="#E0E0E0",
                                  fg=COLORS["text_dark"])
        btn_cancel.place(x=220, y=220)

    def center_window(self, win, width, height):
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        win.geometry(f"{width}x{height}+{x}+{y}")

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