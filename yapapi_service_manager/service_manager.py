import asyncio
from functools import partial
from typing import TYPE_CHECKING

from yapapi.log import enable_default_logger

from .service_wrapper import ServiceWrapper
from .yapapi_connector import YapapiConnector

if TYPE_CHECKING:
    from typing import Type, List, Tuple, Callable, Awaitable, Any, Optional
    from yapapi.services import Service
    from yapapi.network import Network


async def stop_on_golem_exception(_service_manager: 'ServiceManager', e: Exception) -> None:
    print("GOLEM FAILED\n", e)
    print("STOPPING THE LOOP")
    loop = asyncio.get_event_loop()
    loop.stop()


class ServiceManager:
    def __init__(
        self,
        executor_cfg: dict,
        golem_exception_handler: 'Callable[[ServiceManager, Exception], Awaitable[Any]]' = stop_on_golem_exception,
        log_file: str = 'log.log'
    ):
        enable_default_logger(log_file=log_file)

        self.service_wrappers: 'List[ServiceWrapper]' = []
        exception_handler = partial(golem_exception_handler, self)
        self.yapapi_connector = YapapiConnector(executor_cfg, exception_handler)

    def create_service(
        self,
        service_cls: 'Type[Service]',
        start_args: 'Tuple' = (),
        service_wrapper_factory: 'Callable[[Type[Service], Tuple], ServiceWrapper]' = ServiceWrapper,
        network: 'Optional[Network]' = None
    ) -> ServiceWrapper:
        service_wrapper = service_wrapper_factory(service_cls, start_args)
        service_wrapper.network = network
        self.yapapi_connector.create_instance(service_wrapper)
        self.service_wrappers.append(service_wrapper)
        return service_wrapper

    async def create_network(self, ip: str, **kwargs):
        return await self.yapapi_connector.create_network(ip, **kwargs)

    async def close(self):
        for service_wrapper in self.service_wrappers:
            service_wrapper.stop()
        await self.yapapi_connector.stop()
