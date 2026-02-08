"""
GCS bucket for storing package archives.

Uses uniform bucket-level access (no per-object ACLs).
Lifecycle rules auto-delete incomplete multipart uploads.
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
#  STORAGE COMPONENT                                                           #
#                                                                              #
################################################################################


class Storage(pulumi.ComponentResource):
    """
    GCS bucket for AAM package archives.

    Exports:
        bucket: gcp.storage.Bucket
    """

    def __init__(
        self,
        name: str,
        project: str,
        environment: str,
        location: str,
        storage_class: str,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("aam:infra:Storage", name, None, opts)

        logger.info(
            "Creating Storage component: env=%s, location=%s, class=%s",
            environment,
            location,
            storage_class,
        )

        self.bucket = gcp.storage.Bucket(
            f"{name}-packages",
            project=project,
            name=f"aam-packages-{environment}",
            location=location,
            storage_class=storage_class,
            uniform_bucket_level_access=True,
            versioning={"enabled": environment == "prod"},
            lifecycle_rules=[
                {
                    "action": {"type": "AbortIncompleteMultipartUpload"},
                    "condition": {"age": 7},
                },
            ],
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs({"bucket_name": self.bucket.name})
