#!/bin/bash

function print_failure() 
{
    if [[ $? -ne 0 ]]; then
        echo $1
        exit 1
    fi
}

function wait_for_resource()
{
    echo "------ Wait for $1 $2 to be ready -------------"
    oc get $1 $2 -n sso-integration
    while [[ $? -ne 0 ]]
    do
        sleep 2
        oc get $1 $2 -n sso-integration
    done
    echo "------ $1 $2 is ready -------------"
}

function wait_for_job_succeed()
{
    echo "------ Wait for Job $1 to be ready -------------"
    succeeded=$(oc -n sso-integration get job $1 -o jsonpath='{.status.succeeded}')
    while [[ succeeded -ne 1 ]]
    do
        echo "Status: ${succeeded} Sleeping for 3 seconds..."
        sleep 3
        succeeded=$(oc -n sso-integration get job $1 -o jsonpath='{.status.succeeded}')
    done
    echo "------ Job $1 is ready -------------"
}

function wait_for_preprocessing()
{
    wait_for_job_succeed "keycloak-preprocessing"
    wait_for_resource "secret" "sso-configs"
    wait_for_resource "configmap" "argocd-configs"
}