# Custom PowerPoint Export Feature

## Overview
This feature allows users to export research reports as custom PowerPoint presentations using AI-powered slide generation that maps content to specific slide templates.

## Components Added

### 1. Backend API Changes

#### New Schema (`app/models/schemas.py`)
- Added `CustomExportRequest` model for handling custom PowerPoint export requests
- Fields: `markdown_content`, `slide_titles`, `topic`, `request`

#### Research API (`app/api/research.py`)
- Added `/customexport` endpoint that:
  - Takes markdown content and slide titles
  - Uses AI agent to convert markdown to structured JSON slides
  - Returns slide-ready JSON format for PowerPoint generation

#### Export API (`app/api/export.py`)
- Added `/custom-powerpoint` endpoint that:
  - Takes structured slides JSON data
  - Generates actual PowerPoint file using python-pptx
  - Returns downloadable PPTX file

#### Export Service (`app/services/export_service.py`)
- Added `create_custom_powerpoint()` method that:
  - Creates PowerPoint from structured slide data
  - Handles different content types (lists, dictionaries, strings)
  - Supports custom templates
  - Generates proper slide layouts with titles and content

### 2. Frontend Changes

#### Export Dropdown (`frontend/src/components/ExportDropdown.tsx`)
- Added "Custom PowerPoint" option to export dropdown
- Added `downloadCustomPptx()` function that:
  - Calls `/customexport` API to generate structured slides
  - Calls `/custom-powerpoint` API to generate PPTX file
  - Downloads the generated PowerPoint

#### Types (`frontend/src/types/index.ts`)
- Extended `ExportFormat` type to include `'custom-pptx'`

## Usage Flow

1. **User clicks "Custom PowerPoint" in export dropdown**
2. **Frontend calls `/api/v1/research/customexport`** with:
   - Markdown content from the research report
   - Predefined slide titles (configurable)
   - Research topic
3. **AI agent processes the request** using the specialized prompt:
   - Parses markdown content
   - Maps content to slide titles
   - Returns structured JSON with slide data
4. **Frontend calls `/api/v1/export/custom-powerpoint`** with:
   - Generated slides JSON data
   - Topic and template preferences
5. **Backend generates PowerPoint file** using python-pptx
6. **User downloads the custom PowerPoint presentation**

## Default Slide Template Structure

The current implementation uses these default slide titles:
- Company Snapshot
- Key Company Metrics
- Sales Mix
- Revenue by Segment
- Businesses Overview
- Stock Graph History
- Considerations (SWOT format)
- Third-Party Perspectives and Multiples
- Credit Perspectives
- Equity Perspectives
- Board of Directors

## Customization Options

- **Slide titles**: Can be customized by modifying the `slideTitle` array in `ExportDropdown.tsx`
- **PowerPoint template**: Can specify different templates ("business", "academic", "executive", "default")
- **AI prompt**: The conversion prompt can be modified in the `/customexport` endpoint
- **Content mapping**: The AI automatically maps markdown sections to slide titles

## Technical Features

- **Smart content mapping**: AI matches markdown headings to slide titles
- **Multiple content types**: Supports bullet points, structured data (SWOT), and plain text
- **Template support**: Uses existing PowerPoint templates or creates new presentations
- **Error handling**: Graceful fallbacks if content parsing fails
- **File cleanup**: Temporary files are automatically cleaned up after download

## Future Enhancements

- Custom slide title configuration from UI
- Multiple template selection in the dropdown
- Preview of generated slides before download
- Batch export for multiple reports
- Integration with company branding templates
