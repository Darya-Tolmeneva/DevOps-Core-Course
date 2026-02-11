# DevOps Info Service

![CI Workflow](https://github.com/Darya-Tolmeneva/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)

A lightweight Python web application that provides system, runtime, and service information via HTTP endpoints.  
Developed as part of **Lab 01 — Python Web Application** for a DevOps course.

---

## 🚀 Features

- Service metadata endpoint
- Detailed system information (OS, CPU, Python version)
- Runtime uptime tracking
- Health check endpoint for monitoring
- JSON responses suitable for automation and probes

---

## 🛠 Tech Stack

- Python 3.10+
- Flask 3.1.0

---

## 📦 Installation

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
```
---

## Docker

This application can be built and run using Docker.

### Build the image locally

Use the Docker build command to create an image from the Dockerfile:

`docker build -t <image-name> <path-to-app>`

### Run the container

Run the container with port mapping to access the service from the host machine:

`docker run -p <host-port>:<container-port> <image-name>`

### Pull the image from Docker Hub

The image can be pulled from Docker Hub using:

`docker pull <dockerhub-username>/<repository>:<tag>`
