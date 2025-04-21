import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import soundfile as sf
from scipy import signal
import os
from tkinterdnd2 import DND_FILES, TkinterDnD
import librosa

class SpecApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Spectrogram Viewer")
        self.root.geometry("1000x800")
        
        # Audio data
        self.audio_data = None
        self.sample_rate = None
        self.filename = None
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(expand=True, fill="both")
        
        # Create drop zone
        self.create_drop_zone()
        
        # Create plot area
        self.create_plot_area()
    
    def create_drop_zone(self):
        # Drop zone frame
        drop_frame = ttk.LabelFrame(self.main_frame, text="Drop Audio File Here", padding=10)
        drop_frame.pack(fill="x", pady=5)
        
        # Drop zone label
        self.drop_label = tk.Label(drop_frame, text="Drag and drop an audio file here\nor click to browse",
                                 font=("Arial", 12))
        self.drop_label.pack(expand=True, fill="both", pady=20)
        
        # Setup drag and drop
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)
        
        # Bind click event to open file dialog
        self.drop_label.bind("<Button-1>", self.browse_file)
    
    def create_plot_area(self):
        # Plot frame
        plot_frame = ttk.LabelFrame(self.main_frame, text="Audio Analysis", padding=10)
        plot_frame.pack(expand=True, fill="both", pady=5)
        
        # Create matplotlib figure with three subplots
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(10, 12))
        self.fig.subplots_adjust(hspace=0.5)
        
        # Create canvas for the figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")
        
        # Initialize empty plots
        self.ax1.set_title("Waveform")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Amplitude")
        
        self.ax2.set_title("Spectrogram")
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Frequency (Hz)")
        
        self.ax3.set_title("MFCC")
        self.ax3.set_xlabel("Time (s)")
        self.ax3.set_ylabel("MFCC Coefficients")
        
        self.canvas.draw()
    
    def handle_drop(self, event):
        # Get the dropped file path
        file_path = event.data
        
        # Check if it's an audio file
        if not self.is_audio_file(file_path):
            messagebox.showerror("Error", "Please drop an audio file (WAV, MP3, etc.)")
            return
        
        # Load and process the audio file
        self.load_audio_file(file_path)
    
    def browse_file(self, event=None):
        # Open file dialog
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.ogg *.flac"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self.load_audio_file(file_path)
    
    def is_audio_file(self, file_path):
        # Check if file has an audio extension
        audio_extensions = {'.wav', '.mp3', '.ogg', '.flac'}
        return os.path.splitext(file_path)[1].lower() in audio_extensions
    
    def load_audio_file(self, file_path):
        try:
            # Load audio file
            self.audio_data, self.sample_rate = sf.read(file_path)
            self.filename = os.path.basename(file_path)
            
            # Update drop zone label
            self.drop_label.config(text=f"Loaded: {self.filename}")
            
            # Update plots
            self.update_plots()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audio file: {str(e)}")
    
    def update_plots(self):
        if self.audio_data is None:
            return
        
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        
        # Convert stereo to mono if needed
        if len(self.audio_data.shape) > 1:
            audio_data = np.mean(self.audio_data, axis=1)
        else:
            audio_data = self.audio_data
        
        # Create time array
        time = np.arange(len(audio_data)) / self.sample_rate
        
        # Plot waveform
        self.ax1.plot(time, audio_data)
        self.ax1.set_title(f"Waveform - {self.filename}")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Amplitude")
        self.ax1.grid(True)
        
        # Plot spectrogram
        f, t, Sxx = signal.spectrogram(audio_data, self.sample_rate)
        self.ax2.pcolormesh(t, f, 10 * np.log10(Sxx), shading='auto')
        self.ax2.set_title(f"Spectrogram - {self.filename}")
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Frequency (Hz)")
        self.ax2.grid(True)
        
        # Plot MFCC
        mfccs = librosa.feature.mfcc(y=audio_data, sr=self.sample_rate)
        self.ax3.imshow(mfccs, aspect='auto', origin='lower')
        self.ax3.set_title(f"MFCC - {self.filename}")
        self.ax3.set_xlabel("Time (s)")
        self.ax3.set_ylabel("MFCC Coefficients")
        
        # Adjust layout and redraw
        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    root = TkinterDnD.Tk()  # Use TkinterDnD's Tk instead of tkinter's
    app = SpecApp(root)
    root.mainloop()
