# yapapi-service-manager

Helper tool for management of [Golem](https://handbook.golem.network/)-based services.

## yapapi-service-manager vs yapapi

The official Golem python requestor development library is [yapapi](https://github.com/golemfactory/yapapi).
`yayapi` is used internally in `yapapi-service-manager`, so there's exactly nothing this library can do that is not available in pure `yapapi`.

`yapapi-service-manager` provides a higher-level services API than `yapapi`. Main features:

* create/destroy services on demand
* persistent wrapper objects that are created before agreement is signed & stay after it was terminated
* most of the interface is `sync` (although this is still an `async` library that will not work when called in non-async context)

On the other hand, if you need either one of

* batch API (TODO: yayapi docs url)
* efficient way of spawning multiple services in clusters (TODO: yayapi docs url)
* stable backward-compatible API & support

than you should use `yapapi`.

Note: this library changes the way services are *managed*, but the way they are *defined* is exactly the same as in `yapapi`.

More general, this library should be considered a temporary stage in requestor API development.
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

* custom runtime (TODO: runtime docs url)
* `yapapi-service-manager` integrated with [Quart](https://pgjones.gitlab.io/quart/) http server
    

## Quickstart


```python
#   Initialize the ServiceManager. You should never have more than one active ServiceManager.
service_manager = ServiceManager(
    # Dictionary with yapapi.Executor config (TODO: link yayapi executor config docs)
    executor_cfg,  
    
    # Handler function executed when yapapi.Executor raises an exception
    # Default handler just stops the current event loop
    golem_exception_handler=service_manager.stop_on_golem_exception,
    
    log_file='log.log',
)

#   Request service creation. From yapapi POV, this creates a single-instance cluster.
#   (TODO: link to yapapi docs)
service_wrapper = service_manager.create_service(
    # Service implementation, class inheriting from yapapi.services.Service
    service_cls,
    
    # Arguments that will be passed to the runtime start.
    # This currenly makes sense only for self-contained runtimes --> Erigon example
    start_args=[],

    # Class inheriting from service_manager.ServiceWrapper, type of the object
    # returned by this function. Sample usage --> Erigon example
    service_wrapper_cls=service_manager.ServiceWrapper,
)

service_wrapper.stop()   # Stop the service. This terminates the agreement.
service_wrapper.started  # True -> we've signed an agreement -> service starts (or started)
service_wrapper.stopped  # True -> something stopped our service_wrapper -> it's not running
service_wrapper.service  # Instance of service_cls

await service_manager.close()  # Close the Executor, stop all Golem-related work
```

## Known issues

1. If a service is created when all providers are busy, it should start when any provider ends the current job and becomes available, but it never starts.
2. If the service fails to start (for whatever reason - e.g. bug in `start()` method (TODO - check)), `ServiceWrapper` will forever stay `started`, but not working.
3. If the provider terminates the agreement (again, for whatever reason - e.g. because our budget run out and we don't accept invoices), this information is not propagated & again we are left with a `started` service that is not working.

Those issues are hard to fix with the latest `yapapi` but we plan to fix them as soon as required improvements are released.
