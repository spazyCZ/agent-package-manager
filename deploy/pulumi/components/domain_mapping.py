"""
Cloud Run domain mappings with managed SSL certificates.

Maps custom domains directly to Cloud Run services, eliminating the need
for a Global HTTPS Load Balancer.  Google provisions and renews SSL
certificates automatically.

DNS setup (per domain):
    CNAME  <domain>  →  ghs.googlehosted.com.
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
#  DOMAIN MAPPING COMPONENT                                                    #
#                                                                              #
################################################################################


class DomainMapping(pulumi.ComponentResource):
    """
    Create Cloud Run domain mappings for one or more custom domains.

    Each mapping provisions a Google-managed SSL certificate and routes
    HTTPS traffic directly to the target Cloud Run service — no load
    balancer required.

    Args:
        name:     Resource name prefix.
        project:  GCP project ID.
        region:   Cloud Run region (e.g. ``us-central1``).
        services: Dict mapping custom domain → Cloud Run service.
                  Example: ``{"test.aamregistry.io": web_service}``

    DNS requirement (manual step per domain):
        Create a CNAME record pointing the domain to ``ghs.googlehosted.com.``
    """

    def __init__(
        self,
        name: str,
        project: str,
        region: str,
        services: dict[str, gcp.cloudrunv2.Service],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:DomainMapping", name, None, opts)

        logger.info(
            "Creating DomainMapping component: domains=%s",
            list(services.keys()),
        )

        self.mappings: list[gcp.cloudrun.DomainMapping] = []

        for domain, service in services.items():
            # -----------------------------------------------------------------
            # Derive a safe resource name from the domain
            # -----------------------------------------------------------------
            safe_name = domain.replace(".", "-")

            logger.info(
                "Mapping domain %s → Cloud Run service",
                domain,
            )

            mapping = gcp.cloudrun.DomainMapping(
                f"{name}-dm-{safe_name}",
                project=project,
                location=region,
                name=domain,
                metadata={
                    "namespace": project,
                },
                spec={
                    "route_name": service.name,
                },
                opts=pulumi.ResourceOptions(parent=self),
            )

            self.mappings.append(mapping)

        self.register_outputs(
            {"domains": [d for d in services.keys()]}
        )
