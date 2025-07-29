import React, { useState } from 'react';
import {
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Icon,
  HStack,
  Text,
  useToast,
} from '@chakra-ui/react';
import { 
  Download, 
  ChevronDown, 
  FileText, 
  FileImage, 
  Presentation, 
  Globe,
  Code
} from 'lucide-react';
import { ExportFormat } from '@/types';

interface ExportDropdownProps {
  taskId: string;
  reportContent: string;
  reportTitle?: string;
  isDisabled?: boolean;
}

export const ExportDropdown: React.FC<ExportDropdownProps> = ({ 
  taskId, 
  reportContent,
  reportTitle = 'research-report',
  isDisabled = false 
}) => {
  const toast = useToast();
  const [isExporting, setIsExporting] = useState(false);

  const exportOptions = [
    {
      format: 'markdown' as ExportFormat,
      label: 'Markdown',
      description: 'Plain text with formatting',
      icon: FileText,
      extension: 'md',
    },
    {
      format: 'pdf' as ExportFormat,
      label: 'PDF',
      description: 'Portable Document Format',
      icon: FileText,
      extension: 'pdf',
    },
    {
      format: 'docx' as ExportFormat,
      label: 'Word',
      description: 'Microsoft Word Document',
      icon: FileImage,
      extension: 'docx',
    },
    {
      format: 'pptx' as ExportFormat,
      label: 'PowerPoint',
      description: 'Microsoft PowerPoint Presentation',
      icon: Presentation,
      extension: 'pptx',
    },
    {
      format: 'custom-pptx' as ExportFormat,
      label: 'Custom PowerPoint',
      description: 'AI-generated slides from template',
      icon: Presentation,
      extension: 'pptx',
    },
    {
      format: 'html' as ExportFormat,
      label: 'HTML',
      description: 'Web page format',
      icon: Globe,
      extension: 'html',
    },
    {
      format: 'json' as ExportFormat,
      label: 'JSON',
      description: 'Raw data format',
      icon: Code,
      extension: 'json',
    },
  ];

  const extractTitleFromContent = (content: string): string => {
    // Look for the first H1 heading in the markdown content
    const h1Match = content.match(/^#\s+(.+)$/m);
    if (h1Match) {
      return h1Match[1].trim().replace(/[^a-zA-Z0-9\s-]/g, '').replace(/\s+/g, '-').toLowerCase();
    }
    return reportTitle;
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const convertToJson = (markdownContent: string, title: string) => {
    return JSON.stringify({
      title: title,
      content: markdownContent,
      format: 'markdown',
      exported_at: new Date().toISOString(),
      task_id: taskId
    }, null, 2);
  };

  const downloadMarkdown = async (content: string, title: string) => {
    try {
      const response = await fetch('/api/v1/export/markdown-export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          markdown_content: content,
          title: title,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to export markdown');
      }
      
      const markdownBlob = await response.blob();
      const url = window.URL.createObjectURL(markdownBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title}.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw error;
    }
  };

  const downloadJson = async (content: string, title: string) => {
    try {
      const response = await fetch('/api/v1/export/json-export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          markdown_content: content,
          title: title,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to export JSON');
      }
      
      const jsonBlob = await response.blob();
      const url = window.URL.createObjectURL(jsonBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw error;
    }
  };

  const downloadHtml = async (content: string, title: string) => {
    try {
      const response = await fetch('/api/v1/export/markdown-to-html', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          markdown_content: content,
          title: title,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate HTML');
      }
      
      const htmlBlob = await response.blob();
      const url = window.URL.createObjectURL(htmlBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title}.html`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw error;
    }
  };

  const downloadPdf = async (content: string, title: string) => {
    try {
      const response = await fetch('/api/v1/export/markdown-to-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          markdown_content: content,
          title: title,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate PDF');
      }
      
      const pdfBlob = await response.blob();
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw error;
    }
  };

  const downloadDocx = async (content: string, title: string) => {
    try {
      const response = await fetch('/api/v1/export/markdown-to-docx', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          markdown_content: content,
          title: title,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate DOCX');
      }
      
      const docxBlob = await response.blob();
      const url = window.URL.createObjectURL(docxBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw error;
    }
  };

  const downloadCustomPptx = async (content: string, title: string) => {
    try {
      // Validate content length
      if (!content || content.length < 100) {
        throw new Error('Content too short for meaningful PowerPoint generation');
      }

      // Default slide titles for custom PowerPoint template
      const slideTitle = [
        "Company Snapshot",
        "Key Company Metrics", 
        "Sales Mix",
        "Revenue by Segment",
        "Businesses Overview",
        "Stock Graph History",
        "Considerations",
        "Third-Party Perspectives and Multiples",
        "Credit Perspectives",
        "Equity Perspectives",
        "Board of Directors"
      ];

      // Show progress to user
      toast({
        title: 'Generating Custom PowerPoint',
        description: 'AI is analyzing content and creating slides...',
        status: 'info',
        duration: 3000,
      });

      // Call the custom export API to generate slide-ready JSON
      const customExportResponse = await fetch('/api/v1/research/customexport', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          markdown_content: content,
          slide_titles: slideTitle,
          topic: title,
          request: null // Optional: could include model config
        }),
      });
      
      if (!customExportResponse.ok) {
        const errorData = await customExportResponse.text();
        throw new Error(`Failed to generate custom export structure: ${errorData}`);
      }
      
      const customExportData = await customExportResponse.json();
      const slidesData = customExportData?.report?.metadata?.slides_data;
      
      if (!slidesData || !slidesData.slides || slidesData.slides.length === 0) {
        throw new Error('No slides data generated from custom export');
      }

      // Show progress for PowerPoint generation
      toast({
        title: 'Creating PowerPoint File',
        description: `Generating ${slidesData.slides.length} slides...`,
        status: 'info',
        duration: 2000,
      });

      // Now call the PowerPoint generation endpoint
      const pptxResponse = await fetch('/api/v1/export/custom-powerpoint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          slides_data: slidesData,
          topic: title,
          template_name: "business"
        }),
      });
      
      if (!pptxResponse.ok) {
        const errorData = await pptxResponse.text();
        throw new Error(`Failed to generate custom PowerPoint: ${errorData}`);
      }
      
      const pptxBlob = await pptxResponse.blob();
      
      // Verify we got a valid file
      if (pptxBlob.size === 0) {
        throw new Error('Generated PowerPoint file is empty');
      }

      const url = window.URL.createObjectURL(pptxBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title}_custom.pptx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Custom PowerPoint export error:', error);
      throw error;
    }
  };

  const downloadPptx = async (content: string, title: string) => {
    try {
      const response = await fetch('/api/v1/export/markdown-to-pptx', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          markdown_content: content,
          title: title,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate PPTX');
      }
      
      const pptxBlob = await response.blob();
      const url = window.URL.createObjectURL(pptxBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title}.pptx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      throw error;
    }
  };

  const handleFormatSelect = async (format: ExportFormat, extension: string) => {
    if (!reportContent) {
      toast({
        title: 'No Content',
        description: 'No report content available to export.',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setIsExporting(true);
    
    try {
      const titleFromContent = extractTitleFromContent(reportContent);
      const filename = `${titleFromContent}.${extension}`;
      
      switch (format) {
        case 'markdown':
          await downloadMarkdown(reportContent, titleFromContent);
          break;
        
        case 'html':
          await downloadHtml(reportContent, titleFromContent);
          break;
        
        case 'json':
          await downloadJson(reportContent, titleFromContent);
          break;
        
        case 'pdf':
          await downloadPdf(reportContent, titleFromContent);
          break;
        
        case 'docx':
          await downloadDocx(reportContent, titleFromContent);
          break;
        
        case 'pptx':
          await downloadPptx(reportContent, titleFromContent);
          break;
        
        case 'custom-pptx':
          await downloadCustomPptx(reportContent, titleFromContent);
          break;
        
        default:
          toast({
            title: 'Unsupported Format',
            description: 'This export format is not yet supported.',
            status: 'error',
            duration: 3000,
          });
      }

      if (['markdown', 'html', 'json', 'pdf', 'docx', 'pptx', 'custom-pptx'].includes(format)) {
        toast({
          title: 'Export Successful',
          description: `Report exported as ${filename}`,
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: error instanceof Error ? error.message : 'Failed to export report',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <>
      <Menu>
        <MenuButton
          as={Button}
          size="sm"
          leftIcon={<Icon as={Download} />}
          rightIcon={<Icon as={ChevronDown} />}
          isDisabled={isDisabled || isExporting}
          isLoading={isExporting}
          variant="solid"
          colorScheme="blue"
        >
          {isExporting ? 'Exporting...' : 'Export'}
        </MenuButton>
        <MenuList>
          {exportOptions.map((option) => (
            <MenuItem
              key={option.format}
              onClick={() => handleFormatSelect(option.format, option.extension)}
              icon={<Icon as={option.icon} />}
              isDisabled={isExporting}
            >
              <HStack spacing={3} align="start">
                <div>
                  <Text fontWeight="medium">{option.label}</Text>
                  <Text fontSize="xs" color="gray.500">
                    {option.description}
                  </Text>
                </div>
              </HStack>
            </MenuItem>
          ))}
        </MenuList>
      </Menu>
    </>
  );
};
