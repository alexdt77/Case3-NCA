resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "case3-vpc"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnets.a
  availability_zone       = var.az_a
  map_public_ip_on_launch = true

  tags = {
    Name                                      = "public-a"
    "kubernetes.io/role/elb"                  = "1"
    "kubernetes.io/cluster/case3-eks-cluster" = "shared"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnets.b
  availability_zone       = var.az_b
  map_public_ip_on_launch = true

  tags = {
    Name                                      = "public-b"
    "kubernetes.io/role/elb"                  = "1"
    "kubernetes.io/cluster/case3-eks-cluster" = "shared"
  }
}

resource "aws_subnet" "private_app_a" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_app_subnets.a
  availability_zone = var.az_a

  tags = {
    Name                                      = "private-app-a"
    "kubernetes.io/role/internal-elb"         = "1"
    "kubernetes.io/cluster/case3-eks-cluster" = "shared"
  }
}

resource "aws_subnet" "private_app_b" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_app_subnets.b
  availability_zone = var.az_b

  tags = {
    Name                                      = "private-app-b"
    "kubernetes.io/role/internal-elb"         = "1"
    "kubernetes.io/cluster/case3-eks-cluster" = "shared"
  }
}

resource "aws_subnet" "private_db_a" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_db_subnets.a
  availability_zone = var.az_a

  tags = {
    Name = "private-db-a"
  }
}

resource "aws_subnet" "private_db_b" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_db_subnets.b
  availability_zone = var.az_b

  tags = {
    Name = "private-db-b"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "case3-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "public-rt"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

resource "aws_eip" "nat_eip_a" {
  domain = "vpc"
  tags   = { Name = "nat-eip-a" }
}

resource "aws_nat_gateway" "nat_a" {
  allocation_id = aws_eip.nat_eip_a.id
  subnet_id     = aws_subnet.public_a.id

  tags = { Name = "nat-gw-a" }
}

resource "aws_eip" "nat_eip_b" {
  domain = "vpc"
  tags   = { Name = "nat-eip-b" }
}

resource "aws_nat_gateway" "nat_b" {
  allocation_id = aws_eip.nat_eip_b.id
  subnet_id     = aws_subnet.public_b.id

  tags = { Name = "nat-gw-b" }
}

resource "aws_route_table" "private_app_a_rt" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_a.id
  }

  tags = { Name = "private-app-a-rt" }
}

resource "aws_route_table_association" "private_app_a_assoc" {
  subnet_id      = aws_subnet.private_app_a.id
  route_table_id = aws_route_table.private_app_a_rt.id
}

resource "aws_route_table" "private_app_b_rt" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_b.id
  }

  tags = { Name = "private-app-b-rt" }
}

resource "aws_route_table_association" "private_app_b_assoc" {
  subnet_id      = aws_subnet.private_app_b.id
  route_table_id = aws_route_table.private_app_b_rt.id
}

resource "aws_route_table" "private_db_rt" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "private-db-rt" }
}

resource "aws_route_table_association" "private_db_a_assoc" {
  subnet_id      = aws_subnet.private_db_a.id
  route_table_id = aws_route_table.private_db_rt.id
}

resource "aws_route_table_association" "private_db_b_assoc" {
  subnet_id      = aws_subnet.private_db_b.id
  route_table_id = aws_route_table.private_db_rt.id
}
