import csv
import os
import time
import threading
import datetime
import wave
import numpy as np
import sounddevice as sd
from typing import Optional, Dict, List, Any
import pydualsense

class DualSenseHapticDataCollector:
    """
    A class to collect and record both inertial and audio data from a DualSense controller.
    This extends the functionality of DualSenseDataCollector to include audio recording.
    """
    
    def __init__(self, 
                 controller: pydualsense.pydualsense = None, 
                 output_dir: str = "data",
                 user_id: str = "unknown",
                 audio_sample_rate: int = 48000,
                 audio_channels: int = 2):
        """
        Initialize the data collector
        
        Args:
            controller: An already initialized DualSense controller instance
            output_dir: Directory to save CSV and audio files
            user_id: Identifier for the user generating the data
            audio_sample_rate: Sample rate for audio recording (default: 44100 Hz)
            audio_channels: Number of audio channels (default: 1 for mono)
        """
        self.controller = controller
        self.output_dir = output_dir
        self.user_id = user_id
        self.is_collecting = False
        self.collection_thread = None
        self.audio_thread = None
        self.data_buffer = []
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        self.audio_lock = threading.Lock()
        self.csv_file = None
        self.csv_writer = None
        self.wav_file = None
        self.wav_filename = None  # Store the WAV filename
        
        # Audio settings
        self.audio_sample_rate = audio_sample_rate
        self.audio_channels = audio_channels
        self.audio_device = None
        
        # Debug flags
        self.debug_output = True
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"DualSenseHapticDataCollector initialized with user_id: {user_id}")
    
    def set_controller(self, controller):
        """Set the DualSense controller instance if not provided at initialization"""
        self.controller = controller
        print(f"Controller set: {controller}")
    
    def set_user_id(self, user_id: str):
        """Update the user ID for data collection"""
        self.user_id = user_id
        print(f"User ID updated to: {user_id}")
    
    def _find_dualsense_mic(self):
        """Find the DualSense microphone device"""
        devices = sd.query_devices()
        for device in devices:
            if "dualsense" in device['name'].lower():
                return device['index']
        return None
    
    def start_collection(self):
        """Start collecting data from the controller"""
        if self.is_collecting:
            print("Data collection is already running")
            return
        
        if not self.controller:
            raise ValueError("No controller has been set. Call set_controller() first.")
        
        # Create timestamp for filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create CSV filename
        csv_filename = f"{self.output_dir}/controller_data_{self.user_id}_{timestamp}.csv"
        
        # Create WAV filename
        self.wav_filename = f"{self.output_dir}/audio_{self.user_id}_{timestamp}.wav"
        
        try:
            # Open and initialize CSV file
            self.csv_file = open(csv_filename, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write header row with audio file reference
            self.csv_writer.writerow([
                'timestamp', 
                'button_press', 
                'gyro_pitch',  # Pitch (up/down rotation)
                'gyro_yaw',    # Yaw (left/right rotation)
                'gyro_roll',   # Roll (tilting left/right)
                'acc_x', 
                'acc_y', 
                'acc_z', 
                'user_id',
                'audio_file'   # Reference to the corresponding audio file
            ])
            self.csv_file.flush()
            
            # Initialize WAV file
            self.wav_file = wave.open(self.wav_filename, 'wb')
            self.wav_file.setnchannels(self.audio_channels)
            self.wav_file.setsampwidth(2)  # 16-bit audio
            self.wav_file.setframerate(self.audio_sample_rate)
            
            # Find DualSense microphone and print device information
            print("\n=== Available Audio Input Devices ===")
            devices = sd.query_devices()
            self.audio_device = None
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:  # Only show input devices
                    device_status = "✓ SELECTED" if "dualsense" in device['name'].lower() else ""
                    print(f"[{i}] {device['name']} {device_status}")
                    if "dualsense" in device['name'].lower():
                        self.audio_device = i
                        print(f"    Sample Rate: {device['default_samplerate']} Hz")
                        print(f"    Input Channels: {device['max_input_channels']}")
                        print(f"    Latency: {device['default_low_input_latency']:.3f}s")
            
            if self.audio_device is None:
                raise ValueError("DualSense microphone not found")
            
            print("\n=== Recording Configuration ===")
            print(f"CSV file: {csv_filename}")
            print(f"WAV file: {self.wav_filename}")
            print(f"Sample Rate: {self.audio_sample_rate} Hz")
            print(f"Channels: {self.audio_channels}")
            print(f"Selected Device: {devices[self.audio_device]['name']}")
            
        except Exception as e:
            print(f"Error initializing files: {e}")
            return
        
        # Start collection threads
        self.is_collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.audio_thread = threading.Thread(target=self._audio_recording_loop)
        
        self.collection_thread.daemon = True
        self.audio_thread.daemon = True
        
        print("\n=== Starting Data Collection ===")
        print("Recording both inertial and audio data...")
        print("Press Ctrl+C to stop recording")
        
        self.collection_thread.start()
        self.audio_thread.start()
        
        print(f"Started data collection. Saving to {csv_filename} and {self.wav_filename}")
    
    def stop_collection(self):
        """Stop collecting data from the controller"""
        if not self.is_collecting:
            print("Data collection is not running")
            return
            
        print("Stopping data collection...")
        
        # Signal threads to stop
        self.is_collecting = False
        
        # Wait for threads to finish
        if self.collection_thread and self.collection_thread.is_alive():
            try:
                self.collection_thread.join(timeout=2.0)
                print("Collection thread joined successfully")
            except Exception as e:
                print(f"Error joining collection thread: {e}")
        
        if self.audio_thread and self.audio_thread.is_alive():
            try:
                self.audio_thread.join(timeout=2.0)
                print("Audio thread joined successfully")
            except Exception as e:
                print(f"Error joining audio thread: {e}")
        
        # Do one final write of any remaining data
        try:
            print(f"Final write: {len(self.data_buffer)} records")
            self._write_buffer_to_csv(force=True)
            self._write_audio_buffer(force=True)
        except Exception as e:
            print(f"Error during final write: {e}")
        
        # Close files
        if hasattr(self, 'csv_file') and self.csv_file and not self.csv_file.closed:
            try:
                self.csv_file.close()
                print("CSV file closed successfully")
            except Exception as e:
                print(f"Error closing CSV file: {e}")
        
        if hasattr(self, 'wav_file') and self.wav_file:
            try:
                self.wav_file.close()
                print("WAV file closed successfully")
            except Exception as e:
                print(f"Error closing WAV file: {e}")
        
        self.csv_writer = None
        self.csv_file = None
        self.wav_file = None
        print("Data collection stopped")
    
    def _audio_recording_loop(self):
        """Main loop for audio recording"""
        print("Audio recording loop started")
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio callback status: {status}")
            with self.audio_lock:
                self.audio_buffer.extend(indata.flatten())
            
            # Write to WAV file if buffer gets large enough
            if len(self.audio_buffer) >= self.audio_sample_rate:  # 1 second of audio
                self._write_audio_buffer()
        
        try:
            with sd.InputStream(device=self.audio_device,
                              channels=self.audio_channels,
                              samplerate=self.audio_sample_rate,
                              callback=audio_callback):
                while self.is_collecting:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Error in audio recording: {e}")
    
    def _write_audio_buffer(self, force=False):
        """Write audio buffer to WAV file"""
        if not self.wav_file or (not self.is_collecting and not force):
            return
        
        try:
            with self.audio_lock:
                if self.audio_buffer:
                    # Convert to 16-bit PCM
                    audio_data = np.array(self.audio_buffer, dtype=np.float32)
                    audio_data = (audio_data * 32767).astype(np.int16)
                    
                    # Write to WAV file
                    self.wav_file.writeframes(audio_data.tobytes())
                    self.audio_buffer.clear()
        except Exception as e:
            print(f"Error writing audio data: {e}")
    
    def _collection_loop(self):
        """Main loop for data collection"""
        record_count = 0
        last_write_time = time.time()
        
        # Button press counters and state tracking
        button_counters = {
            "cross": 0, "circle": 0, "triangle": 0, "square": 0,
            "up": 0, "down": 0, "left": 0, "right": 0,
            "L1": 0, "L2": 0, "L3": 0, "R1": 0, "R2": 0, "R3": 0
        }
        
        # Track button states to detect consecutive presses
        button_active = {
            "cross": False, "circle": False, "triangle": False, "square": False,
            "up": False, "down": False, "left": False, "right": False,
            "L1": False, "L2": False, "L3": False, "R1": False, "R2": False, "R3": False
        }
        
        print("Collection loop started")
        
        while self.is_collecting:
            try:
                # Get current timestamp
                timestamp = datetime.datetime.now().isoformat()
                
                # Check which buttons are pressed
                button_press = self._get_pressed_buttons()
                
                # Parse pressed buttons
                current_buttons = set(button_press.split(",")) if button_press != "none" else set()
                
                # Update button counters
                for button in button_counters.keys():
                    if button in current_buttons:
                        if not button_active[button]:
                            button_counters[button] += 1
                            button_active[button] = True
                    else:
                        button_active[button] = False
                
                # Get gyro data
                gyro_pitch = self.controller.state.gyro.Pitch
                gyro_yaw = self.controller.state.gyro.Yaw
                gyro_roll = self.controller.state.gyro.Roll
                
                # Get accelerometer data
                acc_x = self.controller.state.accelerometer.X
                acc_y = self.controller.state.accelerometer.Y
                acc_z = self.controller.state.accelerometer.Z
                
                # Print real-time data (less frequently)
                if self.debug_output and record_count % 50 == 0:
                    print("\rInertial Data - Gyro(P,Y,R): [{:6.2f}, {:6.2f}, {:6.2f}] | Acc(X,Y,Z): [{:6.2f}, {:6.2f}, {:6.2f}] | Records: {}".format(
                        gyro_pitch, gyro_yaw, gyro_roll,
                        acc_x, acc_y, acc_z,
                        record_count
                    ), end="", flush=True)
                    
                    print("\nButton press counts:")
                    for button, count in button_counters.items():
                        if count > 0:
                            print(f"  {button}: {count} times")
                
                # Create data entry with audio file reference
                data_entry = [
                    timestamp,
                    button_press,
                    gyro_pitch,
                    gyro_yaw,
                    gyro_roll,
                    acc_x,
                    acc_y,
                    acc_z,
                    self.user_id,
                    os.path.basename(self.wav_filename)  # Use stored filename instead of wav_file.filename
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
                
                # Collect at approximately 250Hz
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
            
        return ",".join(pressed) if pressed else "none"
    
    def _write_buffer_to_csv(self, force=False):
        """Write all buffered data to CSV and clear the buffer"""
        if (not self.csv_writer or (not self.is_collecting and not force)):
            return
        
        try:
            acquired = self.buffer_lock.acquire(timeout=1.0)
            
            if acquired:
                try:
                    if self.csv_file and not self.csv_file.closed and self.data_buffer:
                        buffer_len = len(self.data_buffer)
                        self.csv_writer.writerows(self.data_buffer)
                        self.csv_file.flush()
                        
                        if buffer_len >= 100 or force:
                            print(f"\nWrote {buffer_len} records to CSV file")
                        
                        self.data_buffer.clear()
                finally:
                    self.buffer_lock.release()
        except Exception as e:
            print(f"Error writing to CSV: {e}")
    
    def record_event(self, event_name: str, extra_data: Optional[Dict[str, Any]] = None):
        """Record a specific event with the current sensor data"""
        if not self.is_collecting or not self.controller:
            print(f"Cannot record event '{event_name}': collection not active")
            return
            
        try:
            timestamp = datetime.datetime.now().isoformat()
            
            data_entry = [
                timestamp,
                f"EVENT:{event_name}",
                self.controller.state.gyro.Pitch,
                self.controller.state.gyro.Yaw,
                self.controller.state.gyro.Roll,
                self.controller.state.accelerometer.X,
                self.controller.state.accelerometer.Y,
                self.controller.state.accelerometer.Z,
                self.user_id,
                os.path.basename(self.wav_filename) if self.wav_filename else "none"  # Use stored filename
            ]
            
            with self.buffer_lock:
                self.data_buffer.append(data_entry)
            
            print(f"Recorded event: {event_name}")
            self._write_buffer_to_csv(force=True)
                
        except Exception as e:
            print(f"Error recording event: {e}")


if __name__ == "__main__":
    # Example usage
    import pydualsense
    
    print("Initializing DualSense controller...")
    ds = pydualsense()
    ds.init()
    
    print("Starting data collection for 10 seconds...")
    collector = DualSenseHapticDataCollector(controller=ds, user_id="test_user")
    collector.start_collection()
    
    try:
        print("Move the controller and speak into the microphone...")
        for i in range(10):
            print(f"Collecting data: {i+1}/10 seconds")
            time.sleep(1)
            
        collector.record_event("test_event")
        
    finally:
        collector.stop_collection()
        ds.close()
        print("Data collection complete") 