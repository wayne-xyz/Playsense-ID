import csv
import os
import time
import threading
import datetime
from typing import Optional, Dict, List, Any
import pydualsense

class DualSenseDataCollector:
    """
    A class to collect and record data from a DualSense controller.
    This can be imported and used in pin_code_app.py.
    """
    
    def __init__(self, 
                 controller:pydualsense.pydualsense=None, 
                 output_dir: str = "data",
                 user_id: str = "unknown"):
        """
        Initialize the data collector
        
        Args:
            controller: An already initialized DualSense controller instance
            output_dir: Directory to save CSV files
            user_id: Identifier for the user generating the data
        """
        self.controller = controller
        self.output_dir = output_dir
        self.user_id = user_id
        self.is_collecting = False
        self.collection_thread = None
        self.data_buffer = []
        self.buffer_lock = threading.Lock()
        self.csv_file = None
        self.csv_writer = None
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def set_controller(self, controller):
        """Set the DualSense controller instance if not provided at initialization"""
        self.controller = controller
    
    def set_user_id(self, user_id: str):
        """Update the user ID for data collection"""
        self.user_id = user_id
    
    def start_collection(self):
        """Start collecting data from the controller"""
        if self.is_collecting:
            print("Data collection is already running")
            return
        
        if not self.controller:
            raise ValueError("No controller has been set. Call set_controller() first.")
        
        # Create a new CSV file with timestamp in filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/controller_data_{self.user_id}_{timestamp}.csv"
        
        # Open file and create CSV writer
        self.csv_file = open(filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        
        # Write header row
        self.csv_writer.writerow([
            'timestamp', 
            'button_press', 
            'gyro_pitch',  # Pitch (up/down rotation)
            'gyro_yaw',    # Yaw (left/right rotation)
            'gyro_roll',   # Roll (tilting left/right)
            'acc_x', 
            'acc_y', 
            'acc_z', 
            'user_id'
        ])
        
        # Start collection thread
        self.is_collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
        print(f"Started data collection. Saving to {filename}")
    
    def stop_collection(self):
        """Stop collecting data and close the CSV file"""
        if not self.is_collecting:
            print("Data collection is not running")
            return
        
        self.is_collecting = False
        
        # Wait for collection thread to stop
        if self.collection_thread:
            self.collection_thread.join(timeout=1.0)
        
        # Flush any remaining data in buffer
        self._write_buffer_to_csv()
        
        # Close the CSV file
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
        
        print("Data collection stopped")
    
    def _collection_loop(self):
        """Main loop for data collection"""
        while self.is_collecting:
            try:
                # Get current timestamp
                timestamp = datetime.datetime.now().isoformat()
                
                # Check which buttons are pressed
                button_press = self._get_pressed_buttons()
                
                # Get gyro data
                gyro_pitch = self.controller.state.gyro.Pitch
                gyro_yaw = self.controller.state.gyro.Yaw
                gyro_roll = self.controller.state.gyro.Roll
                
                # Get accelerometer data
                acc_x = self.controller.state.accelerometer.X
                acc_y = self.controller.state.accelerometer.Y
                acc_z = self.controller.state.accelerometer.Z
                
                # Create data entry
                data_entry = [
                    timestamp,
                    button_press,
                    gyro_pitch,
                    gyro_yaw,
                    gyro_roll,
                    acc_x,
                    acc_y,
                    acc_z,
                    self.user_id
                ]
                
                # Add to buffer
                with self.buffer_lock:
                    self.data_buffer.append(data_entry)
                    
                    # Write to CSV if buffer gets large enough
                    if len(self.data_buffer) >= 100:
                        self._write_buffer_to_csv()
                
                # Collect at approximately 250Hz
                time.sleep(0.004)
                
            except Exception as e:
                print(f"Error in data collection: {e}")
                time.sleep(0.1)
    
    def _get_pressed_buttons(self) -> str:
        """Return a string representation of which buttons are currently pressed"""
        pressed = []
        
        # Check DualSense buttons
        if self.controller.state.cross:
            pressed.append("cross")
        if self.controller.state.circle:
            pressed.append("circle")
        if self.controller.state.triangle:
            pressed.append("triangle")
        if self.controller.state.square:
            pressed.append("square")
        
        # Check D-pad
        if self.controller.state.DpadUp:
            pressed.append("up")
        if self.controller.state.DpadDown:
            pressed.append("down")
        if self.controller.state.DpadLeft:
            pressed.append("left")
        if self.controller.state.DpadRight:
            pressed.append("right")
        
        # Other buttons
        if self.controller.state.L1:
            pressed.append("L1")
        if self.controller.state.L2:
            pressed.append("L2")
        if self.controller.state.L3:
            pressed.append("L3")
        if self.controller.state.R1:
            pressed.append("R1")
        if self.controller.state.R2:
            pressed.append("R2")
        if self.controller.state.R3:
            pressed.append("R3")
            
        # Return as comma-separated string or "none"
        return ",".join(pressed) if pressed else "none"
    
    def _write_buffer_to_csv(self):
        """Write all buffered data to CSV and clear the buffer"""
        if not self.csv_writer:
            return
            
        with self.buffer_lock:
            # Write all entries to CSV
            self.csv_writer.writerows(self.data_buffer)
            self.csv_file.flush()  # Ensure data is written to disk
            
            # Clear buffer
            self.data_buffer.clear()
    
    def record_event(self, event_name: str, extra_data: Optional[Dict[str, Any]] = None):
        """
        Record a specific event with the current sensor data
        
        Args:
            event_name: Name of the event to record (e.g., "pin_entered", "verification_success")
            extra_data: Optional additional data to include
        """
        if not self.is_collecting or not self.controller:
            return
            
        try:
            # Get current timestamp
            timestamp = datetime.datetime.now().isoformat()
            
            # Create data entry with event name as button_press
            data_entry = [
                timestamp,
                f"EVENT:{event_name}",
                self.controller.state.gyro.Pitch,
                self.controller.state.gyro.Yaw,
                self.controller.state.gyro.Roll,
                self.controller.state.accelerometer.X,
                self.controller.state.accelerometer.Y,
                self.controller.state.accelerometer.Z,
                self.user_id
            ]
            
            # Add to buffer
            with self.buffer_lock:
                self.data_buffer.append(data_entry)
                
            # Immediately write if it's an important event
            self._write_buffer_to_csv()
                
        except Exception as e:
            print(f"Error recording event: {e}")


# Example of how to use in pin_code_app.py:
"""
from GUI.collect import DualSenseDataCollector

# In PINCodeApp.__init__:
self.data_collector = DualSenseDataCollector(output_dir="data", user_id="user1")

# After controller initialization:
self.data_collector.set_controller(self.dualsense)

# Start collection when needed:
self.data_collector.start_collection()

# Record specific events:
self.data_collector.record_event("pin_entered")

# Stop collection when done:
self.data_collector.stop_collection()
"""

if __name__ == "__main__":
    # This demonstrates standalone use
    import pydualsense
    
    print("Initializing DualSense controller...")
    ds = pydualsense()
    ds.init()
    
    print("Starting data collection for 10 seconds...")
    collector = DualSenseDataCollector(controller=ds, user_id="test_user")
    collector.start_collection()
    
    try:
        print("Move the controller around to generate data...")
        for i in range(10):
            print(f"Collecting data: {i+1}/10 seconds")
            time.sleep(1)
            
        # Record a test event
        collector.record_event("test_event")
        
    finally:
        collector.stop_collection()
        ds.close()
        print("Data collection complete")



