variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-north-1"
}

variable "project" {
  description = "Name prefix for all resources, so they're easy to identify"
  type        = string
  default     = "dq-gate"
}

variable "slack_webhook_url" {
  description = "Slack incoming webhook for failure alerts (optional)"
  type        = string
  default     = ""
  sensitive   = true
}