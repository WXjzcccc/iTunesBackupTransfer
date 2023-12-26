from tkinter import *
from tkinter import ttk,filedialog,messagebox,PhotoImage,Label
from myparser.Parser import Parser
import os

def generate_tree(tree,data,roots):
    '''
    @tree:          tree对象
    @data:          文件列表
    @roots:         根路径
    '''
    dic = {}
    folder_icon = PhotoImage(file='static/folder.png')
    file_icon = PhotoImage(file='static/file.png')
    tree.file_icon = file_icon
    tree.folder_icon = folder_icon
    for root in roots:
        tmp = tree.insert('', 'end', text=root, values=root, image=tree.folder_icon)
        dic.update({root:tmp})
    for v in data:
        val = v[1]
        if v[1].endswith('/'):
            val = v[1][:-1]
        parent = os.path.dirname(val)
        if val not in roots:
            t = tree.insert(dic.get(parent), 'end', text=val.split('/')[-1], values=v, image=tree.folder_icon if v[2] == 2 else tree.file_icon)
            dic.update({val:t})

def on_treeview_click(event):
    def delayed_print():
        item = tree.focus()  # 获取点击的项
        item_text = tree.item(item, "values")  # 获取项的文本内容
        print("Clicked item:", item_text,len(item_text))
    main.after(10, delayed_print)

def on_treeview_right_click(event):
    # 获取右击位置的节点
    item = tree.identify_row(event.y)
    if item:
        # 选中右击的节点
        tree.selection_set(item)
        # 显示右键菜单
        right_click_menu = Menu(main, tearoff=False)
        right_click_menu.add_command(label="导出选中节点", command=lambda: on_menu_selection(item))
        right_click_menu.post(event.x_root, event.y_root)

def on_menu_selection(item):
    # 获取选中的菜单项
    file_path = filedialog.askdirectory()
    values = tree.item(item,'values')
    print("Selected path:", file_path)
    if file_path == '':
        return
    parser.copy_selected(values,file_path)
    messagebox.showinfo("提示", "导出成功！")

def on_button1_clicked():
    file_path = filedialog.askdirectory()
    print("Selected path:", file_path)
    parser.setFile(backup_path,file_path)
    button1.config(text="正在导出...")
    main.update()
    parser.copy_all()
    button1.config(text="一键导出所有")
    main.update()
    messagebox.showinfo("提示", "导出成功！")

main = Tk()
main.title('iBT by WXjzc')
main.geometry("300x400")
messagebox.showinfo("提示", "请选择iTunes备份数据")
backup_path = filedialog.askdirectory()
if backup_path == "":
    exit()
parser = Parser()
parser.setDB(backup_path)
tree = ttk.Treeview(main, columns=(), show="tree headings", displaycolumns=())
tree.heading("#0", text="文件列表", anchor=W)


generate_tree(tree, parser.get_file_list(), parser.get_roots())
tree.pack(expand=1, fill=BOTH)
tree.bind('<Button-1>', on_treeview_click)
tree.bind('<Button-3>', on_treeview_right_click)
button1 = Button(main, text='一键导出所有',command=on_button1_clicked)
button1.pack()
main.mainloop()