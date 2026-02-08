"""
Secret Manager secrets for sensitive configuration.

Creates secrets for DB credentials, JWT signing key,
Redis password, etc. Values are set via ``pulumi config set --secret``.
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
#  SECRETS COMPONENT                                                           #
#                                                                              #
################################################################################


class Secrets(pulumi.ComponentResource):
    """
    Secret Manager entries for application credentials.

    Stores the DB password and a JWT secret key.

    Exports:
        db_password_secret:  gcp.secretmanager.Secret
        jwt_secret:          gcp.secretmanager.Secret
    """

    def __init__(
        self,
        name: str,
        project: str,
        environment: str,
        db_password: pulumi.Input[str],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:Secrets", name, None, opts)

        logger.info("Creating Secrets component: env=%s", environment)

        # ---------------------------------------------------------------------
        # Database password secret
        # ---------------------------------------------------------------------
        self.db_password_secret = gcp.secretmanager.Secret(
            f"{name}-db-password",
            project=project,
            secret_id=f"aam-db-password-{environment}",
            replication={"auto": {}},
            opts=pulumi.ResourceOptions(parent=self),
        )

        gcp.secretmanager.SecretVersion(
            f"{name}-db-password-version",
            secret=self.db_password_secret.id,
            secret_data=db_password,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ---------------------------------------------------------------------
        # JWT signing key secret (value set via `pulumi config set --secret`)
        # ---------------------------------------------------------------------
        self.jwt_secret = gcp.secretmanager.Secret(
            f"{name}-jwt-secret",
            project=project,
            secret_id=f"aam-jwt-secret-{environment}",
            replication={"auto": {}},
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {
                "db_password_secret_id": self.db_password_secret.secret_id,
                "jwt_secret_id": self.jwt_secret.secret_id,
            }
        )
