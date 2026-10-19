terraform {
  required_version = ">= 1.16.0, < 2.0.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "6.65.0" }
  }
}
provider "aws" { region = var.region }
variable "region" {
  type    = string
  default = "us-east-1"
}
variable "bucket_name" {
  type        = string
  description = "Globally unique owner-selected bucket; no default account or credentials"
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,61}[a-z0-9]$", var.bucket_name))
    error_message = "Use a valid 4-63 character lowercase bucket name."
  }
}
resource "aws_s3_bucket" "lake" {
  bucket        = var.bucket_name
  force_destroy = false
  tags          = { Project = "lakehouse-guardian", Environment = "portfolio-evaluation" }
}
resource "aws_s3_bucket_versioning" "lake" {
  bucket = aws_s3_bucket.lake.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "lake" {
  bucket = aws_s3_bucket.lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
resource "aws_s3_bucket_public_access_block" "lake" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_policy" "tls" {
  bucket = aws_s3_bucket.lake.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Deny", Principal = "*", Action = "s3:*", Resource = [aws_s3_bucket.lake.arn, "${aws_s3_bucket.lake.arn}/*"], Condition = { Bool = { "aws:SecureTransport" = "false" } } }] })
}
resource "aws_glue_catalog_database" "lake" {
  name        = "guardian_mobility"
  description = "Proposed Glue catalog; no AWS execution is claimed"
}
output "bucket_arn" { value = aws_s3_bucket.lake.arn }
output "catalog_database" { value = aws_glue_catalog_database.lake.name }
