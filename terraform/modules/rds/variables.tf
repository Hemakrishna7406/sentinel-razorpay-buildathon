variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "database_subnet_ids" {
  type = list(string)
}

variable "instance_class" {
  type = string
}

variable "allocated_storage" {
  type = number
}
