# Builder Pattern Example

This example demonstrates the new fluent Builder API for creating FastAPI applications.

## Features Demonstrated

- **Builder Pattern**: Chainable, intuitive API for app configuration
- **Automatic Metrics**: Prometheus-compatible `/metrics` endpoint
- **Security Headers**: Auto-configured for production
- **Request ID**: Every request gets a unique ID in `X-Request-ID` header
- **Request Timing**: Response time in `X-Response-Time` header
- **Health Check**: Configurable health endpoint

## Running the Example

```bash
# Install dependencies
pip install fastapi-bootstrap[all]

# Run the server
cd examples/builder
uvicorn app:app --reload
```

## Endpoints

- `GET /` - Root endpoint
- `GET /users` - List users
- `GET /users/{id}` - Get specific user
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Swagger UI

## Builder Pattern vs Traditional

### Traditional (still supported)
```python
app = create_app(
    api_list=[router],
    title="My API",
    version="1.0.0",
    stage="prod",
    cors_origins=["https://myapp.com"],
)
```

### Builder Pattern (new)
```python
app = (
    bootstrap()
    .title("My API")
    .version("1.0.0")
    .stage("prod")
    .with_cors(origins=["https://myapp.com"])
    .with_security_headers()
    .with_metrics()
    .add_router(router)
    .build()
)
```

## Response Headers

When making requests, you'll see these headers in responses:

```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Response-Time: 1.23ms
```

## Metrics Output

Visit `/metrics` to see Prometheus-format metrics:

```
# HELP fastapi_bootstrap_http_requests_total Total HTTP requests
# TYPE fastapi_bootstrap_http_requests_total counter
fastapi_bootstrap_http_requests_total{method="GET",path="/",status="200"} 5

# HELP fastapi_bootstrap_http_request_duration_seconds HTTP request duration
# TYPE fastapi_bootstrap_http_request_duration_seconds histogram
fastapi_bootstrap_http_request_duration_seconds_bucket{method="GET",path="/",le="0.005"} 3
...
```
