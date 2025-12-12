resource "null_resource" "wait_for_cluster" {
  depends_on = [
    aws_eks_cluster.cluster,
    aws_eks_node_group.default
  ]

  provisioner "local-exec" {
    command = "echo 'EKS cluster ready'"
  }
}
