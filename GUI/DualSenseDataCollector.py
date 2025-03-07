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
        
        # Debug flags
        self.debug_output = True
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"DualSenseDataCollector initialized with user_id: {user_id}")
    
    def set_controller(self, controller):
        """Set the DualSense controller instance if not provided at initialization"""
        self.controller = controller
        print(f"Controller set: {controller}")
    
    def set_user_id(self, user_id: str):
        """Update the user ID for data collection"""
        self.user_id = user_id
        print(f"User ID updated to: {user_id}")
    
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
        try:
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
            # Flush header immediately
            self.csv_file.flush()
            print(f"CSV file created at: {filename}")
        except Exception as e:
            print(f"Error creating CSV file: {e}")
            return
        
        # Start collection thread
        self.is_collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
        print(f"Started data collection. Saving to {filename}")
    
    def stop_collection(self):
        """Stop collecting data from the controller"""
        if not self.is_collecting:
            print("Data collection is not running")
            return
            
        print("Stopping data collection...")
        
        # Signal the collection thread to stop
        self.is_collecting = False
        
        # Wait for collection thread to finish (with timeout)
        if self.collection_thread and self.collection_thread.is_alive():
            try:
                self.collection_thread.join(timeout=2.0)
                print("Collection thread joined successfully")
            except Exception as e:
                print(f"Error joining collection thread: {e}")
        
        # Do one final write of any remaining data
        try:
            print(f"Final write: {len(self.data_buffer)} records")
            self._write_buffer_to_csv(force=True)
        except Exception as e:
            print(f"Error during final CSV write: {e}")
        
        # Close the CSV file
        if hasattr(self, 'csv_file') and self.csv_file and not self.csv_file.closed:
            try:
                self.csv_file.close()
                print("CSV file closed successfully")
            except Exception as e:
                print(f"Error closing CSV file: {e}")
        
        self.csv_writer = None
        self.csv_file = None
        print("Data collection stopped")
    
    def _collection_loop(self):
        """Main loop for data collection"""
        record_count = 0
        last_write_time = time.time()
        
        print("Collection loop started")
        
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
                
                # Print real-time inertial data (less frequently to reduce console spam)
                if self.debug_output and record_count % 50 == 0:
                    print("\rInertial Data - Gyro(P,Y,R): [{:6.2f}, {:6.2f}, {:6.2f}] | Acc(X,Y,Z): [{:6.2f}, {:6.2f}, {:6.2f}] | Records: {}".format(
                        gyro_pitch, gyro_yaw, gyro_roll,
                        acc_x, acc_y, acc_z,
                        record_count
                    ), end="", flush=True)
                
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
                    record_count += 1
                
                # Write to CSV if buffer gets large enough or enough time has passed
                current_time = time.time()
                if len(self.data_buffer) >= 20 or (current_time - last_write_time) > 1.0:
                    self._write_buffer_to_csv()
                    last_write_time = current_time
                
                # Collect at approximately 250Hz but ensure we don't overwhelm the system
                time.sleep(0.004)
                
            except Exception as e:
                print(f"\nError in data collection: {e}")
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
            pressed.append("square")# rectangle/square
        
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
    
    def _write_buffer_to_csv(self, force=False):
        """
        Write all buffered data to CSV and clear the buffer
        
        Args:
            force: If True, write even if conditions aren't met
        """
        # Skip if writer not initialized or not collecting (unless forced)
        if (not self.csv_writer or (not self.is_collecting and not force)):
            return
        
        try:
            # Use a timeout to prevent blocking indefinitely
            acquired = self.buffer_lock.acquire(timeout=1.0)
            
            if acquired:
                try:
                    # Check if file is still open and buffer has data
                    if self.csv_file and not self.csv_file.closed and self.data_buffer:
                        # Get buffer length for logging
                        buffer_len = len(self.data_buffer)
                        
                        # Write all entries to CSV
                        self.csv_writer.writerows(self.data_buffer)
                        self.csv_file.flush()  # Ensure data is written to disk
                        
                        # Log every few writes to avoid console spam
                        if buffer_len >= 100 or force:
                            print(f"\nWrote {buffer_len} records to CSV file")
                        
                        # Clear buffer
                        self.data_buffer.clear()
                finally:
                    self.buffer_lock.release()
        except Exception as e:
            print(f"Error writing to CSV: {e}")
    
    def record_event(self, event_name: str, extra_data: Optional[Dict[str, Any]] = None):
        """
        Record a specific event with the current sensor data
        
        Args:
            event_name: Name of the event to record (e.g., "pin_entered", "verification_success")
            extra_data: Optional additional data to include
        """
        if not self.is_collecting or not self.controller:
            print(f"Cannot record event '{event_name}': collection not active")
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
            
            print(f"Recorded event: {event_name}")
            
            # Immediately write if it's an important event
            self._write_buffer_to_csv(force=True)
                
        except Exception as e:
            print(f"Error recording event: {e}")


# Example of how to use in pin_code_app.py:
"""
from GUI.DualSenseDataCollector import DualSenseDataCollector

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



