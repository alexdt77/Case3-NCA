resource "aws_cloudwatch_log_group" "employee_lifecycle" {
  name              = "/case3/employee_lifecycle"
  retention_in_days = 30

  tags = {
    Name = "employee-lifecycle"
  }
}
