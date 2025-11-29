import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import json
import os

# === 全局配置 ===
# 配色方案 (扁平化风格)
COLORS = {
    "primary": "#4A90E2",  # 主色调（蓝色）
    "primary_hover": "#357ABD",  # 鼠标悬停时的深蓝色
    "bg_light": "#FFFFFF",  # 纯白背景
    "bg_gray": "#F5F7FA",  # 浅灰背景（用于侧边栏）
    "text_dark": "#333333",  # 深色文字
    "text_light": "#FFFFFF",  # 浅色文字
    "accent": "#FF6B6B"  # 强调色（如删除/警告，暂未大量使用）
}

# 字体配置
FONTS = {
    "h1": ("Microsoft YaHei UI", 12, "bold"),
    "body": ("Microsoft YaHei UI", 10),
    "small": ("Microsoft YaHei UI", 9)
}


class ModernButton(tk.Button):
    """自定义扁平化按钮，支持悬停变色"""

    def __init__(self, master, text, command, bg=COLORS["primary"], fg=COLORS["text_light"], **kwargs):
        super().__init__(master, text=text, command=command, bg=bg, fg=fg,
                         font=FONTS["body"], relief="flat", activebackground=COLORS["primary_hover"],
                         activeforeground=fg, cursor="hand2", **kwargs)
        self.default_bg = bg
        self.hover_bg = COLORS["primary_hover"]

        # 绑定鼠标移入移出事件
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self["bg"] = self.hover_bg

    def on_leave(self, e):
        self["bg"] = self.default_bg


class WebManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ 网站收藏管理器 (Pro)")
        self.root.geometry("900x600")
        self.root.configure(bg=COLORS["bg_light"])

        # 配置全局样式 (ttk)
        self.configure_styles()

        # 数据文件路径
        self.data_file = "bookmarks.json"
        self.data = self.load_data()

        # 界面布局
        self.setup_ui()

    def configure_styles(self):
        """配置 ttk 组件的样式"""
        style = ttk.Style()
        style.theme_use("clam")  # 使用 clam 主题作为基础，因为它更容易自定义颜色

        # Treeview (表格) 样式
        style.configure("Treeview",
                        background=COLORS["bg_light"],
                        foreground=COLORS["text_dark"],
                        rowheight=30,  # 增加行高
                        fieldbackground=COLORS["bg_light"],
                        font=FONTS["body"],
                        borderwidth=0)

        # 表头样式
        style.configure("Treeview.Heading",
                        background=COLORS["bg_gray"],
                        foreground=COLORS["text_dark"],
                        font=FONTS["h1"],
                        relief="flat")

        # 选中行的颜色
        style.map("Treeview",
                  background=[('selected', COLORS["primary"])],
                  foreground=[('selected', COLORS["text_light"])])

        # 下拉框样式
        style.configure("TCombobox", padding=5)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "常用工具": [{"name": "Google", "url": "https://www.google.com"}],
            "学习资料": [],
            "娱乐": []
        }

    def save_data(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        # === 左侧：分组列表 (侧边栏) ===
        left_frame = tk.Frame(self.root, width=220, bg=COLORS["bg_gray"])
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        left_frame.pack_propagate(False)

        # 侧边栏标题
        lbl_group = tk.Label(left_frame, text="📁 分组列表", bg=COLORS["bg_gray"], fg=COLORS["text_dark"],
                             font=FONTS["h1"])
        lbl_group.pack(fill=tk.X, pady=(20, 10), padx=10)

        # 分组列表框 (Listbox)
        # 这里的 highlightthickness=0 去除了丑陋的黑框
        self.group_listbox = tk.Listbox(left_frame, font=FONTS["body"], selectmode=tk.SINGLE,
                                        bd=0, bg=COLORS["bg_gray"], fg=COLORS["text_dark"],
                                        selectbackground=COLORS["primary"], selectforeground=COLORS["text_light"],
                                        highlightthickness=0, activestyle="none")
        self.group_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.group_listbox.bind("<<ListboxSelect>>", self.on_group_select)

        # 侧边栏底部按钮区域
        btn_frame_left = tk.Frame(left_frame, bg=COLORS["bg_gray"])
        btn_frame_left.pack(fill=tk.X, padx=15, pady=20)

        ModernButton(btn_frame_left, text="+ 新建分组", command=self.add_group).pack(fill=tk.X, pady=5)

        # === 右侧：网站列表 (主内容区) ===
        right_frame = tk.Frame(self.root, bg=COLORS["bg_light"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 顶部标题栏
        header_frame = tk.Frame(right_frame, bg=COLORS["bg_light"])
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(header_frame, text="🌐 网站列表", bg=COLORS["bg_light"], fg=COLORS["text_dark"], font=FONTS["h1"]).pack(
            side=tk.LEFT)
        tk.Label(header_frame, text="(双击打开，右键管理)", bg=COLORS["bg_light"], fg="#999999",
                 font=FONTS["small"]).pack(side=tk.LEFT, padx=10, pady=5)

        # 添加网站按钮 (放在右上角)
        ModernButton(header_frame, text="+ 添加网站", command=self.add_website, width=12).pack(side=tk.RIGHT)

        # 表格区域
        tree_frame = tk.Frame(right_frame, bg=COLORS["bg_light"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("name", "url")
        self.site_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.site_tree.heading("name", text="网站名称")
        self.site_tree.heading("url", text="网址 URL")

        self.site_tree.column("name", width=200, anchor="w")
        self.site_tree.column("url", width=400, anchor="w")

        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.site_tree.yview)
        self.site_tree.configure(yscroll=scrollbar.set)

        self.site_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.site_tree.bind("<Double-1>", self.open_website)

        # 设置斑马纹 tag
        self.site_tree.tag_configure("even", background="#FAFAFA")
        self.site_tree.tag_configure("odd", background=COLORS["bg_light"])

        # === 右键菜单 ===
        self.create_context_menus()

        # 初始刷新
        self.refresh_group_list()

    def create_context_menus(self):
        # 菜单样式相对难定制，保持系统原生
        self.group_menu = tk.Menu(self.root, tearoff=0, font=FONTS["body"])
        self.group_menu.add_command(label="✏️ 重命名", command=self.rename_group)
        self.group_menu.add_separator()
        self.group_menu.add_command(label="🗑️ 删除分组", command=self.delete_group)
        self.group_listbox.bind("<Button-3>", self.show_group_menu)

        self.site_menu = tk.Menu(self.root, tearoff=0, font=FONTS["body"])
        self.site_menu.add_command(label="✏️ 编辑", command=self.edit_website)
        self.site_menu.add_separator()
        self.site_menu.add_command(label="🗑️ 删除", command=self.delete_website)
        self.site_tree.bind("<Button-3>", self.show_site_menu)

    # === 逻辑与功能 ===

    def refresh_group_list(self):
        current_selection = self.group_listbox.curselection()
        selected_group = self.group_listbox.get(current_selection[0]) if current_selection else None

        self.group_listbox.delete(0, tk.END)
        for group in self.data.keys():
            self.group_listbox.insert(tk.END, f"  {group}")  # 加两个空格增加左边距感

        if selected_group:
            # 去掉空格匹配
            clean_list = [self.group_listbox.get(i).strip() for i in range(self.group_listbox.size())]
            if selected_group.strip() in clean_list:
                idx = clean_list.index(selected_group.strip())
                self.group_listbox.selection_set(idx)
                self.group_listbox.activate(idx)
        elif self.group_listbox.size() > 0:
            # 默认选中第一个
            self.group_listbox.selection_set(0)
            self.on_group_select(None)

    def on_group_select(self, event):
        selection = self.group_listbox.curselection()
        if selection:
            group_name = self.group_listbox.get(selection[0]).strip()
            self.refresh_site_list(group_name)

    def refresh_site_list(self, group_name):
        for item in self.site_tree.get_children():
            self.site_tree.delete(item)

        sites = self.data.get(group_name, [])
        for i, site in enumerate(sites):
            # 斑马纹逻辑
            tag = "even" if i % 2 == 0 else "odd"
            self.site_tree.insert("", tk.END, iid=str(i), values=(site["name"], site["url"]), tags=(tag,))

    def open_website(self, event):
        item_id = self.site_tree.selection()
        if item_id:
            item = self.site_tree.item(item_id)
            url = item['values'][1]
            webbrowser.open(url)

    # === 弹窗与操作逻辑 ===

    def center_window(self, win, width, height):
        """让窗口在屏幕居中"""
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        win.geometry(f"{width}x{height}+{x}+{y}")

    def add_group(self):
        name = simpledialog.askstring("新建分组", "请输入分组名称：")
        if name:
            if name in self.data:
                messagebox.showerror("错误", "该分组已存在")
            else:
                self.data[name] = []
                self.save_data()
                self.refresh_group_list()

    def add_website(self):
        # 创建美化版弹窗
        add_window = tk.Toplevel(self.root)
        add_window.title("添加新网站")
        add_window.configure(bg=COLORS["bg_light"])
        self.center_window(add_window, 420, 300)

        # 获取默认分组
        current_selection = self.group_listbox.curselection()
        default_group = self.group_listbox.get(current_selection[0]).strip() if current_selection else ""
        existing_groups = list(self.data.keys())

        # UI 构建帮助函数
        def create_input(label_text, y_pos):
            tk.Label(add_window, text=label_text, bg=COLORS["bg_light"], font=FONTS["body"]).place(x=40, y=y_pos)
            entry = tk.Entry(add_window, width=30, font=FONTS["body"], relief="solid", bd=1)
            entry.place(x=130, y=y_pos)
            return entry

        entry_name = create_input("网站名称:", 40)
        entry_name.focus_set()

        entry_url = create_input("网址 URL:", 90)
        entry_url.insert(0, "https://")

        # 分组下拉框 (需要特殊处理，因为它是 Combobox)
        tk.Label(add_window, text="选择分组:", bg=COLORS["bg_light"], font=FONTS["body"]).place(x=40, y=140)
        combo_group = ttk.Combobox(add_window, values=existing_groups, width=28, font=FONTS["body"])
        combo_group.place(x=130, y=140)
        if default_group:
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

            # 选中并刷新
            try:
                # 重新获取带空格的列表项以便匹配
                full_list = self.group_listbox.get(0, tk.END)
                # 模糊匹配去除空格
                clean_list = [s.strip() for s in full_list]
                idx = clean_list.index(group)
                self.group_listbox.selection_clear(0, tk.END)
                self.group_listbox.selection_set(idx)
                self.refresh_site_list(group)
            except:
                pass
            add_window.destroy()

        # 底部按钮
        btn_confirm = ModernButton(add_window, text="确认添加", command=confirm_add, width=12)
        btn_confirm.place(x=80, y=220)

        btn_cancel = ModernButton(add_window, text="取消", command=add_window.destroy, width=12,
                                  bg="#E0E0E0", fg=COLORS["text_dark"])
        # 覆写取消按钮的悬停颜色为灰色
        btn_cancel.hover_bg = "#D0D0D0"
        btn_cancel.place(x=220, y=220)

    def show_group_menu(self, event):
        self.group_listbox.selection_clear(0, tk.END)
        self.group_listbox.selection_set(self.group_listbox.nearest(event.y))
        self.group_listbox.activate(self.group_listbox.nearest(event.y))
        self.group_menu.post(event.x_root, event.y_root)

    def rename_group(self):
        selection = self.group_listbox.curselection()
        if not selection: return
        old_name = self.group_listbox.get(selection[0]).strip()

        new_name = simpledialog.askstring("重命名", "请输入新名称：", initialvalue=old_name)
        if new_name and new_name != old_name:
            self.data[new_name] = self.data.pop(old_name)
            self.save_data()
            self.refresh_group_list()
            self.refresh_site_list(new_name)

    def delete_group(self):
        selection = self.group_listbox.curselection()
        if not selection: return
        group_name = self.group_listbox.get(selection[0]).strip()

        if messagebox.askyesno("确认", f"确定要删除分组 '{group_name}' 及其所有内容吗？"):
            del self.data[group_name]
            self.save_data()
            self.refresh_group_list()
            for item in self.site_tree.get_children():
                self.site_tree.delete(item)

    def show_site_menu(self, event):
        item_id = self.site_tree.identify_row(event.y)
        if item_id:
            self.site_tree.selection_set(item_id)
            self.site_menu.post(event.x_root, event.y_root)

    def edit_website(self):
        selection = self.group_listbox.curselection()
        item_id = self.site_tree.selection()
        if not selection or not item_id: return

        group_name = self.group_listbox.get(selection[0]).strip()
        index = int(item_id[0])
        site_data = self.data[group_name][index]

        new_name = simpledialog.askstring("编辑", "名称：", initialvalue=site_data["name"])
        if not new_name: return
        new_url = simpledialog.askstring("编辑", "网址：", initialvalue=site_data["url"])
        if not new_url: return

        self.data[group_name][index] = {"name": new_name, "url": new_url}
        self.save_data()
        self.refresh_site_list(group_name)

    def delete_website(self):
        selection = self.group_listbox.curselection()
        item_id = self.site_tree.selection()
        if not selection or not item_id: return

        group_name = self.group_listbox.get(selection[0]).strip()
        index = int(item_id[0])

        if messagebox.askyesno("确认", "确定删除该网站吗？"):
            self.data[group_name].pop(index)
            self.save_data()
            self.refresh_site_list(group_name)


if __name__ == "__main__":
    root = tk.Tk()
    # 尝试设置高分屏支持（Windows）
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    app = WebManagerApp(root)
    root.mainloop()