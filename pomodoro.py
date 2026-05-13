import tkinter as tk
from tkinter import messagebox, simpledialog

WORK_MINUTES = 25
BREAK_MINUTES = 5


class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("番茄钟")
        self.root.geometry("320x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#EF9A9A")

        self.state = "idle"  # idle / running / paused
        self.is_work = True
        self.remaining = WORK_MINUTES * 60
        self.timer_id = None

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Title
        self.title_label = tk.Label(
            self.root, text="番茄钟", font=("微软雅黑", 20, "bold"),
            bg="#EF9A9A", fg="#B71C1C"
        )
        self.title_label.pack(pady=(30, 10))

        # Countdown display
        self.time_label = tk.Label(
            self.root, text="25:00", font=("Consolas", 64, "bold"),
            bg="#EF9A9A", fg="#B71C1C"
        )
        self.time_label.pack(pady=10)

        # Status label
        self.status_label = tk.Label(
            self.root, text="准备开始", font=("微软雅黑", 14),
            bg="#EF9A9A", fg="#C62828"
        )
        self.status_label.pack(pady=(0, 30))

        # Button frame
        btn_frame = tk.Frame(self.root, bg="#EF9A9A")
        btn_frame.pack()

        btn_style = {
            "font": ("微软雅黑", 12),
            "width": 7,
            "height": 1,
            "relief": "flat",
            "cursor": "hand2",
        }

        self.start_btn = tk.Button(
            btn_frame, text="开始", command=self.start,
            bg="#FFFFFF", fg="#C62828", activebackground="#FFCDD2", **btn_style
        )
        self.start_btn.grid(row=0, column=0, padx=5)

        self.pause_btn = tk.Button(
            btn_frame, text="暂停", command=self.pause,
            bg="#FFFFFF", fg="#C62828", activebackground="#FFCDD2",
            state="disabled", **btn_style
        )
        self.pause_btn.grid(row=0, column=1, padx=5)

        self.reset_btn = tk.Button(
            btn_frame, text="重置", command=self.reset,
            bg="#FFFFFF", fg="#C62828", activebackground="#FFCDD2", **btn_style
        )
        self.reset_btn.grid(row=0, column=2, padx=5)

        # Rest button (second row)
        self.rest_btn = tk.Button(
            self.root, text="休息", command=self.rest,
            bg="#FFFFFF", fg="#C62828", activebackground="#FFCDD2", **btn_style
        )
        self.rest_btn.pack(pady=(15, 0))

    def _format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _update_display(self):
        self.time_label.config(text=self._format_time(self.remaining))

    def _set_theme(self, is_work):
        bg = "#EF9A9A" if is_work else "#A5D6A7"
        fg = "#B71C1C" if is_work else "#1B5E20"
        status_fg = "#C62828" if is_work else "#2E7D32"
        self.root.configure(bg=bg)
        for widget in [self.title_label, self.time_label, self.status_label]:
            widget.configure(bg=bg, fg=fg)
        self.status_label.configure(fg=status_fg)
        btn_frame = self.start_btn.master
        btn_frame.configure(bg=bg)
        self.rest_btn.configure(bg=bg)

    def _tick(self):
        if self.state != "running":
            return
        if self.remaining > 0:
            self.remaining -= 1
            self._update_display()
            self.timer_id = self.root.after(1000, self._tick)
        else:
            self._on_finish()

    def _on_finish(self):
        self.state = "idle"
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")

        if self.is_work:
            messagebox.showinfo("番茄钟", "工作时间结束！休息一下吧。")
            self.is_work = False
            self.remaining = BREAK_MINUTES * 60
            self.status_label.config(text="休息中")
        else:
            messagebox.showinfo("番茄钟", "休息结束！开始新的工作吧。")
            self.is_work = True
            self.remaining = WORK_MINUTES * 60
            self.status_label.config(text="准备开始")

        self._set_theme(self.is_work)
        self._update_display()

    def start(self):
        if self.state == "running":
            return
        self.state = "running"
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.status_label.config(text="工作中" if self.is_work else "休息中")
        self._tick()

    def pause(self):
        if self.state != "running":
            return
        self.state = "paused"
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.status_label.config(text="已暂停")

    def rest(self):
        minutes = simpledialog.askinteger(
            "自定义休息时间", "请输入休息时间（分钟）：",
            parent=self.root, minvalue=1, maxvalue=120
        )
        if minutes is None:
            return
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.state = "idle"
        self.is_work = False
        self.remaining = minutes * 60
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.status_label.config(text="休息中")
        self._set_theme(False)
        self._update_display()

    def reset(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.state = "idle"
        self.is_work = True
        self.remaining = WORK_MINUTES * 60
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.status_label.config(text="准备开始")
        self._set_theme(True)
        self._update_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
