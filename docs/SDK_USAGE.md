# SDK Usage Guide

## Python SDK for MLSDM Neuro Engine

The MLSDM Python SDK provides a simple and intuitive interface for interacting with the Neuro Engine service.

## Installation

```bash
pip install Hippocampal-CA1-LAM
```

## Quick Start

### Synchronous Client

```python
from src.mlsdm.sdk import NeuroEngineClient

# Initialize client
client = NeuroEngineClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"  # Optional
)

# Check health
health = client.health()
print(health)  # {'status': 'alive', 'timestamp': ...}

# Get metrics
metrics = client.metrics()
print(f"Memory: {metrics['memory_mb']:.2f} MB")

# Generate neural response
response = client.generate(
    input_pattern=[0.1, 0.2, 0.3, 0.4, 0.5],
    steps=10
)
print(f"Output: {response['output_pattern']}")
print(f"Processing time: {response['processing_time_ms']:.2f} ms")

# Get engine info
info = client.info()
print(f"Neurons: {info['network']['n_neurons']}")

# Close client
client.close()
```

### Using Context Manager

```python
from src.mlsdm.sdk import NeuroEngineClient

with NeuroEngineClient(base_url="http://localhost:8000") as client:
    health = client.health()
    print(health)
    
    response = client.generate([0.1, 0.2, 0.3])
    print(response)
```

### Async Client

```python
import asyncio
from src.mlsdm.sdk import AsyncNeuroEngineClient

async def main():
    async with AsyncNeuroEngineClient(base_url="http://localhost:8000") as client:
        health = await client.health()
        print(health)
        
        response = await client.generate([0.1, 0.2, 0.3])
        print(response)

asyncio.run(main())
```

## Configuration

### Authentication

The SDK supports multiple authentication modes:

#### API Key Authentication

```python
client = NeuroEngineClient(
    base_url="http://localhost:8000",
    api_key="your-api-key-here"
)
```

#### No Authentication (Development)

```python
client = NeuroEngineClient(
    base_url="http://localhost:8000"
    # No api_key parameter
)
```

### Timeouts

Configure request timeout:

```python
client = NeuroEngineClient(
    base_url="http://localhost:8000",
    timeout=60.0  # 60 seconds
)
```

## API Reference

### NeuroEngineClient

#### `__init__(base_url, api_key=None, timeout=30.0)`

Initialize the client.

**Parameters:**
- `base_url` (str): Base URL of the neuro engine service
- `api_key` (str, optional): API key for authentication
- `timeout` (float): Request timeout in seconds

#### `health() -> dict`

Check service health.

**Returns:**
- dict: Health status with `status` and `timestamp` fields

#### `metrics() -> dict`

Get service metrics.

**Returns:**
- dict: Metrics including CPU, memory, and uptime

#### `generate(input_pattern, steps=10) -> dict`

Generate neural response from input pattern.

**Parameters:**
- `input_pattern` (List[float]): Input pattern to process
- `steps` (int): Number of simulation steps

**Returns:**
- dict: Response with `output_pattern` and `processing_time_ms`

#### `info() -> dict`

Get neuro engine information.

**Returns:**
- dict: Engine information including network configuration

#### `close()`

Close the client connection.

## Error Handling

```python
from src.mlsdm.sdk import NeuroEngineClient
import httpx

try:
    with NeuroEngineClient(base_url="http://localhost:8000") as client:
        response = client.generate([0.1, 0.2, 0.3])
except httpx.HTTPStatusError as e:
    print(f"HTTP error: {e.response.status_code} - {e.response.text}")
except httpx.ConnectError:
    print("Could not connect to service")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Examples

### Batch Processing

```python
from src.mlsdm.sdk import NeuroEngineClient

patterns = [
    [0.1, 0.2, 0.3],
    [0.4, 0.5, 0.6],
    [0.7, 0.8, 0.9],
]

with NeuroEngineClient(base_url="http://localhost:8000") as client:
    for i, pattern in enumerate(patterns):
        response = client.generate(pattern)
        print(f"Pattern {i}: {response['output_pattern']}")
```

### Performance Monitoring

```python
from src.mlsdm.sdk import NeuroEngineClient
import time

with NeuroEngineClient(base_url="http://localhost:8000") as client:
    # Monitor metrics before
    metrics_before = client.metrics()
    
    # Run workload
    for _ in range(100):
        client.generate([0.1, 0.2, 0.3])
    
    # Monitor metrics after
    metrics_after = client.metrics()
    
    memory_increase = metrics_after['memory_mb'] - metrics_before['memory_mb']
    print(f"Memory increase: {memory_increase:.2f} MB")
```

## See Also

- [API Reference](API_REFERENCE.md)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Deployment Runbook](RUNBOOK.md)
