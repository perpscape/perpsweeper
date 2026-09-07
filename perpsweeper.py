import tkinter as tk
from tkinter import messagebox
import random

DIFFICULTIES = {
    "Easy": {"rows": 8, "cols": 8, "mines": 10},
    "Normal": {"rows": 16, "cols": 16, "mines": 40},
    "Hard": {"rows": 24, "cols": 24, "mines": 99},
    "Insane": {"rows": 30, "cols": 50, "mines": 350},
    "Crazy": {"rows": 50, "cols": 100, "mines": 600},
    "Crazy+": {"rows": 99, "cols": 199, "mines": 1200},
    "salsa": {"rows": 1, "cols": 2, "mines": 1}
}

class Minesweeper(tk.Tk):
    def __init__(self, difficulty="Normal"):
        super().__init__()
        self.title("sweepminer y")
        self.geometry("400x400")

        self.iconbitmap('mart.ico')
        self.header = tk.Frame(self)
        self.header.pack(fill=tk.X)
        
        self.difficulty = difficulty
        settings = DIFFICULTIES[difficulty]
        self.rows = settings["rows"]
        self.cols = settings["cols"]
        self.mines = settings["mines"]
        self.flags = 0
        self.first_click = True
        self.cell_size = 20  # Default zoom level
        
        # viewport offsets used for magnifier-focused view
        self.offset_row = 0
        self.offset_col = 0
        self.magnifier_mode = False
        self.view_rows = self.rows
        self.view_cols = self.cols

        self.emoji_font = ("Consolas", 12)
        
        self.timer_label = tk.Label(self.header, text="⏱ 0s", font=self.emoji_font)
        self.timer_label.pack(side=tk.LEFT, padx=10)
        self.elapsed_time = 0
        # timer_active means timer has been started; paused toggles pause/resume
        self.timer_active = False

        # always bind keys and handle them conditionally
        self.bind("<Key>", self.on_key_press)

        self.cells = [[{"mine": False, "revealed": False, "flagged": False} for _ in range(self.cols)] for _ in range(self.rows)]

        self.mine_label = tk.Label(self.header, text=f"💣 {self.mines}", font=self.emoji_font)
        self.mine_label.pack(side=tk.LEFT, padx=10)
        self.flag_label = tk.Label(self.header, text=f"🚩 {self.flags}", font=self.emoji_font)
        self.flag_label.pack(side=tk.LEFT, padx=10)
        self.restart_button = tk.Button(self.header, text="Restart", command=self.restart_game)
        self.restart_button.pack(side=tk.RIGHT, padx=10)

        self.difficulty_var = tk.StringVar(value=difficulty)
        self.difficulty_menu = tk.OptionMenu(self.header, self.difficulty_var, *DIFFICULTIES.keys(), command=self.change_difficulty)
        self.difficulty_menu.pack(side=tk.RIGHT, padx=10)

        # Add a bottom frame for the magnifier label
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        # magnifier status label (hidden when off)
        self.magnifier_label = tk.Label(self.bottom_frame, text="Magnifier is on", font=self.emoji_font)
        # don't pack now; only pack when active

        self.canvas = tk.Canvas(self, bg="lightgray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Configure>", self.redraw)

        self.redraw()

    def place_mines(self, safe_r, safe_c):
        positions = set()
        all_positions = {(r, c) for r in range(self.rows) for c in range(self.cols)}

        if safe_r is not None and safe_c is not None:
            excluded = {(safe_r + dr, safe_c + dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1]
                        if 0 <= safe_r + dr < self.rows and 0 <= safe_c + dc < self.cols}
            available = list(all_positions - excluded)
            if len(available) < self.mines:
                available = list(all_positions - {(safe_r, safe_c)})
        else:
            available = list(all_positions)

        random.shuffle(available)
        for i in range(self.mines):
            r, c = available[i]
            self.cells[r][c]["mine"] = True


    def redraw(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if self.magnifier_mode and self.difficulty in ["Easy", "Normal", "Hard", "Insane", "Crazy"]:
            self.view_rows = min(self.rows, 21)
            self.view_cols = min(self.cols, 21)
            self.cell_size = max(5, min(w // self.view_cols if self.view_cols else w, h // self.view_rows if self.view_rows else h))
        else:
            self.view_rows = self.rows
            self.view_cols = self.cols
            self.cell_size = max(5, min(w // self.view_cols if self.view_cols else w, h // self.view_rows if self.view_rows else h))

        for vr in range(self.view_rows):
            for vc in range(self.view_cols):
                r = self.offset_row + vr
                c = self.offset_col + vc
                if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
                    continue
                x1 = vc * self.cell_size
                y1 = vr * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                cell = self.cells[r][c]
                color = "white"
                text = ""
                if cell["revealed"]:
                    color = "lightgrey"
                    count = self.count_adjacent_mines(r, c)
                    if cell["mine"]:
                        text = "💣"
                        color = "red"
                    elif count > 0:
                        text = str(count)
                elif cell["flagged"]:
                    text = "🚩"
                outline_width = 1
                if self.magnifier_mode and self.difficulty in ["Easy", "Normal", "Hard", "Insane", "Crazy"] and (r == 0 or r == self.rows - 1 or c == 0 or c == self.cols - 1):
                    outline_width = 4
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black", width=outline_width)
                if text:
                    color = "black"
                    if text.isdigit():
                        color_map = {
                            "1": "blue", "2": "green", "3": "red", "4": "darkblue",
                            "5": "darkred", "6": "turquoise", "7": "black", "8": "gray"
                        }
                        color = color_map.get(text, "black")
                    self.canvas.create_text(
                        (x1 + x2) // 2,
                        (y1 + y2) // 2,
                        text=text,
                        font=("Consolas", max(8, self.cell_size // 2), "bold"),
                        fill=color
                    )
        # removed pause overlay

    def get_cell_coords(self, event):
        col_in_view = event.x // self.cell_size
        row_in_view = event.y // self.cell_size
        col = self.offset_col + col_in_view
        row = self.offset_row + row_in_view
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return row, col
        return None, None

    def on_left_click(self, event):
        r, c = self.get_cell_coords(event)
        if r is None:
            return
        # In magnifier mode, do not focus viewport on clicked tile; just reveal as normal
        if self.first_click:
            if self.difficulty == "Crazy+":
                self.place_mines(None, None)
            else:
                self.place_mines(r, c)
            self.first_click = False
            self.start_timer()
        cell = self.cells[r][c]
        if cell["flagged"] or cell["revealed"]:
            return
        cell["revealed"] = True
        if cell["mine"]:
            self.stop_timer()
            self.reveal_all()
            messagebox.showinfo("Bad", "Bro is 🤣🤣🤣", icon="error")
        else:
            count = self.count_adjacent_mines(r, c)
            if count == 0:
                self.reveal_neighbors(r, c)
            self.check_win()
        self.redraw()

    def on_right_click(self, event):
        r, c = self.get_cell_coords(event)
        if r is None:
            return
        cell = self.cells[r][c]
        if cell["revealed"]:
            return
        cell["flagged"] = not cell["flagged"]
        self.flags = sum(cell["flagged"] for row in self.cells for cell in row)
        self.flag_label.config(text=f"🚩 {self.flags}")
        self.redraw()

    def count_adjacent_mines(self, row, col):
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.cells[nr][nc]["mine"]:
                        count += 1
        return count

    def reveal_neighbors(self, row, col):
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    cell = self.cells[nr][nc]
                    if not cell["revealed"] and not cell["mine"]:
                        cell["revealed"] = True
                        if self.count_adjacent_mines(nr, nc) == 0:
                            self.reveal_neighbors(nr, nc)

    def reveal_all(self):
        for row in self.cells:
            for cell in row:
                cell["revealed"] = True

    def check_win(self):
        for row in self.cells:
            for cell in row:
                if not cell["mine"] and not cell["revealed"]:
                    return
        self.stop_timer()
        self.reveal_all()
        messagebox.showinfo("Good", "You done win")

    def restart_game(self):
        # reset the current window and game state without destroying the window
        difficulty = self.difficulty_var.get()
        self.difficulty = difficulty
        settings = DIFFICULTIES[difficulty]
        self.rows = settings["rows"]
        self.cols = settings["cols"]
        self.mines = settings["mines"]
        self.flags = 0
        self.first_click = True
        self.elapsed_time = 0
        self.timer_active = False
        self.offset_row = 0
        self.offset_col = 0
        self.magnifier_mode = False
        # update labels
        self.mine_label.config(text=f"💣 {self.mines}")
        self.flag_label.config(text=f"🚩 {self.flags}")
        self.timer_label.config(text=f"⏱️ {self.elapsed_time}s")
        try:
            self.magnifier_label.pack_forget()
        except Exception:
            pass
        self.cells = [[{"mine": False, "revealed": False, "flagged": False} for _ in range(self.cols)] for _ in range(self.rows)]
        self.redraw()

    def change_difficulty(self, new_difficulty):
        # change difficulty in-place and reset game state
        self.difficulty_var.set(new_difficulty)
        self.restart_game()
        
    def start_timer(self):
        if not self.timer_active:
            self.timer_active = True
            self.update_timer()

    def update_timer(self):
        if self.timer_active:
            self.elapsed_time += 1
            label_text = f"⏱️ {self.elapsed_time}s"
            self.timer_label.config(text=label_text)
            # schedule next tick
            self.after(1000, self.update_timer)

    def stop_timer(self):
        self.timer_active = False
        self.timer_label.config(text=f"⏱️ {self.elapsed_time}s")
        
    def zoom_in(self, event=None):
        self.cell_size = min(self.cell_size + 5, 100)
        self.redraw()

    def zoom_out(self, event=None):
        self.cell_size = max(self.cell_size - 5, 5)
        self.redraw()

    def toggle_magnifier(self):
        # toggled by pressing M; only applicable to Insane and Crazy
        if self.difficulty not in ["Easy", "Normal", "Hard", "Insane", "Crazy"]:
            return
        self.magnifier_mode = not self.magnifier_mode
        if self.magnifier_mode:
            # show magnifier label at bottom
            self.magnifier_label.pack(side=tk.BOTTOM, pady=2)
            # set view size to max 21x21 and center around current offset
            self.view_rows = min(self.rows, 21)
            self.view_cols = min(self.cols, 21)
            # ensure offset is valid
            self.offset_row = max(0, min(self.offset_row, self.rows - self.view_rows))
            self.offset_col = max(0, min(self.offset_col, self.cols - self.view_cols))
        else:
            # hide magnifier label and reset viewport
            try:
                self.magnifier_label.pack_forget()
            except Exception:
                pass
            self.view_rows = self.rows
            self.view_cols = self.cols
            self.offset_row = 0
            self.offset_col = 0
        self.redraw()

    def on_key_press(self, event):
        ch = (event.char or "").lower()
        if self.magnifier_mode and self.difficulty in ["Insane", "Crazy"]:
            if event.keysym == "Up":
                self.offset_row = max(0, self.offset_row - 1)
                self.redraw()
                return
            elif event.keysym == "Down":
                self.offset_row = min(self.rows - self.view_rows, self.offset_row + 1)
                self.redraw()
                return
            elif event.keysym == "Left":
                self.offset_col = max(0, self.offset_col - 1)
                self.redraw()
                return
            elif event.keysym == "Right":
                self.offset_col = min(self.cols - self.view_cols, self.offset_col + 1)
                self.redraw()
                return
        if ch == 'm':
            self.toggle_magnifier()
        elif ch == '+':
            if self.difficulty in ["Insane", "Crazy"]:
                self.zoom_in()
        elif ch == '-':
            if self.difficulty in ["Insane", "Crazy"]:
                self.zoom_out()

if __name__ == "__main__":
    Minesweeper().mainloop()
