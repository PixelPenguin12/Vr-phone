import asyncio
import websockets
import pyautogui
import base64
from io import BytesIO

out = BytesIO()

async def capture_and_send(websocket, path):
    while True:
        screenshot = pyautogui.screenshot()

        screenshot.save(out, format='JPEG')

        encoded_image = base64.b64encode(out.getvalue()).decode('utf-8')
        

        await websocket.send(encoded_image)

start_server = websockets.serve(capture_and_send, "192.168.1.122", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()