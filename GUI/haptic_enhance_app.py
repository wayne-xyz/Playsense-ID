# this is the app for the haptic enhancement data collection

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from pydualsense import pydualsense
from DualSenseHapticDataCollector import DualSenseHapticDataCollector

class HapticEnhanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Haptic Enhancement Data Collection")
        self.root.geometry("1000x900")  # Increased height to 900
        
        # Controller status
        self.controller_connected = False
        self.collector = None
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(expand=True, fill="both", padx=30, pady=30)
        
        # Status section
        self.create_status_section()
        
        # Button press display section
        self.create_button_display_section()
        
        # Control section
        self.create_control_section()
        
        # Initialize controller
        self.initialize_controller()
    
    def create_status_section(self):
        # Status frame
        status_frame = ttk.LabelFrame(self.main_frame, text="Controller Status", padding=20)
        status_frame.pack(fill="x", pady=20)  # Increased spacing
        
        # Controller connection status with larger font
        self.status_label = ttk.Label(status_frame, text="Controller: Disconnected", 
                                    foreground="red", font=("Arial", 16))  # Increased font size
        self.status_label.pack(pady=20)  # Increased spacing
        
        # Last update time with larger font
        self.update_time_label = ttk.Label(status_frame, text="Last Update: Never",
                                         font=("Arial", 16))  # Increased font size
        self.update_time_label.pack(pady=20)  # Increased spacing
    
    def create_button_display_section(self):
        # Button display frame
        button_frame = ttk.LabelFrame(self.main_frame, text="Button Press Display", padding=20)
        button_frame.pack(fill="x", pady=20)  # Increased spacing
        
        # Create a grid of labels for different buttons with larger size
        self.button_labels = {}
        buttons = [
            ('cross', '✕'), ('circle', '○'), ('triangle', '△'), ('square', '□'),
            ('dpad_up', '↑'), ('dpad_down', '↓'), ('dpad_left', '←'), ('dpad_right', '→')
        ]
        
        for i, (button, symbol) in enumerate(buttons):
            row = i // 4
            col = i % 4
            label = ttk.Label(button_frame, text=f"{symbol}: Not Pressed", 
                            width=25, padding=15, font=("Arial", 14))  # Increased size and font
            label.grid(row=row, column=col, padx=15, pady=15)  # Increased spacing
            self.button_labels[button] = label
    
    def create_control_section(self):
        # Control frame
        control_frame = ttk.LabelFrame(self.main_frame, text="Data Collection Control", padding=20)
        control_frame.pack(fill="x", pady=20)  # Increased spacing
        
        # Collection status with larger font
        self.collection_status = ttk.Label(control_frame, text="Collection Status: Stopped", 
                                         foreground="red", font=("Arial", 16))  # Increased font size
        self.collection_status.pack(pady=20)  # Increased spacing
        
        # Start/Stop button with larger size
        self.toggle_button = ttk.Button(control_frame, text="Start Collection", 
                                      command=self.toggle_collection, width=25)  # Increased width
        self.toggle_button.pack(pady=20)  # Increased spacing
        
        # Instructions with larger font
        instructions = (
            "Instructions:\n"
            "1. Connect DualSense controller\n"
            "2. Press Start Collection to begin\n"
            "3. Use controller buttons\n"
            "4. Press Stop Collection when done"
        )
        ttk.Label(control_frame, text=instructions, justify=tk.LEFT, 
                 font=("Arial", 14)).pack(pady=20)  # Increased font size and spacing
    
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
    
    def toggle_collection(self):
        if not self.controller_connected:
            messagebox.showwarning("Warning", "Controller not connected!")
            return
        
        if self.collector is None:
            # Start collection
            try:
                self.collector = DualSenseHapticDataCollector(
                    controller=self.dualsense, 
                    user_id="haptic_user",
                    output_dir="data/haptic_data"  # Create a specific directory for haptic data
                )
                self.collector.start_collection()
                self.collection_status.config(text="Collection Status: Recording", 
                                           foreground="green")
                self.toggle_button.config(text="Stop Collection")
                
                # Update status to show audio recording
                self.collection_status.config(
                    text="Collection Status: Recording (Inertial + Audio)", 
                    foreground="green"
                )
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

if __name__ == "__main__":
    root = tk.Tk()
    app = HapticEnhanceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()