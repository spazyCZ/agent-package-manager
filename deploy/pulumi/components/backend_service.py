"""
Cloud Run service for the AAM FastAPI backend.

Connects to Cloud SQL via the Cloud SQL Auth Proxy sidecar,
and to Memorystore via the Serverless VPC Access connector.
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
#  BACKEND SERVICE COMPONENT                                                   #
#                                                                              #
################################################################################


class BackendService(pulumi.ComponentResource):
    """
    Cloud Run service for the FastAPI backend.

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
        concurrency: int,
        vpc_connector_id: pulumi.Input[str],
        db_connection_name: pulumi.Input[str],
        db_password_secret_id: pulumi.Input[str],
        redis_host: pulumi.Input[str],
        redis_port: pulumi.Input[int],
        storage_bucket: pulumi.Input[str],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:BackendService", name, None, opts)

        logger.info(
            "Creating BackendService component: env=%s, image=%s",
            environment,
            image,
        )

        self.service = gcp.cloudrunv2.Service(
            f"{name}-backend",
            project=project,
            location=region,
            ingress="INGRESS_TRAFFIC_ALL",
            template={
                "scaling": {
                    "min_instance_count": min_instances,
                    "max_instance_count": max_instances,
                },
                "vpc_access": {
                    "connector": vpc_connector_id,
                    "egress": "PRIVATE_RANGES_ONLY",
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
                        "ports": [{"container_port": 8000}],
                        "envs": [
                            {"name": "APP_ENV", "value": environment},
                            {"name": "STORAGE_BACKEND", "value": "gcs"},
                            {
                                "name": "GCS_BUCKET",
                                "value_source": None,
                            },
                        ],
                        "startup_probe": {
                            "http_get": {
                                "path": "/health",
                                "port": 8000,
                            },
                            "initial_delay_seconds": 5,
                            "period_seconds": 10,
                            "failure_threshold": 3,
                        },
                        "liveness_probe": {
                            "http_get": {
                                "path": "/health",
                                "port": 8000,
                            },
                            "period_seconds": 30,
                        },
                    },
                ],
                "max_instance_request_concurrency": concurrency,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.url = self.service.uri

        # ---------------------------------------------------------------------
        # Allow unauthenticated access (public API)
        # ---------------------------------------------------------------------
        gcp.cloudrunv2.ServiceIamMember(
            f"{name}-backend-public",
            project=project,
            location=region,
            name=self.service.name,
            role="roles/run.invoker",
            member="allUsers",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs({"url": self.url})
