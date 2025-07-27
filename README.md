# Deep Research Application

A comprehensive full-stack application for AI-powered research using Azure AI Foundry Agent Service. This application orchestrates multiple large language models to conduct deep research, provides real-time progress tracking, and exports findings in multiple formats.

## 🚀 Features

### Core Capabilities
- **Multi-LLM Orchestration**: Coordinate GPT-4, GPT-3.5-turbo, Deepseek, Grok, and Mistral for specialized research tasks
- **Azure AI Foundry Integration**: Leverage Azure's Agent Service for sophisticated AI workflows
- **Real-time Web Grounding**: Integrate live web search via Bing API for current information
- **Multiple Export Formats**: Generate reports in Markdown, PDF, and PowerPoint presentations
- **Real-time Progress Tracking**: WebSocket-based live updates during research execution
- **Enterprise Security**: Azure AD B2C authentication with role-based access control

### Advanced Features
- **Intelligent Task Decomposition**: Break complex research topics into manageable subtasks
- **Source Citation and Verification**: Automatic source tracking and credibility assessment
- **Template-based PowerPoint Generation**: Match corporate presentation templates
- **Collaborative Research**: Multi-user research sessions with shared progress tracking
- **Research History and Analytics**: Track research patterns and optimize workflows

## 🏗️ Architecture

```
deep_research/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Configuration and Azure services
│   │   ├── models/         # Data models and schemas
│   │   ├── services/       # Business logic services
│   │   └── main.py         # FastAPI application
│   ├── tests/              # Backend test suite
│   ├── Dockerfile          # Container configuration
│   └── requirements.txt    # Python dependencies
├── frontend/               # React.js frontend (coming next)
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client services
│   │   └── utils/          # Utility functions
│   └── package.json        # Node.js dependencies
├── infrastructure/         # Azure Infrastructure as Code
│   ├── bicep/             # Bicep templates
│   └── terraform/         # Terraform alternatives
└── .github/               # CI/CD workflows
    └── workflows/
```

## 🎯 Technology Stack

### Backend (Python)
- **FastAPI**: High-performance async API framework
- **Azure AI Foundry**: Agent Service for LLM orchestration
- **Azure SDK**: Comprehensive Azure service integration
- **Pydantic**: Data validation and settings management
- **WebSockets**: Real-time communication
- **WeasyPrint & python-pptx**: Document generation

### Frontend (React.js)
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe development
- **Material-UI/Chakra UI**: Modern component library
- **React Query**: State management and caching
- **WebSocket Client**: Real-time updates
- **Chart.js**: Progress visualization

### Azure Services
- **Azure AI Foundry Hub & Project**: AI orchestration platform
- **Azure Container Apps**: Scalable container hosting
- **Azure Cosmos DB**: Document database for session management
- **Azure Blob Storage**: File storage for exports
- **Azure Key Vault**: Secure secret management
- **Azure Monitor**: Logging and telemetry
- **Azure AD B2C**: Authentication and authorization

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** for backend development
- **Node.js 18+** for frontend development (coming next)
- **Azure Subscription** with required services
- **Azure CLI** installed and configured
- **Docker** (optional, for containerization)

### Backend Setup

1. **Clone and navigate to backend**:
   ```bash
   git clone <repository-url>
   cd deep_research/backend
   ```

2. **Run the setup script**:
   ```powershell
   # Windows PowerShell
   .\setup.ps1
   
   # Or manually:
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Azure services**:
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Update .env with your Azure configuration
   # See backend/README.md for detailed configuration
   ```

4. **Start the development server**:
   ```bash
   python run.py serve
   ```

   The API will be available at:
   - **API Documentation**: http://localhost:8010/docs
   - **Health Check**: http://localhost:8010/api/v1/health/

### Frontend Setup (Coming Next)

The React.js frontend will be implemented in the next phase, featuring:
- Modern research interface inspired by Microsoft's Copilot Studio
- Real-time progress visualization
- Interactive model selection and configuration
- Export management and download interface
- Collaborative research session management

## 📚 API Documentation

### Research Endpoints
- `POST /api/v1/research/start` - Start a new research task
- `GET /api/v1/research/status/{task_id}` - Get research progress
- `WebSocket /api/v1/research/ws/{task_id}` - Real-time updates
- `GET /api/v1/research/report/{task_id}` - Get completed research

### Export Endpoints
- `POST /api/v1/export/` - Create export in PDF/PPTX/Markdown
- `GET /api/v1/export/download/{export_id}` - Download generated file
- `GET /api/v1/export/status/{export_id}` - Check export progress

### Example Usage

