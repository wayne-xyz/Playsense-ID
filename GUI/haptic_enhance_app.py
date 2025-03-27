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
        self.root.geometry("600x600")  # Increased height from 400 to 600 while keeping width at 600
        
        # Controller status
        self.controller_connected = False
        self.collector = None
        self.haptic_mode = tk.StringVar(value="non-haptic")  # Default mode
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)  # Reduced padding from 20
        
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
            
            # Handle haptic feedback for fixed-haptic mode
            if hasattr(self, 'dualsense') and self.controller_connected:
                mode = self.haptic_mode.get()
                if mode == "fixed-haptic":
                    if is_pressed:
                        # Set both motors to lowest intensity (1) when button is pressed
                        self.dualsense.setLeftMotor(1)
                        self.dualsense.setRightMotor(1)
                    else:
                        # Stop vibration when button is released
                        self.dualsense.setLeftMotor(0)
                        self.dualsense.setRightMotor(0)
    
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

if __name__ == "__main__":
    root = tk.Tk()
    app = HapticEnhanceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()