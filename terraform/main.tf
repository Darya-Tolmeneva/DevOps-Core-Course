terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  zone      = var.zone
  folder_id = var.folder_id
}

# -------- Network --------
resource "yandex_vpc_network" "network" {
  name = "terraform-network"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "terraform-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.5.0.0/24"]
}

# -------- Security Group --------
resource "yandex_vpc_security_group" "vm_sg" {
  name       = "terraform-sg"
  network_id = yandex_vpc_network.network.id

  # SSH
  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = [var.my_ip]
  }

  # HTTP
  ingress {
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Custom port 5000
  ingress {
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# -------- VM --------
resource "yandex_compute_instance" "vm" {
  name        = "terraform-vm"
  platform_id = "standard-v2"

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = var.image_id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    security_group_ids = [yandex_vpc_security_group.vm_sg.id]
    nat                = true
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.public_key_path)}"
  }

  labels = {
    environment = "terraform"
    project     = "vm-task"
  }
}
