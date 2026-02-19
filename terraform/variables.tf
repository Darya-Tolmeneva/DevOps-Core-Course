variable "zone" {
  description = "Yandex Cloud zone"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
}

variable "image_id" {
  description = "Ubuntu image ID"
  type        = string
}

variable "my_ip" {
  description = "IP for SSH access"
  type        = string
}

variable "public_key_path" {
  description = "Path to SSH public key"
  type        = string
}

