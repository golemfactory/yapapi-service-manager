# yapapi-service-manager

Helper tool for management of [Golem](https://handbook.golem.network/)-based services.

Installation:

```
$ pip3 install git+https://github.com/golemfactory/yapapi-service-manager.git
```

## yapapi-service-manager vs yapapi

The official Golem requestor agent library for Python is [yapapi](https://github.com/golemfactory/yapapi).
`yayapi` is used internally in `yapapi-service-manager`, so there's exactly nothing this library can do that is not available in pure `yapapi`.

`yapapi-service-manager` provides a higher-level services API than `yapapi`. Main features:

* create/destroy services on demand
* service wrapper objects that are created before agreement is signed & stay after it was terminated
* fire-and-forget methods with synchronous interface (although this is still an `async` library that will not work when called in non-async context)

There are a lot of features available in `yapapi` but not in `yapapi-service-manager`. 
If you need either one of:

* [task API](https://handbook.golem.network/requestor-tutorials/task-processing-development)
* efficient way of spawning multiple services in [clusters](https://handbook.golem.network/yapapi/api-reference#cluster-objects)
* stable backward-compatible API & support

then, you should use pure `yapapi`.

Note: This library changes the way services are *managed*, but the way they are *defined* is exactly the same as in `yapapi`.

More generally, this library should be considered a temporary stage in requestor API development.
In the long term, `yapapi-service-manager` will either be merged into `yapapi` (with possible serious API changes) or abandoned.


## Examples

1. Simple service that just prints provider time few times. This is pretty useless, just demonstrates the base usage.


```
$ python3 examples/clock.py
```

2. "Standard" interactive python console, but running on a provider machine.
   

```
$ python3 examples/python_shell.py
```

3.  More complex usage: [Erigon](https://github.com/golemfactory/yagna-service-erigon). Features:

* custom runtime
* integration with [Quart](https://pgjones.gitlab.io/quart/) http server

Detailed description of this example is in the [Golem handbook](https://handbook.golem.network/requestor-tutorials/service-development/service-example-2-erigon).
    

## Quickstart


```python
from yapapi_service_manager import ServiceManager

#   Initialize the ServiceManager. You should never have more than one active ServiceManager.
service_manager = ServiceManager(
    # Dictionary with yapapi.Golem config (https://handbook.golem.network/yapapi/api-reference#_engine-objects)
    executor_cfg,  
    
    # Handler function executed when yapapi.Executor raises an exception
    # Default handler just stops the current event loop
    golem_exception_handler=yapapi_service_manager.stop_on_golem_exception,
    
    log_file='log.log',
)

#   Request service creation. From the yapapi POV, this is equivalent to
#   https://handbook.golem.network/yapapi/api-reference#run_service (with num_instances = 1)
service_wrapper = service_manager.create_service(
    # Service implementation, class inheriting from yapapi.services.Service
    service_cls,
    
    # Arguments that will be passed to the runtime start.
    # This currenly makes sense only for custom runtimes --> Erigon example
    start_args=[],

    # Factory function returning instance of yapapi_service_manager.ServiceWrapper
    # Sample usage --> Erigon example
    service_wrapper_factory=yapapi_service_manager.ServiceWrapper,
)

service_wrapper.stop()   # Stop the service. This terminates the agreement.
service_wrapper.status   # pending -> starting -> running -> stopping -> stopped
                         # (also possible-but-not-expected: unresponsive and failed)
service_wrapper.service  # Instance of service_cls

await service_manager.close()  # Close the Executor, stop all Golem-related work
```

## Known issues

1. If a new service is requested (i.e. an instance of ServiceWrapper is created) when all providers are busy, it should start when any provider ends the current job and becomes available, but it never starts.
2. If the service fails to start (for whatever reason - e.g. bug in `start()` method), `ServiceWrapper` will forever stay `started`, but not working.
3. If the provider terminates the agreement (again, for whatever reason - e.g. because our budget runs out and we stop accepting invoices), this information is not propagated & we are left with a `running` service that is not working.

Those issues are hard to fix outside of `yapapi` so we plan to have them addressed as soon as required improvements in `yapapi` are released.
