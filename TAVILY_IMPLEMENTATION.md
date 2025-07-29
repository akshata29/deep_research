# Execute Research Task with Bing Grounding vs Tavily Search

## Overview

This implementation adds a new option for Execute Research Task that allows end users to select between using **Bing Grounding** or **Tavily** for web search. The user can configure their preferred search method in the Settings page, and the system will use the selected method when executing research tasks.

## Implementation Details

### Backend Changes

#### 1. New Tavily Search Service (`backend/app/services/tavily_search_service.py`)
- **TavilySearchService**: A complete service for interacting with Tavily API
- **Features**:
  - Asynchronous web search using Tavily API
  - Result formatting for LLM consumption with citations
  - Error handling and logging
  - Support for images and text search results
  - Context formatting with numbered citations

#### 2. New API Endpoint (`backend/app/api/research.py`)
- **`/execute-tavily`**: New endpoint that replicates `/execute` functionality but uses Tavily search
- **Process**:
  - **Step 1**: Generate search queries (same as `/execute`) - no Bing grounding
  - **Step 2**: For each query:
    - Call Tavily Search API to get web results
    - Format results as context with citations [1], [2], etc.
    - Send context + query to LLM (task model) WITHOUT grounding
    - Use specialized search prompt for organizing information
  - **Step 3**: Aggregate findings and return structured report

#### 3. Enhanced Configuration
- Added `TAVILY_API_KEY` to environment configuration
- Service properly handles missing API key with clear error messages

### Frontend Changes

#### 1. User Settings (`frontend/src/pages/SettingsPage.tsx`)
- Added **Search Method** selection in General Settings tab
- Options:
  - "Bing Grounding (AI with real-time search)"
  - "Tavily Search (Direct web search API)"
- Includes helpful descriptions for each option

#### 2. API Integration (`frontend/src/services/api.ts` & `frontend/src/hooks/useApi.ts`)
- **New API method**: `executeResearchWithTavily()`
- **New hook**: `useExecuteResearchWithTavily()`
- Maintains same interface as existing execute methods

#### 3. Smart Execution Logic (`frontend/src/hooks/useDeepResearch.ts`)
- **Automatic selection**: Based on user's `searchMethod` setting
- **Dynamic status updates**: Shows which search method is being used
- **Backward compatibility**: Defaults to Bing if no preference set

#### 4. Visual Indicators (`frontend/src/components/Research/SearchResult.tsx`)
- **Search Method Badge**: Shows current search method (Bing vs Tavily)
- **Color coding**: Purple for Tavily, Blue for Bing
- **Descriptive text**: Explains what each method does

### Key Features

#### 1. Prompt Engineering for Tavily
The system uses a specialized prompt when processing Tavily search results:

```
Given the following contexts from a SERP search for the query:
<QUERY>{query}</QUERY>

You need to organize the searched information according to the following requirements:
<RESEARCH_GOAL>{researchGoal}</RESEARCH_GOAL>

The following context from the SERP search:
<CONTEXT>{context}</CONTEXT>

Citation Rules:
- Please cite the context at the end of sentences when appropriate.
- Please use the format of citation number [number] to reference the context.
- If a sentence comes from multiple contexts, please list all relevant citation numbers, e.g., [1][2].
```

#### 2. Structured Data Flow
1. **Query Generation**: Same JSON schema as original `/execute`
2. **Tavily Search**: Direct API calls with structured results
3. **Context Formatting**: Numbered citations for LLM processing
4. **LLM Processing**: Task model without grounding tools
5. **Results Aggregation**: Same format as original implementation

#### 3. Error Handling
- Graceful fallback if Tavily API fails
- Continues with other queries if one fails
- Clear error messages in logs and user interface

### Configuration

#### Environment Variables
```bash
TAVILY_API_KEY=your_tavily_api_key_here
```

#### User Settings
Users can set their preference in Settings > General > Search Method:
- **Bing Grounding**: Uses Azure AI with real-time search capabilities
- **Tavily Search**: Uses direct web search API for comprehensive results

### Usage

1. **Configure API Key**: Set `TAVILY_API_KEY` in environment variables
2. **User Selection**: User chooses search method in Settings page
3. **Automatic Execution**: System automatically uses selected method for research tasks
4. **Visual Feedback**: UI shows which search method is active

### Benefits

#### Bing Grounding
- AI-powered search with reasoning
- Built-in grounding and fact-checking
- Integrated with Azure AI services

#### Tavily Search
- Direct web search API access
- Comprehensive search results
- More control over search parameters
- Potentially more sources and data

### Backward Compatibility

- Existing functionality remains unchanged
- Default setting is "Bing Grounding" 
- Settings are stored in localStorage
- No breaking changes to existing APIs

## Testing

To test the implementation:

1. Set `TAVILY_API_KEY` environment variable
2. Navigate to Settings and select "Tavily Search"
3. Create a research project and execute search tasks
4. Verify the search method indicator shows "Tavily Search API"
5. Check that results include proper citations [1], [2], etc.

The system will automatically use the selected search method for all future research executions until changed in settings.
