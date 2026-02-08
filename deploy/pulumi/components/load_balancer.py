"""
Global HTTPS Load Balancer with managed SSL certificate.

Routes ``/api/*`` to the backend Cloud Run service and
everything else to the web frontend Cloud Run service.
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
#  LOAD BALANCER COMPONENT                                                     #
#                                                                              #
################################################################################


class LoadBalancer(pulumi.ComponentResource):
    """
    Global HTTPS Load Balancer with path-based routing.

    Exports:
        ip_address: pulumi.Output[str]  — global static IP
    """

    def __init__(
        self,
        name: str,
        project: str,
        environment: str,
        domain: str,
        backend_service: gcp.cloudrunv2.Service,
        web_service: gcp.cloudrunv2.Service,
        enable_cdn: bool,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:LoadBalancer", name, None, opts)

        logger.info(
            "Creating LoadBalancer component: env=%s, domain=%s, cdn=%s",
            environment,
            domain,
            enable_cdn,
        )

        # ---------------------------------------------------------------------
        # Global static IP
        # ---------------------------------------------------------------------
        self.ip_address = gcp.compute.GlobalAddress(
            f"{name}-ip",
            project=project,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # Serverless NEGs (Network Endpoint Groups)
        # ---------------------------------------------------------------------
        backend_neg = gcp.compute.RegionNetworkEndpointGroup(
            f"{name}-backend-neg",
            project=project,
            region=backend_service.location,
            network_endpoint_type="SERVERLESS",
            cloud_run={"service": backend_service.name},
            opts=pulumi.ResourceOptions(parent=self),
        )

        web_neg = gcp.compute.RegionNetworkEndpointGroup(
            f"{name}-web-neg",
            project=project,
            region=web_service.location,
            network_endpoint_type="SERVERLESS",
            cloud_run={"service": web_service.name},
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # Backend services (GLB concept, not "our" backend)
        # ---------------------------------------------------------------------
        backend_svc = gcp.compute.BackendService(
            f"{name}-backend-svc",
            project=project,
            protocol="HTTP",
            enable_cdn=enable_cdn,
            backends=[{"group": backend_neg.id}],
            opts=pulumi.ResourceOptions(parent=self),
        )

        web_svc = gcp.compute.BackendService(
            f"{name}-web-svc",
            project=project,
            protocol="HTTP",
            enable_cdn=enable_cdn,
            backends=[{"group": web_neg.id}],
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # URL map — path-based routing
        # ---------------------------------------------------------------------
        url_map = gcp.compute.URLMap(
            f"{name}-url-map",
            project=project,
            default_service=web_svc.id,
            host_rules=[
                {
                    "hosts": [domain],
                    "path_matcher": "aam-paths",
                },
            ],
            path_matchers=[
                {
                    "name": "aam-paths",
                    "default_service": web_svc.id,
                    "path_rules": [
                        {
                            "paths": ["/api/*", "/health", "/ready"],
                            "service": backend_svc.id,
                        },
                    ],
                },
            ],
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # Managed SSL certificate
        # ---------------------------------------------------------------------
        ssl_cert = gcp.compute.ManagedSslCertificate(
            f"{name}-ssl",
            project=project,
            managed={"domains": [domain]},
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # HTTPS proxy + forwarding rule
        # ---------------------------------------------------------------------
        https_proxy = gcp.compute.TargetHttpsProxy(
            f"{name}-https-proxy",
            project=project,
            url_map=url_map.id,
            ssl_certificates=[ssl_cert.id],
            opts=pulumi.ResourceOptions(parent=self),
        )

        gcp.compute.GlobalForwardingRule(
            f"{name}-https-fwd",
            project=project,
            target=https_proxy.id,
            port_range="443",
            ip_address=self.ip_address.address,
            load_balancing_scheme="EXTERNAL",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # HTTP → HTTPS redirect
        # ---------------------------------------------------------------------
        redirect_url_map = gcp.compute.URLMap(
            f"{name}-redirect",
            project=project,
            default_url_redirect={
                "https_redirect": True,
                "strip_query": False,
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        http_proxy = gcp.compute.TargetHttpProxy(
            f"{name}-http-proxy",
            project=project,
            url_map=redirect_url_map.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        gcp.compute.GlobalForwardingRule(
            f"{name}-http-fwd",
            project=project,
            target=http_proxy.id,
            port_range="80",
            ip_address=self.ip_address.address,
            load_balancing_scheme="EXTERNAL",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {"ip_address": self.ip_address.address}
        )
