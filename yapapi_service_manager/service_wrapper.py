import uuid

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Type, Optional
    from yapapi.services import Service, Cluster


class ServiceWrapper:
    def __init__(self, service_cls: 'Type[Service]'):
        self.service_cls = service_cls
        self.id = self._create_id()
        self.stopped = False
        self._cluster: 'Optional[Cluster]' = None
        self.run_service_params: dict = {}

    @property
    def status(self):
        if self.service is not None:
            service_state = self.service.state.value
            if service_state == 'terminated':
                if self.stopped:  # pylint: disable=no-else-return
                    return 'stopped'
                else:
                    return 'failed'
            else:
                return service_state
        else:
            if self.stopped:  # pylint: disable=no-else-return
                return 'stopped'
            else:
                return 'pending'

    @property
    def cluster(self):
        return self._cluster

    @cluster.setter
    def cluster(self, cluster: 'Cluster'):
        #   TODO: change to a public attribute when it is available in yapapi
        #         (this is already requested, issue 459)
        cluster_srv_cls = cluster._service_class  # pylint: disable=protected-access
        if cluster_srv_cls != self.service_cls:
            raise ValueError(f"Expected: {self.service_cls.__name__}, got {cluster_srv_cls.__name__}")

        if self.stopped:
            #   This is a very-rare-but-possible situation when we got stopped before the cluster
            #   was created --> cluster has to be stopped as well
            cluster.stop()

        self._cluster = cluster

    @property
    def service(self):
        if self._cluster and self._cluster.instances:
            return self._cluster.instances[0]
        return None

    def stop(self):
        if self.stopped:
            return
        self.stopped = True
        print(f"STOPPING {self}")

        if self.cluster is not None:
            self.cluster.stop()

    @staticmethod
    def _create_id() -> str:
        return uuid.uuid4().hex

    def __repr__(self):
        name = self.service_cls.__name__
        return f"{name}[id={self.id}]"
