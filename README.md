# Model Training for the authentication 
Leverage the inertial data to train a model for the authentication.
By using the dualsense controller, we can collect the data and train a model to verify the user.


##  PIN Code Application - GUI For data collection

A GUI application for setting and verifying PIN codes using a DualSense controller.

## Features

- Set a PIN code with confirmation
- Verify a PIN code
- Use on-screen digit pad or DualSense controller for input
- Two-tab interface for setting and verifying PIN codes

## Requirements

- Python 3.6+
- Tkinter (included with most Python installations)
- PyDualSense library

## Installation

1. Make sure you have Python installed
2. Install the PyDualSense library:
   ```
   pip install pydualsense
   ```

## Usage


### Windows 

- add hidapi.dll
- conda install cffi

Run the application:
```
python pin_code_app.py
```

### Without DualSense Controller

You can use the application with your mouse:
- Click on the text fields to set focus
- Use the on-screen number pad to enter digits
- Use the on-screen buttons to delete, clear, or save/verify

### With DualSense Controller

Connect your DualSense controller before starting the application. Then:
- Use the D-pad to navigate between fields
- Press X to confirm numbers
- Press Triangle to delete the last digit
- Press Circle to clear the current field

## Tab Navigation

- **Set PIN Tab**: Enter and confirm your PIN code
- **Verify PIN Tab**: Verify a previously saved PIN code


## Haptic model by Audio playing features 

- Enable the audio haptic feature

## Note

This application requires the PyDualSense library to interface with the DualSense controller. If a controller is not detected, the application will still function using the on-screen controls.