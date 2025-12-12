output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnet_ids" {
  value = [
    aws_subnet.public_a.id,
    aws_subnet.public_b.id
  ]
}

output "private_app_subnet_ids" {
  value = [
    aws_subnet.private_app_a.id,
    aws_subnet.private_app_b.id
  ]
}

output "private_db_subnet_ids" {
  value = [
    aws_subnet.private_db_a.id,
    aws_subnet.private_db_b.id
  ]
}

output "eks_cluster_name" {
  value = aws_eks_cluster.cluster.name
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.cluster.endpoint
}

output "eks_cluster_oidc_issuer" {
  value = data.aws_eks_cluster.eks.identity[0].oidc[0].issuer
}

output "eks_version" {
  value = aws_eks_cluster.cluster.version
}

output "eks_node_role_arn" {
  value = aws_iam_role.eks_node_role.arn
}

output "eks_node_group_name" {
  value = aws_eks_node_group.default.node_group_name
}

output "eks_node_instance_types" {
  value = aws_eks_node_group.default.instance_types
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.employees.name
}

output "alb_sg_id" {
  value = aws_security_group.alb_sg.id
}

output "eks_nodes_sg_id" {
  value = aws_security_group.eks_nodes_sg.id
}

output "eks_control_plane_sg_id" {
  value = aws_security_group.eks_control_plane_sg.id
}

output "db_sg_id" {
  value = aws_security_group.db_sg.id
}



