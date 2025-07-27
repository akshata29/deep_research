# Deep Research Backend

Python FastAPI backend for the Deep Research application, providing AI-powered research capabilities using Azure AI Foundry Agent Service.

## Features

- **Multi-LLM Orchestration**: Coordinate multiple AI models for different research tasks
- **Azure AI Foundry Integration**: Leverage Azure AI agents and services
- **Bing Grounding**: Real-time web search integration
- **Export Services**: Generate reports in Markdown, PDF, and PPTX formats
- **WebSocket Support**: Real-time progress updates
- **Azure Integration**: Cosmos DB, Blob Storage, Key Vault, and more

## Architecture

```
backend/
├── app/
│   ├── api/                 # FastAPI route handlers
│   │   ├── research.py      # Research endpoints
│   │   ├── export.py        # Export endpoints
│   │   └── health.py        # Health check endpoints
│   ├── core/                # Core configuration and utilities
│   │   ├── config.py        # Application settings
│   │   ├── azure_config.py  # Azure service management
│   │   └── logging_config.py # Logging configuration
│   ├── models/              # Data models and schemas
│   │   └── schemas.py       # Pydantic models
│   ├── services/            # Business logic services
│   │   ├── research_orchestrator.py  # Main research coordination
│   │   ├── ai_agent_service.py       # Azure AI agent management
│   │   ├── web_search_service.py     # Bing search integration
│   │   └── export_service.py         # Report export functionality
│   └── main.py              # FastAPI application entry point
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
└── .env.example            # Environment configuration template
```

## Prerequisites

- Python 3.11+
- Azure subscription with required services
- Azure AI Foundry project setup
- Docker (for containerization)

## Required Azure Services

1. **Azure AI Foundry Hub and Project**
2. **Azure Cosmos DB** (for session management)
3. **Azure Blob Storage** (for file exports)
4. **Azure Key Vault** (for secrets management)
5. **Bing Search API** (for web grounding)

## Local Development Setup

### 1. Environment Configuration

Copy the environment template and configure your Azure settings:

```bash
cp .env.example .env
```

Update `.env` with your Azure configuration:

```env
# Azure Configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_RESOURCE_GROUP=deep-research-rg

# Azure AI Foundry
AZURE_AI_PROJECT_NAME=deep-research-project
AZURE_AI_ENDPOINT=https://your-ai-foundry-endpoint.cognitiveservices.azure.com

# Azure Services
KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
COSMOS_DB_ENDPOINT=https://your-cosmosdb.documents.azure.com:443/
STORAGE_ACCOUNT_URL=https://yourstorageaccount.blob.core.windows.net
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Azure Authentication

Ensure you're authenticated with Azure:

```bash
# Install Azure CLI if not already installed
# Login to Azure
az login

# Set subscription
az account set --subscription "your-subscription-id"
```

### 4. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

# Or use the Python module
python -m uvicorn app.main:app --reload
```

The API will be available at:
- **API Documentation**: http://localhost:8010/docs
- **Health Check**: http://localhost:8010/api/v1/health/
- **Alternative Docs**: http://localhost:8010/redoc

## API Endpoints

### Health Endpoints
- `GET /api/v1/health/` - Comprehensive health check
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe
- `GET /api/v1/health/detailed` - Detailed health information

### Research Endpoints
- `GET /api/v1/research/models` - Get available AI models
- `POST /api/v1/research/start` - Start a research task
- `GET /api/v1/research/status/{task_id}` - Get research status
- `GET /api/v1/research/report/{task_id}` - Get completed report
- `DELETE /api/v1/research/cancel/{task_id}` - Cancel research task
- `GET /api/v1/research/list` - List all research tasks
- `WebSocket /api/v1/research/ws/{task_id}` - Real-time updates

### Export Endpoints
- `POST /api/v1/export/` - Create export task
- `GET /api/v1/export/status/{export_id}` - Get export status
- `GET /api/v1/export/download/{export_id}` - Download exported file
- `DELETE /api/v1/export/cleanup/{export_id}` - Clean up export
- `GET /api/v1/export/list` - List export tasks

