import asyncio
import sys
import shlex

from yapapi.payload import vm
from yapapi.services import Service

from service_manager import ServiceManager


class PythonShell(Service):
    @classmethod
    async def get_payload(cls):
        #   This image is created from examples/python-shell/provider/Dockerfile and pushed as described here:
        #   https://handbook.golem.network/requestor-tutorials/convert-a-docker-image-into-a-golem-image
        image_hash = "4c68e8d799acfa105a6b7b3553fcee2afa7f474b7aa4ce6a29f01d9e"
        return await vm.repo(image_hash=image_hash)

    async def start(self):
        print(f"Initializing shell on provider {self.provider_name}, wait for prompt ...")
        self._ctx.run('/bin/sh', '-c', 'nohup python shell.py run &')
        yield self._ctx.commit()
        print("Python shell is ready.")

    async def run(self):
        while True:
            #   Print python shell output
            self._ctx.run('/usr/local/bin/python', 'shell.py', 'read')
            future_results = yield self._ctx.commit()
            result = future_results.result()[-1]
            print(result.stdout, end='', flush=True)

            #   Pass command to shell
            signal = await self._listen()
            cmd = signal.message
            cmd = shlex.quote(cmd)
            self._ctx.run('/bin/sh', '-c', f"echo {cmd} | python shell.py write")
            yield self._ctx.commit()


async def async_stdin_reader():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    return reader


async def run_service(service_manager):
    shell = service_manager.create_service(PythonShell)

    #   TODO
    #   ServiceWrapper should have a "state" property that would use
    #   *   started/stopped on SeviceWrapper
    #   *   service.state
    #   so this would be prettier.
    while not shell.started or not shell.service.state.value == 'running':
        print("Waiting for the service to start")
        await asyncio.sleep(1)

    reader = await async_stdin_reader()
    while True:
        line = await reader.readline()
        line = line.decode()
        shell.service.send_message_nowait(line)


def main():
    executor_cfg = {
        'subnet_tag': 'devnet-beta.2',
        'budget': 1,
    }
    service_manager = ServiceManager(executor_cfg)
    try:
        loop = asyncio.get_event_loop()
        run_service_task = loop.create_task(run_service(service_manager))
        loop.run_until_complete(run_service_task)
    except KeyboardInterrupt:
        shutdown = loop.create_task(service_manager.close())
        loop.run_until_complete(shutdown)
        run_service_task.cancel()


if __name__ == '__main__':
    main()
