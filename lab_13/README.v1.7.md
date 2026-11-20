# Integrated NoSQL Database Labs 1-13

Docker image: jahnavii15/integrated-nosql-labs:1.7

## Contents

This image extends version 1.6. Existing experiment files are preserved.

Lab 13.1 - MongoDB Replica Set and Failover
- docker-compose.yml
- failover_test.py

Lab 13.2 - MongoDB Replica Set on Kubernetes
- mongo-headless.yaml
- mongo-statefulset.yaml

## Environment
- Python 3.13.16
- PyMongo 4.19.0 (inherited from the base image)
- MongoDB 7.0 deployment configurations

## Inspect the image

docker pull jahnavii15/integrated-nosql-labs:1.7
docker run -d --name integrated-nosql-labs jahnavii15/integrated-nosql-labs:1.7
docker exec -it integrated-nosql-labs sh

Experiment files are available under /app.
Lab 13 files are available under /app/lab13.

## Lab 13.1 - Docker Compose

The deployment requires a separately generated MongoDB keyfile.
The private keyfile is intentionally excluded from this image.

Place the keyfile beside docker-compose.yml before deployment.
Run the Compose configuration from that directory.

## Lab 13.2 - Kubernetes

The deployment requires:
1. A Kubernetes namespace named lab13.
2. A Kubernetes Secret named mongo-keyfile containing the keyfile.
3. The headless Service and StatefulSet manifests.

Apply the manifests in the Kubernetes cluster after creating the prerequisites.

## Security

Do not publish the MongoDB keyfile, passwords, or other credentials.
Supply secrets separately during deployment.

## Important

This image packages experiment files and configurations.
Packaging does not automatically execute or independently validate every experiment.
MongoDB and Kubernetes experiments require their respective services and prerequisites.