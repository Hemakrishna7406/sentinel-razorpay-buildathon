terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "sentinel-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "sentinel-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Sentinel"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

module "vpc" {
  source = "./modules/vpc"

  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

module "eks" {
  source = "./modules/eks"

  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  cluster_version    = var.eks_cluster_version
}

module "rds" {
  source = "./modules/rds"

  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  database_subnet_ids = module.vpc.database_subnet_ids
  instance_class     = var.rds_instance_class
  allocated_storage  = var.rds_allocated_storage
}

module "elasticache" {
  source = "./modules/elasticache"

  environment    = var.environment
  vpc_id        = module.vpc.vpc_id
  subnet_ids    = module.vpc.elasticache_subnet_ids
  node_type     = var.elasticache_node_type
  num_cache_nodes = var.elasticache_num_nodes
}

module "msk" {
  source = "./modules/msk"

  environment        = var.environment
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.private_subnet_ids
  instance_type     = var.msk_instance_type
  ebs_volume_size   = var.msk_ebs_volume_size
}

module "ecr" {
  source = "./modules/ecr"

  environment = var.environment
  repositories = [
    "sentinel-api",
    "sentinel-worker",
    "sentinel-audit",
    "sentinel-frontend"
  ]
}
