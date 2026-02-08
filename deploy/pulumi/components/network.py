"""
VPC network, subnets, and VPC connectors for Cloud Run.

Creates a custom VPC with a private services subnet and a
Serverless VPC Access connector so Cloud Run can reach
Cloud SQL and Memorystore over private IP.
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
#  NETWORK COMPONENT                                                           #
#                                                                              #
################################################################################


class Network(pulumi.ComponentResource):
    """
    VPC network with private services subnet and VPC connector.

    Exports:
        network:       gcp.compute.Network
        subnet:        gcp.compute.Subnetwork
        vpc_connector: gcp.vpcaccess.Connector
    """

    def __init__(
        self,
        name: str,
        project: str,
        region: str,
        environment: str,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:Network", name, None, opts)

        logger.info(
            "Creating Network component: env=%s, region=%s",
            environment,
            region,
        )

        # ---------------------------------------------------------------------
        # VPC Network
        # ---------------------------------------------------------------------
        self.network = gcp.compute.Network(
            f"{name}-vpc",
            project=project,
            auto_create_subnetworks=False,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # Private services subnet
        # ---------------------------------------------------------------------
        self.subnet = gcp.compute.Subnetwork(
            f"{name}-subnet",
            project=project,
            region=region,
            network=self.network.id,
            ip_cidr_range="10.0.0.0/20",
            private_ip_google_access=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # Private services connection (for Cloud SQL, Memorystore)
        # ---------------------------------------------------------------------
        self.private_ip_range = gcp.compute.GlobalAddress(
            f"{name}-private-ip",
            project=project,
            purpose="VPC_PEERING",
            address_type="INTERNAL",
            prefix_length=16,
            network=self.network.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.private_connection = gcp.servicenetworking.Connection(
            f"{name}-private-conn",
            network=self.network.id,
            service="servicenetworking.googleapis.com",
            reserved_peering_ranges=[self.private_ip_range.name],
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # Serverless VPC Access connector (for Cloud Run → private resources)
        # ---------------------------------------------------------------------
        self.vpc_connector = gcp.vpcaccess.Connector(
            f"{name}-connector",
            project=project,
            region=region,
            network=self.network.id,
            ip_cidr_range="10.8.0.0/28",
            min_instances=2,
            max_instances=3,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {
                "network_id": self.network.id,
                "subnet_id": self.subnet.id,
                "vpc_connector_id": self.vpc_connector.id,
            }
        )
