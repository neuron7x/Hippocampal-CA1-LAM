# Configuration Guide

## MLSDM Configuration System

MLSDM uses Pydantic Settings for configuration management with environment variable support.

## Configuration Priority

Configuration values are loaded in the following priority order (highest to lowest):

1. Environment variables
2. Configuration files (future)
3. Default values

## Environment Variables

All configuration can be set via environment variables with the prefix `MLSDM_`.

### Global Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MLSDM_ENVIRONMENT` | string | `development` | Deployment environment (`development`, `staging`, `production`) |
| `MLSDM_DEBUG` | boolean | `false` | Enable debug mode |

### Server Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MLSDM_SERVER__HOST` | string | `0.0.0.0` | Server bind host |
| `MLSDM_SERVER__PORT` | integer | `8000` | Server port |
| `MLSDM_SERVER__WORKERS` | integer | `1` | Number of worker processes |
| `MLSDM_SERVER__LOG_LEVEL` | string | `info` | Logging level |
| `MLSDM_SERVER__RELOAD` | boolean | `false` | Enable auto-reload (development) |

### Security Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MLSDM_SECURITY__AUTH_MODE` | string | `api_key` | Authentication mode (`api_key`, `oidc`, `none`) |
| `MLSDM_SECURITY__API_KEY` | string | - | API key for authentication |
| `MLSDM_SECURITY__OIDC_ISSUER` | string | - | OIDC issuer URL |
| `MLSDM_SECURITY__OIDC_AUDIENCE` | string | - | OIDC audience |
| `MLSDM_SECURITY__MTLS_ENABLED` | boolean | `false` | Enable mTLS verification |
| `MLSDM_SECURITY__MTLS_CA_CERT` | path | - | Path to CA certificate |
| `MLSDM_SECURITY__MTLS_CLIENT_CERT` | path | - | Path to client certificate |
| `MLSDM_SECURITY__MTLS_CLIENT_KEY` | path | - | Path to client key |

### Neuro Engine Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MLSDM_NEURO__N_NEURONS` | integer | `100` | Number of neurons in network |
| `MLSDM_NEURO__SEED` | integer | `42` | Random seed for reproducibility |
| `MLSDM_NEURO__DT` | float | `0.1` | Time step in milliseconds |

### Storage Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MLSDM_STORAGE__BACKEND` | string | `file` | Storage backend (`file`, `sqlite`, `postgres`, `redis`) |
| `MLSDM_STORAGE__FILE_PATH` | path | `/tmp/mlsdm_state` | Path for file-based storage |
| `MLSDM_STORAGE__DATABASE_URL` | string | - | Database connection URL |
| `MLSDM_STORAGE__REDIS_URL` | string | - | Redis connection URL |

## Configuration Examples

### Development Environment

```bash
export MLSDM_ENVIRONMENT=development
export MLSDM_DEBUG=true
export MLSDM_SECURITY__AUTH_MODE=none
export MLSDM_SERVER__RELOAD=true
export MLSDM_SERVER__LOG_LEVEL=debug

python -m src.mlsdm.serve serve --mode neuro
```

### Production Environment with API Key

```bash
export MLSDM_ENVIRONMENT=production
export MLSDM_SECURITY__AUTH_MODE=api_key
export MLSDM_SECURITY__API_KEY="your-secure-api-key-here"
export MLSDM_SERVER__WORKERS=4
export MLSDM_SERVER__LOG_LEVEL=info

python -m src.mlsdm.serve serve --mode api --port 8000
```

### Production with mTLS

```bash
export MLSDM_ENVIRONMENT=production
export MLSDM_SECURITY__AUTH_MODE=api_key
export MLSDM_SECURITY__API_KEY="your-api-key"
export MLSDM_SECURITY__MTLS_ENABLED=true
export MLSDM_SECURITY__MTLS_CA_CERT=/path/to/ca.crt
export MLSDM_SECURITY__MTLS_CLIENT_CERT=/path/to/client.crt
export MLSDM_SECURITY__MTLS_CLIENT_KEY=/path/to/client.key

python -m src.mlsdm.serve serve --mode api
```

## CLI Commands

### Validate Configuration

Check if configuration is valid:

```bash
python -m src.mlsdm.serve config validate
```

Output:
```
✓ Configuration is valid
  Environment: production
  Auth mode: api_key
  Storage backend: file
```

### Print Effective Configuration

Show all effective configuration values:

```bash
python -m src.mlsdm.serve config print-effective
```

Output:
```
Effective Configuration:
==================================================
Environment: production
Debug: False

Server:
  Host: 0.0.0.0
  Port: 8000
  Workers: 4
  Log Level: info

Security:
  Auth Mode: api_key
  mTLS Enabled: true

Neuro Engine:
  N Neurons: 100
  Seed: 42
  dt: 0.1

Storage:
  Backend: file
  File Path: /tmp/mlsdm_state
```

## Docker Configuration

When running in Docker, pass environment variables:

```bash
docker run -e MLSDM_SECURITY__API_KEY=key \
           -e MLSDM_ENVIRONMENT=production \
           -p 8000:8000 \
           hippocampal-ca1-lam:latest
```

Or use env file:

```bash
# .env file
MLSDM_ENVIRONMENT=production
MLSDM_SECURITY__AUTH_MODE=api_key
MLSDM_SECURITY__API_KEY=your-key-here
MLSDM_SERVER__WORKERS=4

# Run with env file
docker run --env-file .env -p 8000:8000 hippocampal-ca1-lam:latest
```

## Kubernetes Configuration

Use ConfigMap and Secrets:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mlsdm-config
data:
  MLSDM_ENVIRONMENT: "production"
  MLSDM_SERVER__WORKERS: "4"
  MLSDM_NEURO__N_NEURONS: "1000"
---
apiVersion: v1
kind: Secret
metadata:
  name: mlsdm-secrets
type: Opaque
stringData:
  MLSDM_SECURITY__API_KEY: "your-secure-api-key"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlsdm-neuro
spec:
  template:
    spec:
      containers:
      - name: mlsdm
        envFrom:
        - configMapRef:
            name: mlsdm-config
        - secretRef:
            name: mlsdm-secrets
```

## Best Practices

1. **Never commit secrets**: Use environment variables or secret management systems
2. **Use separate configs per environment**: development, staging, production
3. **Validate configuration on startup**: Run `config validate` in your deployment pipeline
4. **Use mTLS in production**: Enable mutual TLS for service-to-service communication
5. **Monitor configuration changes**: Log effective configuration on startup
6. **Use strong API keys**: Generate cryptographically secure keys (32+ characters)

## Troubleshooting

### Configuration not loading

Check environment variables are properly set:
```bash
env | grep MLSDM_
```

### Invalid configuration

Run validation to see what's wrong:
```bash
python -m src.mlsdm.serve config validate
```

### Debug configuration loading

Enable debug mode:
```bash
export MLSDM_DEBUG=true
python -m src.mlsdm.serve config print-effective
```

## See Also

- [SDK Usage Guide](SDK_USAGE.md)
- [Deployment Runbook](RUNBOOK.md)
- [API Reference](API_REFERENCE.md)
