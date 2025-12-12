resource "aws_dynamodb_table" "tf_locks" {
  name         = "case3-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "case3-terraform-locks"
    Environment = "case3"
  }
}
