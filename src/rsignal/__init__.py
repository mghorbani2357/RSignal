import asyncio
import datetime
import json
import logging
import traceback
import uuid
from contextlib import suppress

import websockets


class RSignalServer(object):
    logger = logging.getLogger('websockets')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(logging.FileHandler('/var/log/rsignal/rsignal-plain.log'))
    signals = dict()

    def __init__(self, address, port):
        """
            Args:
                address(str): Listening host address.
                port(int): Listening port.
        """

        self.start_server = websockets.serve(self.listen, address, port, ping_interval=None)

    async def listen(self, websocket, path):
        """
            Args:
                websocket(websockets.client.WebSocketClientProtocol): Full duplex websocket channel.
                path(str): Incoming websocket path.
        """

        channel_id = str(uuid.uuid4())

        self.logger.info(f'{str(datetime.datetime.now())} [INFO] [RSignal.Channel.Opening]: ' + json.dumps({
            "remote_address": websocket.remote_address[0],
            "port": websocket.remote_address[1],
            "path": path,
            "channel_id": channel_id,
        }))

        # region Validation

        try:
            side, signal_id = path.split('/')[1:3]
            if side not in ('publisher', 'subscriber'):
                raise ValueError
        except ValueError:
            self.logger.info(f'{str(datetime.datetime.now())} [INFO] [RSignal.Channel.Validating] Invalid path: ' + json.dumps({
                "channel_id": channel_id,
                "exception": str(traceback.format_exc()),
            }))

            await websocket.send(json.dumps({
                "status": "failed",
                "description": f"Invalid Path: {path}"
            }))
            websocket.close()
            return

        # endregion

        signal = self.signals.get(signal_id, {
            "publishers": list(),
            "subscribers": list()
        })

        match side:
            case 'publisher':
                signal["publishers"].append(websocket)
                self.signals.update({signal_id: signal})
                await self.delegate_signal(websocket, signal_id)
            case 'subscriber':
                signal["subscribers"].append(websocket)
                self.signals.update({signal_id: signal})

    async def delegate_signal(self, websocket, signal_id):
        while websocket.open:
            try:
                message = await websocket.recv()

                self.logger.debug(
                    f'{str(datetime.datetime.now())} [DEBUG] [RSignal.Delegate.SignalReceived] '
                    f'Message received: ' + json.dumps({
                        "status": "failed",
                        "description": message
                    })
                )

                for subscriber in self.signals.get(signal_id).get('subscribers'):
                    try:
                        await subscriber.send(message)

                    except websockets.WebSocketException:
                        self.logger.error(
                            f'{str(datetime.datetime.now())} [ERROR] [RSignal.Delegate.Subscriber] '
                            f'Failed to send message: ' + json.dumps({
                                "status": "failed",
                                "description": str(traceback.format_exc())
                            })
                        )
                        with suppress(Exception):
                            self.signals[signal_id]['subscribers'].remove(subscriber)

                self.logger.info(
                    f'{str(datetime.datetime.now())} [INFO] [RSignal.Delegate.SignalRaised] '
                    f'Signal successfully published: ' + json.dumps({
                        "status": "ok",
                        "description": None
                    })
                )

            except websockets.WebSocketException:
                self.logger.error(
                    f'{str(datetime.datetime.now())} [ERROR] [RSignal.Delegate.Publisher] '
                    f'Receiving message failed: ' + json.dumps({
                        "status": "failed",
                        "description": str(traceback.format_exc())
                    }))
                with suppress(Exception):
                    self.signals[signal_id]['publishers'].remove(websocket)

    def run(self):
        asyncio.get_event_loop().run_until_complete(self.start_server)
        asyncio.get_event_loop().run_forever()
