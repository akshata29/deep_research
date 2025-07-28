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
          downloadFile(reportContent, filename, 'text/markdown');
          break;
        
        case 'html':
          await downloadHtml(reportContent, titleFromContent);
          break;
        
        case 'json':
          const jsonContent = convertToJson(reportContent, reportTitle);
          downloadFile(jsonContent, filename, 'application/json');
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
        
        default:
          toast({
            title: 'Unsupported Format',
            description: 'This export format is not yet supported.',
            status: 'error',
            duration: 3000,
          });
      }

      if (['markdown', 'html', 'json', 'pdf', 'docx', 'pptx'].includes(format)) {
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
