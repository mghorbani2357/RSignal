import asyncio
import websockets
import configs

async def websocket_receiver(websocket):
    '''
    Messages from sockets are retrieved by this function
    :param websocket: websocket instance
    :return:
    '''
    data = await websocket.recv()
    data = {
        "data": data
    }
    print(data)


start_server = websockets.serve(websocket_receiver, configs.ws_api, configs.ws_port)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()