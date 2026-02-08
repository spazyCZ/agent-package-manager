"""
Cloud Run service for the AAM React web frontend.

Serves the production-built SPA via an Nginx container.
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
#  WEB SERVICE COMPONENT                                                       #
#                                                                              #
################################################################################


class WebService(pulumi.ComponentResource):
    """
    Cloud Run service for the React SPA frontend.

    Exports:
        service: gcp.cloudrunv2.Service
        url:     pulumi.Output[str]
    """

    def __init__(
        self,
        name: str,
        project: str,
        region: str,
        environment: str,
        image: str,
        cpu: str,
        memory: str,
        min_instances: int,
        max_instances: int,
        backend_url: pulumi.Input[str],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:WebService", name, None, opts)

        logger.info(
            "Creating WebService component: env=%s, image=%s",
            environment,
            image,
        )

        self.service = gcp.cloudrunv2.Service(
            f"{name}-web",
            project=project,
            location=region,
            ingress="INGRESS_TRAFFIC_ALL",
            template={
                "scaling": {
                    "min_instance_count": min_instances,
                    "max_instance_count": max_instances,
                },
                "containers": [
                    {
                        "image": image,
                        "resources": {
                            "limits": {
                                "cpu": cpu,
                                "memory": memory,
                            },
                        },
                        "ports": [{"container_port": 80}],
                        "envs": [
                            {
                                "name": "VITE_API_URL",
                                "value": backend_url,
                            },
                        ],
                        "startup_probe": {
                            "http_get": {
                                "path": "/health",
                                "port": 80,
                            },
                            "initial_delay_seconds": 3,
                            "period_seconds": 5,
                            "failure_threshold": 3,
                        },
                    },
                ],
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.url = self.service.uri

        # Allow unauthenticated access (public website)
        gcp.cloudrunv2.ServiceIamMember(
            f"{name}-web-public",
            project=project,
            location=region,
            name=self.service.name,
            role="roles/run.invoker",
            member="allUsers",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs({"url": self.url})
