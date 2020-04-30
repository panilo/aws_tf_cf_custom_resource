provider "aws" {
  profile = "danilo"
  region  = var.region
}

# Create the lambda
module "lambda" {
  source = "./modules/lambda"

  fn_name   = "es_cluster_with_fga_lambda"
  code_path = "./src"
  handler   = "CreateESClusterFGA.handler"

  iam_policy_definition = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowAllESActions",
            "Effect": "Allow",
            "Action": "es:*",
            "Resource": "*"
        },
        {
          "Sid": "AllowCFPolling",
          "Effect": "Allow",
          "Action": [
            "lambda:AddPermission",
            "lambda:RemovePermission",
            "events:PutRule",
            "events:DeleteRule",
            "events:PutTargets",
            "events:RemoveTargets"
          ],
          "Resource": "*"
        }
    ]
}
  EOF

  tags = {
    project = "test-cf-custom-resource"
  }
}

# Create the cloudformation stack
module "cf_custom_resource" {
  source = "./modules/cloudformation_custom_resource_stack"

  lambda_arn = module.lambda.arn

  tags = {
    project = "test-cf-custom-resource"
  }
}
