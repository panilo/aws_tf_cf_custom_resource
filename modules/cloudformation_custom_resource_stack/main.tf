locals {
  domain_name = "mycustomescluster"
}

data "template_file" "lambda_to_create_custom_resources" {
  template = file("${path.module}/cf_custom_resource_tpl.json")
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

resource "aws_cloudformation_stack" "my_custom_resource" {
  name = "MyCustomResourceStack"

  template_body = data.template_file.lambda_to_create_custom_resources.rendered
  timeouts {
    create = "120m"
  }
  timeout_in_minutes = 120

  parameters = {
    LambdaArn               = var.lambda_arn
    DomainName              = local.domain_name
    ESVersion               = "7.4"
    AutoSnapStartHour       = 23
    DataNodeInstanceType    = "t2.small.elasticsearch"
    DataNodeInstanceCount   = 2
    MasterNodeInstanceType  = "t2.small.elasticsearch"
    MasterNodeInstanceCount = 3
    VolumeType              = "gp2"
    VolumeSize              = 10
    SubnetIds               = join(",", ["subnet-42a4a908", "subnet-eff41f94"])
    SecurityGroupIds        = join(",", ["sg-4b469022"])
    VolumeKmsKeyId          = "asbckeyid"
    AccessPolicies          = <<CONFIG
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "AWS": [
            "*"
          ]
        },
        "Action": [
          "es:*"
        ],
        "Resource": "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${local.domain_name}/*"
      }
    ]
  }
  CONFIG
  }

  tags = var.tags
}
