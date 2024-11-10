import asyncio
import cv2
import numpy as np
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw
from mavsdk.camera import Camera

# Marker detection parameters
ARUCO_DICT = cv2.aruco.DICT_4X4_50  # or any other dictionary that fits your markers
ARUCO_PARAMETERS = cv2.aruco.DetectorParameters()

async def run():
    # Connect to the drone
    drone = System()
    await drone.connect(system_address="udp://:14540")

    # Wait for the drone to connect
    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Connected to drone: {state}")
            break

    # Start the camera stream
    print("Starting camera stream...")
    camera = Camera(drone)
    await camera.start_video_stream()

    # Start offboard mode
    print("Starting offboard mode...")
    try:
        await drone.offboard.set_rate_position(2.0)  # Set position control rate in meters per second
    except OffboardError as e:
        print(f"Offboard error: {e}")
        return

    # Arm the drone
    print("Arming the drone...")
    await drone.action.arm()

    # Takeoff to 10 meters altitude
    print("Taking off...")
    await drone.action.takeoff()
    await asyncio.sleep(10)  # Wait for the drone to reach the takeoff altitude

    # Loop for detecting markers and flying
    marker_found = False
    while not marker_found:
        # Grab the camera frame
        frame = await camera.capture_video_frame()

        # Convert the frame to grayscale (needed for ArUco detection)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect ArUco markers
        corners, ids, _ = cv2.aruco.detectMarkers(gray, cv2.aruco.Dictionary_get(ARUCO_DICT), parameters=ARUCO_PARAMETERS)

        if ids is not None:
            print(f"Detected marker with ID {ids}")
            marker_found = True
            # Compute the position of the marker in the camera's frame
            # You can calculate distance, angle, and use it to adjust the drone position
            # For simplicity, assume we just fly to a fixed position
            await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, -2, 0))  # Fly down towards marker
            await asyncio.sleep(5)  # Wait a little at the marker location

    # Land the drone
    print("Landing...")
    await drone.action.land()

    print("Mission complete!")

# Run the mission
loop = asyncio.get_event_loop()
loop.run_until_complete(run())
