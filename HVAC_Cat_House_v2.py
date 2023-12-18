import time
import board
import busio
import digitalio
import cherrypy
import random

# Define GPIO pins for relays
HEATING_PIN = 21  # Example GPIO pin for heating control
COOLING_PIN = 20  # Example GPIO pin for cooling control

# Initialize MCP9808 temperature sensor
# temp_sensor = adafruit_mcp9808.MCP9808(i2c)


# Initialize MCP9808 temperature sensor (simulated for testing)
class SimulatedI2C:
    def __init__(self, *args, **kwargs):
        pass

    def readfrom_into(self, address, buffer, *args, **kwargs):
        # Simulate reading temperature bytes
        simulated_temperature = random.uniform(65.0, 75.0)
        # Convert simulated temperature to 12-bit format used by MCP9808
        temperature_bytes = int((simulated_temperature - 32) * 5 / 9 / 0.0625).to_bytes(2, 'big')
        buffer[:2] = temperature_bytes
        return len(buffer)

    def writeto(self, address, buffer, *args, **kwargs):
        pass


i2c = SimulatedI2C()


# Initialize MCP9808 temperature sensor (simulated for testing)
class SimulatedMCP9808:
    def __init__(self, i2c, address=0x18):
        self.i2c_device = i2c

    @property
    def temperature(self):
        # Simulate fetching temperature data
        temperature_bytes = bytearray(2)
        self.i2c_device.readfrom_into(0x18, temperature_bytes)
        # Convert the two bytes to a 12-bit temperature value
        temperature_value = int.from_bytes(temperature_bytes, 'big') >> 4
        # Ensure the simulated temperature is within a reasonable range (65°F to 75°F)
        simulated_temperature_celsius = min(max(temperature_value * 0.0625, 18.0), 23.0)
        simulated_temperature_fahrenheit = (simulated_temperature_celsius * 9 / 5) + 32
        return simulated_temperature_fahrenheit


temp_sensor = SimulatedMCP9808(i2c)

# Initialize GPIO pins for relays
heater_relay = digitalio.DigitalInOut(getattr(board, f'D{HEATING_PIN}'))
heater_relay.direction = digitalio.Direction.OUTPUT

cooler_relay = digitalio.DigitalInOut(getattr(board, f'D{COOLING_PIN}'))
cooler_relay.direction = digitalio.Direction.OUTPUT

# Temperature control parameters
min_temperature_fahrenheit = 50  # Set your minimum desired temperature in Fahrenheit
max_temperature_fahrenheit = 90  # Set your maximum desired temperature in Fahrenheit
temperature_range_fahrenheit = 1.0  # Set the acceptable temperature range in Fahrenheit
temp_refresh_rate = 10  # Set the refresh rate of the current temperature in seconds

# Desired temperature in Fahrenheit
desired_temperature_fahrenheit = 72  # Set your desired temperature in Fahrenheit

# CherryPy configuration
cherrypy.config.update({
    'server.socket_host': '0.0.0.0',
    'server.socket_port': 8080,
})


