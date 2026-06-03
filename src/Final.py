
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import main_ds3 as BE

BG       = "#0e0e0e"
BG2      = "#161616"
BG3      = "#1e1e1e"
PANEL    = "#121212"
BORDER   = "#2a2a2a"
GOLD     = "#c9a84c"
GOLD_DIM = "#7a6128"
EMBER    = "#cf4a1a"
RED      = "#8b1a1a"
ASH      = "#a0a0a0"
WHITE    = "#e8e2d4"
FONT_H   = ("Georgia", 14, "bold")
FONT_B   = ("Georgia", 10)
FONT_S   = ("Consolas", 9)

BTN_STYLE   = dict(bg=BG3, fg=GOLD, activebackground=BORDER, activeforeground=WHITE,
                   relief="flat", bd=0, padx=12, pady=5, font=FONT_B, cursor="hand2")
ENTRY_STYLE = dict(bg=BG2, fg=WHITE, insertbackground=GOLD, relief="flat", bd=1,
                   font=FONT_S, highlightbackground=BORDER, highlightcolor=GOLD,
                   highlightthickness=1)

# ── ttk styles ────────────────────────────────────────────────────────────────
def apply_ttk_styles():
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("DS.TNotebook", background=BG, borderwidth=0, tabmargins=[2,4,2,0])
    s.configure("DS.TNotebook.Tab", background=BG3, foreground=ASH,
                font=("Georgia", 10, "bold"), padding=[16, 8], borderwidth=0)
    s.map("DS.TNotebook.Tab",
          background=[("selected", PANEL)], foreground=[("selected", GOLD)])
    s.configure("DS.Treeview", background=BG2, foreground=WHITE,
                fieldbackground=BG2, font=FONT_S, rowheight=22, borderwidth=0)
    s.configure("DS.Treeview.Heading", background=BG3, foreground=GOLD,
                font=("Georgia", 9, "bold"), borderwidth=0)
    s.map("DS.Treeview",
          background=[("selected", GOLD_DIM)], foreground=[("selected", WHITE)])
    s.configure("DS.TCombobox", fieldbackground=BG2, background=BG3,
                foreground=WHITE, arrowcolor=GOLD, font=FONT_S)
    s.map("DS.TCombobox", fieldbackground=[("readonly", BG2)])

# ── widget helpers ────────────────────────────────────────────────────────────
def ghost_btn(parent, text, command=None, **kw):
    b = tk.Button(parent, text=text, command=command, **{**BTN_STYLE, **kw})
    b.bind("<Enter>", lambda e: b.config(bg=BORDER, fg=WHITE))
    b.bind("<Leave>", lambda e: b.config(bg=BG3, fg=GOLD))
    return b

def ember_btn(parent, text, command=None):
    b = tk.Button(parent, text=text, command=command,
                  bg=EMBER, fg=WHITE, activebackground="#a03010",
                  relief="flat", bd=0, padx=14, pady=6,
                  font=("Georgia", 10, "bold"), cursor="hand2")
    b.bind("<Enter>", lambda e: b.config(bg="#a03010"))
    b.bind("<Leave>", lambda e: b.config(bg=EMBER))
    return b

def section_label(parent, text):
    tk.Label(parent, text=text, bg=BG, fg=GOLD,
             font=FONT_H, anchor="w").pack(fill="x", padx=16, pady=(12, 2))
    tk.Frame(parent, bg=GOLD, height=1).pack(fill="x", padx=16, pady=(0, 4))

def make_scrollable_frame(parent):
    outer  = tk.Frame(parent, bg=BG)
    canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
    sb     = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=BG)
    win   = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_inner(e):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(win, width=canvas.winfo_width())
    inner.bind("<Configure>", _on_inner)
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    return outer, inner

def search_entry(parent, on_change):
    """Return a labelled search entry."""
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", padx=16, pady=(6, 2))
    tk.Label(row, text="🔍  Search:", bg=BG, fg=ASH, font=FONT_B).pack(side="left")
    var = tk.StringVar()
    e   = tk.Entry(row, textvariable=var, width=36, **ENTRY_STYLE)
    e.pack(side="left", padx=8)
    var.trace_add("write", lambda *_: on_change(var.get()))
    return var

def _reverse_lookup(item_id_int, dicts):
    """Try to find a human-readable name from multiple id-dict sources."""
    for d in dicts:
        for name, hex_id in d.items():
            try:
                base_id = int.from_bytes(bytes.fromhex(hex_id), 'little')
                if base_id == item_id_int:
                    return name
            except Exception:
                continue
    return None


_REVERSE_MAP: dict[int, str] = {}

def _build_reverse_map():
    """Call once after BE loads. Populates int_id → name for all item dicts."""
    global _REVERSE_MAP
    if not BE:
        return
    for d in [BE.goods_id, BE.rings_id, BE.weapons_id, BE.armors_id]:
        for name, hex_id in d.items():
            try:
                base_id = int.from_bytes(bytes.fromhex(hex_id), 'little')
                _REVERSE_MAP[base_id] = name
            except Exception:
                continue

def _item_display_name(item_id_int):
    if not _REVERSE_MAP:
        _build_reverse_map()

    # 1. Exact match
    name = _REVERSE_MAP.get(item_id_int)
    if name:
        return name

    # 2. Upgraded weapon — check base IDs up to +15 in one O(1) lookup each
    for level in range(1, 16):
        base_name = _REVERSE_MAP.get(item_id_int - level)
        if base_name and base_name in BE.weapons_id:
            return f"{base_name}+{level}"

    return f"0x{item_id_int:08X}"


# ══════════════════════════════════════════════════════════════════════════════
#  SEARCHABLE TREEVIEW WIDGET
# ══════════════════════════════════════════════════════════════════════════════

class SearchTree(tk.Frame):
    """
    Treeview with a live-filter search bar above it.
    columns : list of (col_id, heading, width)
    qty_bar  : if True, shows a "Selected: <name>  Qty: [__]  [Apply]" bar
               above the search row; single-click populates the name + current qty.
    on_qty   : callback(item_name, new_qty) used when qty_bar=True
    """
    def __init__(self, parent, columns, qty_bar=False, on_qty=None, height=18, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._all_rows  = []
        self._columns   = [c[0] for c in columns]
        self._on_qty    = on_qty
        self._sort_col  = None
        self._sort_rev  = False

        # ── optional quantity modifier bar ───────────────────────────────────
        if qty_bar:
            qbar = tk.Frame(self, bg=BG2, pady=6)
            qbar.pack(fill="x", padx=4, pady=(4, 0))

            tk.Label(qbar, text="Selected:", bg=BG2, fg=ASH,
                     font=FONT_B).pack(side="left", padx=(8, 4))
            self._qty_name_var = tk.StringVar(value="—")
            tk.Label(qbar, textvariable=self._qty_name_var, bg=BG2, fg=WHITE,
                     font=("Consolas", 9), width=36, anchor="w").pack(side="left", padx=(0, 12))

            tk.Label(qbar, text="Qty:", bg=BG2, fg=ASH,
                     font=FONT_B).pack(side="left")
            self._qty_var = tk.StringVar(value="")
            tk.Entry(qbar, textvariable=self._qty_var, width=7,
                     **ENTRY_STYLE).pack(side="left", padx=6)

            ghost_btn(qbar, "Apply", command=self._apply_qty).pack(side="left", padx=4)
        else:
            self._qty_name_var = None
            self._qty_var      = None

        # ── search bar ────────────────────────────────────────────────────────
        search_row = tk.Frame(self, bg=BG)
        search_row.pack(fill="x", padx=4, pady=(6, 2))
        tk.Label(search_row, text="🔍", bg=BG, fg=GOLD, font=FONT_B).pack(side="left")
        self._search_var = tk.StringVar()
        tk.Entry(search_row, textvariable=self._search_var, width=40,
                 **ENTRY_STYLE).pack(side="left", padx=6)
        tk.Label(search_row, text="Filter items…", bg=BG, fg="#444",
                 font=("Consolas", 8, "italic")).pack(side="left")
        self._search_var.trace_add("write", lambda *_: self._filter())

        # ── treeview ──────────────────────────────────────────────────────────
        tree_frame = tk.Frame(self, bg=BG)
        tree_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.tree = ttk.Treeview(tree_frame, columns=self._columns,
                                 show="headings", style="DS.Treeview", height=height)
        for col_id, heading, width in columns:
            self.tree.heading(col_id, text=heading,
                              command=lambda c=col_id: self._sort(c))
            self.tree.column(col_id, width=width, anchor="w")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        if qty_bar:
            self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ── public ────────────────────────────────────────────────────────────────
    def load(self, rows):
        self._all_rows = [(r, ()) for r in rows]
        self._filter()

    def selection(self):
        return self.tree.selection()

    def item(self, iid, *args, **kw):
        return self.tree.item(iid, *args, **kw)

    # ── internals ─────────────────────────────────────────────────────────────
    def _filter(self):
        query = self._search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for values, _ in self._all_rows:
            if query and not any(query in str(v).lower() for v in values):
                continue
            self.tree.insert("", "end", values=values)

    def _sort(self, col):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = False
        idx = self._columns.index(col)
        self._all_rows.sort(key=lambda r: str(r[0][idx]).lower(),
                            reverse=self._sort_rev)
        self._filter()

    def _on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if not vals:
            return
        name = vals[0]   # first column = item name
        # qty is always the last column for goods trees
        qty  = vals[-1] if len(vals) > 1 else ""
        self._qty_name_var.set(name)
        self._qty_var.set(str(qty))

    def _apply_qty(self):
        name = self._qty_name_var.get() if self._qty_name_var else ""
        qty  = self._qty_var.get()      if self._qty_var      else ""
        if name == "—" or not name or not qty:
            return
        try:
            new_qty = int(qty)
        except ValueError:
            return
        if self._on_qty:
            self._on_qty(name, new_qty)

    def update_row_qty(self, item_name, new_qty):
        """Update the qty cell in the tree for the given item name."""
        for iid in self.tree.get_children():
            vals = list(self.tree.item(iid, "values"))
            if vals and vals[0] == item_name:
                vals[-1] = new_qty
                self.tree.item(iid, values=vals)
                break
        # also update internal store
        for i, (vals, tags) in enumerate(self._all_rows):
            if vals and vals[0] == item_name:
                lst      = list(vals)
                lst[-1]  = new_qty
                self._all_rows[i] = (tuple(lst), tags)
                break


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

class DS3Editor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dark Souls III  ·  Save Editor")
        self.geometry("1150x780")
        self.minsize(900, 620)
        self.configure(bg=BG)
        _build_reverse_map()
        apply_ttk_styles()

        self.data           = None   # bytearray
        self.path           = None   # str
        self._char_list     = []     # [(name, slot_path)]
        self._import_list   = []     # [(name, slot_path)]
        self._import_source_path = None
        self._toast_after   = None
        self._active_char_btn = None   # currently selected character button

        self._build_header()
        self._build_notebook()
        self._build_statusbar()

    # ── header / status ───────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg="#090909", height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚔  DARK SOULS III  —  SAVE EDITOR",
                 bg="#090909", fg=GOLD,
                 font=("Georgia", 16, "bold")).pack(side="left", padx=20, pady=10)
        tk.Label(hdr, text="Mod at your own risk",
                 bg="#090909", fg="#999",
                 font=("Georgia", 9, "italic")).pack(side="left")
        
        tk.Label(hdr, text="      Made by Alfazari911",
                 bg="#090909", fg="#999",
                 font=("Georgia", 9, "italic")).pack(side="left")

    def _build_statusbar(self):
        self._status_var = tk.StringVar(value="No file loaded.")
        bar = tk.Frame(self, bg="#090909", height=24)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self._status_var, bg="#090909",
                 fg=ASH, font=("Consolas", 9), anchor="w").pack(side="left", padx=12)
        # toast label — shown briefly for success messages, right-aligned
        self._toast_var = tk.StringVar(value="")
        self._toast_lbl = tk.Label(bar, textvariable=self._toast_var,
                                   bg="#090909", fg="#4caf50",
                                   font=("Consolas", 9, "bold"), anchor="e")
        self._toast_lbl.pack(side="right", padx=16)
        self._toast_after = None

    def _status(self, msg):
        self._status_var.set(msg)

    def _toast(self, msg, duration_ms=2500):
        """Show a green success message on the right of the status bar, auto-clears."""
        if self._toast_after:
            self.after_cancel(self._toast_after)
        self._toast_var.set(f"✓  {msg}")
        self._toast_lbl.config(fg="#4caf50")
        self._toast_after = self.after(duration_ms, lambda: self._toast_var.set(""))

    # ── notebook ──────────────────────────────────────────────────────────────
    def _build_notebook(self):
        self.nb = ttk.Notebook(self, style="DS.TNotebook")
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)

        tabs = [
            ("  📂  File  ",         "_tab_file"),
            ("  🧙  Character  ",    "_tab_char"),
            ("  📊  Stats  ",        "_tab_stats"),
            ("  🎒  Inventory  ",    "_tab_inventory"),
            ("  📦  Storage  ",      "_tab_storage"),
            ("  ✨  Spawn Items  ",  "_tab_spawn"),
            ("  🌍  World Flags  ",  "_tab_world"),
        ]
        for label, attr in tabs:
            frame = tk.Frame(self.nb, bg=BG)
            setattr(self, attr, frame)
            self.nb.add(frame, text=label)

        self._build_file_tab()
        self._build_char_tab()
        self._build_stats_tab()
        self._build_inventory_tab()
        self._build_storage_tab()
        self._build_spawn_tab()
        self._build_world_tab()

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 1 — FILE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_file_tab(self):
        outer, scroll = make_scrollable_frame(self._tab_file)
        outer.pack(fill="both", expand=True)

        section_label(scroll, "Open Save File")
        tk.Label(scroll, text="Select a PS4 userdata or PC DS30000.sl2 file.\n"
                              "Characters found will appear as buttons below.",
                 bg=BG, fg=ASH, font=FONT_B, justify="left").pack(anchor="w", padx=24, pady=(0,8))
        ghost_btn(scroll, "  Open File…", self._do_open).pack(anchor="w", padx=24, pady=4)

        section_label(scroll, "Characters Found")
        self._char_btns_frame = tk.Frame(scroll, bg=BG)
        self._char_btns_frame.pack(anchor="w", padx=24, pady=4)
        tk.Label(self._char_btns_frame, text="(open a file to see characters)",
                 bg=BG, fg="#444", font=("Consolas", 9)).pack()

        tk.Frame(scroll, bg=GOLD, height=1).pack(fill="x", padx=16, pady=12)

        section_label(scroll, "Save File")
        tk.Label(scroll, text="Save changes ",
                 bg=BG, fg=ASH, font=FONT_B).pack(anchor="w", padx=24, pady=(0,8))
        ember_btn(scroll, "  💾  Save File", self._do_save).pack(anchor="w", padx=24, pady=4)

        tk.Frame(scroll, bg=GOLD, height=1).pack(fill="x", padx=16, pady=12)

        section_label(scroll, "Import Save (Character Import)")
        tk.Label(scroll,
                 text="Import a character from another save.\n"
                      "You must load your main save first, then select a character that will be replaced. Then click import and choose the character to import.\n"
                      "Importing a character will replace your current character",
                 bg=BG, fg=ASH, font=FONT_B, justify="left").pack(anchor="w", padx=24, pady=(0,8))
        ghost_btn(scroll, "  Open Import File…", self._do_open_import).pack(anchor="w", padx=24, pady=4)

        section_label(scroll, "Import — Characters Found")
        self._import_btns_frame = tk.Frame(scroll, bg=BG)
        self._import_btns_frame.pack(anchor="w", padx=24, pady=4)
        tk.Label(self._import_btns_frame, text="(open import file to see characters)",
                 bg=BG, fg="#444", font=("Consolas", 9)).pack()

    def _do_open(self):
        if BE is None:
            messagebox.showinfo("Preview", "Backend not loaded.")
            return
        result = BE.open_file()
        if result is None:
            return
        self._char_list, source_path = result
        self._status(f"File scanned: {source_path}  —  {len(self._char_list)} character(s) found")
        self._refresh_char_buttons()

    def _refresh_char_buttons(self):
        for w in self._char_btns_frame.winfo_children():
            w.destroy()
        self._active_char_btn = None
        if not self._char_list:
            tk.Label(self._char_btns_frame, text="(no characters found)",
                     bg=BG, fg="#444", font=("Consolas", 9)).pack()
            return
        self._char_btn_map = {}   # name → button widget
        for name, _ in self._char_list:
            btn = ghost_btn(self._char_btns_frame, f"  👤  {name}",
                            command=lambda n=name: self._load_character(n))
            btn.pack(side="left", padx=4)
            self._char_btn_map[name] = btn

    def _load_character(self, name):
        if BE is None:
            return
        data, path = BE.load_character_by_name(name, self._char_list)
        if data is None:
            return
        self.data = data
        self.path = path

        # ── reset all char buttons to default, highlight selected one red ────
        for btn_name, btn in self._char_btn_map.items():
            if btn_name == name:
                btn.config(bg=RED, fg=WHITE)
                btn.unbind("<Enter>")
                btn.unbind("<Leave>")
            else:
                btn.config(bg=BG3, fg=GOLD)
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BORDER, fg=WHITE))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG3, fg=GOLD))
        self._active_char_btn = name

        self._status(f"Loaded: {name}  ({path})")
        self._toast(f"Character '{name}' loaded")
        BE.sort_inventory_index(self.data)
        self._refresh_all_tabs()

    def _do_save(self):
        if self.data is None:
            messagebox.showwarning("No File", "Load a character first.")
            return
        if BE:
            BE.save_file(self.data, self.path)
            self._toast("File saved successfully")

    def _do_open_import(self):
        if BE is None:
            return
        result = BE.open_file_import()
        if result is None:
            return
        self._import_list, self._import_source_path = result
        self._status(f"Import file scanned: {self._import_source_path}")
        self._refresh_import_buttons()

    def _refresh_import_buttons(self):
        for w in self._import_btns_frame.winfo_children():
            w.destroy()
        if not self._import_list:
            tk.Label(self._import_btns_frame, text="(no characters found)",
                     bg=BG, fg="#444", font=("Consolas", 9)).pack()
            return
        for name, _ in self._import_list:
            ghost_btn(self._import_btns_frame, f"  👤  {name}",
                      command=lambda n=name: self._do_import_character(n)
                      ).pack(side="left", padx=4)

    def _do_import_character(self, name):
        if self.data is None:
            messagebox.showwarning("No File", "Load a save file first (the destination).")
            return
        import_data, _ = BE.load_character_by_name(name, self._import_list)
        if import_data is None:
            return
        result = BE.import_save_from_data(self.data, import_data)
        if result is None:
            messagebox.showerror("Error", "Import failed — Steam ID not found.")
            return
        self.data = result
        # self.path stays as the CURRENT save's slot path — do NOT change it
        self._toast(f"Imported '{name}' — Steam ID preserved")
        self._refresh_all_tabs()
        messagebox.showinfo("Import Successful", f"Character '{name}' imported successfully.\n")

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 2 — CHARACTER
    # ══════════════════════════════════════════════════════════════════════════
    def _build_char_tab(self):
        p = self._tab_char
        self._char_vars = {}

        # ── outer container, no scrolling needed ─────────────────────────────
        outer = tk.Frame(p, bg=BG)
        outer.pack(fill="both", expand=True, padx=32, pady=20)

        # Fields: (label, key, kind, max_width)
        fields = [
            ("Character Name", "char_name", "str"),
            ("New Game Plus",  "ng",        "int"),
            ("Souls",          "souls",     "int"),
            ("HP",             "hp",        "int"),
            ("FP",             "fp",        "int"),
            ("Stamina",        "stamina",   "int"),
        ]

        LABEL_W = 18   # fixed label column width (chars)
        ENTRY_W = 22

        for key_idx, (label, key, kind) in enumerate(fields):
            row = tk.Frame(outer, bg=BG)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label, bg=BG, fg=ASH, font=FONT_B,
                     width=LABEL_W, anchor="w").pack(side="left")
            var = tk.StringVar(value="" if kind == "str" else "0")
            self._char_vars[key] = var
            tk.Entry(row, textvariable=var, width=ENTRY_W, **ENTRY_STYLE).pack(side="left", padx=8)
            ghost_btn(row, "Apply",
                      command=lambda k=key, t=kind: self._apply_char_field(k, t)
                      ).pack(side="left")

        # separator
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x", pady=14)

        # action buttons
        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(anchor="w")
        ember_btn(btn_row, "  Apply All", self._apply_all_char).pack(side="left", padx=(0, 10))
        ghost_btn(btn_row, "  Refresh",   self._refresh_char_tab).pack(side="left")

    def _apply_char_field(self, key, kind):
        if self.data is None:
            messagebox.showwarning("No File", "Load a character first.")
            return
        if BE is None:
            return
        try:
            raw = self._char_vars[key].get()
            val = raw if kind == "str" else int(raw)
            if   key == "char_name": self.data = BE.change_name(self.data, val)
            elif key == "souls":     self.data = BE.change_souls(self.data, val)
            elif key == "hp":        self.data = BE.change_hp(self.data, val)
            elif key == "fp":        self.data = BE.change_fp(self.data, val)
            elif key == "stamina":   self.data = BE.change_st(self.data, val)
            elif key == "ng":        self.data = BE.change_ng(self.data, val)
            self._toast(f"Applied: {key} = {val}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _apply_all_char(self):
        for key, kind in [("char_name","str"),("ng","int"),("souls","int"),
                           ("hp","int"),("fp","int"),("stamina","int")]:
            self._apply_char_field(key, kind)

    def _refresh_char_tab(self):
        if self.data is None or BE is None:
            return
        try:
            info = BE.read_character_data(self.data)
            self._char_vars["char_name"].set(info["name"])
            self._char_vars["ng"].set(str(info["ng"]))
            self._char_vars["souls"].set(str(info["souls"]))
            self._char_vars["hp"].set(str(info["hp"]))
            self._char_vars["fp"].set(str(info["fp"]))
            self._char_vars["stamina"].set(str(info["stamina"]))
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 3 — STATS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_stats_tab(self):
        outer, scroll = make_scrollable_frame(self._tab_stats)
        outer.pack(fill="both", expand=True)

        section_label(scroll, "Character Statistics")
        self._stat_vars = {}

        stat_names = list(BE.stats_offsets_for_stats_tap.keys()) if BE else [
            "Level","Vigor","Attunement","Endurance","Vitality",
            "Strength","Dexterity","Intelligence","Faith","Luck",
        ]

        cols = tk.Frame(scroll, bg=BG)
        cols.pack(fill="both", expand=True, padx=16, pady=4)
        left  = tk.Frame(cols, bg=BG)
        right = tk.Frame(cols, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(8, 4))
        right.pack(side="left", fill="both", expand=True, padx=(4, 8))

        for i, stat in enumerate(stat_names):
            parent = left if i % 2 == 0 else right
            row = tk.Frame(parent, bg=BG)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=stat, bg=BG, fg=ASH, font=FONT_B,
                     width=28, anchor="w").pack(side="left")
            var = tk.StringVar(value="0")
            self._stat_vars[stat] = var
            tk.Entry(row, textvariable=var, width=8, **ENTRY_STYLE).pack(side="left", padx=4)

        tk.Frame(scroll, bg=GOLD, height=1).pack(fill="x", padx=16, pady=10)
        row = tk.Frame(scroll, bg=BG)
        row.pack(anchor="w", padx=24, pady=8)
        ember_btn(row, "  Apply All Stats",  self._apply_all_stats).pack(side="left", padx=(0,8))
        ghost_btn(row, "  Refresh",          self._refresh_stats_tab).pack(side="left")

    def _apply_all_stats(self):
        if self.data is None:
            messagebox.showwarning("No File", "Load a character first.")
            return
        if BE is None:
            return
        for stat, var in self._stat_vars.items():
            try:
                self.data = BE.change_stats(self.data, stat, int(var.get()))
            except Exception as e:
                messagebox.showerror("Error", f"{stat}: {e}")
                return
        self._toast("All stats applied")

    def _refresh_stats_tab(self):
        if self.data is None or BE is None:
            return
        try:
            info = BE.read_character_data(self.data)
            for stat, val in info["stats"].items():
                if stat in self._stat_vars:
                    self._stat_vars[stat].set(str(val))
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 4 — INVENTORY
    # ══════════════════════════════════════════════════════════════════════════
    def _build_inventory_tab(self):
        p = self._tab_inventory
        btn_row = tk.Frame(p, bg=BG)
        btn_row.pack(anchor="w", padx=24, pady=8)
        tk.Label(btn_row, text="Inventory", bg=BG, fg=GOLD, font=FONT_H).pack(side="left", padx=(0,16))
        ghost_btn(btn_row, "  🔄 Refresh", self._refresh_inventory_tab).pack(side="left")

        inv_nb = ttk.Notebook(p, style="DS.TNotebook")
        inv_nb.pack(fill="both", expand=True, padx=8, pady=4)

        self._inv_trees = {}
        cats = [
            ("⚔ Weapons", "weapons", False),
            ("🛡 Armors",  "armors",  False),
            ("🧪 Goods",   "goods",   True),
            ("💍 Rings",   "rings",   False),
        ]
        for label, key, has_qty in cats:
            frame = tk.Frame(inv_nb, bg=BG)
            inv_nb.add(frame, text=f"  {label}  ")
            if has_qty:
                cols = [("name", "Item Name", 360), ("id", "Item ID", 130), ("qty", "Qty", 60)]
                st = SearchTree(frame, columns=cols, qty_bar=True,
                                on_qty=lambda name, qty, k=key: self._inv_apply_qty(k, name, qty))
            else:
                cols = [("name", "Item Name", 360), ("id", "Item ID", 130)]
                st = SearchTree(frame, columns=cols)
            st.pack(fill="both", expand=True, padx=4, pady=4)
            self._inv_trees[key] = st

    def _refresh_inventory_tab(self):
        if self.data is None or BE is None:
            return
        try:
            _, weapons, armors, goods, rings, _ = BE.inventoryprint(self.data)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        def rows_nq(items):
            return [(_item_display_name(iid), f"0x{iid:08X}") for _,iid,_,_,_ in items]
        def rows_q(items):
            return [(_item_display_name(iid), f"0x{iid:08X}", qty) for _,iid,qty,_,_ in items]

        self._inv_trees["weapons"].load(rows_nq(weapons))
        self._inv_trees["armors"].load(rows_nq(armors))
        self._inv_trees["goods"].load(rows_q(goods))
        self._inv_trees["rings"].load(rows_nq(rings))
        self._toast("Inventory refreshed")

    def _inv_apply_qty(self, category, item_name, new_qty):
        """Called by the qty bar Apply button in inventory goods."""
        if self.data is None or BE is None:
            return
        if item_name.startswith("0x") or item_name == "—":
            messagebox.showwarning("Unknown Item", "Cannot map raw ID to a known item name.")
            return
        try:
            result    = BE.add_goods_rings(self.data, item_name, new_qty,
                                           stack=False, item_type="goods")
            self.data = result[0] if isinstance(result, tuple) else result
            self._inv_trees[category].update_row_qty(item_name, new_qty)
            self._toast(f"Inventory: {item_name} → {new_qty}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _inv_qty_edited(self, category, iid, col, new_val):
        # kept for backward compat, not called by new SearchTree
        pass

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 5 — STORAGE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_storage_tab(self):
        p = self._tab_storage
        btn_row = tk.Frame(p, bg=BG)
        btn_row.pack(anchor="w", padx=24, pady=8)
        tk.Label(btn_row, text="Storage Box", bg=BG, fg=GOLD, font=FONT_H).pack(side="left", padx=(0,16))
        ghost_btn(btn_row, "  🔄 Refresh", self._refresh_storage_tab).pack(side="left")

        stor_nb = ttk.Notebook(p, style="DS.TNotebook")
        stor_nb.pack(fill="both", expand=True, padx=8, pady=4)

        self._stor_trees = {}
        cats = [
            ("⚔ Weapons", "weapons", False),
            ("🛡 Armors",  "armors",  False),
            ("🧪 Goods",   "goods",   True),
            ("💍 Rings",   "rings",   False),
        ]
        for label, key, has_qty in cats:
            frame = tk.Frame(stor_nb, bg=BG)
            stor_nb.add(frame, text=f"  {label}  ")
            if has_qty:
                cols = [("name", "Item Name", 360), ("id", "Item ID", 130), ("qty", "Qty", 60)]
                st = SearchTree(frame, columns=cols, qty_bar=True,
                                on_qty=lambda name, qty, k=key: self._stor_apply_qty(k, name, qty))
            else:
                cols = [("name", "Item Name", 360), ("id", "Item ID", 130)]
                st = SearchTree(frame, columns=cols)
            st.pack(fill="both", expand=True, padx=4, pady=4)
            self._stor_trees[key] = st

    def _refresh_storage_tab(self):
        if self.data is None or BE is None:
            return
        try:
            weapons, armors, goods, rings, _ = BE.get_all_storage(self.data)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        def rows_nq(items):
            return [(_item_display_name(iid), f"0x{iid:08X}") for _,iid,_,_,_ in items]
        def rows_q(items):
            return [(_item_display_name(iid), f"0x{iid:08X}", qty) for _,iid,qty,_,_ in items]

        self._stor_trees["weapons"].load(rows_nq(weapons))
        self._stor_trees["armors"].load(rows_nq(armors))
        self._stor_trees["goods"].load(rows_q(goods))
        self._stor_trees["rings"].load(rows_nq(rings))
        self._toast("Storage refreshed")

    def _stor_apply_qty(self, category, item_name, new_qty):
        """Called by the qty bar Apply button in storage goods."""
        if self.data is None or BE is None:
            return
        if item_name.startswith("0x") or item_name == "—":
            messagebox.showwarning("Unknown Item", "Cannot map raw ID to a known item name.")
            return
        try:
            self.data = BE.modify_goods_storage_quantity(self.data, item_name, new_qty)
            self._stor_trees[category].update_row_qty(item_name, new_qty)
            self._toast(f"Storage: {item_name} → {new_qty}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _stor_qty_edited(self, category, iid, col, new_val):
        # kept for backward compat
        pass

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 6 — SPAWN ITEMS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_spawn_tab(self):
        p = self._tab_spawn

        # Outer horizontal split: left = notebook, right = terminal
        pane = tk.Frame(p, bg=BG)
        pane.pack(fill="both", expand=True)

        left = tk.Frame(pane, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(pane, bg="#0a0a0a", width=220)
        right.pack(side="right", fill="y", padx=(4, 6), pady=6)
        right.pack_propagate(False)

        # Terminal header
        tk.Label(right, text="▸ SPAWN LOG", bg="#0a0a0a", fg=GOLD,
                font=("Consolas", 8, "bold"), anchor="w").pack(fill="x", padx=6, pady=(6, 2))
        tk.Frame(right, bg=GOLD, height=1).pack(fill="x", padx=6)

        # Scrollable text widget
        self._spawn_log = tk.Text(
            right, bg="#0a0a0a", fg="#4caf50",
            font=("Consolas", 8), relief="flat", bd=0,
            state="disabled", wrap="word",
            highlightthickness=0, cursor="arrow"
        )
        log_sb = ttk.Scrollbar(right, orient="vertical", command=self._spawn_log.yview)
        self._spawn_log.configure(yscrollcommand=log_sb.set)
        log_sb.pack(side="right", fill="y", pady=4)
        self._spawn_log.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=4)

        # Clear button
        ghost_btn(right, "Clear", command=self._clear_spawn_log).pack(pady=(0, 4))

        # Build the tab notebook into the left pane
        spawn_nb = ttk.Notebook(left, style="DS.TNotebook")
        spawn_nb.pack(fill="both", expand=True, padx=8, pady=8)

        for label, builder in [
            ("  🧪 Goods  ",   self._build_spawn_goods),
            ("  ⚔ Weapons  ",  lambda f: self._build_spawn_wa(f, "weapon")),
            ("  🛡 Armors  ",   lambda f: self._build_spawn_wa(f, "armor")),
            ("  💍 Rings  ",    self._build_spawn_rings),
        ]:
            frame = tk.Frame(spawn_nb, bg=BG)
            spawn_nb.add(frame, text=label)
            builder(frame)
    def _log_spawn(self, msg):
        """Append a timestamped line to the spawn terminal."""
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self._spawn_log.config(state="normal")
        self._spawn_log.insert("end", line)
        self._spawn_log.see("end")
        self._spawn_log.config(state="disabled")

    def _clear_spawn_log(self):
        self._spawn_log.config(state="normal")
        self._spawn_log.delete("1.0", "end")
        self._spawn_log.config(state="disabled")
    # ── spawn goods ───────────────────────────────────────────────────────────
    def _build_spawn_goods(self, parent):
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="x", padx=16, pady=8)
        section_label(top, "Add Individual Good")

        row = tk.Frame(top, bg=BG)
        row.pack(anchor="w", padx=8, pady=4)
        goods_names = list(BE.goods_id.keys()) if BE else []

        # searchable combo using a Listbox popup
        self._spawn_goods_var = tk.StringVar()
        self._spawn_goods_cb  = self._make_search_combo(row, goods_names, self._spawn_goods_var, width=44)
        self._spawn_goods_cb.pack(side="left", padx=(0,8))

        tk.Label(row, text="Qty:", bg=BG, fg=ASH, font=FONT_B).pack(side="left")
        self._spawn_goods_qty = tk.StringVar(value="99")
        tk.Entry(row, textvariable=self._spawn_goods_qty, width=6, **ENTRY_STYLE).pack(side="left", padx=4)
        self._stack_goods_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            row,
            text="Stack",
            variable=self._stack_goods_var,
            bg=BG,
            fg=ASH,
            selectcolor=BG2,
            activebackground=BG,
            activeforeground=ASH
        ).pack(side="left", padx=(8, 4))

        ghost_btn(row, "  Add", self._spawn_single_good).pack(side="left", padx=8)

        tk.Frame(top, bg=GOLD, height=1).pack(fill="x", padx=8, pady=8)
        section_label(top, "Bulk Add by Category")

        cats = list(BE.GOODS_CATEGORIES.keys()) if BE else []
        grid = tk.Frame(top, bg=BG)
        grid.pack(anchor="w", padx=8, pady=4)
        for i, cat in enumerate(cats):
            ghost_btn(grid, cat, command=lambda c=cat: self._bulk_category(c)
                     ).grid(row=i//3, column=i%3, padx=5, pady=3, sticky="ew")

        tk.Frame(top, bg=GOLD, height=1).pack(fill="x", padx=8, pady=8)
        all_row = tk.Frame(top, bg=BG)
        all_row.pack(anchor="w", padx=8, pady=4)
        ember_btn(all_row, "  Bulk Add ALL Goods",
                  lambda: self._bulk_type("goods")).pack(side="left")

    def _make_search_combo(self, parent, all_values, var, width=40):
        """
        Entry + popup Listbox search combo.
        - Type to filter the list live.
        - Click a row or press Enter to select (popup closes).
        - Click anywhere outside or press Escape to dismiss without selecting.
        """
        frame = tk.Frame(parent, bg=BG)

        entry = tk.Entry(frame, textvariable=var, width=width, **ENTRY_STYLE)
        entry.pack(side="left")

        _s = {"win": None, "lb": None, "_click_id": None}

        # ── close ────────────────────────────────────────────────────────────
        def _close():
            # unbind the global click-outside listener
            if _s["_click_id"]:
                try:
                    self.unbind("<Button-1>", _s["_click_id"])
                except Exception:
                    pass
                _s["_click_id"] = None
            if _s["win"] and _s["win"].winfo_exists():
                _s["win"].destroy()
            _s["win"] = None
            _s["lb"]  = None

        # ── open ─────────────────────────────────────────────────────────────
        def _open(filtered):
            _close()
            if not filtered:
                return

            # wait until entry is mapped so winfo_rootx is valid
            entry.update_idletasks()
            x = entry.winfo_rootx()
            y = entry.winfo_rooty() + entry.winfo_height() + 2
            w = max(entry.winfo_width(), 300)

            win = tk.Toplevel(self)          # child of root, not frame
            win.overrideredirect(True)
            win.geometry(f"{w}x200+{x}+{y}")
            win.configure(bg=BG2)
            win.attributes("-topmost", True)
            _s["win"] = win

            lb_frame = tk.Frame(win, bg=BG2)
            lb_frame.pack(fill="both", expand=True)
            lb = tk.Listbox(lb_frame, bg=BG2, fg=WHITE,
                            selectbackground=GOLD_DIM, selectforeground=WHITE,
                            font=FONT_S, relief="flat", bd=0,
                            highlightthickness=0, activestyle="none")
            sb = ttk.Scrollbar(lb_frame, orient="vertical", command=lb.yview)
            lb.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
            lb.pack(side="left", fill="both", expand=True)
            _s["lb"] = lb

            for v in filtered:
                lb.insert("end", v)

            def _pick(evt=None):
                sel = lb.curselection()
                if sel:
                    var.set(lb.get(sel[0]))
                _close()
                entry.focus_set()

            lb.bind("<ButtonRelease-1>", _pick)
            lb.bind("<Return>",          _pick)
            lb.bind("<Escape>",          lambda e: _close())

            # ── global click-outside-to-close ─────────────────────────────
            def _on_global_click(evt):
                w_id = str(evt.widget)
                # allow clicks on the entry and the popup itself
                if (str(entry) in w_id or
                        (_s["win"] and str(_s["win"]) in w_id)):
                    return
                _close()

            # small delay so this open-click itself doesn't immediately close
            self.after(50, lambda: _s.update(
                {"_click_id": self.bind("<Button-1>", _on_global_click, add="+")}
            ))

        def _on_click(evt):
            q = var.get().lower()
            filtered = [v for v in all_values if q in v.lower()] if q else all_values
            _open(filtered)

        entry.bind("<Button-1>", _on_click)

        # ── key handler ───────────────────────────────────────────────────────
        def _on_key(evt):
            # ignore pure modifier / navigation keys that don't change text
            if evt.keysym in ("Up", "Down", "Left", "Right",
                              "Shift_L", "Shift_R", "Control_L", "Control_R",
                              "Alt_L", "Alt_R", "Return", "Escape",
                              "Tab", "Caps_Lock"):
                return
            q        = var.get().lower()
            filtered = [v for v in all_values if q in v.lower()] if q else all_values
            _open(filtered)

        def _on_arrow(evt):
            lb = _s["lb"]
            if lb is None:
                q        = var.get().lower()
                filtered = [v for v in all_values if q in v.lower()] if q else all_values
                _open(filtered)
                return
            cur = lb.curselection()
            if evt.keysym == "Down":
                nxt = (cur[0] + 1) if cur else 0
            else:
                nxt = (cur[0] - 1) if cur else lb.size() - 1
            nxt = max(0, min(nxt, lb.size() - 1))
            lb.selection_clear(0, "end")
            lb.selection_set(nxt)
            lb.see(nxt)

        def _on_enter(evt):
            lb = _s["lb"]
            if lb:
                sel = lb.curselection()
                if sel:
                    var.set(lb.get(sel[0]))
                _close()

        entry.bind("<KeyRelease>", _on_key)
        entry.bind("<Down>",       _on_arrow)
        entry.bind("<Up>",         _on_arrow)
        entry.bind("<Return>",     _on_enter)
        entry.bind("<Escape>",     lambda e: _close())

        return frame

    def _filter_combo(self, cb, all_values, query):
        # no longer used — kept to avoid AttributeError if called
        pass

    def _spawn_single_good(self):
        self._spawn_item(
            self._spawn_goods_var.get(),
            "goods",
            qty=self._safe_int(self._spawn_goods_qty.get(), 99),
            stack=self._stack_goods_var.get()
        )

    def _bulk_category(self, category):
        if self.data is None:
            messagebox.showwarning("No File", "Load a character first.")
            return
        if not messagebox.askyesno("Confirm", f"Bulk add all: {category}?"):
            return
        if BE:
            try:
                self.data = BE.bulk_add_goods_category(self.data, category)
                self._toast(f"Bulk added: {category}")
                self._log_spawn(f"★ Bulk: {category}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _bulk_type(self, item_type):
        if self.data is None:
            messagebox.showwarning("No File", "Load a character first.")
            return
        if not messagebox.askyesno("Confirm", f"Bulk add ALL {item_type}?"):
            return
        if BE:
            try:
                self.data = BE.bulk_add_goods_rings(self.data, item_type)
                self._toast(f"Bulk add: {item_type} done")
                self._log_spawn(f"★ Bulk all: {item_type}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── spawn weapons / armors ────────────────────────────────────────────────
    def _build_spawn_wa(self, parent, item_type):
        label = "Weapon" if item_type == "weapon" else "Armor"
        section_label(parent, f"Add Individual {label}")

        row = tk.Frame(parent, bg=BG)
        row.pack(anchor="w", padx=24, pady=8)
        src = list((BE.weapons_id if item_type == "weapon" else BE.armors_id).keys()) if BE else []
        var = tk.StringVar()
        cb  = self._make_search_combo(row, src, var, width=52)
        cb.pack(side="left", padx=(0,8))
        if item_type == "weapon":
            self._spawn_weapon_var = var
        else:
            self._spawn_armor_var  = var
        ghost_btn(row, "  Add",
                  command=lambda t=item_type, v=var: self._spawn_wa(t, v)
                  ).pack(side="left")

        tk.Frame(parent, bg=GOLD, height=1).pack(fill="x", padx=16, pady=8)
        all_row = tk.Frame(parent, bg=BG)
        all_row.pack(anchor="w", padx=24, pady=4)
        ember_btn(all_row, f"  Bulk Add ALL {label}s",
                  lambda t=item_type: self._bulk_wa(t)).pack(side="left")

    def _spawn_wa(self, item_type, var):
        name = var.get()
        if not name or self.data is None:
            return
        if BE:
            try:
                self.data, flag = BE.add_weapon_armor(self.data, name, item_type)
                if flag:
                    messagebox.showwarning("Slots Full", "No inventory slots available.")
                else:
                    self._toast(f"Spawned: {name}")
                    self._log_spawn(f"+ {name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _bulk_wa(self, item_type):
        if self.data is None:
            messagebox.showwarning("No File", "Load a character first.")
            return
        if not messagebox.askyesno("Confirm", f"Bulk add ALL {item_type}s? (may take a moment)"):
            return
        if BE:
            try:
                self.data = BE.bulk_add_weapon_or_armor(self.data, item_type)
                self._toast(f"Bulk add: {item_type}s done")
                self._log_spawn(f"★ Bulk all: {item_type}s")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── spawn rings ────────────────────────────────────────────────────────────
    def _build_spawn_rings(self, parent):
        section_label(parent, "Add Individual Ring")
        row = tk.Frame(parent, bg=BG)
        row.pack(anchor="w", padx=24, pady=8)
        ring_names = list(BE.rings_id.keys()) if BE else []
        self._spawn_ring_var = tk.StringVar()
        cb = self._make_search_combo(row, ring_names, self._spawn_ring_var, width=52)
        cb.pack(side="left", padx=(0,8))
        ghost_btn(row, "  Add", self._spawn_single_ring).pack(side="left")

        tk.Frame(parent, bg=GOLD, height=1).pack(fill="x", padx=16, pady=8)
        all_row = tk.Frame(parent, bg=BG)
        all_row.pack(anchor="w", padx=24, pady=4)
        ember_btn(all_row, "  Bulk Add ALL Rings",
                  lambda: self._bulk_type("rings")).pack(side="left")

    def _spawn_single_ring(self):
        self._spawn_item(self._spawn_ring_var.get(), "rings", qty=1)

    def _spawn_item(self, name, item_type, qty=99, stack=False):
        if self.data is None:
            messagebox.showwarning("No File", "Load a character first.")
            return
        if not name:
            return
        if BE:
            try:
                result = BE.add_goods_rings(self.data, name, qty,
                                             stack=stack, item_type=item_type)
                self.data = result[0] if isinstance(result, tuple) else result
                self._toast(f"Added: {name} ×{qty}")
                self._log_spawn(f"+ {name} ×{qty}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════════════════════════
    #  TAB 7 — WORLD FLAGS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_world_tab(self):
        p = self._tab_world
        outer, scroll = make_scrollable_frame(p)
        outer.pack(fill="both", expand=True)

        # action buttons
        btn_row = tk.Frame(scroll, bg=BG)
        btn_row.pack(anchor="w", padx=24, pady=8)
        ghost_btn(btn_row, "  🔄 Refresh Flags",     self._refresh_world_tab).pack(side="left", padx=(0,8))
        ember_btn(btn_row, "  ☠  Kill All Bosses",    self._kill_all_bosses).pack(side="left", padx=(0,8))
        ghost_btn(btn_row, "  🔥 Unlock All Bonfires",self._unlock_all_bonfires).pack(side="left")

        # ── Boss grid ─────────────────────────────────────────────────────────
        section_label(scroll, "Boss Status")
        boss_outer = tk.Frame(scroll, bg=BG)
        boss_outer.pack(fill="x", padx=24, pady=4)

        # search for bosses
        self._boss_search = tk.StringVar()
        sr = tk.Frame(boss_outer, bg=BG)
        sr.pack(anchor="w", pady=(0, 6))
        tk.Label(sr, text="🔍", bg=BG, fg=GOLD, font=FONT_B).pack(side="left")
        tk.Entry(sr, textvariable=self._boss_search, width=36, **ENTRY_STYLE).pack(side="left", padx=6)
        self._boss_search.trace_add("write", lambda *_: self._filter_boss_grid())

        self._boss_grid = tk.Frame(boss_outer, bg=BG)
        self._boss_grid.pack(fill="x")
        self._boss_vars   = {}
        self._boss_rows   = {}   # boss_name → row widget

        boss_names = list(BE.bosses_offsets_for_bosses_tap.keys()) if BE else []
        for i, boss in enumerate(boss_names):
            row = tk.Frame(self._boss_grid, bg=BG)
            row.grid(row=i//2, column=i%2, padx=8, pady=3, sticky="ew")
            tk.Label(row, text=boss, bg=BG, fg=ASH, font=FONT_B,
                     width=38, anchor="w").pack(side="left")
            var = tk.StringVar(value="Alive")
            self._boss_vars[boss] = var
            self._boss_rows[boss] = row
            om = ttk.OptionMenu(row, var, "Alive", "Alive", "Defeated",
                                command=lambda val, b=boss: self._set_boss(b, val))
            om.config(width=10)
            om.pack(side="left", padx=4)
        self._boss_grid.columnconfigure(0, weight=1)
        self._boss_grid.columnconfigure(1, weight=1)

        tk.Frame(scroll, bg=GOLD, height=1).pack(fill="x", padx=16, pady=12)

        # ── Bonfire grid ──────────────────────────────────────────────────────
        section_label(scroll, "Bonfire / Area Status")
        bf_outer = tk.Frame(scroll, bg=BG)
        bf_outer.pack(fill="x", padx=24, pady=4)

        self._bf_search = tk.StringVar()
        sr2 = tk.Frame(bf_outer, bg=BG)
        sr2.pack(anchor="w", pady=(0, 6))
        tk.Label(sr2, text="🔍", bg=BG, fg=GOLD, font=FONT_B).pack(side="left")
        tk.Entry(sr2, textvariable=self._bf_search, width=36, **ENTRY_STYLE).pack(side="left", padx=6)
        self._bf_search.trace_add("write", lambda *_: self._filter_bf_grid())

        self._bf_grid   = tk.Frame(bf_outer, bg=BG)
        self._bf_grid.pack(fill="x")
        self._bonfire_vars = {}
        self._bonfire_rows = {}

        bf_names = list(BE.bonfire_offsets_for_bonfire_tap.keys()) if BE else []
        for i, bf in enumerate(bf_names):
            row = tk.Frame(self._bf_grid, bg=BG)
            row.grid(row=i//2, column=i%2, padx=8, pady=3, sticky="ew")
            tk.Label(row, text=bf, bg=BG, fg=ASH, font=FONT_B,
                     width=38, anchor="w").pack(side="left")
            var = tk.StringVar(value="Locked")
            self._bonfire_vars[bf] = var
            self._bonfire_rows[bf] = row
            om = ttk.OptionMenu(row, var, "Locked", "Locked", "Unlocked",
                                command=lambda val, b=bf: self._set_bonfire(b, val))
            om.config(width=10)
            om.pack(side="left", padx=4)
        self._bf_grid.columnconfigure(0, weight=1)
        self._bf_grid.columnconfigure(1, weight=1)

    def _filter_boss_grid(self):
        q = self._boss_search.get().lower()
        for boss, row in self._boss_rows.items():
            if q and q not in boss.lower():
                row.grid_remove()
            else:
                row.grid()
    if not sys:
        exit()
    def _filter_bf_grid(self):
        q = self._bf_search.get().lower()
        for bf, row in self._bonfire_rows.items():
            if q and q not in bf.lower():
                row.grid_remove()
            else:
                row.grid()

    def _refresh_world_tab(self):
        if self.data is None or BE is None:
            return
        try:
            bosses   = BE.get_boss_status(self.data)
            bonfires = BE.get_bonfire_status(self.data)
            for boss, status in bosses.items():
                if boss in self._boss_vars:
                    self._boss_vars[boss].set(status)
            for bf, status in bonfires.items():
                if bf in self._bonfire_vars:
                    self._bonfire_vars[bf].set(status)
            self._toast("World flags refreshed")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _set_boss(self, boss_name, status):
        if self.data is None or BE is None:
            return
        try:
            self.data = BE.change_boss_status(self.data, boss_name, status)
            self._toast(f"Boss: {boss_name} → {status}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _set_bonfire(self, bonfire_name, status):
        if self.data is None or BE is None:
            return
        try:
            self.data = BE.change_bonfire_status(self.data, bonfire_name, status)
            self._toast(f"Bonfire: {bonfire_name} → {status}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _kill_all_bosses(self):
        if self.data is None:
            messagebox.showwarning("No File", "Load a character first.")
            return
        if not messagebox.askyesno("Confirm", "Set ALL bosses to Defeated?"):
            return
        if BE:
            for boss in BE.bosses_offsets_for_bosses_tap:
                try:
                    self.data = BE.change_boss_status(self.data, boss, "Defeated")
                    if boss in self._boss_vars:
                        self._boss_vars[boss].set("Defeated")
                except Exception:
                    pass
            self._toast("All bosses set to Defeated")

    def _unlock_all_bonfires(self):
        if self.data is None:
            messagebox.showwarning("No File", "Load a character first.")
            return
        if not messagebox.askyesno("Confirm", "Unlock ALL bonfires?"):
            return
        if BE:
            for bf in BE.bonfire_offsets_for_bonfire_tap:
                try:
                    self.data = BE.change_bonfire_status(self.data, bf, "Unlocked")
                    if bf in self._bonfire_vars:
                        self._bonfire_vars[bf].set("Unlocked")
                except Exception:
                    pass
            self._toast("All bonfires unlocked")

    # ══════════════════════════════════════════════════════════════════════════
    #  GLOBAL REFRESH
    # ══════════════════════════════════════════════════════════════════════════
    def _refresh_all_tabs(self):
        self._refresh_char_tab()
        self._refresh_stats_tab()
        self._refresh_inventory_tab()
        self._refresh_storage_tab()
        self._refresh_world_tab()

    # ── utils ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _safe_int(val, default=0):
        try:
            return int(val)
        except (ValueError, TypeError):
            return default


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = DS3Editor()
    app.mainloop()
