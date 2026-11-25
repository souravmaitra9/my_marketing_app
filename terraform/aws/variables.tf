variable "region" {
  description = "AWS region. Confirm the EKS and RDS engine versions below are still offered there before apply."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Short project name used in resource names."
  type        = string
  default     = "leaflet"
}

variable "environment" {
  description = "Environment name, for example example or prod."
  type        = string
  default     = "example"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "cluster_version" {
  description = "EKS Kubernetes version."
  type        = string
  default     = "1.31"
}

variable "cluster_public_access_cidrs" {
  description = "CIDRs allowed to reach the public EKS endpoint. Tighten this before real use."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.large"]
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "db_name" {
  type    = string
  default = "leaflet"
}

variable "db_username" {
  type    = string
  default = "leaflet"
}

variable "db_password" {
  description = "RDS master password. Pass TF_VAR_db_password or -var. Do not commit it."
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_engine_version" {
  type    = string
  default = "16.4"
}

variable "db_skip_final_snapshot" {
  description = "Skip the final snapshot so an example stack can be destroyed. Turn this off for anything you need to keep."
  type        = bool
  default     = true
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "redis_engine_version" {
  type    = string
  default = "7.1"
}