class TemperatureControlApp(object):
    @cherrypy.expose
    def index(self, message="", circle_class=""):
        current_temperature_fahrenheit = temp_sensor.temperature

        # Determine the state (heating, cooling, or within the desired range)
        state = "Within Desired Range"

        if current_temperature_fahrenheit < (desired_temperature_fahrenheit - temperature_range_fahrenheit):
            heater_relay.value = True
            cooler_relay.value = False
            state = "Heating: Temperature below desired range"
            circle_class = "heating"
        elif current_temperature_fahrenheit > (desired_temperature_fahrenheit + temperature_range_fahrenheit):
            heater_relay.value = False
            cooler_relay.value = True
            state = "Cooling: Temperature above desired range"
            circle_class = "cooling"
        else:
            heater_relay.value = False
            cooler_relay.value = False
            if not circle_class:  # If not already set by an invalid input
                circle_class = "within_range"

        return f"""
        <html>
        <head>
            <title>Temperature Control System</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #1a1a1a;
                    color: #ffffff;
                }}

                h1 {{
                    text-align: center;
                    font-size: 24px;
                    color: #ffffff;
                }}

                p {{
                    text-align: center;
                    font-size: 20px;
                    color: #ffffff;
                }}

                form {{
                    text-align: center;
                }}

                label {{
                    font-size: 24px;
                    color: #ffffff;
                    display: block;
                    margin-bottom: 5px;
                }}

                input[type="number"] {{
                    width: 70%;
                    padding: 8px;
                    margin: 8px 0;
                    box-sizing: border-box;
                    font-size: 24px;
                }}

                input[type="submit"] {{
                    width: 70%;
                    padding: 10px;
                    font-size: 24px;
                    background-color: #3498db;
                    color: #ffffff;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }}

                .circle {{
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    display: block;
                    margin: 10px auto;
                }}

                .heating {{
                    background-color: red;
                }}

                .cooling {{
                    background-color: blue;
                }}

                .within_range {{
                    background-color: green;
                }}

                .active {{
                    background-color: yellow;
                }}

                @media only screen and (max-width: 600px) {{
                    /* Adjust styles for smaller screens */
                    body {{
                        margin: 10px;
                    }}

                    h1 {{
                        font-size: 40px;
                    }}

                    p {{
                        font-size: 24px;
                    }}

                    label, input[type="number"], input[type="submit"] {{
                        width: 80%;
                        font-size: 24px;
                        margin: 0 auto 10px;
                    }}

                    input[type="submit"] {{
                        width: 80%;
                        padding: 10px;
                        font-size: 24px;
                        background-color: #3498db;
                        color: #ffffff;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        margin: 0 auto;
                    }}
                }}
            </style>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="refresh" content="{temp_refresh_rate}">
        </head>
        <body>
            <div style="text-align: right; padding: 10px;">
                <a href="/settings" style="color: #ffffff; text-decoration: none; font-size: 35px;">&#9881;</a>
            </div>
            <h1>Temperature Control System</h1>
            <p>Current Temperature: {current_temperature_fahrenheit:.1f} &deg;F</p>
            <form method="post" action="set_desired_temperature">
                <label for="desired_temperature">Desired Temperature:</label>
                <input type="number" step="1" name="desired_temperature" value="{desired_temperature_fahrenheit:.0f}">
                <br>
                <input type="submit" value="Set">
            </form>
            <div class="circle {circle_class}"></div>
            <p class="{state.lower().replace(' ', '-')}">{state}</p>
            <p style="color: yellow;">{message}</p>
        </body>
        </html>
        """

    @cherrypy.expose
    def settings(self, message="", circle_class=""):
        return f"""
                <html>
                <head>
                    <title>Temperature Control System - Settings</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                            background-color: #1a1a1a;
                            color: #ffffff;
                        }}

                        h1, label, input[type="number"], input[type="submit"] {{
                            font-size: 24px;
                        }}

                        form {{
                            text-align: center;
                        }}

                        input[type="number"] {{
                            width: 70%;
                            padding: 8px;
                            margin: 8px 0;
                            box-sizing: border-box;
                        }}

                        input[type="submit"] {{
                            width: 70%;
                            padding: 10px;
                            border-radius: 5px;
                            cursor: pointer;
                            background-color: #3498db;
                            color: #ffffff;
                            border: none;
                        }}

                        .input-container {{
                            text-align: center;
                            margin: 10px;
                        }}

                        .input-container input {{
                            margin-bottom: 10px;
                        }}

                        h1 {{
                            text-align: center;
                            font-size: 40px;
                        }}

                        .back-button {{
                            color: #ffffff;
                            text-decoration: none;
                            font-size: 35px;
                        }}

                        @media only screen and (max-width: 600px) {{
                            body {{
                                margin: 10px;
                            }}

                            h1, label, input[type="number"], input[type="submit"] {{
                                width: 80%;
                                font-size: 24px;
                                margin: 0 auto 10px;
                            }}

                            input[type="submit"] {{
                                width: 80%;
                                padding: 10px;
                                font-size: 24px;
                                background-color: #3498db;
                                color: #ffffff;
                                border: none;
                                border-radius: 5px;
                                cursor: pointer;
                                margin: 0 auto;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    <div style="text-align: left; padding: 10px;">
                        <a href="/" class="back-button">&#9665; Back</a>
                    </div>
                    <h1>Settings Page</h1>

                    <div class="input-container">
                        <form method="post" action="set_temperature_range">
                            <label for="temperature_range">Temperature Range:</label>
                            <br>
                            <input type="number" step="0.1" name="temperature_range" value="{temperature_range_fahrenheit:.1f}">
                            <br>
                            <input type="submit" value="Set">
                        </form>
                    </div>

                    <div class="input-container">
                        <form method="get" action="set_temp_refresh_rate">
                            <label for="temp_refresh_rate">Refresh Rate (seconds):</label>
                            <br>
                            <input type="number" step="1" name="temp_refresh_rate_input" value="{temp_refresh_rate}">
                            <br>
                            <input type="submit" value="Set">
                        </form>
                    </div>

                </body>
                </html>
                """

    @cherrypy.expose
    def set_desired_temperature(self, desired_temperature):
        global desired_temperature_fahrenheit

        # Convert the input to float, ignore errors (e.g., non-numeric input)
        try:
            temp_input = float(desired_temperature)
        except ValueError:
            message = "Invalid temperature! Please enter a valid number."
        else:
            # Check if the desired temperature is within the acceptable range
            if (
                    min_temperature_fahrenheit <= temp_input <= max_temperature_fahrenheit
            ):
                desired_temperature_fahrenheit = temp_input
                message = "Desired temperature updated successfully."
            else:
                message = f"Stop it you PSYCHOPATH! Please enter a temperature within {min_temperature_fahrenheit} and {max_temperature_fahrenheit}."

        raise cherrypy.HTTPRedirect(f'/?message={message}')

    @cherrypy.expose
    def set_temperature_range(self, temperature_range):
        global temperature_range_fahrenheit

        # Convert the input to float, ignore errors (e.g., non-numeric input)
        try:
            range_input = float(temperature_range)
        except ValueError:
            message = "Invalid temperature range! Please enter a valid number."
        else:
            temperature_range_fahrenheit = range_input
            message = "Temperature range updated successfully."

        raise cherrypy.HTTPRedirect(f'/settings?message={message}')

    @cherrypy.expose
    def set_temp_refresh_rate(self, temp_refresh_rate_input):
        global temp_refresh_rate

        # Convert the input to int, ignore errors (e.g., non-numeric input)
        try:
            refresh_rate_input = int(temp_refresh_rate_input)
        except ValueError:
            message = "Invalid refresh rate! Please enter a valid number."
        else:
            temp_refresh_rate = refresh_rate_input
            message = "Refresh rate updated successfully."

        raise cherrypy.HTTPRedirect(f'/settings?message={message}')


def temperature_control_loop():
    while True:
        # Sense a change in temperature every iteration
        time.sleep(temp_refresh_rate)  # Get new temperature every {temp_refresh_rate} seconds
        current_temperature_fahrenheit = temp_sensor.temperature

        # Check if the temperature is below the acceptable range
        if current_temperature_fahrenheit < (desired_temperature_fahrenheit - temperature_range_fahrenheit):
            heater_relay.value = True
            cooler_relay.value = False
            print("Heating: Temperature below desired range")

        # Check if the temperature is above the acceptable range
        elif current_temperature_fahrenheit > (desired_temperature_fahrenheit + temperature_range_fahrenheit):
            heater_relay.value = False
            cooler_relay.value = True
            print("Cooling: Temperature above desired range")

        # Temperature is within acceptable range
        else:
            heater_relay.value = False
            cooler_relay.value = False
            print("Temperature within desired range")


if __name__ == '__main__':
    cherrypy.tree.mount(TemperatureControlApp(), '/')

    # Run the temperature control loop in a separate thread
    import threading

    temperature_thread = threading.Thread(target=temperature_control_loop)
    temperature_thread.start()

    # Start the CherryPy server manually
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()
