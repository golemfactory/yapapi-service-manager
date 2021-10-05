import asyncio
from typing import TYPE_CHECKING
from functools import wraps

from yapapi import Golem

if TYPE_CHECKING:
    from typing import List, Callable, Awaitable, Any
    from .service_wrapper import ServiceWrapper


def with_exception_handler(f):
    @wraps(f)
    async def wrapped(self, *args, **kwargs):
        try:
            return await f(self, *args, **kwargs)
        except Exception as e:  # pylint: disable=broad-except
            await self.exception_handler(e)
    return wrapped


class YapapiConnector:
    def __init__(self, executor_cfg: dict, exception_handler: 'Callable[[Exception], Awaitable[Any]]'):
        self.golem = Golem(**executor_cfg)
        self.exception_handler = exception_handler
        self.run_service_tasks: 'List[asyncio.Task]' = []

    def create_instance(self, service_wrapper: 'ServiceWrapper'):
        run_service = asyncio.get_event_loop().create_task(self.run_service(service_wrapper))
        self.run_service_tasks.append(run_service)

    async def stop(self):
        for task in self.run_service_tasks:
            task.cancel()

        await self.golem.stop()

    @with_exception_handler
    async def create_network(self, ip: str, **kwargs):
        await self.golem.start()
        return await self.golem.create_network(ip, **kwargs)

    @with_exception_handler
    async def run_service(self, service_wrapper: 'ServiceWrapper'):
        await self.golem.start()
        cluster = await self.golem.run_service(
            service_wrapper.service_cls,
            num_instances=1,
            **service_wrapper.run_service_params,
        )

        service_wrapper.cluster = cluster
