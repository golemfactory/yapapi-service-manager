from yapapi import Golem
import asyncio

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Optional, Callable, Awaitable, Any
    from .service_wrapper import ServiceWrapper


class YapapiConnector():
    def __init__(self, executor_cfg: dict, exception_handler: 'Callable[[Exception], Awaitable[Any]]'):
        self.executor_cfg = executor_cfg
        self._exception_handler = exception_handler

        self.command_queue: 'asyncio.Queue' = asyncio.Queue()
        self.run_service_tasks: 'List[asyncio.Task]' = []
        self.executor_task: 'Optional[asyncio.Task]' = None

    def create_instance(self, service_wrapper: 'ServiceWrapper'):
        if self.executor_task is None:
            self.executor_task = asyncio.create_task(self.run())
        self.command_queue.put_nowait(service_wrapper)

    async def stop(self):
        #   Remove all sheduled services from queue and stop Executor task generator
        while not self.command_queue.empty():
            self.command_queue.get_nowait()
        self.command_queue.put_nowait('CLOSE')

        for task in self.run_service_tasks:
            task.cancel()

        if self.executor_task is not None:
            #   NOTE: we're not cancelling the task because we want Golem to exit gracefully (__aexit__)
            #   TODO: is this really necessary?
            await self.executor_task

    async def run(self):
        try:
            await self._run_golem()
        except Exception as e:
            await self._exception_handler(e)

    async def _run_golem(self):
        async with Golem(**self.executor_cfg) as golem:
            subnet_tag = self.executor_cfg.get('subnet_tag', '')
            print(
                f"Using subnet: {subnet_tag}  "
                f"payment driver: {golem.driver}  "
                f"network: {golem.network}\n"
            )
            while True:
                data = await self.command_queue.get()
                if type(data) is str:
                    assert data == 'CLOSE'
                    break
                else:
                    run_service = asyncio.create_task(self._run_service(golem, data))
                    self.run_service_tasks.append(run_service)

    async def _run_service(self, golem: Golem, service_wrapper: 'ServiceWrapper'):
        cluster = await golem.run_service(service_wrapper.service_cls)

        #   TODO: this will change when yapapi issue 372 is fixed
        cluster.instance_start_args = service_wrapper.start_args

        #   TODO: this will be removed when yapapi issue 461 is fixed
        #         (currently the cluster is "fully operable" only after all instances started)
        while not cluster.instances:
            await asyncio.sleep(0.1)

        service_wrapper.cluster = cluster
