import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from pydualsense import pydualsense

class PINCodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PIN Code Application")
        self.root.geometry("400x600")
        
        # PIN code storage
        self.saved_pin = ""
        
        # Variables for PIN inputs
        self.set_pin = tk.StringVar()
        self.confirm_pin = tk.StringVar()
        self.verify_pin = tk.StringVar()
        
        # Current text field focus
        self.current_focus = None
        
        # Selected number for controller navigation
        self.selected_number = 5  # Start in the middle (5)
        self.number_buttons = {}  # Store references to number buttons
        
        # Create tabbed interface
        self.tab_control = ttk.Notebook(root)
        
        # Set PIN tab
        self.set_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.set_tab, text="Set PIN")
        
        # Verify PIN tab
        self.verify_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.verify_tab, text="Verify PIN")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Build the UI for each tab
        self.build_set_pin_tab()
        self.build_verify_pin_tab()
        
        # Initialize highlighting
        self.update_button_highlight()
        
        # Initialize DualSense controller
        self.initialize_controller()
    
    def build_set_pin_tab(self):
        # Title
        tk.Label(self.set_tab, text="Set PIN Code", font=("Arial", 16)).pack(pady=10)
        
        # PIN entry frame
        entry_frame = tk.Frame(self.set_tab)
        entry_frame.pack(pady=10)
        
        # PIN entry
        tk.Label(entry_frame, text="Enter PIN:").grid(row=0, column=0, padx=5, pady=5)
        self.pin_entry = tk.Entry(entry_frame, textvariable=self.set_pin, show="*", width=10, font=("Arial", 14))
        self.pin_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Confirm PIN entry
        tk.Label(entry_frame, text="Confirm PIN:").grid(row=1, column=0, padx=5, pady=5)
        self.confirm_entry = tk.Entry(entry_frame, textvariable=self.confirm_pin, show="*", width=10, font=("Arial", 14))
        self.confirm_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Number pad
        numpad_frame = tk.Frame(self.set_tab)
        numpad_frame.pack(pady=20)
        
        # Create number buttons (0-9)
        button_font = ("Arial", 14, "bold")
        for i in range(1, 10):
            row = (i-1) // 3
            col = (i-1) % 3
            btn = tk.Button(numpad_frame, text=str(i), width=5, height=2, font=button_font, 
                          command=lambda num=i: self.append_digit(num),
                          bg="light gray", relief=tk.RAISED)
            btn.grid(row=row, column=col, padx=5, pady=5)
            self.number_buttons[i] = btn
        
        # Button for 0
        zero_btn = tk.Button(numpad_frame, text="0", width=5, height=2, font=button_font, 
                command=lambda: self.append_digit(0),
                bg="light gray", relief=tk.RAISED)
        zero_btn.grid(row=3, column=1, padx=5, pady=5)
        self.number_buttons[0] = zero_btn
        
        # Delete button (left)
        del_btn = tk.Button(numpad_frame, text="⌫", width=5, height=2, font=button_font, 
                command=self.delete_digit,
                bg="light gray", relief=tk.RAISED)
        del_btn.grid(row=3, column=0, padx=5, pady=5)
        self.number_buttons[-1] = del_btn  # Use -1 to represent delete
        
        # Clear button (right)
        clear_btn = tk.Button(numpad_frame, text="Clear", width=5, height=2, font=button_font, 
                command=self.clear_input,
                bg="light gray", relief=tk.RAISED)
        clear_btn.grid(row=3, column=2, padx=5, pady=5)
        self.number_buttons[-2] = clear_btn  # Use -2 to represent clear
        
        # Save button
        save_btn = tk.Button(self.set_tab, text="Save PIN", width=15, height=2, font=("Arial", 12),
                          command=self.save_pin_code,
                          bg="light gray", relief=tk.RAISED)
        save_btn.pack(pady=20)
        self.number_buttons[-3] = save_btn  # Use -3 to represent save
        
        # Instructions label
        instructions = (
            "DualSense Controls:\n"
            "• Use D-pad to navigate the number pad\n"
            "• Press ✕ to enter the highlighted number\n"
            "• Press △ to delete\n"
            "• Press ○ to clear"
        )
        tk.Label(self.set_tab, text=instructions, justify=tk.LEFT).pack(pady=10)
        
        # Set initial focus
        self.pin_entry.focus_set()
        self.current_focus = self.pin_entry
    
    def build_verify_pin_tab(self):
        # Title
        tk.Label(self.verify_tab, text="Verify PIN Code", font=("Arial", 16)).pack(pady=10)
        
        # PIN entry frame
        entry_frame = tk.Frame(self.verify_tab)
        entry_frame.pack(pady=20)
        
        # PIN entry
        tk.Label(entry_frame, text="Enter PIN:").grid(row=0, column=0, padx=5, pady=5)
        self.verify_entry = tk.Entry(entry_frame, textvariable=self.verify_pin, show="*", width=10, font=("Arial", 14))
        self.verify_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Number pad
        numpad_frame = tk.Frame(self.verify_tab)
        numpad_frame.pack(pady=20)
        
        # Create number buttons (0-9)
        button_font = ("Arial", 14, "bold")
        for i in range(1, 10):
            row = (i-1) // 3
            col = (i-1) % 3
            btn = tk.Button(numpad_frame, text=str(i), width=5, height=2, font=button_font, 
                          command=lambda num=i: self.append_digit(num),
                          bg="light gray", relief=tk.RAISED)
            btn.grid(row=row, column=col, padx=5, pady=5)
            # Use 100+i to distinguish verify tab buttons from set tab buttons
            self.number_buttons[100+i] = btn
        
        # Button for 0
        zero_btn = tk.Button(numpad_frame, text="0", width=5, height=2, font=button_font, 
                command=lambda: self.append_digit(0),
                bg="light gray", relief=tk.RAISED)
        zero_btn.grid(row=3, column=1, padx=5, pady=5)
        self.number_buttons[100] = zero_btn
        
        # Delete button (left)
        del_btn = tk.Button(numpad_frame, text="⌫", width=5, height=2, font=button_font, 
                command=self.delete_digit,
                bg="light gray", relief=tk.RAISED)
        del_btn.grid(row=3, column=0, padx=5, pady=5)
        self.number_buttons[-101] = del_btn  # Use -101 to represent delete in verify tab
        
        # Clear button (right)
        clear_btn = tk.Button(numpad_frame, text="Clear", width=5, height=2, font=button_font, 
                command=self.clear_input,
                bg="light gray", relief=tk.RAISED)
        clear_btn.grid(row=3, column=2, padx=5, pady=5)
        self.number_buttons[-102] = clear_btn  # Use -102 to represent clear in verify tab
        
        # Verify button
        verify_btn = tk.Button(self.verify_tab, text="Verify PIN", width=15, height=2, font=("Arial", 12),
                            command=self.verify_pin_code,
                            bg="light gray", relief=tk.RAISED)
        verify_btn.pack(pady=20)
        self.number_buttons[-103] = verify_btn  # Use -103 to represent verify
        
        # Instructions label
        instructions = (
            "DualSense Controls:\n"
            "• Use D-pad to navigate the number pad\n"
            "• Press ✕ to enter the highlighted number\n"
            "• Press △ to delete\n"
            "• Press ○ to clear"
        )
        tk.Label(self.verify_tab, text=instructions, justify=tk.LEFT).pack(pady=10)
    
    def save_pin_code(self):
        if not self.set_pin.get():
            messagebox.showerror("Error", "Please enter a PIN code")
            return
        
        if self.set_pin.get() != self.confirm_pin.get():
            messagebox.showerror("Error", "PIN codes do not match")
            return
        
        self.saved_pin = self.set_pin.get()
        messagebox.showinfo("Success", "PIN code saved successfully")
        # Clear inputs
        self.set_pin.set("")
        self.confirm_pin.set("")
        # Switch to verify tab
        self.tab_control.select(1)
        self.verify_entry.focus_set()
        self.current_focus = self.verify_entry
        # Reset selected number for new tab
        self.selected_number = 5
        self.update_button_highlight()
    
    def verify_pin_code(self):
        if not self.verify_pin.get():
            messagebox.showerror("Error", "Please enter a PIN code")
            return
        
        if not self.saved_pin:
            messagebox.showerror("Error", "No PIN code has been saved yet")
            self.tab_control.select(0)
            return
        
        if self.verify_pin.get() == self.saved_pin:
            messagebox.showinfo("Success", "PIN code verified successfully")
            self.verify_pin.set("")
        else:
            messagebox.showerror("Error", "Incorrect PIN code")
            self.verify_pin.set("")
    
    def append_digit(self, digit):
        # Get current focused entry
        if self.root.focus_get() == self.pin_entry:
            current_val = self.set_pin.get()
            self.set_pin.set(current_val + str(digit))
            self.current_focus = self.pin_entry
        elif self.root.focus_get() == self.confirm_entry:
            current_val = self.confirm_pin.get()
            self.confirm_pin.set(current_val + str(digit))
            self.current_focus = self.confirm_entry
        elif self.root.focus_get() == self.verify_entry:
            current_val = self.verify_pin.get()
            self.verify_pin.set(current_val + str(digit))
            self.current_focus = self.verify_entry
        else:
            # If no field is focused, select the appropriate one based on tab
            if self.tab_control.index(self.tab_control.select()) == 0:
                # Set PIN tab
                self.pin_entry.focus_set()
                self.current_focus = self.pin_entry
                self.set_pin.set(str(digit))
            else:
                # Verify PIN tab
                self.verify_entry.focus_set()
                self.current_focus = self.verify_entry
                self.verify_pin.set(str(digit))
    
    def delete_digit(self):
        # Delete the last digit
        if self.root.focus_get() == self.pin_entry:
            current_val = self.set_pin.get()
            self.set_pin.set(current_val[:-1])
        elif self.root.focus_get() == self.confirm_entry:
            current_val = self.confirm_pin.get()
            self.confirm_pin.set(current_val[:-1])
        elif self.root.focus_get() == self.verify_entry:
            current_val = self.verify_pin.get()
            self.verify_pin.set(current_val[:-1])
    
    def clear_input(self):
        # Clear the current field
        if self.root.focus_get() == self.pin_entry:
            self.set_pin.set("")
        elif self.root.focus_get() == self.confirm_entry:
            self.confirm_pin.set("")
        elif self.root.focus_get() == self.verify_entry:
            self.verify_pin.set("")
    
    def switch_focus(self, direction):
        current_tab = self.tab_control.index(self.tab_control.select())
        
        if current_tab == 0:  # Set PIN tab
            if direction == "down":
                if self.current_focus == self.pin_entry:
                    self.confirm_entry.focus_set()
                    self.current_focus = self.confirm_entry
            elif direction == "up":
                if self.current_focus == self.confirm_entry:
                    self.pin_entry.focus_set()
                    self.current_focus = self.pin_entry
        else:
            # Only one field on the verify tab
            self.verify_entry.focus_set()
            self.current_focus = self.verify_entry
    
    def move_highlight(self, direction):
        """Move the highlighted button based on direction, by using the D-pad on the DualSense controller"""
        # Number pad layout:
        # 1 2 3
        # 4 5 6
        # 7 8 9
        # ⌫ 0 Clear
        
        current_number = self.selected_number
        current_tab = self.tab_control.index(self.tab_control.select())
        
        print(f"Moving highlight {direction} from {current_number} on tab {current_tab}")
        
        # Adjust for the current tab - if we're in verify tab and have a regular number
        if current_tab == 1:
            # Convert from verify tab button ID (100+) to regular number for easier logic
            if current_number >= 100 and current_number <= 109:
                temp_number = current_number - 100
            elif current_number <= -100:
                temp_number = current_number + 100
            else:
                temp_number = current_number
        else:
            temp_number = current_number
        
        # Movement logic
        if direction == "up":
            if temp_number in [1, 2, 3]:
                # Already at top row, do nothing or wrap to bottom
                if temp_number == 2:
                    temp_number = 0  # Go to 0
                elif temp_number == 1:
                    temp_number = -1  # Go to delete
                elif temp_number == 3:
                    temp_number = -2  # Go to clear
            elif temp_number in [4, 5, 6]:
                # Go up one row
                temp_number -= 3
            elif temp_number in [7, 8, 9]:
                # Go up one row
                temp_number -= 3
            elif temp_number == 0:
                # From 0 go to 8
                temp_number = 8
            elif temp_number in [-1, -2]:  # Delete or Clear
                # From bottom row special buttons, go to 7 or 9
                temp_number = 7 if temp_number == -1 else 9
            
        elif direction == "down":
            if temp_number in [1, 2, 3]:
                # Go down one row
                temp_number += 3
            elif temp_number in [4, 5, 6]:
                # Go down one row
                temp_number += 3
            elif temp_number in [7, 8, 9]:
                # From 7/8/9 go to special bottom row
                if temp_number == 8:
                    temp_number = 0
                elif temp_number == 7:
                    temp_number = -1  # Delete
                elif temp_number == 9:
                    temp_number = -2  # Clear
            elif temp_number in [0, -1, -2]:
                # From bottom row, go to save/verify button
                temp_number = -3 if current_tab == 0 else -103
                
        elif direction == "left":
            if temp_number in [2, 3, 5, 6, 8, 9]:
                # Not on left edge, move left
                temp_number -= 1
            elif temp_number == 0:
                # From 0, go to delete
                temp_number = -1
            elif temp_number == -2:  # Clear
                # From Clear, go to 0
                temp_number = 0
                
        elif direction == "right":
            if temp_number in [1, 2, 4, 5, 7, 8]:
                # Not on right edge, move right
                temp_number += 1
            elif temp_number == -1:  # Delete
                # From Delete, go to 0
                temp_number = 0
            elif temp_number == 0:
                # From 0, go to Clear
                temp_number = -2
        
        # Adjust back for current tab (verify tab buttons have 100 added)
        if current_tab == 1 and temp_number >= 0 and temp_number <= 9:
            self.selected_number = temp_number + 100
        elif current_tab == 1 and temp_number < 0 and temp_number != -3 and temp_number != -103:
            # For special buttons
            self.selected_number = temp_number - 100
        else:
            self.selected_number = temp_number
        
        print(f"New selected number: {self.selected_number}")
        self.update_button_highlight()
    
    def update_button_highlight(self):
        """Update the visual appearance of buttons to show which is selected"""
        # Add more debugging
        print(f"Update highlight called for number: {self.selected_number}")
        print(f"Available button IDs: {list(self.number_buttons.keys())}")
        
        # Reset all button colors - use a more explicit default color
        for btn_id, button in self.number_buttons.items():
            button.config(bg="light gray",fg="black", relief=tk.RAISED)
        
        # Highlight the selected button with a more noticeable color
        if self.selected_number in self.number_buttons:
            print(f"Highlighting button: {self.selected_number}")
            selected_button = self.number_buttons[self.selected_number]
            # Use a much more noticeable color and effect
            selected_button.config(bg="red", fg="red", relief=tk.SUNKEN)
            
            # Force update the UI
            self.root.update_idletasks()
        else:
            print(f"WARNING: Button {self.selected_number} not found in buttons dictionary!")
    
    def handle_selected_button(self):
        """Handle the currently selected button action"""
        current_number = self.selected_number
        current_tab = self.tab_control.index(self.tab_control.select())
        
        # Adjust for verify tab
        if current_tab == 1 and current_number >= 0 and current_number <= 9:
            # Convert back from 100+ to actual number
            digit = current_number - 100
            self.append_digit(digit)
        elif current_tab == 0 and current_number >= 0 and current_number <= 9:
            # Normal digit in set tab
            self.append_digit(current_number)
        elif current_number in [-1, -101]:
            # Delete button
            self.delete_digit()
        elif current_number in [-2, -102]:
            # Clear button
            self.clear_input()
        elif current_number == -3:
            # Save button (set tab)
            self.save_pin_code()
        elif current_number == -103:
            # Verify button (verify tab)
            self.verify_pin_code()
    
    def initialize_controller(self):
        try:
            self.dualsense = pydualsense()
            self.dualsense.init()
            
            # Start controller input thread
            self.controller_running = True
            self.controller_thread = threading.Thread(target=self.controller_loop)
            self.controller_thread.daemon = True
            self.controller_thread.start()
            
        except Exception as e:
            print(f"Error initializing DualSense controller: {e}")
            messagebox.showwarning("Controller Warning", 
                                "DualSense controller not detected. You can still use the on-screen buttons.")
    
    def controller_loop(self):
        # Track button states to detect press events (not holds)
        button_states = {
            'cross': False,
            'triangle': False,
            'circle': False,
            'dpad_up': False,
            'dpad_down': False,
            'dpad_left': False,
            'dpad_right': False
        }
        
        while self.controller_running:
            try:
                # Get controller state
                # Handle D-pad for navigation
                if self.dualsense.state.DpadUp:
                    if not button_states['dpad_up']:
                        button_states['dpad_up'] = True
                        print("Button pressed: D-pad UP")
                        self.root.after(0, self.move_highlight, "up")
                else:
                    button_states['dpad_up'] = False
                
                if self.dualsense.state.DpadDown:
                    if not button_states['dpad_down']:
                        button_states['dpad_down'] = True
                        print("Button pressed: D-pad DOWN")
                        self.root.after(0, self.move_highlight, "down")
                else:
                    button_states['dpad_down'] = False
                
                if self.dualsense.state.DpadLeft:
                    if not button_states['dpad_left']:
                        button_states['dpad_left'] = True
                        print("Button pressed: D-pad LEFT")
                        self.root.after(0, self.move_highlight, "left")
                else:
                    button_states['dpad_left'] = False
                
                if self.dualsense.state.DpadRight:
                    if not button_states['dpad_right']:
                        button_states['dpad_right'] = True
                        print("Button pressed: D-pad RIGHT")
                        self.root.after(0, self.move_highlight, "right")
                else:
                    button_states['dpad_right'] = False
                
                # Handle cross button (confirm/enter number)
                if self.dualsense.state.cross:
                    if not button_states['cross']:
                        button_states['cross'] = True
                        print("Button pressed: CROSS")
                        # Handle the current selection
                        self.root.after(0, self.handle_selected_button)
                else:
                    button_states['cross'] = False
                
                # Handle triangle button (delete)
                if self.dualsense.state.triangle:
                    if not button_states['triangle']:
                        button_states['triangle'] = True
                        print("Button pressed: TRIANGLE")
                        self.root.after(0, self.delete_digit)
                else:
                    button_states['triangle'] = False
                
                # Handle circle button (clear)
                if self.dualsense.state.circle:
                    if not button_states['circle']:
                        button_states['circle'] = True
                        print("Button pressed: CIRCLE")
                        self.root.after(0, self.clear_input)
                else:
                    button_states['circle'] = False
                
                # Sleep to prevent high CPU usage
                time.sleep(0.05)
                
            except Exception as e:
                print(f"Error reading controller input: {e}")
                time.sleep(1)  # Longer sleep on error
    
    def on_closing(self):
        # Cleanup controller
        self.controller_running = False
        if hasattr(self, 'dualsense'):
            try:
                self.dualsense.close()
            except:
                pass
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PINCodeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop() 