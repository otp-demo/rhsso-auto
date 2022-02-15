#!/bin/bash
docker build -t quay.io/leoliu2011/python39oc:v1  -f Dockerfile-python39-oc .
docker push quay.io/leoliu2011/python39oc:v1

docker build -t quay.io/leoliu2011/keycloak-preprocessing -f Dockerfile-pre .
docker push quay.io/leoliu2011/keycloak-preprocessing

docker build -t quay.io/leoliu2011/argocd-keycloak-integration .
docker push quay.io/leoliu2011/argocd-keycloak-integration

docker build -t quay.io/leoliu2011/cluster-keycloak-integration:v1 -f Dockerfile-cluster .
docker push quay.io/leoliu2011/cluster-keycloak-integration:v1

docker build -t quay.io/mahesh_v/azure-keycloak-integration:v1 -f Dockerfile-azure .
docker push quay.io/mahesh_v/azure-keycloak-integration:v1

docker build -t quay.io/leoliu2011/aws-keycloak-integration:v1 -f Dockerfile-aws .
docker push quay.io/leoliu2011/aws-keycloak-integration:v1

docker build -t quay.io/mahesh_v/ansible-keycloak-integration:v1 -f Dockerfile-ansible .
docker push quay.io/mahesh_v/ansible-keycloak-integration:v1