import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime, timedelta
import os
import sys
import winreg as reg

# --- ШАГ 1: ОПРЕДЕЛЕНИЕ ПУТИ ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.realpath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))

os.chdir(BASE_DIR)

class StealthTimer:
    def __init__(self, root):
        self.root = root
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.8)
        self.root.overrideredirect(True)
        self.root.geometry("220x125+100+100")
        
        self.color_normal = '#2c3e50'
        self.color_warning = '#d35400'
        self.color_danger = '#c0392b'
        self.root.configure(bg=self.color_normal)

        self.task_name = ""
        self.ask_new_task()
        self.is_paused = False
        self.elapsed_time = timedelta(0)
        self.daily_total = timedelta(0)
        self.last_start_time = datetime.now()

        self.task_label = tk.Label(root, text=self.task_name, font=("Segoe UI", 9), 
                                   fg="#bdc3c7", bg=self.color_normal, wraplength=200)
        self.task_label.pack(pady=(5, 0))

        self.label = tk.Label(root, text="00:00:00", font=("Consolas", 20, "bold"), 
                              fg="#ecf0f1", bg=self.color_normal)
        self.label.pack()

        self.btn_frame = tk.Frame(root, bg=self.color_normal)
        self.btn_frame.pack(pady=2)

        self.btn_pause = tk.Button(self.btn_frame, text="⏸ Пауза", command=self.toggle_pause,
                                   font=("Segoe UI", 8), bg="#34495e", fg="white", 
                                   relief="flat", bd=0, width=8)
        self.btn_pause.pack(side=tk.LEFT, padx=2)

        self.btn_switch = tk.Button(self.btn_frame, text="🔄 Сменить", command=self.switch_task,
                                    font=("Segoe UI", 8), bg="#34495e", fg="white", 
                                    relief="flat", bd=0, width=8)
        self.btn_switch.pack(side=tk.LEFT, padx=2)

        self.btn_startup = tk.Button(root, text="Автозагрузка", command=self.toggle_startup,
                                     font=("Segoe UI", 7), relief="flat", bd=0)
        self.btn_startup.pack(pady=5)
        self.refresh_startup_button()

        for widget in [self.label, self.task_label, self.root, self.btn_frame]:
            widget.bind("<ButtonPress-1>", self.start_move)
            widget.bind("<B1-Motion>", self.do_move)
            widget.bind("<Button-3>", self.stop_and_save)

        self.update_clock()

    def ask_new_task(self):
        new_name = simpledialog.askstring("Задача", "Над чем работаем?", parent=self.root)
        self.task_name = new_name if new_name else "Без названия"

    def toggle_pause(self):
        if not self.is_paused:
            self.elapsed_time += datetime.now() - self.last_start_time
            self.is_paused = True
            self.btn_pause.config(text="▶ Старт", bg="#27ae60")
        else:
            self.last_start_time = datetime.now()
            self.is_paused = False
            self.btn_pause.config(text="⏸ Пауза", bg="#34495e")

    def switch_task(self):
        session_duration = self.save_to_file()
        self.daily_total += session_duration
        self.ask_new_task()
        self.task_label.config(text=self.task_name)
        self.elapsed_time = timedelta(0)
        self.last_start_time = datetime.now()
        self.change_theme(self.color_normal)
        if self.is_paused: self.toggle_pause()

    def update_clock(self):
        if not self.is_paused:
            total_now = self.elapsed_time + (datetime.now() - self.last_start_time)
            str_time = str(total_now).split('.')[0]
            if len(str_time) == 7: str_time = "0" + str_time
            self.label.config(text=str_time)
            minutes = total_now.total_seconds() / 60
            if minutes >= 60: self.change_theme(self.color_danger)
            elif minutes >= 30: self.change_theme(self.color_warning)
            else: self.change_theme(self.color_normal)
        self.root.after(1000, self.update_clock)

    def change_theme(self, color):
        if self.root["bg"] != color:
            self.root.configure(bg=color)
            self.label.configure(bg=color)
            self.task_label.configure(bg=color)
            self.btn_frame.configure(bg=color)

    def save_to_file(self):
        if not self.is_paused:
            duration = self.elapsed_time + (datetime.now() - self.last_start_time)
        else:
            duration = self.elapsed_time
        duration_str = str(duration).split('.')[0]
        
        log_path = os.path.join(BASE_DIR, "work_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%d.%m.%Y %H:%M')} | {self.task_name} | {duration_str}\n")
        return duration

    def stop_and_save(self, event):
        last_duration = self.save_to_file()
        self.daily_total += last_duration
        total_str = str(self.daily_total).split('.')[0]
        messagebox.showinfo("Итог дня", f"Сегодня вы проработали: {total_str}")
        self.root.destroy()

    def toggle_startup(self):
        if getattr(sys, 'frozen', False):
            pth = sys.executable
            key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
            try:
                if self.is_in_startup():
                    reg.DeleteValue(key, "StealthTimerApp")
                else:
                    reg.SetValueEx(key, "StealthTimerApp", 0, reg.REG_SZ, pth)
            finally:
                reg.CloseKey(key)
            self.refresh_startup_button()
        else:
            messagebox.showwarning("Внимание", "Работает только в EXE")

    def is_in_startup(self):
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, reg.KEY_READ)
            reg.QueryValueEx(key, "StealthTimerApp")
            reg.CloseKey(key)
            return True
        except:
            return False

    def refresh_startup_button(self):
        if self.is_in_startup():
            self.btn_startup.config(text="Автозагрузка: ВКЛ", bg="#27ae60", fg="white")
        else:
            self.btn_startup.config(text="Автозагрузка: ВЫКЛ", bg="#95a5a6", fg="white")

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = StealthTimer(root)
    root.deiconify()
    root.mainloop()