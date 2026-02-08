import tkinter as tk
from tkinter import filedialog, messagebox

from phaseshift import pitchshift   # your DSP function


class PhaseVocoderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Phase Vocoder")

        self.wavfile = None

        # ===== FILE SELECTION =====
        tk.Button(root, text="Select WAV File",
                  command=self.select_file)\
            .grid(row=0, column=0, padx=10, pady=10)

        self.file_label = tk.Label(root, text="No file selected")
        self.file_label.grid(row=0, column=1, padx=10)

        # ===== MODE SELECTION =====
        self.mode = tk.StringVar(value="tune")

        tk.Radiobutton(root, text="Pitch Shift (Tune)",
                       variable=self.mode, value="tune")\
            .grid(row=1, column=0, sticky="w", padx=10)

        tk.Radiobutton(root, text="Time Stretch",
                       variable=self.mode, value="stretch")\
            .grid(row=1, column=1, sticky="w", padx=10)

        # ===== PITCH / STRETCH FACTOR =====
        tk.Label(root, text="Pitch / Stretch Ratio:")\
            .grid(row=2, column=0, padx=10, pady=10)

        self.factor_entry = tk.Entry(root)
        self.factor_entry.insert(0, "1.0")
        self.factor_entry.grid(row=2, column=1)

        # ===== PROCESS BUTTON =====
        tk.Button(root, text="Process & Play",
                  command=self.start_processing)\
            .grid(row=3, column=0, columnspan=2, pady=20)

        self.status = tk.Label(root, text="")
        self.status.grid(row=4, column=0, columnspan=2)

    # --------------------------------------------------
    def select_file(self):
        self.wavfile = filedialog.askopenfilename(
            filetypes=[("WAV files", "*.wav")]
        )
        if self.wavfile:
            self.file_label.config(text=self.wavfile.split("/")[-1])

    # --------------------------------------------------
    def start_processing(self):
        if not self.wavfile:
            messagebox.showerror("Error", "Please select a WAV file")
            return

        # ---- SAFE parsing of pitch_ratio ----
        try:
            pitch_ratio = float(self.factor_entry.get())
            if pitch_ratio <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error", "Pitch / Stretch ratio must be a number > 0"
            )
            return

        self.status.config(text="Processing... Please wait")
        self.root.update_idletasks()

        # ---- IMPORTANT: run DSP + PyAudio in MAIN THREAD ----
        try:
            pitchshift(
                wavfile=self.wavfile,
                pitch_ratio=pitch_ratio,
                mode=self.mode.get()
            )
            self.status.config(text="Done!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status.config(text="")


# ===== RUN GUI =====
if __name__ == "__main__":
    root = tk.Tk()
    app = PhaseVocoderGUI(root)
    root.mainloop()
