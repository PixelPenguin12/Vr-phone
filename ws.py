import websocket
import json
import pyvjoy
import math

# Initialize variables
beta = 0.05

# Initialize quaternion components
q0 = 1.0
q1 = 0.0
q2 = 0.0
q3 = 0.0

def on_message(ws, message):
    global q0, q1, q2, q3

    # Parse sensor data from the message
    sensor_data = json.loads(message)
    sensor_type = sensor_data['type']
    values = sensor_data['values']

    # If gyroscope data
    if sensor_type == 'android.sensor.gyroscope':
        gyro_x = math.radians(values[0])  # Convert degrees to radians
        gyro_y = math.radians(values[1])
        gyro_z = math.radians(values[2])

        # Compute rate of change of quaternion
        qDot1 = 0.5 * (-q1 * gyro_x - q2 * gyro_y - q3 * gyro_z)
        qDot2 = 0.5 * (q0 * gyro_x + q2 * gyro_z - q3 * gyro_y)
        qDot3 = 0.5 * (q0 * gyro_y - q1 * gyro_z + q3 * gyro_x)
        qDot4 = 0.5 * (q0 * gyro_z + q1 * gyro_y - q2 * gyro_x)

        # Integrate to yield quaternion
        q0 += qDot1
        q1 += qDot2
        q2 += qDot3
        q3 += qDot4

    # If magnetometer data
    elif sensor_type == 'android.sensor.magnetic_field':
        mag_x = values[0]
        mag_y = values[1]
        mag_z = values[2]

        # Normalize magnetometer data
        mag_norm = math.sqrt(mag_x * mag_x + mag_y * mag_y + mag_z * mag_z)
        if mag_norm != 0:
            mag_x /= mag_norm
            mag_y /= mag_norm
            mag_z /= mag_norm

        # Compute error between estimated direction and measured direction of magnetic field
        hx = 2 * mag_x * (0.5 - q2 * q2 - q3 * q3) + 2 * mag_y * (q1 * q2 - q0 * q3) + 2 * mag_z * (q1 * q3 + q0 * q2)
        hy = 2 * mag_x * (q1 * q2 + q0 * q3) + 2 * mag_y * (0.5 - q1 * q1 - q3 * q3) + 2 * mag_z * (q2 * q3 - q0 * q1)
        bx = math.sqrt(hx * hx + hy * hy)
        bz = 2 * mag_x * (q1 * q3 - q0 * q2) + 2 * mag_y * (q2 * q3 + q0 * q1) + 2 * mag_z * (0.5 - q1 * q1 - q2 * q2)

        # Compute gradient descent step
        s0 = -2 * q2
        s1 = 2 * q3
        s2 = -2 * q0
        s3 = 2 * q1
        j0 = s1 * hx - s3 * bz
        j1 = s0 * hx + s2 * bz
        j2 = s0 * hy - 2 * s1 * bx + s2 * bz
        j3 = -2 * s0 * bx - s1 * hy

        # Normalize gradient
        norm = math.sqrt(j0 * j0 + j1 * j1 + j2 * j2 + j3 * j3)
        if norm != 0:
            j0 /= norm
            j1 /= norm
            j2 /= norm
            j3 /= norm

        # Compute rate of change of quaternion using magnetometer data
        qDot1 = -beta * j0
        qDot2 = -beta * j1
        qDot3 = -beta * j2
        qDot4 = -beta * j3

        # Integrate to yield quaternion
        q0 += qDot1
        q1 += qDot2
        q2 += qDot3
        q3 += qDot4

    print(f"{math.radians(q0):.5}\t{math.radians(q1):.5}\t{math.radians(q2):.5}\t{math.radians(q3):.5}")

    # Compute Euler angles
    roll = math.atan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 * q1 + q2 * q2))
    pitch = math.asin(max(-1, min(1, 2 * (q0 * q2 - q3 * q1)))) # Ensure asin argument is in range [-1, 1]
    yaw = math.atan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (q2 * q2 + q3 * q3))

    # Apply rotation (e.g., to control a virtual joystick)
    simulate_joystick(roll, pitch, yaw)

def on_error(ws, error):
    print("Error occurred:", error)

def on_close(ws):
    print("Connection closed")

def on_open(ws):
    print("Connected")

def connect(url):
    ws = websocket.WebSocketApp(url,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()

def simulate_joystick(roll, pitch, yaw):
    # Create a virtual joystick
    joystick = pyvjoy.VJoyDevice(1)

    # Map roll, pitch, and yaw angles to joystick range
    roll_mapped = int((roll + math.pi) * (32767 / (2 * math.pi)))
    pitch_mapped = int((pitch + math.pi / 2) * (32767 / math.pi))
    yaw_mapped = int((yaw + math.pi) * (32767 / (2 * math.pi)))

    # Update the virtual joystick position
    joystick.set_axis(pyvjoy.HID_USAGE_X, int(roll * 10000))
    joystick.set_axis(pyvjoy.HID_USAGE_Y, int(pitch * 10000))
    joystick.set_axis(pyvjoy.HID_USAGE_Z, int(yaw * 10000))
    #print(f"Roll: {roll:.5}\tPitch: {pitch:.5}\tYaw: {yaw:.5}")

connect("ws://192.168.1.122:2415/sensors/connect?types=[\"android.sensor.gyroscope\",\"android.sensor.magnetic_field\"]")
