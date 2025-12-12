resource "aws_dynamodb_table" "employees" {
  name         = "employees"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "id"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = {
    Name        = "employees-table"
    Environment = "case3-v2"
  }
}

output "employees_table_name" {
  value = aws_dynamodb_table.employees.name
}
