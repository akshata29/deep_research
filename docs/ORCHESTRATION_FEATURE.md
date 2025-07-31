# Multi-Agent Research Orchestration Feature

## Overview

The Multi-Agent Research Orchestration feature is a next-generation research system built on Microsoft Semantic Kernel that uses multiple specialized AI agents to conduct comprehensive enterprise research. Through MagenticOrchestration, various AI agents dynamically collaborate to automatically generate high-quality research reports from both internal documents and external web sources.

## Architecture

### Core Components

1. **DeepResearchAgent**: Main orchestrator that coordinates the entire research process
2. **Specialized Agents**: Seven different agent types, each with specific roles
3. **Memory Management**: Persistent context and knowledge storage using Semantic Kernel Memory
4. **Search Integration**: Combined internal (Azure AI Search) and external (Tavily) search capabilities
5. **Quality Control**: Built-in credibility assessment and reflection mechanisms

### Agent Specializations

#### Core Research Agents
- **LeadResearcher**: Research coordination and strategic planning
- **Researcher1**: Technical analysis and documentation review
- **Researcher2**: Market research and competitive analysis  
- **Researcher3**: Risk assessment and compliance analysis

#### Quality & Validation Agents
- **CredibilityCritic**: Source quality assessment and reliability validation
- **ReflectionCritic**: Quality validation and improvement recommendations

#### Output Generation Agents
- **Summarizer**: Knowledge synthesis and summarization
- **ReportWriter**: Professional report writing with citations
- **CitationAgent**: Reference management and citation formatting
- **Translator**: Professional terminology translation

## Technical Implementation

### Backend Structure

```
app/orchestration/
├── __init__.py
├── deep_research_agent.py      # Main orchestrator
├── agent_factory.py            # Agent creation and configuration
├── config/
│   ├── orchestration_config.py # Configuration management
│   ├── project_config.yaml     # Project-specific settings
│   └── project_config_template.yaml
├── memory/
│   ├── memory_manager.py       # Semantic memory management
│   ├── memory_plugin.py        # Kernel plugin for memory operations
│   ├── shared_memory_plugin.py # Inter-agent communication
│   └── utils.py                # Embedding utilities
├── search/
│   ├── modular_search_plugin.py # Combined search capabilities
│   ├── azure_search_provider.py # Internal document search
│   └── web_search_provider.py   # External web search
└── prompts/
    ├── agent_prompts.py        # Individual agent instructions
    └── manager_prompts.py      # Orchestration manager prompts
```

### Frontend Components

```
frontend/src/
├── pages/OrchestrationPage.tsx    # Main orchestration interface
├── hooks/useOrchestrationApi.ts   # API integration hooks
└── components/Layout.tsx          # Navigation updates
```

### API Endpoints

- `POST /api/v1/orchestration/research` - Start multi-agent research
- `GET /api/v1/orchestration/sessions/{sessionId}/summary` - Get session status
- `GET /api/v1/orchestration/sessions` - List active sessions
- `DELETE /api/v1/orchestration/sessions/{sessionId}` - Cleanup session
- `GET /api/v1/orchestration/health` - System health check

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Existing Azure OpenAI configuration is used
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_GPT41_DEPLOYMENT=gpt-4
AZURE_GPT41_MINI_DEPLOYMENT=gpt-4-mini
AZURE_O3_DEPLOYMENT=o3
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# Optional: Azure Search for internal documents
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your-search-key-here
AZURE_SEARCH_INDEX_NAME=your-index-name

# Optional: Web Search via Tavily
TAVILY_API_KEY=your-tavily-api-key-here
TAVILY_MAX_RESULTS=10
TAVILY_MAX_RETRIES=3
```

### Project Configuration

The system uses `project_config.yaml` for detailed configuration:

```yaml
system:
  company: "Your Company Name"
  research_domain: "Enterprise Research & Development"

data_sources:
  web_search:
    enabled: true
    max_results: 10
    
agents:
  lead_researcher:
    model: "gpt-4"
    max_iterations: 5
    
  researchers:
    count: 3
    model: "gpt-4-mini"
    
  report_writer:
    model: "o3"  # Uses reasoning model for high-quality reports
```

## Usage

### Via UI

1. Navigate to the "Research Orchestration" page
2. Enter your research query in the text area
3. Click "Start Orchestration" to begin multi-agent research
4. Monitor progress and view results
5. Download the final report when complete

### Via API

```python
import requests

# Start research
response = requests.post('/api/v1/orchestration/research', json={
    'query': 'Analyze the latest developments in AI orchestration technologies'
})

session_id = response.json()['session_id']
result = response.json()['result']
```

## Features

### Multi-Source Research
- **Internal Documents**: Search enterprise document repositories via Azure AI Search
- **Web Research**: External information gathering via Tavily API
- **Fallback Strategy**: Automatically uses web search when internal sources are insufficient

### Quality Assurance
- **Source Reliability**: Automated credibility assessment for all sources
- **Fact Checking**: Cross-referencing across multiple sources
- **Reflection Process**: Self-improvement loops for quality enhancement

### Memory Management
- **Persistent Context**: Research context maintained across sessions
- **Shared Knowledge**: Agents can share insights and collaborate
- **Search History**: Previous research can inform new queries

### Professional Output
- **Structured Reports**: Enterprise-grade formatting and organization
- **Proper Citations**: Academic-style references and source attribution
- **Multiple Languages**: Translation capabilities for global organizations

## Performance Characteristics

### Scalability
- **Parallel Processing**: Multiple agents work simultaneously
- **Resource Management**: Automatic cleanup and optimization
- **Session Persistence**: Long-running research sessions supported

### Response Times
- **Simple Queries**: 2-5 minutes
- **Complex Research**: 5-15 minutes
- **Comprehensive Analysis**: 10-30 minutes

### Quality Metrics
- **Source Reliability**: 0.8+ confidence scores for all included sources
- **Citation Coverage**: 100% attribution for all claims
- **Fact Verification**: Multi-source validation for key findings

## Troubleshooting

### Common Issues

1. **Configuration Errors**
   - Verify all required environment variables are set
   - Check Azure OpenAI deployment names match configuration
   - Ensure API keys have proper permissions

2. **Performance Issues**
   - Monitor system health via `/orchestration/health` endpoint
   - Check active session count and cleanup unused sessions
   - Verify network connectivity to Azure services

3. **Search Limitations**
   - Internal search requires properly configured Azure AI Search
   - Web search requires valid Tavily API key
   - Both can be disabled if not available

### Monitoring

Use the health endpoint to monitor system status:

```json
{
  "status": "healthy",
  "active_sessions_count": 2,
  "configuration": {
    "azure_openai_configured": true,
    "azure_search_configured": true,
    "web_search_configured": true,
    "embedding_configured": true
  }
}
```

## Security Considerations

### Data Protection
- **Memory Isolation**: Each session has isolated memory space
- **Credential Security**: API keys managed via environment variables
- **Access Control**: Session-based research isolation

### Compliance
- **Source Attribution**: Full traceability of all information sources
- **Audit Trail**: Complete logging of research activities
- **Data Retention**: Configurable memory retention policies

## Future Enhancements

### Planned Features
- **Custom Agent Types**: User-defined specialist agents
- **Integration APIs**: Connect to additional enterprise systems
- **Advanced Analytics**: Research performance metrics and insights
- **Collaborative Research**: Multi-user research sessions

### Extensibility
- **Plugin Architecture**: Easy addition of new search providers
- **Custom Prompts**: Configurable agent instructions
- **Model Selection**: Dynamic model assignment based on task complexity
