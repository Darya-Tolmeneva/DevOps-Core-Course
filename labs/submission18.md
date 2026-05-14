# Lab 18 — Reproducible Builds with Nix

## 1. Nix Installation

Nix was installed using the Determinate Systems installer.

Verification:

```bash
nix --version
```

Output:

```text
nix (Determinate Nix 3.20.0) 2.34.6
```

Basic Nix usage test:

```bash
nix run nixpkgs#hello
```

Output:

```text
Hello, world!
```

## 2. Lab 1 Python App Rebuilt with Nix

The Lab 1 Flask application was copied into:

```text
labs/lab18/app_python
```

The original `requirements.txt` contained:

```text
Flask==3.1.0
```

The application also used Prometheus and JSON logging libraries, so the Nix derivation included:

```text
flask
prometheus-client
python-json-logger
```

## 3. `default.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";

  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        baseName = baseNameOf path;
      in
        baseName == "app.py"
        || baseName == "requirements.txt";
  };

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    prometheus-client
    python-json-logger
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service

    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';
}
```

### Explanation

- `buildPythonApplication` builds the Python application in a Nix-controlled environment.
- `pname` and `version` define the package name and version used in the Nix store path.
- `cleanSourceWith` filters the source so only `app.py` and `requirements.txt` affect the build hash.
- `format = "other"` is used because the app does not use `setup.py` or `pyproject.toml`.
- `propagatedBuildInputs` declares Python runtime dependencies.
- `makeWrapper` wraps the Python script with the correct interpreter and dependency path.
- The install phase copies `app.py` into `$out/bin/devops-info-service`.

## 4. Running the Nix-Built App

The first run failed because the app tried to write to `/data`, which is not writable when running locally as a normal user.

Fix:

```bash
mkdir -p ./nix-data
DATA_DIR=$PWD/nix-data PORT=5000 ./result/bin/devops-info-service
```

Health check:

```bash
curl localhost:5000/health
```

Output:

```json
{"status":"healthy","timestamp":"2026-05-14T18:46:34.586832+00:00","uptime_seconds":19}
```

Root endpoint output excerpt:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "visits": {
    "count": 1,
    "file": "/home/darya/DevOps-Core-Course/labs/lab18/app_python/nix-data/visits"
  }
}
```

Visits endpoint:

```bash
curl localhost:5000/visits
```

Output:

```json
{"file":"/home/darya/DevOps-Core-Course/labs/lab18/app_python/nix-data/visits","timestamp":"2026-05-14T18:46:45.326886+00:00","visits":1}
```

## 5. Reproducibility Proof for Nix Build

After filtering the source with `cleanSourceWith`, two builds produced the same Nix store path and the same output hash.

Store path from build 1:

```text
/nix/store/3pwza70hwzwv1z2axc3svvkxalsr8wlm-devops-info-service-1.0.0
```

Store path from build 2:

```text
/nix/store/3pwza70hwzwv1z2axc3svvkxalsr8wlm-devops-info-service-1.0.0
```

Output hash from build 1:

```text
da13e24357686ca2c6c951367badaa746b6534accff44c6b5ad6d2df25a44f0f
```

Output hash from build 2:

```text
da13e24357686ca2c6c951367badaa746b6534accff44c6b5ad6d2df25a44f0f
```

`diff` produced no output, proving the paths and hashes were identical.

### Important Finding

The first reproducibility attempt produced different store paths because `src = ./.` included generated files such as `nix-data/` and hash output files. This changed the Nix input hash.

Fixing the derivation with `cleanSourceWith` made the build reproducible by limiting the source input to only the required application files.

## 6. Lab 1 `pip install` vs Nix

| Aspect | Lab 1: pip + venv | Lab 18: Nix |
|---|---|---|
| Python version | Depends on system Python | Provided by pinned Nix packages |
| Dependency resolution | Runtime with `pip install` | Build-time through Nix |
| Transitive dependencies | Can drift unless fully locked | Included in Nix closure |
| Reproducibility | Approximate | Identical store path and hash |
| Isolation | Virtual environment | Nix sandbox and store |
| Output identity | No content-addressed output | `/nix/store/<hash>-name-version` |

`requirements.txt` gives weaker guarantees because it usually pins only direct Python dependencies. Nix captures the entire dependency closure, including Python, libraries, build tools, and package versions.

## 7. Nix Store Path Format

Example:

```text
/nix/store/3pwza70hwzwv1z2axc3svvkxalsr8wlm-devops-info-service-1.0.0
```

