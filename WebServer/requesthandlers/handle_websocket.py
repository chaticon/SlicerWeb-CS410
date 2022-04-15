from typing import Union, Optional, Awaitable

from tornado.websocket import WebSocketHandler


class SlicerWebSocketHandler(WebSocketHandler):
    def open(self, *args: str, **kwargs: str) -> Optional[Awaitable[None]]:
        return super().open(*args, **kwargs)

    def on_close(self) -> None:
        super().on_close()

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        pass