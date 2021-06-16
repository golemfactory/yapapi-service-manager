import asyncio

from yapapi.payload import vm
from yapapi.services import Service

from service_manager import ServiceManager


class PythonShell(Service):
    @classmethod
    async def get_payload(cls):
        #   This image is based on examples/python-shell/provider/Dockerfile
        #   created & pushed the way described in docs:
        #   https://handbook.golem.network/requestor-tutorials/hello-world#building-and-publishing-the-image
        image_hash = "4c68e8d799acfa105a6b7b3553fcee2afa7f474b7aa4ce6a29f01d9e"
        return await vm.repo(image_hash=image_hash)

    async def start(self):
        self._ctx.run('/bin/sh', '-c', 'nohup python shell.py run &')
        yield self._ctx.commit()

    async def run(self):
        print("RUNNING")

        while True:
            self._ctx.run('/bin/sh', '-c', "echo 'x=1' | python shell.py write")
            self._ctx.run('/usr/local/bin/python', 'shell.py', 'read')
            self._ctx.run('/bin/sh', '-c', "echo 'y=2' | python shell.py write")
            self._ctx.run('/usr/local/bin/python', 'shell.py', 'read')
            self._ctx.run('/bin/sh', '-c', "echo 'x+y' | python shell.py write")
            self._ctx.run('/usr/local/bin/python', 'shell.py', 'read')
            future_result = yield self._ctx.commit()
            all_results = future_result.result()
            this_result = all_results[-1]
            print(this_result.stdout)


async def main(service_manager):
    shell = service_manager.create_service(PythonShell)

    while not shell.started:
        print("Waiting for the service to start")
        await asyncio.sleep(1)

    print("Shell starts")
    await asyncio.Future()


if __name__ == '__main__':
    executor_cfg = {
        'subnet_tag': 'devnet-beta.2',
        'budget': 1,
    }
    service_manager = ServiceManager(executor_cfg)
    try:
        loop = asyncio.get_event_loop()
        main_task = loop.create_task(main(service_manager))
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:
        shutdown = loop.create_task(service_manager.close())
        loop.run_until_complete(shutdown)
        main_task.cancel()
