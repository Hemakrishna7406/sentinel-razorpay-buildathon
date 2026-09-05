resource "aws_security_group" "msk" {
  name        = "sentinel-${var.environment}-msk-sg"
  description = "MSK security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  ingress {
    from_port   = 9094
    to_port     = 9094
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

resource "aws_msk_cluster" "main" {
  cluster_name           = "sentinel-${var.environment}"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = var.instance_type
    client_subnets  = var.subnet_ids
    security_groups = [aws_security_group.msk.id]

    storage_info {
      ebs_storage_info {
        volume_size = var.ebs_volume_size
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
    encryption_at_rest_kms_key_arn = aws_kms_key.msk.arn
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.msk.name
      }
    }
  }
}

resource "aws_kms_key" "msk" {
  description = "KMS key for MSK encryption"
}

resource "aws_cloudwatch_log_group" "msk" {
  name              = "/aws/msk/sentinel-${var.environment}"
  retention_in_days = 7
}
