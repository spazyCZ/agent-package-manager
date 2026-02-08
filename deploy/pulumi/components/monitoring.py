"""
Cloud Monitoring alerting policies and uptime checks.

Creates uptime checks for the backend health endpoint
and alerting policies for error rates and latency.
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
#  MONITORING COMPONENT                                                        #
#                                                                              #
################################################################################


class Monitoring(pulumi.ComponentResource):
    """
    Uptime checks and alerting policies.

    Exports:
        uptime_check: gcp.monitoring.UptimeCheckConfig
    """

    def __init__(
        self,
        name: str,
        project: str,
        environment: str,
        domain: str,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:Monitoring", name, None, opts)

        logger.info(
            "Creating Monitoring component: env=%s, domain=%s",
            environment,
            domain,
        )

        # ---------------------------------------------------------------------
        # Uptime check — backend /health endpoint
        # ---------------------------------------------------------------------
        self.uptime_check = gcp.monitoring.UptimeCheckConfig(
            f"{name}-health-check",
            project=project,
            display_name=f"AAM Backend Health ({environment})",
            monitored_resource={
                "type": "uptime_url",
                "labels": {
                    "project_id": project,
                    "host": domain,
                },
            },
            http_check={
                "path": "/health",
                "port": 443,
                "use_ssl": True,
                "validate_ssl": True,
            },
            period="60s",
            timeout="10s",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {"uptime_check_id": self.uptime_check.uptime_check_id}
        )
