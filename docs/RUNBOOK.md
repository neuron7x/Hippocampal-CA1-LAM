# MLSDM Deployment Runbook

## Overview

This runbook provides step-by-step instructions for deploying MLSDM services (API and Neuro Engine) in various environments.

## Prerequisites

- Python 3.8+
- Docker (for containerized deployment)
- Kubernetes cluster (for K8s deployment)
- Required dependencies installed

## Local Development Deployment

### Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
export MLSDM_ENVIRONMENT=development
export MLSDM_DEBUG=true
export MLSDM_SECURITY__AUTH_MODE=none
```

3. **Start API service**:
```bash
python -m src.mlsdm.serve serve --mode api --reload
```

4. **Start Neuro Engine** (in another terminal):
```bash
python -m src.mlsdm.serve serve --mode neuro --port 8001 --reload
```

5. **Verify deployment**:
```bash
# Check API health
curl http://localhost:8000/health

# Check Neuro Engine health
curl http://localhost:8001/healthz
```

## Docker Deployment

### Build Image

```bash
# Build production image
docker build -t mlsdm:latest -f docker/Dockerfile .

# Build with version tag
docker build -t mlsdm:1.0.0 -f docker/Dockerfile .
```

### Run API Service

```bash
docker run -d \
  --name mlsdm-api \
  -p 8000:8000 \
  -e MLSDM_ENVIRONMENT=production \
  -e MLSDM_SECURITY__AUTH_MODE=api_key \
  -e MLSDM_SECURITY__API_KEY="${API_KEY}" \
  mlsdm:latest \
  python -m src.mlsdm.serve serve --mode api
```

### Run Neuro Engine Service

```bash
docker run -d \
  --name mlsdm-neuro \
  -p 8001:8000 \
  -e MLSDM_ENVIRONMENT=production \
  -e MLSDM_NEURO__N_NEURONS=1000 \
  mlsdm:latest \
  python -m src.mlsdm.serve serve --mode neuro
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    image: mlsdm:latest
    ports:
      - "8000:8000"
    environment:
      MLSDM_ENVIRONMENT: production
      MLSDM_SECURITY__AUTH_MODE: api_key
      MLSDM_SECURITY__API_KEY: ${API_KEY}
    command: python -m src.mlsdm.serve serve --mode api
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  neuro:
    image: mlsdm:latest
    ports:
      - "8001:8000"
    environment:
      MLSDM_ENVIRONMENT: production
      MLSDM_NEURO__N_NEURONS: 1000
      MLSDM_NEURO__SEED: 42
    command: python -m src.mlsdm.serve serve --mode neuro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

Deploy with:
```bash
API_KEY=your-secure-key docker-compose up -d
```

## Kubernetes Deployment

### Create Namespace

```bash
kubectl create namespace mlsdm
```

### Deploy ConfigMap

Create `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mlsdm-config
  namespace: mlsdm
data:
  MLSDM_ENVIRONMENT: "production"
  MLSDM_SERVER__WORKERS: "4"
  MLSDM_NEURO__N_NEURONS: "1000"
  MLSDM_NEURO__SEED: "42"
```

Apply:
```bash
kubectl apply -f k8s/configmap.yaml
```

### Deploy Secrets

Create secrets:
```bash
kubectl create secret generic mlsdm-secrets \
  --from-literal=MLSDM_SECURITY__API_KEY="your-secure-api-key" \
  -n mlsdm
```

### Deploy API Service

Create `k8s/api-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlsdm-api
  namespace: mlsdm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mlsdm-api
  template:
    metadata:
      labels:
        app: mlsdm-api
    spec:
      containers:
      - name: api
        image: mlsdm:1.0.0
        ports:
        - containerPort: 8000
        command:
        - python
        - -m
        - src.mlsdm.serve
        - serve
        - --mode
        - api
        envFrom:
        - configMapRef:
            name: mlsdm-config
        - secretRef:
            name: mlsdm-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: mlsdm-api
  namespace: mlsdm
spec:
  selector:
    app: mlsdm-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

Apply:
```bash
kubectl apply -f k8s/api-deployment.yaml
```

### Deploy Neuro Engine Service

Create `k8s/neuro-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlsdm-neuro
  namespace: mlsdm
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mlsdm-neuro
  template:
    metadata:
      labels:
        app: mlsdm-neuro
    spec:
      containers:
      - name: neuro
        image: mlsdm:1.0.0
        ports:
        - containerPort: 8000
        command:
        - python
        - -m
        - src.mlsdm.serve
        - serve
        - --mode
        - neuro
        envFrom:
        - configMapRef:
            name: mlsdm-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: mlsdm-neuro
  namespace: mlsdm
