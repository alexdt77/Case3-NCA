resource "aws_eks_cluster" "cluster" {
  name     = "case3-eks-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.29"

  vpc_config {
    subnet_ids = [
      aws_subnet.private_app_a.id,
      aws_subnet.private_app_b.id
    ]

    security_group_ids = [
      aws_security_group.eks_control_plane_sg.id,
      aws_security_group.eks_nodes_sg.id
    ]

    endpoint_private_access = true
    endpoint_public_access  = true
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource
  ]

  tags = {
    Name = "case3-eks-cluster"
  }
}

resource "aws_launch_template" "eks_nodes" {
  name_prefix            = "case3-eks-nodes-"
  description            = "Launch template for EKS worker nodes"
  update_default_version = true

  vpc_security_group_ids = [
    aws_security_group.eks_nodes_sg.id
  ]

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name = "case3-eks-node"
    }
  }
}

resource "aws_eks_node_group" "default" {
  cluster_name    = aws_eks_cluster.cluster.name
  node_group_name = "default-ng"
  node_role_arn   = aws_iam_role.eks_node_role.arn

  subnet_ids = [
    aws_subnet.private_app_a.id,
    aws_subnet.private_app_b.id
  ]

  scaling_config {
    desired_size = 2
    min_size     = 1
    max_size     = 3
  }

  instance_types = ["t3.large"]
  ami_type       = "AL2_x86_64"
  capacity_type  = "ON_DEMAND"

  launch_template {
    id      = aws_launch_template.eks_nodes.id
    version = "$Latest"
  }

  depends_on = [
    aws_iam_role_policy_attachment.worker_node,
    aws_iam_role_policy_attachment.cni,
    aws_iam_role_policy_attachment.ecr_readonly,
    aws_iam_role_policy_attachment.ssm_managed_core,
    aws_eks_cluster.cluster,
    aws_iam_openid_connect_provider.eks_oidc
  ]

  tags = {
    Name                                          = "case3-eks-node-group"
    "k8s.io/cluster-autoscaler/enabled"           = "true"
    "k8s.io/cluster-autoscaler/case3-eks-cluster" = "owned"
  }
}

resource "aws_eks_addon" "ebs_csi" {
  cluster_name  = aws_eks_cluster.cluster.name
  addon_name    = "aws-ebs-csi-driver"
  addon_version = "v1.53.0-eksbuild.1"

  service_account_role_arn = aws_iam_role.ebs_csi_role.arn

  resolve_conflicts_on_update = "OVERWRITE"
  resolve_conflicts_on_create = "OVERWRITE"
}


