# Lab 01 — Python Web Application

## Framework Selection

**Chosen framework: Flask**

Flask was selected because it is lightweight, easy to understand, and well-suited for small production-ready services such as health checks, monitoring endpoints, and internal DevOps tools. It allows rapid development without unnecessary complexity.

### Framework Comparison

| Framework | Advantages                    | Disadvantages                      | Use Case                     |
| --------- | ----------------------------- | ---------------------------------- | ---------------------------- |
| **Flask** | Simple, lightweight, flexible | No built-in async, fewer built-ins | Small services, DevOps tools |
| **FastAPI**   | Async support, OpenAPI docs   | Slightly steeper learning curve    | High-performance APIs        |
| **Django**    | Full-featured, ORM included   | Overkill for small services        | Large web applications       |

Flask provides the best balance between simplicity and production readiness for this laboratory work.

---

## Best Practices Applied

### 1. Clean Code Organization

**What was done:**

* Logical separation of configuration, helpers, routes, and error handlers
* Clear and descriptive function names
* Imports grouped according to PEP 8

**Code example:**

```python
START_TIME = datetime.now(timezone.utc)

def get_system_info():
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'architecture': platform.machine(),
        'python_version': platform.python_version()
    }
```

**Why it matters:**
Clean code improves readability, maintainability, and reduces the likelihood of bugs.

---

### 2. Configuration via Environment Variables

**What was done:**
Application host, port, and debug mode are configurable through environment variables.

**Code example:**

```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Why it matters:**
Environment-based configuration is essential for deploying applications across different environments (local, CI, containers, Kubernetes).

---

### 3. Error Handling

**What was done:**
Custom JSON responses for 404 and 500 errors.

**Code example:**

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404
```

**Why it matters:**
Consistent error handling improves debugging, observability, and user experience.

---

### 4. Logging

**What was done:**
Structured logging is enabled for application startup and incoming requests.

**Code example:**

```python
logger.info('Application starting...')
logger.info(f"Request: {request.method} {request.path}")
```

**Why it matters:**
Logging is critical for monitoring, troubleshooting, and auditing in production systems.

---

## API Documentation

### GET /

**Description:** Returns service metadata, system information, runtime details, and request context.

**Request example:**

```bash
curl http://localhost:5000/
```

**Response example (shortened):**

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "hostname": "my-host",
    "platform": "Linux"
  }
}
```

---

### GET /health

**Description:** Health check endpoint used for monitoring and probes.

**Request example:**

```bash
curl http://localhost:5000/health
```

**Response example:**

```json
{
  "status": "healthy",
  "uptime_seconds": 3600
}
```

---

### Testing Commands

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/ | jq
```
![Testing](./screenshots/test.png)
---

## Testing Evidence

The following evidence demonstrates correct application behavior:

* Screenshot of `/` endpoint returning full JSON response
* Screenshot of `/health` endpoint returning healthy status
* Screenshot of formatted JSON output using `jq`
* Terminal output showing successful application startup

All screenshots are stored in the `docs/screenshots/` directory.

---

## Challenges & Solutions

### Challenge: Timezone consistency

**Problem:** Mixing local time and UTC could lead to inconsistent timestamps.

**Solution:**
All timestamps are generated using `datetime.now(timezone.utc)` to ensure consistency and correctness.

---

## GitHub Community

Starring repositories helps support open-source contributors and increases the visibility of useful projects. Following developers allows engineers to learn best practices, stay updated with industry trends, and grow professionally through community collaboration.
