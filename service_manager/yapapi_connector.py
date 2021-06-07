from yapapi.executor import Golem
import asyncio

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .service_wrapper import ServiceWrapper


class YapapiConnector():
    def __init__(self, executor_cfg: dict):
        self.executor_cfg = executor_cfg

        self.command_queue = asyncio.Queue()
        self.run_service_tasks = []
        self.executor_task = None

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

        await self.executor_task

    async def run(self):
        async with Golem(**self.executor_cfg) as golem:
            print(
                f"Using subnet: {self.executor_cfg['subnet_tag']}  "
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
        while not cluster.instances:
            await asyncio.sleep(0.1)
        service_wrapper.service = cluster.instances[0]
