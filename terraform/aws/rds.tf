resource "aws_db_subnet_group" "this" {
  name       = "${local.name}-postgres"
  subnet_ids = aws_subnet.private[*].id
  tags       = local.tags
}

resource "aws_security_group" "postgres" {
  name        = "${local.name}-postgres"
  description = "Postgres from inside the VPC"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "Postgres from the VPC. Prefer the node security group once a launch template exists."
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.name}-postgres" })
}

resource "aws_db_instance" "this" {
  identifier                 = "${local.name}-postgres"
  engine                     = "postgres"
  engine_version             = var.db_engine_version
  instance_class             = var.db_instance_class
  allocated_storage          = 20
  storage_encrypted          = true
  db_name                    = var.db_name
  username                   = var.db_username
  password                   = var.db_password
  db_subnet_group_name       = aws_db_subnet_group.this.name
  vpc_security_group_ids     = [aws_security_group.postgres.id]
  publicly_accessible        = false
  backup_retention_period    = 7
  skip_final_snapshot        = var.db_skip_final_snapshot
  auto_minor_version_upgrade = true
  deletion_protection        = false
  tags                       = local.tags
}
