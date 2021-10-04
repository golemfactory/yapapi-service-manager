import asyncio
import sys
import shlex

from yapapi.payload import vm
from yapapi.services import Service

from yapapi_service_manager import ServiceManager


class PythonShell(Service):
    @classmethod
    async def get_payload(cls):
        #   This image is created from examples/python-shell/provider/Dockerfile and pushed as described here:
        #   https://handbook.golem.network/requestor-tutorials/convert-a-docker-image-into-a-golem-image
        image_hash = "4c68e8d799acfa105a6b7b3553fcee2afa7f474b7aa4ce6a29f01d9e"
        return await vm.repo(image_hash=image_hash)

    async def start(self):
        async for script in super().start():
            yield script
        print(f"Initializing shell on provider {self.provider_name}, wait for prompt ...")

        script = self._ctx.new_script()
        script.run('/bin/sh', '-c', 'nohup python shell.py run &')
        yield script

        print("Python shell is ready.")

    async def run(self):
        while True:
            #   Print python shell output
            read_script = self._ctx.new_script()
            run_shell = read_script.run('/usr/local/bin/python', 'shell.py', 'read')
            yield read_script

            print(run_shell.result().stdout, end='', flush=True)

            #   Pass command to shell
            signal = await self._listen()
            cmd = signal.message
            cmd = shlex.quote(cmd)

            write_script = self._ctx.new_script()
            write_script.run('/bin/sh', '-c', f"echo {cmd} | python shell.py write")
            yield write_script


async def async_stdin_reader():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    return reader


async def run_service(service_manager):
    shell = service_manager.create_service(PythonShell)

    while shell.status != 'running':
        print(f"Shell is not running yet. Current state: {shell.status}")
        await asyncio.sleep(1)

    reader = await async_stdin_reader()
    while True:
        line = await reader.readline()
        line = line.decode()
        shell.service.send_message_nowait(line)


def main():
    executor_cfg = {
        'subnet_tag': 'devnet-beta',
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
