import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import sounddevice as sd
import soundfile as sf
import os
from scipy.signal import chirp
import time
import logging
import pydualsense
import pyaudio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ChirpGeneratorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chirp Signal Generator")
        self.root.geometry("400x300")
        
        logging.info("Initializing Chirp Generator UI")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frequency inputs
        freq_frame = ttk.LabelFrame(main_frame, text="Frequency Settings", padding="5")
        freq_frame.pack(fill=tk.X, pady=5)
        
        # Start frequency
        ttk.Label(freq_frame, text="Start Frequency (Hz):").grid(row=0, column=0, padx=5, pady=2)
        self.start_freq = tk.StringVar(value="100")
        ttk.Entry(freq_frame, textvariable=self.start_freq, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        # End frequency
        ttk.Label(freq_frame, text="End Frequency (Hz):").grid(row=1, column=0, padx=5, pady=2)
        self.end_freq = tk.StringVar(value="1000")
        ttk.Entry(freq_frame, textvariable=self.end_freq, width=10).grid(row=1, column=1, padx=5, pady=2)
        
        # Duration input
        ttk.Label(freq_frame, text="Duration (ms):").grid(row=2, column=0, padx=5, pady=2)
        self.duration = tk.StringVar(value="1000")
        ttk.Entry(freq_frame, textvariable=self.duration, width=10).grid(row=2, column=1, padx=5, pady=2)
        
        # Sample rate
        ttk.Label(freq_frame, text="Sample Rate (Hz):").grid(row=3, column=0, padx=5, pady=2)
        self.sample_rate = tk.StringVar(value="48000")
        ttk.Entry(freq_frame, textvariable=self.sample_rate, width=10).grid(row=3, column=1, padx=5, pady=2)
        
        # Control buttons
        button_frame = ttk.LabelFrame(main_frame, text="Controls", padding="5")
        button_frame.pack(fill=tk.X, pady=5)
        
        # Play on default speaker
        ttk.Button(button_frame, text="Play on Default Speaker", 
                  command=self.play_default).pack(fill=tk.X, pady=2)
        
        # Play on DualSense
        ttk.Button(button_frame, text="Play on DualSense", 
                  command=self.play_dualsense).pack(fill=tk.X, pady=2)
        
        # Save to file
        ttk.Button(button_frame, text="Save to File", 
                  command=self.save_to_file).pack(fill=tk.X, pady=2)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", font=("Arial", 10))
        self.status_label.pack(pady=5)
        
        # Initialize audio devices
        self.update_audio_devices()
    
    def update_audio_devices(self):
        """Get list of available audio output devices"""
        try:
            self.devices = sd.query_devices()
            self.dualsense_device = None
            
            logging.info("Available audio devices:")
            for i, device in enumerate(self.devices):
                logging.info(f"[{i}] {device['name']}")
                if 'dualsense' in device['name'].lower():
                    self.dualsense_device = i
                    logging.info(f"Found DualSense device at index {i}")
            
            if self.dualsense_device is None:
                logging.warning("No DualSense device found")
        except Exception as e:
            logging.error(f"Error querying audio devices: {str(e)}")
            messagebox.showerror("Error", f"Failed to get audio devices: {str(e)}")
    
    def generate_chirp(self):
        """Generate chirp signal based on current parameters"""
        try:
            # Get parameters
            f0 = float(self.start_freq.get())
            f1 = float(self.end_freq.get())
            duration_ms = float(self.duration.get())
            fs = float(self.sample_rate.get())
            
            logging.info(f"Generating chirp: f0={f0}Hz, f1={f1}Hz, duration={duration_ms}ms, fs={fs}Hz")
            
            # Convert duration to seconds
            duration = duration_ms / 1000
            
            # Generate time array
            t = np.linspace(0, duration, int(fs * duration))
            
            # Generate chirp signal
            signal = chirp(t, f0=f0, f1=f1, t1=duration, method='linear')
            
            logging.info("Chirp signal generated successfully")
            return signal, fs
            
        except ValueError as e:
            logging.error(f"Invalid input parameters: {str(e)}")
            messagebox.showerror("Error", "Please enter valid numbers for all parameters")
            return None, None
        except Exception as e:
            logging.error(f"Error generating chirp: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate chirp: {str(e)}")
            return None, None
    
    def play_default(self):
        """Play chirp on default output device"""
        signal, fs = self.generate_chirp()
        if signal is not None:
            try:
                logging.info("Playing chirp on default speaker")
                self.status_label.config(text="Playing on default speaker...")
                sd.play(signal, fs)
                sd.wait()
                self.status_label.config(text="Ready")
                logging.info("Finished playing on default speaker")
            except Exception as e:
                logging.error(f"Error playing on default speaker: {str(e)}")
                messagebox.showerror("Error", f"Failed to play audio: {str(e)}")
    
    def play_dualsense(self):
        """Play chirp on DualSense controller"""
        if self.dualsense_device is None:
            logging.error("DualSense controller not found")
            messagebox.showerror("Error", "DualSense controller not found")
            return
            
        signal, fs = self.generate_chirp()
        if signal is not None:
            try:
                logging.info(f"Playing chirp on DualSense (device {self.dualsense_device})")
                self.status_label.config(text="Playing on DualSense...")
                
                # Fixed to 2 channels for DualSense
                channels = 2
                logging.info(f"Using {channels} channels for DualSense")
                
                # Ensure signal is not empty before creating multi-channel version
                if len(signal) == 0:
                    raise ValueError("Generated signal is empty")
                
                # Create stereo signal (2 channels)
                multi_channel_signal = np.column_stack((signal, signal))
                
                # Convert numpy array to bytes for PyAudio
                samples = (multi_channel_signal * 32767).astype(np.int16)
                audio_data = samples.tobytes()
                
                # Initialize PyAudio
                p = pyaudio.PyAudio()
                
                # Open stream
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=int(fs),
                    output=True,
                    output_device_index=self.dualsense_device,
                    frames_per_buffer=2048
                )
                
                # Play audio
                stream.write(audio_data)
                
                # Close stream and PyAudio
                stream.stop_stream()
                stream.close()
                p.terminate()
                
                self.status_label.config(text="Ready")
                logging.info("Finished playing on DualSense")
            except Exception as e:
                logging.error(f"Error playing on DualSense: {str(e)}")
                messagebox.showerror("Error", f"Failed to play on DualSense: {str(e)}")
    
    def save_to_file(self):
        """Save chirp signal to WAV file"""
        signal, fs = self.generate_chirp()
        if signal is not None:
            try:
                # Create filename with timestamp
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"chirp_{timestamp}.wav"
                
                logging.info(f"Saving chirp to file: {filename}")
                # Save to file
                sf.write(filename, signal, fs)
                self.status_label.config(text=f"Saved to {filename}")
                logging.info("File saved successfully")
            except Exception as e:
                logging.error(f"Error saving file: {str(e)}")
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

if __name__ == "__main__":
    logging.info("Starting Chirp Generator Application")
    root = tk.Tk()
    app = ChirpGeneratorUI(root)
    root.mainloop()
    logging.info("Application closed")
