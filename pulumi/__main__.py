import os
import pulumi
import pulumi_yandex as yandex

# -----------------------------
# Config variables
# -----------------------------
config = pulumi.Config()
zone = config.get("zone") or "ru-central1-a"
folder_id = config.require("folder_id")
ssh_pub_key_path = config.require("ssh_pub_key_path")
my_ip = config.require("my_ip")  # in CIDR format
image_id = config.require("image_id")  # Ubuntu image ID

# Read SSH public key (expand ~)
with open(os.path.expanduser(ssh_pub_key_path), "r") as f:
    ssh_key = f.read().strip()

# -----------------------------
# Network
# -----------------------------
network = yandex.VpcNetwork(
    "pulumi-network",
    folder_id=folder_id,
    name="pulumi-network"
)

subnet = yandex.VpcSubnet(
    "pulumi-subnet",
    folder_id=folder_id,
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.5.0.0/24"],
    name="pulumi-subnet"
)

# -----------------------------
# Security Group
# -----------------------------
sg = yandex.VpcSecurityGroup(
    "pulumi-sg",
    folder_id=folder_id,
    network_id=network.id,
    name="pulumi-sg",
    description="Allow SSH, HTTP, and port 5000",
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="Allow SSH",
            protocol="TCP",
            port=22,
            v4_cidr_blocks=[my_ip],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="Allow HTTP",
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="Allow app port 5000",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="Allow all outbound",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ]
)

# -----------------------------
# Boot Disk
# -----------------------------
boot_disk = yandex.ComputeDisk(
    "pulumi-boot-disk",
    folder_id=folder_id,
    zone=zone,
    size=10,
    image_id=image_id,
    name="pulumi-boot-disk"
)

# -----------------------------
# Compute Instance
# -----------------------------
vm = yandex.ComputeInstance(
    "pulumi-vm",
    folder_id=folder_id,
    zone=zone,
    platform_id="standard-v2",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        disk_id=boot_disk.id
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[sg.id]
        )
    ],
    metadata={"ssh-keys": f"ubuntu:{ssh_key}"},
    labels={"project": "pulumi-vm-task", "environment": "dev"}
)

# -----------------------------
# Outputs
# -----------------------------
pulumi.export("public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("ssh_command", vm.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh ubuntu@{ip}"
))
