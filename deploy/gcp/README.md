# AAM GCP helpers

This directory contains optional `gcloud` helpers for building and publishing
container images, and for deploying individual services to Cloud Run outside of
Pulumi.

## Build and push the dev web image

These steps build the production web container for `apps/aam-web` using Cloud
Build and push it to Artifact Registry as `web:dev`.

1. Authenticate with Google Cloud.

```bash
gcloud auth login
```

2. Build and push the image.

```bash
./deploy/gcp/deploy_web_dev.sh
```

## Build and push without Cloud Build

If your account can’t use Cloud Build in the project, you can build and push
the image from your machine using Docker.

```bash
./deploy/gcp/deploy_web_dev.sh --local-docker
```

## Optional: Deploy the web service with gcloud

If you want to deploy only the web service to Cloud Run without Pulumi, run the
script with `--deploy-cloud-run`.

```bash
./deploy/gcp/deploy_web_dev.sh --deploy-cloud-run
```

You can combine flags to build locally and deploy:

```bash
./deploy/gcp/deploy_web_dev.sh --local-docker --deploy-cloud-run
```

## Deploy with Pulumi

If you use Pulumi to manage infrastructure, build and push the image first,
then deploy the stack.

```bash
cd deploy/pulumi
pulumi stack select dev
pulumi up
```

## Deploy documentation to GCS

The MkDocs documentation site can be deployed to a Google Cloud Storage bucket
configured for static website hosting.

### Quick deploy (dev bucket)

```bash
./deploy/gcp/deploy_docs.sh
```

This builds the site with `mkdocs build --strict` and syncs it to the
`aam-docs-dev` GCS bucket.

### Deploy to a custom bucket

```bash
./deploy/gcp/deploy_docs.sh --bucket=aam-docs-prod
```

### Install dependencies and deploy

If MkDocs is not yet installed in your environment:

```bash
./deploy/gcp/deploy_docs.sh --install
```

### Build only (no upload)

```bash
./deploy/gcp/deploy_docs.sh --build-only
```

### Preview what would be synced

```bash
./deploy/gcp/deploy_docs.sh --dry-run
```

### What the script does

On first run for a bucket the script will:

1. Create the GCS bucket with uniform bucket-level access
2. Configure static website serving (`index.html` / `404.html`)
3. Grant public read access (`allUsers` as `objectViewer`)

On every run the script:

1. Builds the MkDocs site in strict mode
2. Syncs the `site/` output to the bucket (adds new files, removes stale ones)
3. Sets a short cache TTL on HTML files (60 s) for fast updates

### Accessing the deployed docs

After deployment the site is available at:

```
https://storage.googleapis.com/<BUCKET>/index.html
```

To serve docs under a custom domain with HTTPS, place the bucket behind the
Global HTTPS Load Balancer and add a URL map path rule (e.g. `/docs/*`).

## Notes

These notes explain a few build and naming details that matter when you run the
helpers in this directory.

- The web Dockerfile expects the build context to be the monorepo root because
  it runs `npm run web:build` via Nx.
- These helpers assume the dev stack defaults:
  - Project: `aamregistry`
  - Region: `us-central1`
  - Artifact Registry repo: `aam`