spec:
  selector:
    app: mlsdm-neuro
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

Apply:
```bash
kubectl apply -f k8s/neuro-deployment.yaml
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n mlsdm

# Check services
kubectl get svc -n mlsdm

# Check logs
kubectl logs -f deployment/mlsdm-api -n mlsdm
kubectl logs -f deployment/mlsdm-neuro -n mlsdm
```

## Production Checklist

### Before Deployment

- [ ] Security configured (API keys, mTLS)
- [ ] Resource limits set
- [ ] Health checks configured
- [ ] Logging configured
- [ ] Metrics collection enabled
- [ ] Secrets properly managed
- [ ] Configuration validated: `mlsdm config validate`

### After Deployment

- [ ] Health endpoints responding: `/health`, `/healthz`
- [ ] Metrics available: `/metrics`
- [ ] Authentication working (test with invalid key)
- [ ] Monitor memory usage
- [ ] Monitor response times
- [ ] Set up alerts for failures

## Monitoring

### Health Check Endpoints

- **Liveness**: `/health` or `/healthz` - Returns 200 if service is alive
- **Readiness**: `/health/ready` or `/readyz` - Returns 200 if ready to serve
- **Metrics**: `/metrics` - Returns process metrics

### Prometheus Metrics (Future)

Configure Prometheus to scrape `/metrics` endpoint.

### Logging

Logs are written to stdout/stderr. In Kubernetes, view with:
```bash
kubectl logs -f deployment/mlsdm-api -n mlsdm
```

## Troubleshooting

### Service not starting

1. Check configuration:
```bash
python -m src.mlsdm.serve config validate
```

2. Check logs for errors:
```bash
# Docker
docker logs mlsdm-api

# Kubernetes
kubectl logs deployment/mlsdm-api -n mlsdm
```

### High memory usage

1. Check current memory:
```bash
curl http://localhost:8000/metrics
```

2. Reduce neuron count if needed:
```bash
export MLSDM_NEURO__N_NEURONS=50
```

### Authentication failures

1. Verify API key is set:
```bash
python -m src.mlsdm.serve config print-effective | grep API_KEY
```

2. Test with correct key:
```bash
curl -H "Authorization: Bearer your-key" http://localhost:8000/api/v1/info
```

## Backup and Recovery

### State Backup

If using file storage:
```bash
# Backup state
tar -czf mlsdm-state-backup.tar.gz /tmp/mlsdm_state

# Restore state
tar -xzf mlsdm-state-backup.tar.gz -C /
```

## Upgrade Procedure

1. **Backup current state** (see above)
2. **Update image** to new version
3. **Apply configuration changes** if needed
4. **Rolling update** (Kubernetes automatically handles this)
5. **Verify health checks** after update
6. **Monitor metrics** for anomalies

### Kubernetes Rolling Update

```bash
kubectl set image deployment/mlsdm-api api=mlsdm:1.1.0 -n mlsdm
kubectl rollout status deployment/mlsdm-api -n mlsdm
```

### Rollback

```bash
kubectl rollout undo deployment/mlsdm-api -n mlsdm
```

## Security Best Practices

1. **Use strong API keys**: 32+ characters, cryptographically random
2. **Enable mTLS** for production inter-service communication
3. **Rotate keys regularly**: Update secrets every 90 days
4. **Use Kubernetes secrets**: Never commit secrets to git
5. **Network policies**: Restrict traffic between services
6. **Regular security scans**: Use vulnerability scanners

## See Also

- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [SDK Usage](SDK_USAGE.md)
- [API Reference](API_REFERENCE.md)
