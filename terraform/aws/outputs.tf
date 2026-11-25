output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "rds_address" {
  value = aws_db_instance.this.address
}

output "redis_address" {
  value = aws_elasticache_cluster.this.cache_nodes[0].address
}
