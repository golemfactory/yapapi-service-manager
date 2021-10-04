import asyncio

from yapapi.payload import vm
from yapapi.services import Service

from yapapi_service_manager import ServiceManager


class ProviderClock(Service):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_executed_cnt = 0

    @classmethod
    async def get_payload(cls):
        #   This image was built from a minimal linux: https://hub.docker.com/_/alpine
        #   (all we need is /bin/date)
        image_hash = "badec819d8b00cee2419abed154d4b036d8f66f3e0c040ff22d52b03"
        return await vm.repo(image_hash=image_hash)

    async def run(self):
        while True:
            #   Q: If we want the datetime, why not just use standard datetime library?
            #   A: Because this python code is running on the **requestor** machine. To execute anything on the
            #      provider, we need script.run(). That's a really important distinction.
            script = self._ctx.new_script()
            run_date = script.run('/bin/date')
            yield script

            date_time = run_date.result().stdout.strip()
            print(f"My name is {self.provider_name} and my time is {date_time}")

            self.command_executed_cnt += 1
            await asyncio.sleep(1)


async def run_service(service_manager):
    clock = service_manager.create_service(ProviderClock)

    while clock.status == 'pending':
        print("Looking for a provider")
        await asyncio.sleep(1)

    print("Hey provider, what's the time?")
    while clock.service.command_executed_cnt < 3:
        await asyncio.sleep(1)

    print("OK, that's enough, thanks buddy")
    clock.stop()

    await service_manager.close()


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
