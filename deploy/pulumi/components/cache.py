"""
Memorystore (Redis) instance for session and query caching.

Placed on the private VPC so Cloud Run can reach it via VPC connector.
"""

################################################################################
#                                                                              #
#  IMPORTS & DEPENDENCIES                                                      #
#                                                                              #
################################################################################

import logging

import pulumi
import pulumi_gcp as gcp

################################################################################
#                                                                              #
#  LOGGER                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
#  CACHE COMPONENT                                                             #
#                                                                              #
################################################################################


class Cache(pulumi.ComponentResource):
    """
    Memorystore Redis instance.

    Exports:
        instance: gcp.redis.Instance
        host:     pulumi.Output[str]
        port:     pulumi.Output[int]
    """

    def __init__(
        self,
        name: str,
        project: str,
        region: str,
        environment: str,
        network_id: pulumi.Input[str],
        tier: str,
        memory_size_gb: int,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:Cache", name, None, opts)

        logger.info(
            "Creating Cache component: env=%s, tier=%s, memory=%dGB",
            environment,
            tier,
            memory_size_gb,
        )

        self.instance = gcp.redis.Instance(
            f"{name}-redis",
            project=project,
            region=region,
            display_name=f"aam-redis-{environment}",
            tier=tier,
            memory_size_gb=memory_size_gb,
            redis_version="REDIS_7_0",
            authorized_network=network_id,
            auth_enabled=True,
            transit_encryption_mode="SERVER_AUTHENTICATION",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.host = self.instance.host
        self.port = self.instance.port

        self.register_outputs(
            {
                "host": self.host,
                "port": self.port,
            }
        )
