import asyncio
import websockets
import configs


async def websocket_sender():
    '''
    Messages are sent on sockets after connections are made by this function
    :return null:
    '''
    async with websockets.connect(configs.ws_api + ":" + str(configs.ws_port)) as websocket:
        await websocket.send("hello")


asyncio.get_event_loop().run_until_complete(test())