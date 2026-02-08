"""
Artifact Registry repository for Docker images.

All three environments share one repository in a single
GCP project; images are tagged per environment.
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
#  ARTIFACT REGISTRY COMPONENT                                                 #
#                                                                              #
################################################################################


class ArtifactRegistry(pulumi.ComponentResource):
    """
    Artifact Registry Docker repository.

    Exports:
        repository: gcp.artifactregistry.Repository
    """

    def __init__(
        self,
        name: str,
        project: str,
        region: str,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:ArtifactRegistry", name, None, opts)

        logger.info("Creating ArtifactRegistry component: region=%s", region)

        self.repository = gcp.artifactregistry.Repository(
            f"{name}-repo",
            project=project,
            location=region,
            repository_id="aam",
            format="DOCKER",
            description="AAM container images",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {"repository_id": self.repository.repository_id}
        )
