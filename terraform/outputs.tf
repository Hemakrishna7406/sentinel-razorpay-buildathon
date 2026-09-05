output "vpc_id" {
  value = module.vpc.vpc_id
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "rds_endpoint" {
  value = module.rds.endpoint
}

output "redis_endpoint" {
  value = module.elasticache.primary_endpoint
}

output "msk_bootstrap_brokers" {
  value = module.msk.bootstrap_brokers
}

output "ecr_repositories" {
  value = module.ecr.repository_urls
}
