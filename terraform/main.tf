terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- unique suffix so the bucket name is globally unique ---
resource "random_id" "suffix" {
  byte_length = 4
}

# --- S3 landing bucket: where CSVs arrive ---
resource "aws_s3_bucket" "landing" {
  bucket = "${var.project}-landing-${random_id.suffix.hex}"
}

resource "aws_s3_bucket_public_access_block" "landing" {
  bucket                  = aws_s3_bucket.landing.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- DynamoDB table: where verdicts are stored ---
resource "aws_dynamodb_table" "results" {
  name         = "${var.project}-results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "result_id"

  attribute {
    name = "result_id"
    type = "S"
  }
}

# --- the Lambda function: runs handler.py ---
resource "aws_lambda_function" "gate" {
  function_name    = "${var.project}-gate"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = "${path.module}/../build/function.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/function.zip")
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      RESULTS_TABLE     = aws_dynamodb_table.results.name
      CONFIG_PATH       = "config.yaml"
      SLACK_WEBHOOK_URL = var.slack_webhook_url
    }
  }
}

# --- allow S3 to invoke the Lambda ---
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gate.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.landing.arn
}

# --- the trigger: when a .csv lands, wake the Lambda ---
resource "aws_s3_bucket_notification" "landing" {
  bucket = aws_s3_bucket.landing.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.gate.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}