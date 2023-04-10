import subprocess
import sys
import os

try:
    from PIL import Image
except ImportError:
    print("Installing the Pillow library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import font
import io

root = tk.Tk()
root.title("PyText")

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

root.iconbitmap(resource_path('favicon.ico'))

text = tk.Text(root)
text.grid(row=0, column=0, sticky="nsew")

default_font = font.nametofont("TkFixedFont")
default_font.configure(family="Consolas", size=10)
text.configure(font=default_font)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

def configure_tags():
    for color in ["yellow", "green", "cyan", "pink"]:
        text.tag_configure(color, background=color)

configure_tags()

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt;*.txtp"), ("All Files", "*.*")])
    if file_path:
        ext = file_path.split(".")[-1]
        with open(file_path, "rb") as file:
            content = file.read().decode('utf-8', errors='replace')
            text.delete("1.0", "end")
            text.insert("end", content)

            if ext in ["txt", "txtp"]:
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith("#"): 
                        continue
                    elif "," in line:  
                        start, end, tag_name = line.split(",")
                        text.tag_add(tag_name, start, end)

def save_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".txtp", filetypes=[("TXTP Files", "*.txtp"), ("Text Files", "*.txt"), ("All Files", "*.*")])
    if file_path:
        if file_path.endswith(".txtp"):
            with open(file_path, "w") as file:
                file.write(text.get("1.0", "end"))
                for tag_name in text.tag_names():
                    if tag_name != "sel":
                        tag_ranges = text.tag_ranges(tag_name)
                        for i in range(0, len(tag_ranges), 2):
                            start = tag_ranges[i]
                            end = tag_ranges[i+1]
                            file.write(f"{start},{end},{tag_name}\n")
        else:
            with open(file_path, "w") as file:
                file.write(text.get("1.0", "end"))

def close_file():
    if messagebox.askokcancel("Close", "Do you want to close this file?"):
        root.destroy()

def copy_text(event=None):
    text.event_generate("<<Copy>>")
    return "break"

def paste_text(event=None):
    clipboard = root.clipboard_get()
    if clipboard:
        index = text.index(tk.INSERT)
        text.event_generate("<<Paste>>")
        end_index = text.index(f"{index}+{len(clipboard)}c")
        edit = ("insert", index, clipboard)
        add_edit_state(edit)

    return "break"

def select_all_text(event=None):
    text.tag_add("sel", "1.0", "end-1c")
    text.mark_set("insert", "1.0")
    text.see("insert")
    return "break"

text.bind("<Control-c>", copy_text)
text.bind("<Control-v>", paste_text)
text.bind("<Control-a>", select_all_text)

def undo_text(event=None):
    if len(undo_list) > 0:
        current_edit = undo_list.pop()
        redo_list.append(current_edit)
        apply_edit(current_edit, reverse=True)
    return "break"

def redo_text(event=None):
    if len(redo_list) > 0:
        current_edit = redo_list.pop()
        undo_list.append(current_edit)
        apply_edit(current_edit)
    return "break"

undo_list = []
redo_list = []

def add_edit_state(edit):
    undo_list.append(edit)
    redo_list.clear()

def on_edit(event=None):
    if event and event.type == "7": 
        return
    if event.keysym in ["Up", "Down", "Left", "Right"]:
        return
    if event.char and event.char.isalnum():
        index = text.index(tk.INSERT)
        prev_char = text.get(f"{index}-1c")
        if len(prev_char) == 0:
            return
        edit = ("insert", f"{index}-1c", prev_char)
        add_edit_state(edit)
    elif event.keysym in ["BackSpace", "Delete"]:
        index = text.index(tk.INSERT)
        if event.keysym == "BackSpace":
            prev_char = text.get(f"{index}-1c")
            if len(prev_char) == 0:
                return
            edit = ("delete", f"{index}-1c", prev_char)
        elif event.keysym == "Delete":
            next_char = text.get(index)
            if len(next_char) == 0:
                return
            edit = ("delete", index, next_char)
        add_edit_state(edit)

text.bind("<KeyRelease>", on_edit)

def apply_edit(edit, reverse=False):
    action, index, chars = edit
    if action == "insert":
        if reverse:
            text.delete(index, f"{index}+{len(chars)}c")
        else:
            text.insert(index, chars)
    elif action == "delete":
        if reverse:
            text.insert(index, chars)
        else:
            text.delete(index, f"{index}+{len(chars)}c")

text.bind("<Control-z>", undo_text)
text.bind("<Control-y>", redo_text)

menu_bar = tk.Menu(root)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open", command=open_file)
file_menu.add_command(label="Save", command=save_file)
file_menu.add_separator()
file_menu.add_command(label="Close", command=close_file)
menu_bar.add_cascade(label="File", menu=file_menu)

edit_menu = tk.Menu(menu_bar, tearoff=0)
edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=undo_text)
edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=redo_text)
menu_bar.add_cascade(label="Edit", menu=edit_menu)

highlight_color = "yellow"

def set_highlight_color(color):
    global highlight_color
    highlight_color = color

def apply_highlight_color():
    selection = text.tag_ranges("sel")
    if selection:
        text.tag_add(highlight_color, selection[0], selection[1])

highlight_menu = tk.Menu(menu_bar, tearoff=0)
highlight_menu.add_command(label="Yellow", command=lambda: [set_highlight_color("yellow"), apply_highlight_color()])
highlight_menu.add_command(label="Green", command=lambda: [set_highlight_color("green"), apply_highlight_color()])
highlight_menu.add_command(label="Cyan", command=lambda: [set_highlight_color("cyan"), apply_highlight_color()])
highlight_menu.add_command(label="Pink", command=lambda: [set_highlight_color("pink"), apply_highlight_color()])
menu_bar.add_cascade(label="Highlight", menu=highlight_menu)

view_menu = tk.Menu(menu_bar, tearoff=0)

def set_font_size(size_change):
    global current_font_size, increase_count, decrease_count

    if size_change > 0 and increase_count < 3:
        current_font_size += size_change
        increase_count += 1
        decrease_count = 0
    elif size_change < 0 and decrease_count < 3:
        current_font_size += size_change
        decrease_count += 1
        increase_count = 0

    current_font = font.nametofont(text.cget("font"))
    current_font.configure(size=current_font_size)
    text.configure(font=current_font)

current_font_size = font.nametofont(text.cget("font")).actual()["size"]
increase_count = 0
decrease_count = 0

view_menu.add_command(label="Increase Font Size", command=lambda: set_font_size(2))
view_menu.add_command(label="Decrease Font Size", command=lambda: set_font_size(-2))

def toggle_word_wrap():
    wrap_option = text.cget("wrap")
    if wrap_option == "none":
        text.configure(wrap="word")
    else:
        text.configure(wrap="none")

view_menu.add_separator()
view_menu.add_command(label="Toggle Word Wrap", command=toggle_word_wrap)

menu_bar.add_cascade(label="View", menu=view_menu)

root.config(menu=menu_bar)

root.mainloop()
