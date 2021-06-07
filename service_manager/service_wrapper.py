import uuid

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Type
    from yapapi.executor.services import Service


class ServiceWrapper():
    def __init__(self, service_cls: 'Type[Service]'):
        self.service_cls = service_cls
        self.id = self._create_id()
        self.stopped = False
        self._service = None

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, service):
        if not isinstance(service, self.service_cls):
            raise ValueError(f"This wrapper expects service to be a {self.service_cls.__name__}")
        self._service = service

    @property
    def started(self):
        return self.service is not None

    async def stop(self):
        if self.stopped:
            return
        self.stopped = True
        print(f"STOPPING {self}")

        if self.started:
            #   TODO: stop using a private field
            self.service._cluster.stop()

    async def run_single_command(self, cmd: str):
        self.service.send_message_nowait(cmd)
        service_signal = await self.service.receive_message()
        #   TODO: how do we check if we got response for the signal sent?
        #         this is irrelevant now, but could be useful in the future
        return service_signal.message

    def _create_id(self):
        return uuid.uuid4().hex

    def __repr__(self):
        name = self.service_cls.__name__
        return f"{name}[id={self.id}]"
