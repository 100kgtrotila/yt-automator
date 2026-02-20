import traceback
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk

from src.infrastructure.ioc_container import Container
from src.presentation.controllers import BatchController

COLORS = {
    "bg": "#1a1a1a", "card": "#2b2b2b", "primary": "#3B8ED0",
    "accent": "#E07A5F", "success": "#2CC985", "text": "#eeeeee", "text_gray": "#aaaaaa"
}


class BatchView(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller: BatchController, log_callback):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.log = log_callback

        self.selected_folder = None
        self.selected_image = None
        self.pattern_list = []

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.frame_files = self._create_card("Source Files")
        self.frame_files.master.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)

        ctk.CTkButton(self.frame_files, text="Select MP3 Folder", fg_color=COLORS["card"],
                      border_width=1, border_color=COLORS["primary"], command=self._sel_folder).pack(fill="x", pady=5)
        self.btn_folder_lbl = ctk.CTkLabel(self.frame_files, text="No folder selected", text_color="gray",
                                           font=("Arial", 10))
        self.btn_folder_lbl.pack()

        ctk.CTkButton(self.frame_files, text="Select Fallback Cover", fg_color=COLORS["card"],
                      border_width=1, border_color=COLORS["primary"], command=self._sel_img).pack(fill="x", pady=5)
        self.btn_cover_lbl = ctk.CTkLabel(self.frame_files, text="No cover selected", text_color="gray",
                                          font=("Arial", 10))
        self.btn_cover_lbl.pack()

        self.frame_schedule = self._create_card("Schedule")
        self.frame_schedule.master.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=10)

        ctk.CTkLabel(self.frame_schedule, text="Start Date (YYYY-MM-DD):").pack(anchor="w")
        self.ent_date = ctk.CTkEntry(self.frame_schedule)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_date.pack(fill="x", pady=2)

        ctk.CTkLabel(self.frame_schedule, text="Interval (days):").pack(anchor="w", pady=(5, 0))
        self.ent_freq = ctk.CTkEntry(self.frame_schedule)
        self.ent_freq.insert(0, "1")
        self.ent_freq.pack(fill="x", pady=2)

        self.frame_meta = self._create_card("📝 Metadata Strategy")
        self.frame_meta.master.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)

        self.mode_tab = ctk.CTkTabview(self.frame_meta, height=300)
        self.mode_tab.pack(fill="both", expand=True)
        self._build_simple_ui(self.mode_tab.add("Single Preset"))
        self._build_pattern_ui(self.mode_tab.add("Pattern Mode"))

        self.frame_actions = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=20)

        ctk.CTkButton(self.frame_actions, text="⚡ GENERATE BATCH", fg_color=COLORS["accent"],
                      height=45, font=("Arial", 14, "bold"), command=self._on_generate).pack(side="left", fill="x",
                                                                                             expand=True, padx=(0, 10))

        self.btn_run = ctk.CTkButton(self.frame_actions, text="🚀 START UPLOADING", fg_color=COLORS["success"],
                                     height=45, font=("Arial", 14, "bold"), command=self._on_start_worker)
        self.btn_run.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _create_card(self, title):
        card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=10)
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 16, "bold"), text_color=COLORS["primary"]).pack(anchor="w",
                                                                                                         padx=20,
                                                                                                         pady=(15, 0))
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(padx=20, pady=(10, 20), fill="both", expand=True)
        return content

    def _build_simple_ui(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5)
        self.combo_presets = ctk.CTkComboBox(row, values=["None"], command=self._on_load_preset)
        self.combo_presets.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="💾", width=40, command=self._on_save_preset).pack(side="left", padx=5)
        ctk.CTkButton(row, text="🗑", width=40, fg_color="#AA3333", command=self._on_delete_preset).pack(side="left")

        self._refresh_presets()

        self.ent_title = self._add_field(parent, "Title Template:")
        self.ent_desc = self._add_field(parent, "Description:", is_textbox=True)
        self.ent_tags = self._add_field(parent, "Tags:")

    def _add_field(self, parent, label, is_textbox=False):
        ctk.CTkLabel(parent, text=label, font=("Arial", 12, "bold")).pack(anchor="w")
        if is_textbox:
            widget = ctk.CTkTextbox(parent, height=80)
        else:
            widget = ctk.CTkEntry(parent)
        widget.pack(fill="x", pady=(2, 10))
        return widget

    def _build_pattern_ui(self, parent):
        ctrl = ctk.CTkFrame(parent, fg_color="transparent")
        ctrl.pack(fill="x")
        ctk.CTkLabel(ctrl, text="Add current fields from Single Preset tab to cycle").pack(side="left")
        ctk.CTkButton(ctrl, text="Add Step", width=80, command=self._add_to_pattern).pack(side="right")

        self.scroll_pattern = ctk.CTkScrollableFrame(parent, height=150, fg_color="#222")
        self.scroll_pattern.pack(fill="both", expand=True, pady=5)
        ctk.CTkButton(parent, text="Clear", fg_color="#AA3333", command=self._clear_pattern).pack(anchor="e")


    def _on_generate(self):
        # 1. Collect Data
        form_data = {
            'folder': self.selected_folder,
            'cover': self.selected_image,
            'start_date': self.ent_date.get(),
            'interval': self.ent_freq.get(),
            'title': self.ent_title.get(),
            'desc': self.ent_desc.get("0.0", "end").strip(),
            'tags': self.ent_tags.get(),
            'preset_rotation': None
        }

        if self.mode_tab.get() == "Pattern Mode":
            if not self.pattern_list:
                messagebox.showwarning("Empty", "Pattern list is empty!")
                return
            form_data['preset_rotation'] = self.pattern_list
            form_data['title'] = self.pattern_list[0]['title']
            form_data['desc'] = self.pattern_list[0]['desc']
            form_data['tags'] = self.pattern_list[0]['tags']

        try:
            count = self.controller.generate_batch(form_data)
            messagebox.showinfo("Success", f"Generated {count} jobs successfully!")
            self.log(f"Queue generated: {count} videos.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            traceback.print_exc()

    def _on_start_worker(self):
        self.controller.start_worker()
        self.btn_run.configure(state="disabled", text="Running...")
        self.log("Worker started.")

    def _on_save_preset(self):
        name = ctk.CTkInputDialog(text="Name:", title="Save Preset").get_input()
        if name:
            data = {
                'title': self.ent_title.get(),
                'desc': self.ent_desc.get("0.0", "end").strip(),
                'tags': self.ent_tags.get()
            }
            self.controller.save_preset(name, data)
            self._refresh_presets()

    def _on_load_preset(self, name):
        preset = self.controller.load_preset(name)
        if preset:
            self.ent_title.delete(0, "end");
            self.ent_title.insert(0, preset.title_template)
            self.ent_tags.delete(0, "end");
            self.ent_tags.insert(0, preset.tags_template)
            self.ent_desc.delete("0.0", "end");
            self.ent_desc.insert("0.0", preset.desc_template)

    def _on_delete_preset(self):
        self.controller.delete_preset(self.combo_presets.get())
        self._refresh_presets()

    def _refresh_presets(self):
        names = self.controller.get_preset_names()
        self.combo_presets.configure(values=names if names else ["None"])
        if names: self.combo_presets.set("Select...")

    def _sel_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.selected_folder = p
            self.btn_folder_lbl.configure(text=Path(p).name, text_color="white")

    def _sel_img(self):
        p = filedialog.askopenfilename(filetypes=[("Img", "*.jpg *.png")])
        if p:
            self.selected_image = p
            self.btn_cover_lbl.configure(text=Path(p).name, text_color="white")

    def _add_to_pattern(self):
        item = {
            'title': self.ent_title.get(),
            'desc': self.ent_desc.get("0.0", "end").strip(),
            'tags': self.ent_tags.get()
        }
        if not item['title']: return
        self.pattern_list.append(item)
        self._render_pattern()

    def _render_pattern(self):
        for w in self.scroll_pattern.winfo_children(): w.destroy()
        for i, item in enumerate(self.pattern_list):
            ctk.CTkLabel(self.scroll_pattern, text=f"{i + 1}. {item['title'][:30]}...").pack(anchor="w")

    def _clear_pattern(self):
        self.pattern_list = []
        self._render_pattern()


class MainApp(ctk.CTk):
    def __init__(self, container: Container):
        super().__init__()
        self.title("YT Automator Refactored")
        self.geometry("800x800")

        self.controller = BatchController(container)

        self.log_box = ctk.CTkTextbox(self, height=100)
        self.log_box.pack(side="bottom", fill="x", padx=10, pady=10)

        self.controller.set_logger(self.log_message)

        self.view = BatchView(self, self.controller, self.log_message)
        self.view.pack(fill="both", expand=True, padx=10, pady=5)

    def log_message(self, msg: str):
        def _update():
            self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
            self.log_box.see("end")

        self.after(0, _update)

    def on_close(self):
        self.controller.stop_worker()
        self.destroy()