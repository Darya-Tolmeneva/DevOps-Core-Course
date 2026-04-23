# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview
### Ansible Version
```bash
darya@compute-vm-2-2-20-ssd-1758902485744:~$ ansible --version
ansible [core 2.16.3]
```

### Target VM OS and Version
Ubuntu 24.04 

### Role structure 
```
ansible/
├── inventory/
│   └── hosts.ini              # Static inventory
├── roles/
│   ├── common/                # Common system tasks
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   ├── docker/                # Docker installation
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   └── app_deploy/            # Application deployment
│       ├── tasks/
│       │   └── main.yml
│       ├── handlers/
│       │   └── main.yml
│       └── defaults/
│           └── main.yml
├── playbooks/
│   ├── site.yml               # Main playbook
│   ├── provision.yml          # System provisioning
│   └── deploy.yml             # App deployment
├── group_vars/
│   └── all.yml               # Encrypted variables (Vault)
├── ansible.cfg               # Ansible configuration
└── docs/
    └── LAB05.md              # Documentation
```
This project follows a modular Ansible role-based structure to ensure clarity, scalability, and reusability. Each role (`common`, `docker`, `app_deploy`) is responsible for a specific layer of configuration and contains its own tasks, defaults, and handlers.

### Why roles instead of monolithic playbooks?
Roles provide a clear and modular structure by separating tasks, variables, handlers, and defaults into reusable components. This makes the code easier to maintain, scale, and understand compared to a single large playbook. Roles also allow better reusability across different projects and environments.

## 2. Roles Documentation
### **common**

* **Purpose:** Performs basic system provisioning, including updating apt cache, installing essential packages, and setting the system timezone.
* **Variables:**

  * `common_packages` — list of packages to install (`python3-pip`, `curl`, `git`, `vim`, `htop`)
  * `common_timezone` — system timezone (`UTC` by default)
* **Handlers:** None
* **Dependencies:** None

---

### **docker**

* **Purpose:** Installs and configures Docker on the system, ensures the Docker service is running, and adds a user to the Docker group.
* **Variables:**

  * `docker_packages` — list of Docker-related packages (`docker-ce`, `docker-ce-cli`, `containerd.io`, `python3-docker`)
  * `docker_user` — user to add to the Docker group (default: `{{ ansible_user }}`)
* **Handlers:**

  * `restart docker` — restarts the Docker service when notified
* **Dependencies:** None (can run independently)

---

### **app_deploy**

* **Purpose:** Deploys the application container from Docker Hub, handles stopping/removing old containers, runs a new container, and verifies its health endpoint.
* **Variables:**

  * `app_full_image` — full Docker image with tag (`{{ docker_image }}:{{ docker_image_tag }}`)
  * `app_container_name` — container name (`{{ app_name }}`)
  * `app_port` — exposed port (default: 5000)
  * `app_restart_policy` — restart policy (`unless-stopped`)
  * `app_env` — environment variables for the container
* **Handlers:**

  * `restart application container` — restarts the container when notified
* **Dependencies:** Depends on `docker` role, as Docker must be installed before deploying the container


## 3. Idempotency Demonstration

