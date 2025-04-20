import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import datetime
from pydualsense import pydualsense
from DualSenseHapticDataCollector import DualSenseHapticDataCollector

class LongApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DualSense Button Sequence Recorder")
        self.root.geometry("600x500")
        
        # Controller status
        self.controller_connected = False
        self.dualsense = None
        self.collector = None
        
        # Recording state
        self.recording = False
        self.waiting_for_next = False
        self.current_button_index = 0
        self.button_sequence = ['cross', 'circle', 'triangle', 'square']
        self.button_symbols = {
            'cross': '✕',
            'circle': '○',
            'triangle': '△',
            'square': '□'
        }
        
        # Button states
        self.button_colors = {
            'normal': 'black',
            'target': 'red',
            'pressed': 'green'
        }
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(expand=True, fill="both")
        
        # Create UI sections
        self.create_status_section()
        self.create_button_display_section()
        self.create_control_section()
        
        # Initialize controller
        self.initialize_controller()
    
    def create_status_section(self):
        # Status frame
        status_frame = ttk.LabelFrame(self.main_frame, text="Controller Status", padding=5)
        status_frame.pack(fill="x", pady=5)
        
        # Controller connection status
        self.status_label = ttk.Label(status_frame, text="Controller: Disconnected", 
                                    foreground="red", font=("Arial", 10))
        self.status_label.pack(pady=2)
        
        # Last update time
        self.update_time_label = ttk.Label(status_frame, text="Last Update: Never",
                                         font=("Arial", 10))
        self.update_time_label.pack(pady=2)
    
    def create_button_display_section(self):
        # Button display frame
        button_frame = ttk.LabelFrame(self.main_frame, text="Button Press Display", padding=5)
        button_frame.pack(fill="x", pady=5)
        
        # Create a grid of labels for different buttons in controller layout
        self.button_labels = {}
        
        # Define button positions in a 3x3 grid (controller layout)
        button_positions = {
            'triangle': (0, 1),  # Top
            'square': (1, 0),    # Left middle
            'circle': (1, 2),    # Right middle
            'cross': (2, 1)      # Bottom
        }
        
        # Create buttons in controller layout
        for button, (row, col) in button_positions.items():
            symbol = self.button_symbols[button]
            label = ttk.Label(button_frame, text=f"{symbol}: Not Pressed", 
                            width=15, padding=2, font=("Arial", 12))
            label.grid(row=row, column=col, padx=5, pady=2)
            self.button_labels[button] = label
        
        # Add some spacing to make it look more like a controller
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        # Prompt label
        self.prompt_label = ttk.Label(button_frame, text="", font=("Arial", 12))
        self.prompt_label.grid(row=3, column=0, columnspan=3, pady=10)
    
    def create_control_section(self):
        # Control frame
        control_frame = ttk.LabelFrame(self.main_frame, text="Data Collection Control", padding=5)
        control_frame.pack(fill="x", pady=5)
        
        # User Name Input
        name_frame = ttk.Frame(control_frame)
        name_frame.pack(fill="x", pady=2)
        
        ttk.Label(name_frame, text="User Name:", 
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=2)
        
        self.user_name = tk.StringVar(value="user1")
        self.name_entry = ttk.Entry(name_frame, textvariable=self.user_name, width=20)
        self.name_entry.pack(side=tk.LEFT, padx=2)
        
        # Output Directory Input
        dir_frame = ttk.Frame(control_frame)
        dir_frame.pack(fill="x", pady=2)
        
        ttk.Label(dir_frame, text="Output Directory:", 
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=2)
        
        self.output_dir = tk.StringVar(value="data/button_sequence")
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir, width=30)
        self.dir_entry.pack(side=tk.LEFT, padx=2)
        
        # Start/Stop button
        self.toggle_button = ttk.Button(control_frame, text="Start Recording", 
                                      command=self.toggle_recording, width=15)
        self.toggle_button.pack(pady=5)
        
        # Status message
        self.status_message = ttk.Label(control_frame, text="", font=("Arial", 10))
        self.status_message.pack(pady=2)
    
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
        # Track button states to detect press events
        button_states = {
            'cross': False, 'circle': False, 'triangle': False, 'square': False
        }
        
        while self.controller_running:
            try:
                # Update timestamp
                self.root.after(0, self.update_timestamp)
                
                # Check each button
                for button in button_states.keys():
                    is_pressed = getattr(self.dualsense.state, button)
                    if is_pressed and not button_states[button]:
                        # Button just pressed
                        button_states[button] = True
                        self.root.after(0, self.update_button_display, button, True)
                        if self.recording and button == self.button_sequence[self.current_button_index]:
                            self.handle_button_press(button)
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
            symbol = self.button_symbols[button]
            
            # Determine the color based on button state
            if is_pressed:
                color = self.button_colors['pressed']
            elif self.recording and button == self.button_sequence[self.current_button_index]:
                color = self.button_colors['target']
            else:
                color = self.button_colors['normal']
            
            self.button_labels[button].config(
                text=f"{symbol}: {'Pressed' if is_pressed else 'Not Pressed'}",
                foreground=color
            )
    
    def handle_button_press(self, button):
        if button == self.button_sequence[self.current_button_index]:
            self.current_button_index += 1
            if self.current_button_index < len(self.button_sequence):
                self.root.after(400, self.prompt_next_button)  # 0.4 second delay
            else:
                self.stop_recording()
    
    def prompt_next_button(self):
        if self.current_button_index < len(self.button_sequence):
            next_button = self.button_sequence[self.current_button_index]
            symbol = self.button_symbols[next_button]
            self.prompt_label.config(text=f"Please press {symbol} button")
            
            # Update all button colors
            for button in self.button_labels:
                self.update_button_display(button, False)
    
    def start_recording(self):
        if not self.controller_connected:
            messagebox.showwarning("Warning", "Controller not connected!")
            return
        
        user_name = self.user_name.get().strip()
        if not user_name:
            messagebox.showwarning("Warning", "Please enter a user name!")
            return
        
        output_dir = self.output_dir.get().strip()
        if not output_dir:
            messagebox.showwarning("Warning", "Please enter an output directory!")
            return
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Initialize collector
            self.collector = DualSenseHapticDataCollector(
                controller=self.dualsense,
                output_dir=output_dir,
                user_id=user_name
            )
            
            # Start countdown
            self.prompt_label.config(text="Starting in 2...")
            self.root.after(1000, lambda: self.prompt_label.config(text="Starting in 1..."))
            self.root.after(2000, self.begin_recording)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recording: {e}")
    
    def begin_recording(self):
        try:
            self.collector.start_collection()
            self.recording = True
            self.current_button_index = 0
            self.toggle_button.config(text="Stop Recording")
            self.status_message.config(text="Recording in progress...")
            self.prompt_next_button()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start collection: {e}")
            self.recording = False
            self.toggle_button.config(text="Start Recording")
    
    def stop_recording(self):
        if self.collector:
            try:
                self.collector.stop_collection()
                self.recording = False
                self.toggle_button.config(text="Start Recording")
                self.prompt_label.config(text="")
                self.status_message.config(text="Recording completed and files saved!")
                
                # Reset button displays
                for button in self.button_labels:
                    self.update_button_display(button, False)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop recording: {e}")
    
    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def on_closing(self):
        # Cleanup
        self.controller_running = False
        if self.collector:
            try:
                self.collector.stop_collection()
            except:
                pass
        if self.dualsense:
            try:
                self.dualsense.close()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LongApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
