output "landing_bucket" {
  description = "Name of the S3 bucket where CSVs are dropped"
  value       = aws_s3_bucket.landing.bucket
}

output "results_table" {
  description = "Name of the DynamoDB table holding verdicts"
  value       = aws_dynamodb_table.results.name
}

output "lambda_name" {
  description = "Name of the deployed Lambda function"
  value       = aws_lambda_function.gate.function_name
}