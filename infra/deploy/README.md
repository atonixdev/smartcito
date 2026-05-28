# Deployment Scripts

This folder contains the deploy tooling used by CI/CD to roll Orca out to
OpenStack VMs.

## Expected inputs

- `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PATH`
- `IMAGE_REGISTRY`, `IMAGE_TAG`
- `DEPLOY_STRATEGY` (`blue-green-api` by default, or `rolling-partitions` / `full-stack`)
- `APP_ENV`
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `KAFKA_BROKER_URL` or `MESSAGE_BUS_URL`
- `OBJECT_STORAGE_ENDPOINT`, `OBJECT_STORAGE_BUCKET`
- `AUTH_JWT_SECRET`, `AUTH_ISSUER`, `AUTH_AUDIENCE`

## Scripts

- `deploy_remote.sh`: SSH entrypoint used by CI/CD.
- `update_stack.sh`: Pulls new images, warms the inactive API slot, flips NGINX traffic between blue and green, then rolls the remaining stateless services.
- `run_migrations.sh`: Applies backend database migrations before traffic settles.

## Blue/Green API routing

- `api-router` owns host port `APP_PORT` and forwards traffic to either `citosmart-blue` or `citosmart-green`.
- The active slot is tracked in `infra/deploy/runtime/active_api_slot` on the deployment target.
- `update_stack.sh` deploys the inactive slot, validates it, switches the router, then optionally stops the previous slot.