```bash
darya@compute-vm-2-2-20-ssd-1758902485744:~/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [my-vm]

TASK [common : Update apt cache] ******************************************************************************
changed: [my-vm]

TASK [common : Install essential packages] ********************************************************************
changed: [my-vm]

TASK [common : Set timezone] **********************************************************************************
changed: [my-vm]

TASK [docker : Add Docker official GPG key] *******************************************************************
changed: [my-vm]

TASK [docker : Add Docker apt repository] *********************************************************************
changed: [my-vm]

TASK [docker : Update apt cache after adding Docker repo] *****************************************************
changed: [my-vm]

TASK [docker : Install Docker packages] ***********************************************************************
fatal: [my-vm]: FAILED! => {"cache_update_time": 1771857119, "cache_updated": false, "changed": false, "msg": "'/usr/bin/apt-get -y -o \"Dpkg::Options::=--force-confdef\" -o \"Dpkg::Options::=--force-confold\"       install 'docker-ce=5:29.2.1-1~ubuntu.24.04~noble' 'docker-ce-cli=5:29.2.1-1~ubuntu.24.04~noble' 'containerd.io=2.2.1-1~ubuntu.24.04~noble' 'python3-docker=5.0.3-1ubuntu1.1'' failed: E: Could not get lock /var/lib/dpkg/lock-frontend. It is held by process 2938 (unattended-upgr)\nE: Unable to acquire the dpkg frontend lock (/var/lib/dpkg/lock-frontend), is another process using it?\n", "rc": 100, "stderr": "E: Could not get lock /var/lib/dpkg/lock-frontend. It is held by process 2938 (unattended-upgr)\nE: Unable to acquire the dpkg frontend lock (/var/lib/dpkg/lock-frontend), is another process using it?\n", "stderr_lines": ["E: Could not get lock /var/lib/dpkg/lock-frontend. It is held by process 2938 (unattended-upgr)", "E: Unable to acquire the dpkg frontend lock (/var/lib/dpkg/lock-frontend), is another process using it?"], "stdout": "", "stdout_lines": []}

PLAY RECAP ****************************************************************************************************
my-vm                      : ok=7    changed=6    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0   

darya@compute-vm-2-2-20-ssd-1758902485744:~/DevOps-Core-Course/ansible$ nano roles/common/tasks/main.yml 
darya@compute-vm-2-2-20-ssd-1758902485744:~/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] **********************************************************************************

TASK [Gathering Facts] ****************************************************************************************
ok: [my-vm]

TASK [common : Wait for apt lock to be released] **************************************************************
ok: [my-vm]

TASK [common : Update apt cache] ******************************************************************************
ok: [my-vm]

TASK [common : Install essential packages] ********************************************************************
ok: [my-vm]

TASK [common : Set timezone] **********************************************************************************
ok: [my-vm]

TASK [docker : Add Docker official GPG key] *******************************************************************
ok: [my-vm]

TASK [docker : Add Docker apt repository] *********************************************************************
ok: [my-vm]

TASK [docker : Update apt cache after adding Docker repo] *****************************************************
changed: [my-vm]

TASK [docker : Install Docker packages] ***********************************************************************
changed: [my-vm]

TASK [docker : Ensure Docker service is started and enabled] **************************************************
ok: [my-vm]

TASK [docker : Add user to docker group] **********************************************************************
changed: [my-vm]

RUNNING HANDLER [docker : restart docker] *********************************************************************
changed: [my-vm]

PLAY RECAP ****************************************************************************************************
my-vm                      : ok=12   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

darya@compute-vm-2-2-20-ssd-1758902485744:~/DevOps-Core-Course/ansible$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ***************************************************************************************************************

TASK [Gathering Facts] *********************************************************************************************************************
ok: [my-vm]

TASK [common : Wait for apt lock to be released] *******************************************************************************************
ok: [my-vm]

TASK [common : Update apt cache] ***********************************************************************************************************
ok: [my-vm]

TASK [common : Install essential packages] *************************************************************************************************
ok: [my-vm]

TASK [common : Set timezone] ***************************************************************************************************************
ok: [my-vm]

TASK [docker : Add Docker official GPG key] ************************************************************************************************
ok: [my-vm]

TASK [docker : Add Docker apt repository] **************************************************************************************************
ok: [my-vm]

TASK [docker : Update apt cache after adding Docker repo] **********************************************************************************
ok: [my-vm]

TASK [docker : Install Docker packages] ****************************************************************************************************
ok: [my-vm]

TASK [docker : Ensure Docker service is started and enabled] *******************************************************************************
ok: [my-vm]

TASK [docker : Add user to docker group] ***************************************************************************************************
ok: [my-vm]

PLAY RECAP *********************************************************************************************************************************
my-vm                      : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```

### Analysis: What changed first time? What didn't change second time?
During the first run, several tasks were marked as changed because the system was being configured for the first time, but the playbook initially failed due to the apt lock held by `unattended-upgrades`. After fixing the apt lock, tasks that didn’t finish the first time (e.g., Docker installation) were applied and thus marked as changed. On the third run, all tasks returned ok with changed=0, confirming that the roles are fully idempotent

### What makes your roles idempotent?
The roles are idempotent because they use Ansible modules such as `apt`, `service`, and `user`, which check the current system state before applying changes. If the desired state is already achieved, Ansible does not perform the action again. This ensures that repeated playbook executions do not cause unnecessary changes.

## 4. Ansible Vault Usage

### How store credentials securely
Credentials are stored in an encrypted `group_vars/all.yml` file using Ansible Vault. This ensures that sensitive data such as Docker Hub credentials is not stored in plain text and remains protected even if the repository is shared.

### Vault password management strategy
The Vault password is not stored in version control and is provided securely during execution using `--ask-vault-pass` or a protected password file. In a production environment, the password would be managed through a secure secret management system or CI/CD environment variables.

