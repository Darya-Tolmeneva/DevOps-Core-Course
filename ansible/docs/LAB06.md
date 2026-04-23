# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Darya Tolmeneva
**Date:** 2026-03-05
**Lab Points:** 10

---

## Task 1: Blocks & Tags (2 pts)

### `common` role
Refactored `roles/common/tasks/main.yml` using:
- `block` for package tasks with tags `common`, `packages`
- `block` for user tasks with tags `common`, `users`
- `rescue` for apt-related failure recovery
- `always` for completion logging in `/tmp`

### `docker` role
Refactored `roles/docker/tasks/main.yml` using:
- installation block with tags `docker`, `docker_install`
- configuration block with tags `docker`, `docker_config`
- `rescue` for retry logic
- `always` to ensure Docker service is enabled and started

### Tag verification
Commands used:
```bash
ansible-playbook playbooks/provision.yml --list-tags
ansible-playbook playbooks/provision.yml --tags "docker" --list-tasks
ansible-playbook playbooks/provision.yml --tags "docker_install" --list-tasks
ansible-playbook playbooks/provision.yml --tags "packages" --list-tasks
ansible-playbook playbooks/provision.yml --skip-tags "common" --list-tasks
```

Observed tags:
```text
TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

### Research answers
**What happens if rescue block also fails?**  
The block is still considered failed. `always` still runs.

**Can you have nested blocks?**  
Yes.

**How do tags inherit to tasks within blocks?**  
Tags applied to a block are inherited by tasks inside that block.

---

## Task 2: Docker Compose (3 pts)

### Migration
The application deployment was migrated from direct container management to Docker Compose.

### Role dependency
Added dependency in:
```yaml
roles/app_deploy/meta/main.yml
```

```yaml
---
dependencies:
  - role: docker
```

### Compose deployment
The deployment role now:
1. creates the application directory
2. templates `docker-compose.yml`
3. removes legacy standalone container if needed
4. deploys using `community.docker.docker_compose_v2`
5. waits for the service port
6. verifies `/health`

### Variables used
Configured variables include:
- `app_name`
- `docker_image`
- `docker_image_tag`
- `app_port`
- `app_internal_port`
- `app_secret_key`

### Evidence
Commands used:
```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
docker ps
docker compose -f /opt/python-service/docker-compose.yml ps
curl http://localhost:5000
curl http://localhost:5000/health
```

Successful deployment recap:
```text
my-vm : ok=18 changed=2 unreachable=0 failed=0 skipped=4 rescued=0 ignored=0
```

### Idempotency
The deploy playbook was executed multiple times. The second run showed mostly `ok` instead of `changed`, confirming idempotent behavior.

### Research answers
**Difference between `restart: always` and `restart: unless-stopped`?**  
`always` restarts containers even after manual stop when Docker restarts. `unless-stopped` restarts automatically unless the container was manually stopped.

**How do Docker Compose networks differ from Docker bridge networks?**  
Compose creates project-scoped networks automatically and manages service connectivity inside the project.

**Can you reference Ansible Vault variables in the template?**  
Yes.

---

## Task 3: Wipe Logic (1 pt)

### Implementation
Wipe logic was implemented in:
- `roles/app_deploy/tasks/wipe.yml`
- included at the beginning of `roles/app_deploy/tasks/main.yml`

### Safety mechanism
Wipe execution is controlled by:
- variable: `app_deploy_wipe`
- tag: `app_deploy_wipe`

This prevents accidental destructive execution.

### Test scenarios

**Scenario 1: Normal deployment**
```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```
Result: wipe tasks skipped, application deployed normally.

**Scenario 2: Wipe only**
```bash
ansible-playbook playbooks/deploy.yml -e "app_deploy_wipe=true" --tags app_deploy_wipe --ask-vault-pass
```
Result: application removed, deployment tasks skipped.

**Scenario 3: Clean reinstall**
```bash
ansible-playbook playbooks/deploy.yml -e "app_deploy_wipe=true" --ask-vault-pass
```
Result: old deployment removed first, then fresh deployment created.

**Scenario 4: Safety check**
```bash
ansible-playbook playbooks/deploy.yml --tags app_deploy_wipe --ask-vault-pass
```
Result: wipe block selected by tag but skipped because the variable remained `false`.

### Research answers
**Why use both variable and tag?**  
To create double protection for destructive actions.

**What is the difference between `never` tag and this approach?**  
This approach uses both explicit task selection and a boolean confirmation variable.

**Why must wipe logic come before deployment?**  
So clean reinstall works correctly in one run.

**When would you want clean reinstallation vs rolling update?**  
Clean reinstall is useful when state is broken or needs full reset. Rolling update is better when minimizing downtime.

**How would you extend this to wipe Docker images and volumes too?**  
By adding extra tasks to remove images and volumes after stopping the Compose project.

---

## Task 4: CI/CD (3 pts)

### Workflow
Created:
```text
.github/workflows/ansible-deploy.yml
```

Workflow stages:
1. checkout repository
2. install Python + Ansible + collections
3. run `ansible-lint`
4. prepare vault password file
5. deploy playbook
6. verify application with `curl`

### Secrets
Configured / required secrets:
- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER`

### CI/CD issue found
The VM was provisioned with Terraform and SSH ingress was restricted to `var.my_ip`.  
Because of that, GitHub-hosted runners could not connect to the VM even though local SSH worked.

### Research answers
**What are the security implications of storing SSH keys in GitHub Secrets?**  
The key becomes a sensitive deployment credential and must be scoped carefully.

**How would you implement staging → production deployment?**  
Using separate environments, inventories, approvals, and staged workflow jobs.

**What would you add to make rollbacks possible?**  
Versioned image tags and the ability to redeploy the previous known-good version.

**How does self-hosted runner improve security compared to GitHub-hosted?**  
It avoids opening SSH access for GitHub-hosted runners and keeps execution inside the target environment.

---

## Task 5: Documentation

This file serves as the main Lab 6 documentation.

---

## Testing Results

Commands completed:
```bash
ansible-playbook playbooks/provision.yml --list-tags
ansible-playbook playbooks/provision.yml --tags "docker" --list-tasks
ansible-playbook playbooks/provision.yml --tags "docker_install" --list-tasks
ansible-playbook playbooks/provision.yml --tags "packages" --list-tasks
ansible-playbook playbooks/provision.yml --skip-tags "common" --list-tasks
ansible-playbook playbooks/deploy.yml --syntax-check --ask-vault-pass
ansible-lint playbooks/*.yml roles/*
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

`ansible-lint` result:
```text
Passed: 0 failure(s), 0 warning(s) on 17 files. Last profile that met the validation criteria was 'production'.
```

---

## Challenges & Solutions

**1. Variable mismatches after migration to Compose**  
Fixed by aligning variable names between defaults, tasks, and templates.

**2. Conflict with old standalone container**  
Fixed by removing the old container before Compose deployment.

**3. YAML rendering issues in Compose template**  
Fixed by correcting the template structure and rendered values.

**4. GitHub Actions could not SSH into the VM**  
Cause: Terraform security group allowed port 22 only from `var.my_ip`.

---

## Summary

Lab 6 extended the Lab 5 Ansible project with:
- blocks and tags
- Docker Compose deployment
- role dependency
- wipe logic
- CI/CD workflow
- lint-clean configuration
