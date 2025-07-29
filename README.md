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

### Frontend Setup 

The React.js frontend will be implemented in the next phase, featuring:
- Modern research interface inspired by Microsoft's Copilot Studio
- Real-time progress visualization
- Interactive model selection and configuration
- Export management and download interface
- Collaborative research session management

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