```python
import httpx
import asyncio
import websockets
import json

# Start research
research_request = {
    "prompt": "Latest trends in artificial intelligence and machine learning",
    "model_config": {
        "thinking": "gpt-4",
        "task": "gpt-35-turbo"
    },
    "enable_web_search": True,
    "research_depth": "deep"
}

response = httpx.post("http://localhost:8010/api/v1/research/start", json=research_request)
task_id = response.json()["task_id"]

# Monitor progress via WebSocket
async def monitor_progress():
    uri = f"ws://localhost:8010/api/v1/research/ws/{task_id}"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Progress: {data['data']['progress_percentage']}%")
            if data['data']['status'] == 'completed':
                break

# Export to PDF
export_request = {
    "task_id": task_id,
    "format": "pdf",
    "include_sources": True
}

export_response = httpx.post("http://localhost:8010/api/v1/export/", json=export_request)
export_id = export_response.json()["export_id"]
```

## 🛠️ Development Tools

The backend includes a comprehensive development toolkit:

```bash
# Development server with auto-reload
python run.py serve --debug

# Run test suite with coverage
python run.py test --coverage

# Check application health
python run.py health

# Code formatting and linting
python run.py lint

# Docker operations
python run.py docker build
python run.py docker run

# Environment setup
python run.py setup
```

## 🔧 Configuration

### Required Azure Services

1. **Azure AI Foundry Hub and Project**
2. **Azure Cosmos DB** (for research session management)
3. **Azure Blob Storage** (for export file storage)
4. **Azure Key Vault** (for secure secret management)
5. **Bing Search API** (for web grounding capabilities)

### Environment Configuration

Key environment variables (see `backend/.env.example`):

```env
# Azure Core
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_RESOURCE_GROUP=deep-research-rg

# Azure AI Foundry
AZURE_AI_PROJECT_NAME=deep-research-project
AZURE_AI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com

# Azure Services
KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
COSMOS_DB_ENDPOINT=https://your-cosmosdb.documents.azure.com:443/
STORAGE_ACCOUNT_URL=https://yourstorageaccount.blob.core.windows.net
```

## 🚀 Deployment

### Container Deployment
```bash
# Build and run with Docker
cd backend
docker build -t deep-research-backend .
docker run -p 8010:8010 --env-file .env deep-research-backend
```

### Azure Container Apps (Recommended)
Infrastructure as Code templates for Azure deployment coming in the next phase.

## 🧪 Testing

Comprehensive test suite included:

```bash
# Run all tests
python run.py test

# Run with coverage
python run.py test --coverage

# Run specific test categories
pytest tests/test_services/ -v
pytest tests/test_api/ -v
```

## 📊 Monitoring and Observability

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Azure Monitor Integration**: Application insights and telemetry
- **Health Checks**: Multiple endpoints for container orchestration
- **Performance Metrics**: Request timing and resource usage
- **Error Tracking**: Comprehensive error logging and alerting

## 🔒 Security Features

- **Azure Managed Identity**: No hardcoded credentials
- **Key Vault Integration**: Secure secret management
- **Input Validation**: Comprehensive Pydantic model validation
- **Rate Limiting**: API protection against abuse
- **CORS Configuration**: Secure cross-origin resource sharing
- **TLS/HTTPS**: Encrypted communications in production

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with comprehensive tests
4. Run the test suite (`python run.py test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines (enforced by Black and Flake8)
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints throughout the codebase
- Follow Azure best practices for cloud-native development

## 📈 Roadmap

### Phase 1: Backend Foundation ✅
- [x] FastAPI backend with Azure AI Foundry integration
- [x] Multi-LLM orchestration service
- [x] Web search integration with Bing API
- [x] Export services (PDF, PPTX, Markdown)
- [x] WebSocket real-time updates
- [x] Comprehensive test suite

### Phase 2: Frontend Development (Next)
- [ ] React.js frontend with modern UI
- [ ] Real-time progress visualization
- [ ] Interactive research configuration
- [ ] Export management interface
- [ ] User authentication integration

### Phase 3: Infrastructure & Deployment
- [ ] Azure Infrastructure as Code (Bicep/Terraform)
- [ ] CI/CD pipelines with GitHub Actions
- [ ] Production deployment automation
- [ ] Monitoring and alerting setup

### Phase 4: Advanced Features
- [ ] Collaborative research sessions
- [ ] Research analytics and insights
- [ ] Custom AI agent configuration
- [ ] Enterprise integration features

## 📝 License

[Add appropriate license information]

## 🆘 Support

For support and questions:

- Check the [Backend README](backend/README.md) for detailed setup instructions
- Review the [API Documentation](http://localhost:8010/docs) for endpoint details
- Check [Issues](../../issues) for known problems and solutions
- Create a new issue for bugs or feature requests

## 🙏 Acknowledgments

- Microsoft Azure AI Foundry team for the Agent Service platform
- FastAPI community for the excellent async framework
- The open-source community for the various libraries and tools used

---

**Note**: This is the initial backend implementation. The frontend React.js application and Azure infrastructure templates will be implemented in subsequent phases. The current backend provides a complete API foundation ready for frontend integration.

For detailed setup instructions, see the [Backend README](backend/README.md).
