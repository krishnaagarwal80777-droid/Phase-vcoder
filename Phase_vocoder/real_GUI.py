import tkinter as tk
from tkinter import filedialog, messagebox
import threading

from phaseshift import pitchshift          # offline
from realtime import realtimePitchshift, stop  # realtime


class PhaseVocoderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Phase Vocoder")

        self.wavfile = None

        # ===== MODE =====
        self.proc_type = tk.StringVar(value="offline")
        tk.Radiobutton(root, text="Offline (WAV)",
                       variable=self.proc_type, value="offline").grid(row=0, column=0)
        tk.Radiobutton(root, text="Realtime (Mic)",
                       variable=self.proc_type, value="realtime").grid(row=0, column=1)

        # ===== FILE =====
        tk.Button(root, text="Select WAV",
                  command=self.select_file).grid(row=1, column=0)
        self.file_label = tk.Label(root, text="No file selected")
        self.file_label.grid(row=1, column=1)

        # ===== OPERATION =====
        self.mode = tk.StringVar(value="tune")
        tk.Radiobutton(root, text="Pitch Shift",
                       variable=self.mode, value="tune").grid(row=2, column=0)
        tk.Radiobutton(root, text="Time Stretch",
                       variable=self.mode, value="stretch").grid(row=2, column=1)

        # ===== RATIO =====
        tk.Label(root, text="Pitch / Stretch Ratio").grid(row=3, column=0)
        self.factor = tk.Entry(root)
        self.factor.insert(0, "1.0")
        self.factor.grid(row=3, column=1)

        # ===== BUTTONS =====
        tk.Button(root, text="Start",
                  command=self.start).grid(row=4, column=0)
        tk.Button(root, text="Stop Realtime",
                  command=self.stop_realtime).grid(row=4, column=1)

        self.status = tk.Label(root, text="")
        self.status.grid(row=5, column=0, columnspan=2)

    # ---------------------------------
    def select_file(self):
        self.wavfile = filedialog.askopenfilename(
            filetypes=[("WAV files", "*.wav")]
        )
        if self.wavfile:
            self.file_label.config(text=self.wavfile.split("/")[-1])

    # ---------------------------------
    def start(self):
        try:
            ratio = float(self.factor.get())
            if ratio <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ratio must be > 0")
            return

        if self.proc_type.get() == "offline":
            if not self.wavfile:
                messagebox.showerror("Error", "Select WAV file")
                return
            self.status.config(text="Processing offline...")
            self.root.update()
            pitchshift(self.wavfile, ratio, self.mode.get())
            self.status.config(text="Done")

        else:
            self.status.config(text="Realtime running...")
            t = threading.Thread(
                target=realtimePitchshift,
                args=(ratio,),
                daemon=True
            )
            t.start()

    # ---------------------------------
    def stop_realtime(self):
        stop()
        self.status.config(text="Realtime stopped")


# ===== RUN =====
if __name__ == "__main__":
    root = tk.Tk()
    app = PhaseVocoderGUI(root)
    root.mainloop()