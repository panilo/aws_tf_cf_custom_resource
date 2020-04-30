locals {
  zip_out_path = "${path.module}/zip/${var.fn_name}/${var.fn_name}.zip"
}

# Archive lambda code to upload it
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.code_path
  output_path = local.zip_out_path
}

# Create role for the lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.fn_name}_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Sid": "LambdaAssumeRoleStm"
    }
  ]
}
EOF

  tags = var.tags

}

# Create the appropriate policy to let lambda operate with the right permissions
resource "aws_iam_policy" "addictional_policy" {
  count = length(var.iam_policy_definition) > 0 ? 1 : 0

  name   = "${var.fn_name}_policy"
  policy = var.iam_policy_definition
}

resource "aws_iam_role_policy_attachment" "addictional_policy_attachment" {
  count = length(var.iam_policy_definition) > 0 ? 1 : 0

  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.addictional_policy[0].arn
}

# Attach the lambda default policy for basic execution
resource "aws_iam_role_policy_attachment" "lambda_basic_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# TODO VPC

# Create the lambda
resource "aws_lambda_function" "lambda" {
  function_name = var.fn_name
  handler       = var.handler
  runtime       = var.runtime
  timeout       = var.timeout

  filename         = local.zip_out_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  role = aws_iam_role.lambda_role.arn

  tags = var.tags
}
