# this is the app for the haptic enhancement data collection

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import numpy as np
import sounddevice as sd
from scipy.signal import chirp
import pyaudio
from pydualsense import pydualsense
from DualSenseHapticDataCollector import DualSenseHapticDataCollector
import logging

class HapticEnhanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Haptic Enhancement Data Collection")
        self.root.geometry("600x600")  # Increased height from 400 to 600 while keeping width at 600
        
        # Controller status
        self.controller_connected = False
        self.collector = None
        self.haptic_mode = tk.StringVar(value="non-haptic")  # Default mode
        
        # Chirp sound parameters
        self.chirp_f0 = 50  # Start frequency (Hz)
        self.chirp_f1 = 1000  # End frequency (Hz)
        self.chirp_duration = 0.15  # Duration in seconds (150ms)
        self.chirp_fs = 48000  # Sample rate (Hz)
        
        # Add working device storage
        self.working_dualsense_device = None
        self.dualsense_devices = []  # Initialize empty list for DualSense devices
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)  # Reduced padding from 20
        
        # Status section
        self.create_status_section()
        
        # Button press display section
        self.create_button_display_section()
        
        # Control section
        self.create_control_section()
        
        # Initialize audio devices
        self.update_audio_devices()
        
        # Initialize controller
        self.initialize_controller()
    
    def create_status_section(self):
        # Status frame
        status_frame = ttk.LabelFrame(self.main_frame, text="Controller Status", padding=5)  # Reduced from 10
        status_frame.pack(fill="x", pady=5)  # Reduced from 10
        
        # Controller connection status with smaller font
        self.status_label = ttk.Label(status_frame, text="Controller: Disconnected", 
                                    foreground="red", font=("Arial", 10))  # Reduced from 12
        self.status_label.pack(pady=2)  # Reduced from 10
        
        # Last update time with smaller font
        self.update_time_label = ttk.Label(status_frame, text="Last Update: Never",
                                         font=("Arial", 10))  # Reduced from 12
        self.update_time_label.pack(pady=2)  # Reduced from 10
    
    def create_button_display_section(self):
        # Button display frame
        button_frame = ttk.LabelFrame(self.main_frame, text="Button Press Display", padding=5)  # Reduced from 10
        button_frame.pack(fill="x", pady=5)  # Reduced from 10
        
        # Create a grid of labels for different buttons with smaller size
        self.button_labels = {}
        buttons = [
            ('cross', '✕'), ('circle', '○'), ('triangle', '△'), ('square', '□'),
            ('dpad_up', '↑'), ('dpad_down', '↓'), ('dpad_left', '←'), ('dpad_right', '→')
        ]
        
        for i, (button, symbol) in enumerate(buttons):
            row = i // 4
            col = i % 4
            label = ttk.Label(button_frame, text=f"{symbol}: Not Pressed", 
                            width=15, padding=2, font=("Arial", 9))  # Reduced width, padding and font
            label.grid(row=row, column=col, padx=5, pady=2)  # Reduced spacing
            self.button_labels[button] = label
    
    def create_control_section(self):
        # Control frame
        control_frame = ttk.LabelFrame(self.main_frame, text="Data Collection Control", padding=5)  # Reduced from 10
        control_frame.pack(fill="x", pady=5)  # Reduced from 10
        
        # User Name Input
        name_frame = ttk.Frame(control_frame)
        name_frame.pack(fill="x", pady=2)
        
        ttk.Label(name_frame, text="User Name:", 
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        self.user_name = tk.StringVar(value="user1")  # Default user name
        self.name_entry = ttk.Entry(name_frame, textvariable=self.user_name, width=20)
        self.name_entry.pack(side=tk.LEFT, padx=2)
        
        # Haptic Mode Selection
        mode_frame = ttk.Frame(control_frame)
        mode_frame.pack(fill="x", pady=2)
        
        ttk.Label(mode_frame, text="Haptic Mode:", 
                 font=("Arial", 9)).pack(pady=2)
        
        modes = [("Non-Haptic", "non-haptic"),
                ("Fixed-Haptic", "fixed-haptic"),
                ("Flexible-Haptic", "flexible-haptic")]
        
        for text, mode in modes:
            ttk.Radiobutton(mode_frame, text=text,
                          variable=self.haptic_mode,
                          value=mode,
                          command=self.on_haptic_mode_change).pack(pady=1)
        
        # Collection status with smaller font
        self.collection_status = ttk.Label(control_frame, text="Collection Status: Stopped", 
                                         foreground="red", font=("Arial", 10))  # Reduced from 12
        self.collection_status.pack(pady=2)  # Reduced from 10
        
        # Start/Stop button with smaller size
        self.toggle_button = ttk.Button(control_frame, text="Start Collection", 
                                      command=self.toggle_collection, width=15)  # Reduced from 20
        self.toggle_button.pack(pady=2)  # Reduced from 10
        
        # Instructions with smaller font
        instructions = (
            "Instructions:\n"
            "1. Connect DualSense controller\n"
            "2. Select haptic mode\n"
            "3. Press Start Collection to begin\n"
            "4. Use controller buttons\n"
            "5. Press Stop Collection when done"
        )
        ttk.Label(control_frame, text=instructions, justify=tk.LEFT, 
                 font=("Arial", 9)).pack(pady=2)  # Reduced from 11 and 10
    
    def initialize_controller(self):
        try:
            self.dualsense = pydualsense()
            self.dualsense.init()
            self.controller_connected = True
            self.status_label.config(text="Controller: Connected", foreground="green")
            
            # Start controller input thread
            self.controller_running = True
            self.controller_thread = threading.Thread(target=self.controller_loop)
            self.controller_thread.daemon = True
            self.controller_thread.start()
            
        except Exception as e:
            print(f"Error initializing DualSense controller: {e}")
            self.status_label.config(text="Controller: Error", foreground="red")
            messagebox.showwarning("Controller Warning", 
                                "DualSense controller not detected.")
    
    def controller_loop(self):
        # Track button states to detect press events (not holds)
        button_states = {
            'cross': False, 'circle': False, 'triangle': False, 'square': False,
            'dpad_up': False, 'dpad_down': False, 'dpad_left': False, 'dpad_right': False
        }
        
        # Mapping from our button names to actual attribute names in DSState
        button_attr_map = {
            'cross': 'cross',
            'circle': 'circle',
            'triangle': 'triangle',
            'square': 'square',
            'dpad_up': 'DpadUp',
            'dpad_down': 'DpadDown',
            'dpad_left': 'DpadLeft',
            'dpad_right': 'DpadRight'
        }
        
        while self.controller_running:
            try:
                # Update timestamp
                self.root.after(0, self.update_timestamp)
                
                # Check each button
                for button, attr_name in button_attr_map.items():
                    is_pressed = getattr(self.dualsense.state, attr_name)
                    if is_pressed and not button_states[button]:
                        # Button just pressed
                        button_states[button] = True
                        self.root.after(0, self.update_button_display, button, True)
                    elif not is_pressed and button_states[button]:
                        # Button just released
                        button_states[button] = False
                        self.root.after(0, self.update_button_display, button, False)
                
                time.sleep(0.05)  # Prevent high CPU usage
                
            except Exception as e:
                print(f"Error reading controller input: {e}")
                time.sleep(1)
    
    def update_timestamp(self):
        current_time = time.strftime("%H:%M:%S")
        self.update_time_label.config(text=f"Last Update: {current_time}")
    
    def update_button_display(self, button, is_pressed):
        if button in self.button_labels:
            symbol = {
                'cross': '✕', 'circle': '○', 'triangle': '△', 'square': '□',
                'dpad_up': '↑', 'dpad_down': '↓', 'dpad_left': '←', 'dpad_right': '→'
            }.get(button, button)
            
            color = "green" if is_pressed else "black"
            self.button_labels[button].config(
                text=f"{symbol}: {'Pressed' if is_pressed else 'Not Pressed'}",
                foreground=color
            )
            
            # Handle haptic feedback based on mode
            if hasattr(self, 'dualsense') and self.controller_connected:
                mode = self.haptic_mode.get()
                if mode == "fixed-haptic" and is_pressed:
                    # Start vibration in a separate thread
                    def vibrate_thread():
                        # Set both motors to lowest intensity (1)
                        self.dualsense.setLeftMotor(1)
                        self.dualsense.setRightMotor(1)
                        # Wait for 150ms
                        time.sleep(0.15)
                        # Stop vibration
                        self.dualsense.setLeftMotor(0)
                        self.dualsense.setRightMotor(0)
                    
                    # Start vibration thread
                    vibration_thread = threading.Thread(target=vibrate_thread)
                    vibration_thread.daemon = True
                    vibration_thread.start()
                elif mode == "flexible-haptic" and is_pressed:
                    # Play chirp sound only when button is pressed (not held)
                    self.play_chirp()
    
    def on_haptic_mode_change(self):
        """Handle haptic mode changes"""
        mode = self.haptic_mode.get()
        print(f"Haptic mode changed to: {mode}")
        
        # If collection is running, stop it when mode changes
        if self.collector is not None:
            try:
                self.collector.stop_collection()
                self.collector = None
                self.collection_status.config(text="Collection Status: Stopped", 
                                           foreground="red")
                self.toggle_button.config(text="Start Collection")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop collection: {e}")
    
    def toggle_collection(self):
        if not self.controller_connected:
            messagebox.showwarning("Warning", "Controller not connected!")
            return
        
        if self.collector is None:
            # Start collection
            try:
                mode = self.haptic_mode.get()
                user_name = self.user_name.get().strip()
                if not user_name:
                    messagebox.showwarning("Warning", "Please enter a user name!")
                    return
                    
                self.collector = DualSenseHapticDataCollector(
                    controller=self.dualsense, 
                    user_id=f"{user_name}_{mode}",  # Include user name and mode in user_id
                    output_dir=f"data/haptic_data/{mode}"  # Separate directory for each mode
                )
                self.collector.start_collection()
                self.collection_status.config(
                    text=f"Collection Status: Recording ({mode})", 
                    foreground="green"
                )
                self.toggle_button.config(text="Stop Collection")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start collection: {e}")
                if self.collector:
                    try:
                        self.collector.stop_collection()
                    except:
                        pass
                    self.collector = None
                self.collection_status.config(text="Collection Status: Error", 
                                           foreground="red")
                self.toggle_button.config(text="Start Collection")
        else:
            # Stop collection
            try:
                self.collector.stop_collection()
                self.collector = None
                self.collection_status.config(text="Collection Status: Stopped", 
                                           foreground="red")
                self.toggle_button.config(text="Start Collection")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop collection: {e}")
    
    def on_closing(self):
        # Cleanup
        self.controller_running = False
        if self.collector:
            try:
                self.collector.stop_collection()
            except:
                pass
        if hasattr(self, 'dualsense'):
            try:
                self.dualsense.close()
            except:
                pass
        self.root.destroy()

    def update_audio_devices(self):
        """Get list of available audio output devices"""
        try:
            self.devices = sd.query_devices()
            self.dualsense_devices = []
            
            logging.info("Available audio devices:")
            for i, device in enumerate(self.devices):
                logging.info(f"[{i}] {device['name']}")
                if 'dualsense' in device['name'].lower():
                    self.dualsense_devices.append(i)
                    logging.info(f"Found DualSense device at index {i}")
            
            if not self.dualsense_devices:
                logging.warning("No DualSense devices found")
        except Exception as e:
            logging.error(f"Error querying audio devices: {str(e)}")
            messagebox.showerror("Error", f"Failed to get audio devices: {str(e)}")

    def generate_chirp(self):
        """Generate chirp signal with predefined parameters"""
        try:
            # Generate time array
            t = np.linspace(0, self.chirp_duration, int(self.chirp_fs * self.chirp_duration))
            
            # Generate chirp signal
            signal = chirp(t, f0=self.chirp_f0, f1=self.chirp_f1, t1=self.chirp_duration, method='linear')
            
            # Create stereo signal (2 channels)
            multi_channel_signal = np.column_stack((signal, signal))
            
            # Convert to 16-bit PCM
            samples = (multi_channel_signal * 32767).astype(np.int16)
            return samples.tobytes()
            
        except Exception as e:
            logging.error(f"Error generating chirp: {e}")
            return None

    def play_chirp(self):
        """Play the chirp sound on the default audio device in a separate thread"""
        # Start audio playback in a separate thread
        audio_thread = threading.Thread(target=self._play_chirp_thread)
        audio_thread.daemon = True  # Thread will exit when main program exits
        audio_thread.start()

    def _play_chirp_thread(self):
        """Thread function to handle the actual audio playback"""
        try:
            logging.info("Generating chirp signal...")
            audio_data = self.generate_chirp()
            if audio_data is not None:
                logging.info(f"Audio data generated successfully. Size: {len(audio_data)} bytes")
                
                try:
                    # Initialize PyAudio
                    p = pyaudio.PyAudio()
                    
                    # Get default output device info
                    default_device_index = p.get_default_output_device_info()["index"]
                    default_device_name = p.get_device_info_by_index(default_device_index)["name"]
                    logging.info(f"Using default audio output device: {default_device_name}")
                    
                    # Open stream
                    stream = p.open(
                        format=pyaudio.paInt16,
                        channels=2,
                        rate=self.chirp_fs,
                        output=True,
                        output_device_index=default_device_index,
                        frames_per_buffer=2048
                    )
                    
                    # Play audio
                    stream.write(audio_data)
                    
                    # Close stream and PyAudio
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    
                    logging.info("Successfully played chirp on default device")
                    
                except Exception as e:
                    logging.error(f"Error playing on default device: {str(e)}")
                
        except Exception as e:
            logging.error(f"Error playing chirp: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HapticEnhanceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()