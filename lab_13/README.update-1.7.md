# Integrated NoSQL Database Labs 1-13

Docker image: jahnavii15/integrated-nosql-labs:1.7

This image preserves the previous experiment files and includes the updated Lab 13 deployment configuration.

## Lab 13.1 - MongoDB Replica Set and Monitoring

- Three MongoDB 7.0 nodes
- Keyfile authentication
- PyMongo failover test
- Primary election monitoring
- Percona MongoDB exporter 0.53
- Compose-based exporter deployment

Exporter metrics endpoint: http://localhost:9217/metrics

Exporter credentials are supplied separately using:
- MONGODB_EXPORTER_USER
- MONGODB_EXPORTER_PASSWORD

## Lab 13.2 - Kubernetes

- Three-replica MongoDB StatefulSet
- Headless Service
- Keyfile Secret
- Persistent volume claims

## Pull image

docker pull jahnavii15/integrated-nosql-labs:1.7

## Security

Private MongoDB keyfiles and passwords are excluded from this image.
Supply authentication secrets separately.

## Important

The image packages experiment files and deployment configurations.
It does not automatically launch every experiment.
