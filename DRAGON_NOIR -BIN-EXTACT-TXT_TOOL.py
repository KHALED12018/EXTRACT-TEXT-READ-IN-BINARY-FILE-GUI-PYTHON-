import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class ProfessionalStringsViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("DRAGON_NOIR-DZ-Advanced Binary Strings Extractor")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e1e1e")
        
        self.current_file_path = ""
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure(".", background="#1e1e1e", foreground="#ffffff")
        
        self.style.configure("Top.TFrame", background="#2d2d2d")
        self.style.configure("Content.TFrame", background="#1e1e1e")
        
        self.style.configure("Action.TButton", 
                             background="#007acc", 
                             foreground="#ffffff", 
                             borderwidth=0, 
                             focuscolor="none", 
                             padding=10,
                             font=("Segoe UI", 10, "bold"))
        self.style.map("Action.TButton", background=[("active", "#005999")])
        
        self.style.configure("Secondary.TButton", 
                             background="#3c3c3c", 
                             foreground="#ffffff", 
                             borderwidth=0, 
                             focuscolor="none", 
                             padding=8,
                             font=("Segoe UI", 10))
        self.style.map("Secondary.TButton", background=[("active", "#505050")])
        
        self.style.configure("Path.TLabel", 
                             background="#2d2d2d", 
                             foreground="#aaaaaa", 
                             font=("Consolas", 10, "italic"))

    def create_widgets(self):
        top_panel = ttk.Frame(self.root, style="Top.TFrame", padding=15)
        top_panel.pack(fill=tk.X, side=tk.TOP)
        
        open_btn = ttk.Button(top_panel, text="OPEN BINARY FILE", style="Action.TButton", command=self.open_file)
        open_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.path_lbl = ttk.Label(top_panel, text="No file loaded...", style="Path.TLabel")
        self.path_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        save_btn = ttk.Button(top_panel, text="EXPORT STRINGS", style="Secondary.TButton", command=self.save_to_text)
        save_btn.pack(side=tk.RIGHT, padx=(15, 0))

        search_panel = ttk.Frame(self.root, style="Top.TFrame", padding=(15, 0, 15, 15))
        search_panel.pack(fill=tk.X, side=tk.TOP)
        
        search_lbl = ttk.Label(search_panel, text="SEARCH:", font=("Segoe UI", 10, "bold"), background="#2d2d2d", foreground="#007acc")
        search_lbl.pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_entry = tk.Entry(search_panel, bg="#3c3c3c", fg="#ffffff", insertbackground="#ffffff", borderwidth=1, relief="solid", font=("Segoe UI", 11), selectbackground="#007acc")
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        
        search_btn = ttk.Button(search_panel, text="FIND", style="Secondary.TButton", command=self.perform_search)
        search_btn.pack(side=tk.LEFT)

        main_container = ttk.Frame(self.root, style="Content.TFrame", padding=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        outer_border = tk.Frame(main_container, bg="#007acc", bd=2)
        outer_border.pack(fill=tk.BOTH, expand=True)
        
        inner_frame = tk.Frame(outer_border, bg="#252526", bd=5)
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        v_scroll = tk.Scrollbar(inner_frame, bg="#2d2d2d", activebackground="#007acc")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scroll = tk.Scrollbar(inner_frame, orient=tk.HORIZONTAL, bg="#2d2d2d", activebackground="#007acc")
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.text_area = tk.Text(inner_frame, 
                                 bg="#252526", 
                                 fg="#d4d4d4", 
                                 insertbackground="#ffffff",
                                 selectbackground="#264f78", 
                                 selectforeground="#ffffff",
                                 font=("Consolas", 11), 
                                 bd=0, 
                                 wrap=tk.NONE,
                                 yscrollcommand=v_scroll.set, 
                                 xscrollcommand=h_scroll.set)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        v_scroll.config(command=self.text_area.yview)
        h_scroll.config(command=self.text_area.xview)
        
        self.text_area.tag_config("match", background="#613214", foreground="#ff9e3b", borderwidth=1, relief="solid")

    def open_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
            
        self.current_file_path = file_path
        self.path_lbl.config(text=file_path)
        self.text_area.delete("1.0", tk.END)
        
        try:
            printable = set(bytes(range(32, 127)) + b'\n' + b'\r' + b'\t')
            extracted_strings = []
            
            with open(file_path, "rb") as f:
                current_str = bytearray()
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    for byte in chunk:
                        if byte in printable:
                            current_str.append(byte)
                        else:
                            if len(current_str) >= 4:
                                try:
                                    extracted_strings.append(current_str.decode("ascii"))
                                except:
                                    pass
                            current_str = bytearray()
                if len(current_str) >= 4:
                    try:
                        extracted_strings.append(current_str.decode("ascii"))
                    except:
                        pass
            
            self.text_area.insert(tk.END, "\n".join(extracted_strings))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {str(e)}")

    def perform_search(self):
        self.text_area.tag_remove("match", "1.0", tk.END)
        query = self.search_entry.get()
        if not query:
            return
            
        start_pos = "1.0"
        first_match = None
        
        while True:
            start_pos = self.text_area.search(query, start_pos, stopindex=tk.END, nocase=True)
            if not start_pos:
                break
            if not first_match:
                first_match = start_pos
            end_pos = f"{start_pos}+{len(query)}c"
            self.text_area.tag_add("match", start_pos, end_pos)
            start_pos = end_pos
            
        if first_match:
            self.text_area.see(first_match)
        else:
            messagebox.showinfo("Search", "No matches found.")

    def save_to_text(self):
        if not self.current_file_path:
            messagebox.showwarning("Warning", "No data to export. Please open a file first.")
            return
            
        import os
        base_name = os.path.basename(self.current_file_path)
        default_output_name = f"{base_name}.txt"
        
        save_path = filedialog.asksaveasfilename(initialfile=default_output_name, defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not save_path:
            return
            
        try:
            content = self.text_area.get("1.0", tk.END)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            messagebox.showinfo("Success", "File exported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalStringsViewer(root)
    root.mainloop()