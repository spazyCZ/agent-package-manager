"""
Cloud SQL (PostgreSQL 16) instance, database, and user.

The instance is placed on the private VPC network so only
resources inside the VPC (Cloud Run via VPC connector) can reach it.
"""

################################################################################
#                                                                              #
#  IMPORTS & DEPENDENCIES                                                      #
#                                                                              #
################################################################################

import logging

import pulumi
import pulumi_gcp as gcp
import pulumi_random as random

################################################################################
#                                                                              #
#  LOGGER                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
#  DATABASE COMPONENT                                                          #
#                                                                              #
################################################################################


class Database(pulumi.ComponentResource):
    """
    Cloud SQL PostgreSQL 16 instance with database and application user.

    Exports:
        instance:      gcp.sql.DatabaseInstance
        database:      gcp.sql.Database
        user:          gcp.sql.User
        password:      pulumi.Output[str]  (secret)
        connection_name: pulumi.Output[str]
    """

    def __init__(
        self,
        name: str,
        project: str,
        region: str,
        environment: str,
        network_id: pulumi.Input[str],
        private_connection: gcp.servicenetworking.Connection,
        tier: str,
        disk_size_gb: int,
        high_availability: bool,
        backup_enabled: bool,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:Database", name, None, opts)

        logger.info(
            "Creating Database component: env=%s, tier=%s, ha=%s",
            environment,
            tier,
            high_availability,
        )

        # ---------------------------------------------------------------------
        # Generate a random password for the DB user
        # ---------------------------------------------------------------------
        self.password = random.RandomPassword(
            f"{name}-db-password",
            length=32,
            special=True,
            override_special="!#$%&*()-_=+[]{}<>:?",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # Cloud SQL instance
        # ---------------------------------------------------------------------
        availability_type = "REGIONAL" if high_availability else "ZONAL"

        self.instance = gcp.sql.DatabaseInstance(
            f"{name}-instance",
            project=project,
            region=region,
            database_version="POSTGRES_16",
            deletion_protection=environment == "prod",
            settings={
                "tier": tier,
                "disk_size": disk_size_gb,
                "disk_autoresize": True,
                "availability_type": availability_type,
                "ip_configuration": {
                    "ipv4_enabled": False,
                    "private_network": network_id,
                },
                "backup_configuration": {
                    "enabled": backup_enabled,
                    "start_time": "03:00",
                    "point_in_time_recovery_enabled": backup_enabled,
                },
                "database_flags": [
                    {"name": "log_checkpoints", "value": "on"},
                    {"name": "log_connections", "value": "on"},
                    {"name": "log_disconnections", "value": "on"},
                ],
                "maintenance_window": {
                    "day": 7,
                    "hour": 4,
                    "update_track": "stable",
                },
            },
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[private_connection],
            ),
        )

        # ---------------------------------------------------------------------
        # Database
        # ---------------------------------------------------------------------
        self.database = gcp.sql.Database(
            f"{name}-db",
            project=project,
            instance=self.instance.name,
            name="aam",
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # Application user
        # ---------------------------------------------------------------------
        self.user = gcp.sql.User(
            f"{name}-user",
            project=project,
            instance=self.instance.name,
            name="aam",
            password=self.password.result,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.connection_name = self.instance.connection_name

        self.register_outputs(
            {
                "instance_name": self.instance.name,
                "connection_name": self.connection_name,
                "database_name": self.database.name,
            }
        )
