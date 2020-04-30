import logging
import os
import json
import time

import boto3
from crhelper import CfnResource

REGION_NAME = os.environ.get("AWS_REGION")

logger = logging.getLogger(__name__)

helper = CfnResource(json_logging=False, log_level="DEBUG", boto_level="CRITICAL")


def handler(event, context):
    helper(event, context)


@helper.create
def create(event, context):
    logger.info("Got Create")

    # Get all the resource properties
    arn, resource_props = get_event_attributes(event)

    domain_name = resource_props["DomainName"]
    es_version = resource_props["ESVersion"]
    auto_snap_start_hour = int(resource_props["AutoSnapStartHour"])
    data_node_instance_type = resource_props["DataNodeInstanceType"]
    data_node_instance_count = int(resource_props["DataNodeInstanceCount"])
    master_node_instance_type = resource_props["MasterNodeInstanceType"]
    master_node_instance_count = int(resource_props["MasterNodeInstanceCount"])
    volume_type = resource_props["VolumeType"]
    volume_size = int(resource_props["VolumeSize"])
    subnet_ids = resource_props["SubnetIds"]
    secgrp_ids = resource_props["SecurityGroupIds"]
    volume_kms_key_id = resource_props["VolumeKmsKeyId"]
    access_policy = json.loads(resource_props["AccessPolicies"])

    logger.debug(f"Domain name: {domain_name}")
    logger.debug(f"ES Version: {es_version}")
    logger.debug(f"Snap hour: {auto_snap_start_hour}")
    logger.debug(f"Data node type: {data_node_instance_type}")
    logger.debug(f"Data node count: {data_node_instance_count}")
    logger.debug(f"Master node type: {master_node_instance_type}")
    logger.debug(f"Master node count: {master_node_instance_count}")
    logger.debug(f"Volume type: {volume_type}")
    logger.debug(f"Volume size: {volume_size}")
    logger.debug(f"Subnet ids: {subnet_ids}")
    logger.debug(f"Sec group ids: {secgrp_ids}")
    logger.debug(f"Volume kms key id: {volume_kms_key_id}")
    logger.debug(f"Access policies: {access_policy}")

    # Create the cluster
    client = get_boto_client()
    creation_response = client.create_elasticsearch_domain(
        DomainName=domain_name,
        ElasticsearchVersion=es_version,
        ElasticsearchClusterConfig={
            "InstanceType": data_node_instance_type,
            "InstanceCount": data_node_instance_count,
            "DedicatedMasterEnabled": True,
            "ZoneAwarenessEnabled": True,
            "DedicatedMasterType": master_node_instance_type,
            "DedicatedMasterCount": master_node_instance_count,
        },
        EBSOptions={
            "EBSEnabled": True,
            "VolumeType": volume_type,
            "VolumeSize": volume_size,
        },
        AccessPolicies=json.dumps(access_policy),
        SnapshotOptions={"AutomatedSnapshotStartHour": auto_snap_start_hour},
        VPCOptions={"SubnetIds": subnet_ids, "SecurityGroupIds": secgrp_ids},
        # CognitoOptions={
        #     'Enabled': True | False,
        #     'UserPoolId': 'string',
        #     'IdentityPoolId': 'string',
        #     'RoleArn': 'string'
        # },
        # EncryptionAtRestOptions={
        #     'Enabled': True | False,
        #     'KmsKeyId': 'string'
        # },
        NodeToNodeEncryptionOptions={"Enabled": True},
        # AdvancedOptions={
        #     'string': 'string'
        # },
        # LogPublishingOptions={
        #     'string': {
        #         'CloudWatchLogsLogGroupArn': 'string',
        #         'Enabled': True | False
        #     }
        # },
        DomainEndpointOptions={"EnforceHTTPS": True},
        # AdvancedSecurityOptions={
        #     'Enabled': True | False,
        #     'InternalUserDatabaseEnabled': True | False,
        #     'MasterUserOptions': {
        #         'MasterUserARN': 'string',
        #         'MasterUserName': 'string',
        #         'MasterUserPassword': 'string'
        #     }
        # }
    )

    logger.debug(creation_response)
    es_domain_status = get_domain_status(creation_response)

    created = es_domain_status["Created"]
    if created:
        es_cluster_arn = es_domain_status["ARN"]

        # Items stored in helper.Data will be saved
        # as outputs in your resource in CloudFormation
        helper.Data["ARN"] = es_cluster_arn

        # Return PhysicalResourceId can be used as ARN
        return es_cluster_arn
    else:
        raise Exception("Domain not created")


@helper.poll_create
def pool_create(event, context):
    logger.debug("Attemp update...")

    arn, resource_props = get_event_attributes(event)
    domain_name = resource_props["DomainName"]

    client = get_boto_client()
    update_response = client.describe_elasticsearch_domain(DomainName=domain_name)
    logger.debug("Update response")
    logger.debug(update_response)

    es_domain_status = get_domain_status(update_response)
    processing = es_domain_status["Processing"]
    es_cluster_endpoint = (
        es_domain_status["Endpoints"]["vpc"]
        if "Endpoints" in es_domain_status.keys()
        else ""
    )

    if processing or not es_cluster_endpoint:
        return False
    else:
        helper.Data["Endpoint"] = es_cluster_endpoint
        return True


@helper.update
def update(event, context):
    logger.info("Got Update")
    raise Exception("Operation not yet supported")


@helper.delete
def delete(event, context):
    logger.info("Got Delete")

    resourceArn, resource_props = get_event_attributes(event)
    domain_name = resource_props["DomainName"]

    logger.debug(f"Delete this ARN: '{resourceArn}' - Domain name: '{domain_name}'")

    client = get_boto_client()
    client.delete_elasticsearch_domain(DomainName=domain_name)


def get_boto_client():
    return boto3.client("es", REGION_NAME)


def get_domain_status(response):
    return response["DomainStatus"]


def get_event_attributes(event):
    arn = event["PhysicalResourceId"] if "PhysicalResourceId" in event.keys() else ""
    return (arn, event["ResourceProperties"])
