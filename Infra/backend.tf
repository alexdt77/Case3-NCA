terraform {
  backend "s3" {
    bucket  = "case-3-eks"
    key     = "state/terraform.tfstate"
    region  = "eu-central-1"
    encrypt = true
    #dynamodb_table = "case3-terraform-locks"
  }
}
