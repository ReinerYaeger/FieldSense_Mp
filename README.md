# About

The soil moisture Wireless Sensor Network is designed to collect, analyze, and visualize soil moisture data from various sensors placed across a farm.

This application facilitates the collection of soil moisture data from sensors connected to an arduino and a Raspberry Pi via WiFi.

## System Design 
### Theoretical System Design 
![Soil Moisture Monitoring System](media/images/system%20design/System_Design.png "Soil Moisture Monitoring System")

### Practical System Design
![Soil Moisture Monitoring System](media/images/system%20design/Practical_System_Design.png "Soil Moisture Monitoring System")

# Installation

### Prerequisites

Ensure you have the following installed:

- **XAMPP**
- **Python**
- **Git**

### Database Setup

1. **Import SQL File**: Locate the SQL file included in the base directory and import it into PHPMyAdmin. This file contains necessary data for the application, excluding hardware-specific details.

### Setting Up the Application

Follow these steps to set up the application:

1. **Clone the Project**:
    ```
    git clone https://github.com/ReinerYaeger/MpWsn
    ```
    Clone the project into your desired directory.

2. **Create a Virtual Environment**:
    ```
    python -m venv venv
    ```
    This will create a virtual environment for isolating the project's dependencies.

3. **Install Requirements**:
    ```
    pip install -r requirements.txt
    ```
    This command will install all the required Python packages specified in the `requirements.txt` file.

### Running the Application

After completing the installation steps, you're ready to run the application. Make sure XAMPP is running to support the application's database functionalities.
```
python ./manage runserver
```

### Hardware Files

If you possess the required hardware, find the necessary files for the Arduino and Raspberry Pi 4 in this directory:
``/iot/pi_files``

### Running the Server

To run the server, execute the `server.py` file located in the `/iot/pi_files` directory using the following command:


### Performing Analytics

For performing analytics, run the `analyzer.py` file in the `/iot/pi_files` directory using the command:



