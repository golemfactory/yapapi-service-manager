# yapapi-service-manager

## yapapi-service-manager vs yapapi

The official Golem python requestor development library is [yapapi](https://github.com/golemfactory/yapapi).
`yayapi` is used internally in `yapapi-service-manager`, so there's exactly nothing `yayapi-service-manager` can do that is not available in pure `yapapi`.

`yapapi-service-manager` provides a higher-level API for `yapapi`-based services managment. Main features:

* create/destroy services on demand
* persistent wrapper objects that are created before agreement is signed & stay after it was terminated
* most of the interface is `sync` (although this is still an `async` library)

On the other hand, if you need either one of

* batch API (TODO: yayapi docs url)
* efficient way of spawning multiple services in clusters (TODO: yayapi docs url)
* stable backward-compatible API & support

than you should use `yapapi`.

More general, this library should be considered a temporary stage in requestor API development.
In the long term, `yapapi-service-manager` will either be merged into `yapapi` (maybe with serious API changes) or abandoned.


## Examples

1.  Simple service that just prints provider time few times

    ```python3 examples/clock.py```

2.  (some more advanced usage, that includes start() and sending/receiving messages)


3.  Erigon -> custom runtime & http server

## API reference



## Known issues

1. If a service is created when all available providers are busy, it should start when any provider ends the current job and becomes available, but it never starts.
2. If the service fails to start (for whatever reason - e.g. bug in `start()` method (TODO - check)), `ServiceWrapper` will forever stay `started`, but not working.
3. If the provider terminates the agreement (again, for whatever reason - e.g. because our budget run out and we don't accept invoices), this information is not propagated & again we are left with a `started` service that is not working.

Those issues are hard/impossible to fix when using the latest `yapapi`, but we plan to fix them as soon as required improvements are released.
