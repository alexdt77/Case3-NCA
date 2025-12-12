terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
}

data "aws_eks_cluster" "eks" {
  name = aws_eks_cluster.cluster.name
}

data "aws_eks_cluster_auth" "eks" {
  name = aws_eks_cluster.cluster.name
}

