import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import json
import os


class WebManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("网站收藏管理器 (增强版)")
        self.root.geometry("800x600")

        # 数据文件路径
        self.data_file = "bookmarks.json"
        self.data = self.load_data()

        # 界面布局
        self.setup_ui()

    def load_data(self):
        """加载数据，如果不存在则创建默认数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        # 默认初始数据
        return {
            "常用工具": [{"name": "Google", "url": "https://www.google.com"}],
            "学习资料": [],
            "娱乐": []
        }

    def save_data(self):
        """保存数据到文件"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def setup_ui(self):
        # === 左侧：分组列表 ===
        left_frame = tk.Frame(self.root, width=200, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        left_frame.pack_propagate(False)

        tk.Label(left_frame, text="分组列表", bg="#e0e0e0", font=("Arial", 10, "bold")).pack(fill=tk.X, pady=5)

        self.group_listbox = tk.Listbox(left_frame, font=("Arial", 11), selectmode=tk.SINGLE, bd=0)
        self.group_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.group_listbox.bind("<<ListboxSelect>>", self.on_group_select)

        # 分组操作按钮
        btn_frame_left = tk.Frame(left_frame)
        btn_frame_left.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(btn_frame_left, text="+ 新建分组", command=self.add_group).pack(fill=tk.X)

        # === 右侧：网站列表 ===
        right_frame = tk.Frame(self.root, bg="white")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="网站列表 (双击打开，右键编辑)", bg="#e0e0e0", font=("Arial", 10, "bold")).pack(
            fill=tk.X, pady=5)

        # 使用 Treeview 显示网站名称和 URL
        columns = ("name", "url")
        self.site_tree = ttk.Treeview(right_frame, columns=columns, show="headings")
        self.site_tree.heading("name", text="网站名称")
        self.site_tree.heading("url", text="网址")
        self.site_tree.column("name", width=150)
        self.site_tree.column("url", width=300)
        self.site_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.site_tree.bind("<Double-1>", self.open_website)

        # 网站操作按钮
        btn_frame_right = tk.Frame(right_frame)
        btn_frame_right.pack(fill=tk.X, padx=5, pady=5)
        # 注意：这里的添加网站按钮位置不变
        tk.Button(btn_frame_right, text="+ 添加网站", command=self.add_website).pack(side=tk.RIGHT)

        # === 右键菜单 ===
        self.create_context_menus()

        # 初始刷新
        self.refresh_group_list()

    def create_context_menus(self):
        # 分组右键菜单
        self.group_menu = tk.Menu(self.root, tearoff=0)
        self.group_menu.add_command(label="重命名", command=self.rename_group)
        self.group_menu.add_command(label="删除分组", command=self.delete_group)
        self.group_listbox.bind("<Button-3>", self.show_group_menu)

        # 网站右键菜单
        self.site_menu = tk.Menu(self.root, tearoff=0)
        self.site_menu.add_command(label="编辑", command=self.edit_website)
        self.site_menu.add_command(label="删除", command=self.delete_website)
        self.site_tree.bind("<Button-3>", self.show_site_menu)

    # === 核心逻辑 ===

    def refresh_group_list(self):
        # 保存当前选中的项（如果有），以便刷新后恢复
        current_selection = self.group_listbox.curselection()
        selected_group = self.group_listbox.get(current_selection[0]) if current_selection else None

        self.group_listbox.delete(0, tk.END)
        for group in self.data.keys():
            self.group_listbox.insert(tk.END, group)

        # 尝试恢复选中状态
        if selected_group:
            try:
                idx = self.group_listbox.get(0, tk.END).index(selected_group)
                self.group_listbox.selection_set(idx)
                self.group_listbox.activate(idx)
            except ValueError:
                pass

    def on_group_select(self, event):
        selection = self.group_listbox.curselection()
        if selection:
            group_name = self.group_listbox.get(selection[0])
            self.refresh_site_list(group_name)

    def refresh_site_list(self, group_name):
        # 清空现有列表
        for item in self.site_tree.get_children():
            self.site_tree.delete(item)

        sites = self.data.get(group_name, [])
        for i, site in enumerate(sites):
            self.site_tree.insert("", tk.END, iid=str(i), values=(site["name"], site["url"]))

    def open_website(self, event):
        item_id = self.site_tree.selection()
        if item_id:
            item = self.site_tree.item(item_id)
            url = item['values'][1]
            webbrowser.open(url)

    # === 增删改功能 ===

    def add_group(self):
        name = simpledialog.askstring("新建分组", "请输入分组名称：")
        if name:
            if name in self.data:
                messagebox.showerror("错误", "该分组已存在")
            else:
                self.data[name] = []
                self.save_data()
                self.refresh_group_list()

    def show_group_menu(self, event):
        self.group_listbox.selection_clear(0, tk.END)
        self.group_listbox.selection_set(self.group_listbox.nearest(event.y))
        self.group_listbox.activate(self.group_listbox.nearest(event.y))
        self.group_menu.post(event.x_root, event.y_root)

    def rename_group(self):
        selection = self.group_listbox.curselection()
        if not selection: return
        old_name = self.group_listbox.get(selection[0])

        new_name = simpledialog.askstring("重命名", "请输入新名称：", initialvalue=old_name)
        if new_name and new_name != old_name:
            self.data[new_name] = self.data.pop(old_name)
            self.save_data()
            self.refresh_group_list()
            # 刷新右侧显示
            self.refresh_site_list(new_name)

    def delete_group(self):
        selection = self.group_listbox.curselection()
        if not selection: return
        group_name = self.group_listbox.get(selection[0])

        if messagebox.askyesno("确认", f"确定要删除分组 '{group_name}' 及其所有内容吗？"):
            del self.data[group_name]
            self.save_data()
            self.refresh_group_list()
            # 清空右侧
            for item in self.site_tree.get_children():
                self.site_tree.delete(item)

    # === 【修改部分】 全新的添加网站功能 ===
    def add_website(self):
        # 创建一个独立的顶层窗口
        add_window = tk.Toplevel(self.root)
        add_window.title("添加新网站")
        # 设置窗口大小，确保文字显示完全
        add_window.geometry("400x250")

        # 获取当前主界面选中的分组，作为默认值
        current_selection = self.group_listbox.curselection()
        default_group = self.group_listbox.get(current_selection[0]) if current_selection else ""

        # === 布局输入框 ===
        # 1. 网站名称
        tk.Label(add_window, text="网站名称:", font=("Arial", 10)).place(x=30, y=30)
        entry_name = tk.Entry(add_window, width=30)
        entry_name.place(x=120, y=30)
        entry_name.focus_set()  # 默认聚焦在这里

        # 2. 网址
        tk.Label(add_window, text="网址 (URL):", font=("Arial", 10)).place(x=30, y=80)
        entry_url = tk.Entry(add_window, width=30)
        entry_url.insert(0, "https://")  # 默认填入 https://
        entry_url.place(x=120, y=80)

        # 3. 分组（下拉框）
        tk.Label(add_window, text="选择分组:", font=("Arial", 10)).place(x=30, y=130)
        # 获取现有的所有分组名
        existing_groups = list(self.data.keys())
        combo_group = ttk.Combobox(add_window, values=existing_groups, width=27)
        combo_group.place(x=120, y=130)

        # 如果当前有选中的分组，默认填入
        if default_group:
            combo_group.set(default_group)
        elif existing_groups:
            combo_group.current(0)

        # === 确认按钮逻辑 ===
        def confirm_add():
            name = entry_name.get().strip()
            url = entry_url.get().strip()
            group = combo_group.get().strip()

            if not name:
                messagebox.showwarning("提示", "请输入网站名称", parent=add_window)
                return
            if not url:
                messagebox.showwarning("提示", "请输入网址", parent=add_window)
                return
            if not group:
                messagebox.showwarning("提示", "请输入或选择一个分组", parent=add_window)
                return

            # 如果分组不存在，则新建分组
            if group not in self.data:
                self.data[group] = []
                # 注意：新建分组后，可能需要刷新左侧列表
                self.refresh_group_list()

            # 添加数据
            self.data[group].append({"name": name, "url": url})
            self.save_data()

            # 刷新界面：如果当前左侧正好选中的是这个分组，或者新建了分组，刷新右侧列表
            # 为了简单起见，我们直接调用刷新逻辑
            # 如果新建了分组，我们需要在左侧Listbox中选中它，以便用户看到结果
            try:
                # 找到该分组在列表中的位置
                all_groups = self.group_listbox.get(0, tk.END)
                idx = all_groups.index(group)
                self.group_listbox.selection_clear(0, tk.END)
                self.group_listbox.selection_set(idx)
                self.group_listbox.activate(idx)
                # 刷新右侧
                self.refresh_site_list(group)
            except:
                pass

            add_window.destroy()

        # 按钮
        btn_confirm = tk.Button(add_window, text="确认添加", command=confirm_add, bg="#e0e0e0", width=10)
        btn_confirm.place(x=100, y=190)

        btn_cancel = tk.Button(add_window, text="取消", command=add_window.destroy, width=10)
        btn_cancel.place(x=220, y=190)

    def show_site_menu(self, event):
        item_id = self.site_tree.identify_row(event.y)
        if item_id:
            self.site_tree.selection_set(item_id)
            self.site_menu.post(event.x_root, event.y_root)

    def edit_website(self):
        selection = self.group_listbox.curselection()
        item_id = self.site_tree.selection()
        if not selection or not item_id: return

        group_name = self.group_listbox.get(selection[0])
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

        group_name = self.group_listbox.get(selection[0])
        index = int(item_id[0])

        if messagebox.askyesno("确认", "确定删除该网站吗？"):
            self.data[group_name].pop(index)
            self.save_data()
            self.refresh_site_list(group_name)


if __name__ == "__main__":
    root = tk.Tk()
    app = WebManagerApp(root)
    root.mainloop()