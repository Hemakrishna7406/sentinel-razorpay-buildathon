resource "aws_db_subnet_group" "main" {
  name       = "sentinel-${var.environment}-db-subnet"
  subnet_ids = var.database_subnet_ids

  tags = {
    Name = "sentinel-${var.environment}-db-subnet"
  }
}

resource "aws_security_group" "rds" {
  name        = "sentinel-${var.environment}-rds-sg"
  description = "RDS security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "random_password" "master" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "rds_password" {
  name = "sentinel-${var.environment}-rds-password"
}

resource "aws_secretsmanager_secret_version" "rds_password" {
  secret_id     = aws_secretsmanager_secret.rds_password.id
  secret_string = random_password.master.result
}

resource "aws_db_instance" "main" {
  identifier     = "sentinel-${var.environment}"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.allocated_storage * 2
  storage_encrypted     = true

  db_name  = "sentinel"
  username = "sentinel_admin"
  password = random_password.master.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az               = true
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true

  skip_final_snapshot = false
  final_snapshot_identifier = "sentinel-${var.environment}-final-${formatdate("YYYYMMDDhhmmss", timestamp())}"

  deletion_protection = true
}
