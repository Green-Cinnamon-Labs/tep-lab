terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_key_pair" "bootstrap_key" {
  key_name   = "k8s-bootstrap-lab-key"
  public_key = file("../../.aws/ec2-keys/k8s-bootstrap-lab-key.pem.pub")
}

resource "aws_security_group" "bootstrap_sg" {
  name   = "bootstrap-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "bootstrap" {
  ami                         = "ami-0c398cb65a93047f2" # Ubuntu Server 22.04 LTS (HVM),EBS General Purpose (SSD) Volume Type. Support available from Canonical (http://www.ubuntu.com/cloud/services).
  instance_type               = "t3.small" # 2 vCPU, 2 GiB RAM
  key_name                    = aws_key_pair.bootstrap_key.key_name
  vpc_security_group_ids      = [aws_security_group.bootstrap_sg.id]
  associate_public_ip_address = true

  tags = {
    Name = "k8s-bootstrap-lab"
  }
}