Meaning:

- `/nix/store` — immutable Nix store location.
- `3pwza70hwzwv1z2axc3svvkxalsr8wlm` — hash derived from build inputs.
- `devops-info-service` — package name.
- `1.0.0` — package version.

Same inputs produce the same store path.

## 8. Reproducible Docker Image with Nix

### 8.1 `docker.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "DATA_DIR=/tmp/data"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
  };

  created = "1970-01-01T00:00:01Z";
}
```

### Explanation

- `dockerTools.buildLayeredImage` creates a Docker image from Nix derivations.
- `contents = [ app ]` includes the Nix-built application closure.
- `Cmd` runs the application.
- `Env` configures the application inside the container.
- `created = "1970-01-01T00:00:01Z"` avoids non-reproducible build timestamps.

### 8.2 Nix Docker Image Build

Build output:

```bash
file result
```

Output:

```text
result: symbolic link to /nix/store/4llqh1kpzqljdlpr0gp2i1602m60m990-devops-info-service-nix.tar.gz
```

SHA256:

```bash
sha256sum result
```

Output:

```text
3140b4e0e56d62009904d20b6b822b1d9caf366149d12db6ec364c6308aa4aed  result
```

Loaded image:

```bash
docker images | grep devops-info-service-nix
```

Output:

```text
devops-info-service-nix:1.0.0         28cd08ec1f32        216MB             0B
```

### 8.3 Running the Nix Docker Image

Run command:

```bash
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
```

Health check:

```bash
curl localhost:5001/health
```

Output:

```json
{"status":"healthy","timestamp":"2026-05-14T18:53:43.845943+00:00","uptime_seconds":10}
```

Root endpoint output excerpt:

```json
{
  "system": {
    "hostname": "b9cbd311eef0",
    "python_version": "3.13.12"
  },
  "visits": {
    "count": 1,
    "file": "/tmp/data/visits"
  }
}
```

Visits endpoint:

```json
{"file":"/tmp/data/visits","timestamp":"2026-05-14T18:53:51.232202+00:00","visits":1}
```

### 8.4 Nix Docker Reproducibility Proof

The Nix Docker image was rebuilt twice.

Hash 1:

```text
3140b4e0e56d62009904d20b6b822b1d9caf366149d12db6ec364c6308aa4aed  result
```

Hash 2:

```text
3140b4e0e56d62009904d20b6b822b1d9caf366149d12db6ec364c6308aa4aed  result
```

`diff` produced no output. This proves that the Nix-built Docker image tarball is bit-for-bit reproducible.

## 9. Lab 2 Dockerfile Comparison

Traditional Docker builds were tested by building the same Dockerfile twice and saving both images.

Hash 1:

```text
f1726a7a499211768d022201add0f6251d72941eff29c331386e121f0717759f  -
```

Hash 2:

```text
b5fc80b521911ef26f5a5bf334fbcd34f981975570a56993058a764dc647b25f  -
```

Diff:

```text
1c1
< f1726a7a499211768d022201add0f6251d72941eff29c331386e121f0717759f  -
---
> b5fc80b521911ef26f5a5bf334fbcd34f981975570a56993058a764dc647b25f  -
```

The traditional Docker export hashes differed, so the exported artifacts were not bit-for-bit reproducible.

Traditional Docker container health check:

```bash
curl localhost:5000/health
```

Output:

```json
{"status":"healthy","timestamp":"2026-05-14T19:00:04.900516+00:00","uptime_seconds":3}
```

## 10. Image Size Comparison

```text
devops-info-service-nix:1.0.0         28cd08ec1f32        216MB
lab2-app:test1                        5bac4d859918        157MB
lab2-app:test2                        5bac4d859918        157MB
```

| Image | Size | Reproducibility |
|---|---:|---|
| Lab 2 Dockerfile | 157MB | Different `docker save` hashes |
| Nix dockerTools | 216MB | Identical tarball hashes |

The Nix image was larger in this run, but it provided reproducible output. The Lab 2 Docker image was smaller, but its exported artifact was not bit-for-bit identical across builds.

## 11. Docker History Comparison

Lab 2 Docker history showed build-time timestamps:

```text
IMAGE          CREATED              CREATED BY                                      SIZE
5bac4d859918   About a minute ago   CMD ["python" "app.py"]                         0B
<missing>      About a minute ago   EXPOSE [5000/tcp]                               0B
<missing>      About a minute ago   USER appuser                                    0B
<missing>      About a minute ago   RUN /bin/sh -c chown -R appuser:appuser /app…   12.6MB
<missing>      About a minute ago   COPY . . # buildkit                             12.6MB
<missing>      About a minute ago   RUN /bin/sh -c pip install --no-cache-dir -r…   12.7MB
```

Nix Docker history showed deterministic layers based on Nix store paths:

```text
IMAGE          CREATED   CREATED BY   SIZE      COMMENT
28cd08ec1f32   N/A                    411B      store paths: ['/nix/store/d34ivk4pbyz4y24c9myzjv0xrv3nki6z-devops-info-service-nix-customisation-layer']
<missing>      N/A                    11.4kB    store paths: ['/nix/store/3pwza70hwzwv1z2axc3svvkxalsr8wlm-devops-info-service-1.0.0']
<missing>      N/A                    1.08MB    store paths: ['/nix/store/10hk7srr12wgp2hqm5lai0xxr69m76b7-python3.13-flask-3.1.2']
<missing>      N/A                    2.56MB    store paths: ['/nix/store/hmgasx01bmwlz4nr23gm13q9hnqkqw19-python3.13-werkzeug-3.1.6']
<missing>      N/A                    1.85MB    store paths: ['/nix/store/2kwicy8c1ab6zw8p1ps3nnn623b68dn0-python3.13-jinja2-3.1.6']
```

Traditional Dockerfiles include build-time metadata and depend on mutable base images. Nix images are built from immutable store paths and deterministic inputs.

## 12. Bonus: Nix Flakes

### 12.1 `flake.nix`

```nix
{
  description = "DevOps Info Service - reproducible Nix build";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      devShells.${system} = {
        default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python3
            python3Packages.flask
            python3Packages.prometheus-client
            python3Packages.python-json-logger
          ];
        };
      };
    };
}
```

### 12.2 Flake Build

Command:

```bash
nix build
readlink result
```

Output:

```text
/nix/store/ssf8nh3fzlija2nnnqir1d4hd60vwzrr-devops-info-service-1.0.0
```

Docker image through flake:

```bash
nix build .#dockerImage
sha256sum result
```

Output:

```text
e0c6a5a5e981ddf4413243740005dbbf9c2baa403f0a439154f0a0f7a1f68c1a  result
```

### 12.3 `flake.lock` Evidence

`flake.lock` pinned nixpkgs to an exact Git revision and content hash.

```json
"nixpkgs": {
  "locked": {
    "lastModified": 1751274312,
    "narHash": "sha256-/bVBlRpECLVzjV19t5KMdMFWSwKLtb5RyXdjz3LJT+g=",
    "owner": "NixOS",
    "repo": "nixpkgs",
    "rev": "50ab793786d9de88ee30ec4e4c24fb4236fc2674",
    "type": "github"
  },
  "original": {
    "owner": "NixOS",
    "ref": "nixos-24.11",
    "repo": "nixpkgs",
    "type": "github"
  }
}
```

This locks the exact nixpkgs revision, including Python, Flask, build tools, and transitive dependencies.

### 12.4 Development Shell

Command:

```bash
nix develop
python --version
python -c "import flask; print(flask.__version__)"
```

Output:

```text
Python 3.12.8
3.0.3
```

The development shell provides a reproducible Python environment without manually creating a virtual environment.

## 13. Lab 10 Helm Values vs Nix Flakes

| Aspect | Helm `values.yaml` | Nix Flakes |
|---|---|---|
| Locks image tag | Yes | Can lock build input and image output |
| Locks Python version | No | Yes |
| Locks transitive dependencies | No | Yes |
| Locks build tools | No | Yes |
| Reproducibility | Tag-based | Hash-based |
| Mutable references | Image tags can be overwritten | `flake.lock` pins exact Git revision and hash |

Helm is useful for Kubernetes deployment configuration, but it does not make the container image itself reproducible. Nix Flakes solve the build reproducibility problem by locking all build inputs.

## 14. Reflection

If Nix had been used from Lab 1, the Python version and dependencies would have been reproducible from the start. This would reduce "works on my machine" problems because every developer and CI runner would use the same dependency graph.

If Nix had been used from Lab 2, the Docker image could have been produced from immutable Nix store paths instead of relying on mutable base images and build-time metadata. This would make CI/CD artifacts easier to audit and reproduce.

Nix is especially useful for:

- CI/CD pipelines;
- security audits;
- rollback scenarios;
- multi-machine development;
- long-term reproducibility.
