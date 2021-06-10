import asyncio

from yapapi.payload import vm
from yapapi.services import Service

from service_manager import ServiceManager


class ProviderClock(Service):
    @classmethod
    async def get_payload(cls):
        #   We use a "standard" yapapi blender image (because every provider has it downloaded)
        #   Could be any other working image, because this Service does exactly nothing.
        image_hash = "9a3b5d67b0b27746283cb5f287c13eab1beaa12d92a9f536b747c7ae"
        return await vm.repo(image_hash=image_hash)

    async def run(self):
        while True:
            #   Q: If we want the datetime, Why not just use standard datetime library?
            #   A: Because python is running on the **requestor** machine. Data is extracted from provider only
            #      by means of self._ctx. That's a really important distinction.
            self._ctx.run('/bin/date')
            future_result = yield self._ctx.commit()
            all_results = future_result.result()

            #   all_results might contain also results of deploy() and start() operations (for the first iteration)
            #   but this particular operation is always last
            this_result = all_results[-1]

            print("My time is", this_result.stdout)
            await asyncio.sleep(1)


async def main(service_manager):
    clock = service_manager.create_service(ProviderClock)

    while not clock.started:
        print("Waiting for the service to start")
        await asyncio.sleep(1)

    print("Hey provider, what's the time?")
    await asyncio.sleep(10)
    print("OK, that's enough, thanks buddy")
    await clock.stop()
    await service_manager.close()


if __name__ == '__main__':
    service_manager = ServiceManager()
    try:
        loop = asyncio.get_event_loop()
        main_task = loop.create_task(main(service_manager))
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:
        shutdown = loop.create_task(service_manager.close())
        loop.run_until_complete(shutdown)
        main_task.cancel()