### Example of encrypted file
```bash
darya@compute-vm-2-2-20-ssd-1758902485744:~/DevOps-Core-Course/ansible$ cat group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
63366361613166383333663764663561353764393731653738356338353039663433306166623336
6162373536313438336263633565653437343761633566390a623935663235363735333730303535
63373238373035636661616564656232626532316561636236633537653263663132356634343932
3331383330653863660a393637306434613038316632313438653832316266333963656463313639
63316663633965393337356538346632326163653862626334396130626438643535353631653937
38646562313237363836303739663361316134326266313435333030346361316662323831646336
38343866623835396139393062316633376135373761666134386239393630343762353562353638
39663739313036363836343665313731623262363737313165356536643435613565393564666361
37303366336265336335313136323164353532306566343763346237656631303165343464333539
33663965376265393839663438656338303235653562333664346531643461363930393539386632
36653666343839626264353933623539336632393632663738373638636237353339653535326430
34343437303039303130636261393563663331663439306438306565366266373162333033653635
30396138643433663530616165323065626265653137323039353433323338396134613130316165
37633835646330326133346633303839343163663863383937663131333039336430386137326135
35623665646435633831653561326132633032653836616262336639613862336636363362616434
36393962393739313939333663326662383761623038643130323339306466383438313733383533
6464
```

## Why Ansible Vault is important
Ansible Vault is important because it allows you to securely store sensitive data, such as passwords, API tokens, and credentials, in encrypted files. This prevents confidential information from being exposed in version control while still allowing Ansible to use it during deployments. Using Vault ensures both security and compliance in automated infrastructure management.

## 5. Deployment Verification

```bash
darya@compute-vm-2-2-20-ssd-1758902485744:~/DevOps-Core-Course/ansible$ ansible-playbook playbooks/deploy.yml --ask-vault-pass
Vault password: 

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [my-vm]

TASK [app_deploy : Log in to Docker Hub] ***************************************
ok: [my-vm]

TASK [app_deploy : Pull Docker image] ******************************************
changed: [my-vm]

TASK [app_deploy : Stop existing container (if running)] ***********************
fatal: [my-vm]: FAILED! => {"changed": false, "msg": "Cannot create container when image is not specified!"}
...ignoring

TASK [app_deploy : Remove old container (if exists)] ***************************
ok: [my-vm]

TASK [app_deploy : Run new container] ******************************************
changed: [my-vm]

TASK [app_deploy : Wait for application port to be open] ***********************
ok: [my-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [my-vm]

RUNNING HANDLER [app_deploy : restart application container] *******************
changed: [my-vm]

PLAY RECAP *********************************************************************
my-vm                      : ok=9    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1

darya@compute-vm-2-2-20-ssd-1758902485744:~/DevOps-Core-Course/ansible$ ansible webservers -a "docker ps" --ask-vault-pass
Vault password: 
my-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                           COMMAND           CREATED         STATUS         PORTS                              NAMES
a41b41f7ac27   din19pg/python-service:latest   "python app.py"   5 minutes ago   Up 4 minutes   0.0.0.0:5000->5000/tcp, 8000/tcp   python-service
darya@compute-vm-2-2-20-ssd-1758902485744:~/DevOps-Core-Course/ansible$ curl http://93.77.180.237:5000/health
{"status":"healthy","timestamp":"2026-02-23T19:17:22.573982+00:00","uptime_seconds":317}
darya@compute-vm-2-2-20-ssd-1758902485744:~/DevOps-Core-Course/ansible$ curl http://93.77.180.237:5000/
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"51.250.111.212","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-02-23T19:17:48.512557+00:00","timezone":"UTC","uptime_human":"0 hours, 5 minutes","uptime_seconds":343},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":2,"hostname":"a41b41f7ac27","platform":"Linux","platform_version":"#100-Ubuntu SMP PREEMPT_DYNAMIC Tue Jan 13 16:40:06 UTC 2026","python_version":"3.12.12"}}
```

## 6. Key Decisions

### Why use roles instead of plain playbooks?
Roles provide a structured and modular way to organize Ansible code. They separate tasks, variables, handlers, and defaults into logical components, making the project cleaner and easier to maintain. This structure is especially useful in larger automation projects.

### How do roles improve reusability?
Roles encapsulate specific functionality (e.g., Docker installation or app deployment), allowing them to be reused across multiple projects or environments. By separating logic from configuration through variables, the same role can work in different setups without modification.

### What makes a task idempotent?
A task is idempotent if running it multiple times produces the same result without causing additional changes. In Ansible, this is achieved by using declarative modules (like `apt`, `docker_container`, `service`) that check the current state before making changes.

### How do handlers improve efficiency?
Handlers run only when notified by a task that has made a change. This prevents unnecessary actions, such as restarting a service when no configuration was modified, improving overall efficiency and stability.

### Why is Ansible Vault necessary?
Ansible Vault is used to securely store sensitive data such as passwords, API tokens, and credentials. It ensures that confidential information is encrypted in version control while still being usable during deployment.