## Usage Examples

### Start a Research Task

```python
import httpx

research_request = {
    "prompt": "What are the latest trends in artificial intelligence and machine learning?",
    "model_config": {
        "thinking": "gpt-4",
        "task": "gpt-35-turbo"
    },
    "enable_web_search": True,
    "research_depth": "deep",
    "language": "en"
}

response = httpx.post("http://localhost:8010/api/v1/research/start", json=research_request)
task_data = response.json()
task_id = task_data["task_id"]
```

### Monitor Research Progress

```python
import asyncio
import websockets
import json

async def monitor_research(task_id):
    uri = f"ws://localhost:8010/api/v1/research/ws/{task_id}"
    
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Progress: {data.get('data', {}).get('progress_percentage', 0)}%")
            
            if data.get('data', {}).get('status') == 'completed':
                break

asyncio.run(monitor_research(task_id))
```

### Export Report

```python
export_request = {
    "task_id": task_id,
    "format": "pdf",
    "include_sources": True,
    "include_metadata": True
}

response = httpx.post("http://localhost:8010/api/v1/export/", json=export_request)
export_data = response.json()
export_id = export_data["export_id"]

# Check export status
status_response = httpx.get(f"http://localhost:8010/api/v1/export/status/{export_id}")
status_data = status_response.json()

if status_data["status"] == "completed":
    # Download the file
    download_response = httpx.get(f"http://localhost:8010/api/v1/export/download/{export_id}")
    with open("research_report.pdf", "wb") as f:
        f.write(download_response.content)
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_main.py -v
```

## Docker Deployment

### Build Docker Image

```bash
docker build -t deep-research-backend .
```

### Run Container

```bash
docker run -p 8010:8010 \
  -e AZURE_SUBSCRIPTION_ID=your-subscription-id \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e KEY_VAULT_URL=https://your-keyvault.vault.azure.net/ \
  deep-research-backend
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | Environment name | No | `development` |
| `DEBUG` | Debug mode | No | `False` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | Yes | - |
| `AZURE_TENANT_ID` | Azure tenant ID | Yes | - |
| `AZURE_AI_PROJECT_NAME` | AI Foundry project name | Yes | - |
| `KEY_VAULT_URL` | Azure Key Vault URL | Yes | - |
| `COSMOS_DB_ENDPOINT` | Cosmos DB endpoint | Yes | - |
| `STORAGE_ACCOUNT_URL` | Storage account URL | Yes | - |

### Azure Key Vault Secrets

Store these secrets in Azure Key Vault:
- `bing-search-key` - Bing Search API subscription key
- `openai-api-key` - Azure OpenAI API key (if using direct API)

## Monitoring and Logging

The application includes comprehensive logging and monitoring:

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Azure Monitor Integration**: Automatic telemetry for production
- **Health Checks**: Multiple health endpoints for container orchestration
- **Performance Metrics**: Request timing and resource usage tracking

## Security Features

- **Azure Managed Identity**: No hardcoded credentials
- **Key Vault Integration**: Secure secret management
- **HTTPS/TLS**: Encrypted communications
- **Input Validation**: Pydantic model validation
- **Rate Limiting**: API rate limiting protection
- **CORS Configuration**: Configurable cross-origin resource sharing

## Troubleshooting

### Common Issues

1. **Azure Authentication Errors**
   ```bash
   # Ensure you're logged in
   az login
   az account show
   ```

2. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt --force-reinstall
   ```

3. **Azure Service Connectivity**
   ```bash
   # Test health endpoint
   curl http://localhost:8010/api/v1/health/detailed
   ```

4. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify WebSocket support in proxy/load balancer

### Debug Mode

Enable debug mode for detailed error information:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Performance Optimization

- **Connection Pooling**: HTTP client connection reuse
- **Async Operations**: Non-blocking I/O operations
- **Caching**: In-memory caching of frequently accessed data
- **Rate Limiting**: Prevent API abuse and manage costs
- **Resource Cleanup**: Automatic cleanup of temporary files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the test suite
5. Submit a pull request

## License

[Add appropriate license information]
