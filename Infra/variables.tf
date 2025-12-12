variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "public_subnets" {
  type = map(string)
  default = {
    a = "10.20.1.0/24"
    b = "10.20.2.0/24"
  }
}

variable "private_app_subnets" {
  type = map(string)
  default = {
    a = "10.20.11.0/24"
    b = "10.20.12.0/24"
  }
}

variable "private_db_subnets" {
  type = map(string)
  default = {
    a = "10.20.21.0/24"
    b = "10.20.22.0/24"
  }
}

variable "az_a" {
  default = "eu-central-1a"
}
variable "az_b" {
  default = "eu-central-1b"
}

variable "my_ip" {
  description = "Your laptop IP for kubectl access"
  type        = string
}


