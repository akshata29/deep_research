import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Select,
  Input,
  Checkbox,
  CheckboxGroup,
  Stack,
  Text,
  Alert,
  AlertIcon,
  AlertDescription,
  Progress,
  useToast,
  Icon,
  Box,
  Divider,
} from '@chakra-ui/react';
import { Download, FileText, Globe, Code } from 'lucide-react';
import { useCreateExport, useExportStatus } from '@/hooks/useApi';
import { ExportFormat } from '@/types';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  taskId: string;
  initialFormat?: ExportFormat;
}

export const ExportDialog: React.FC<ExportDialogProps> = ({
  isOpen,
  onClose,
  taskId,
  initialFormat = 'pdf',
}) => {
  const toast = useToast();
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>(initialFormat);
  const [filename, setFilename] = useState('');
  const [includeSections, setIncludeSections] = useState<string[]>([
    'summary',
    'content',
    'sources',
    'metadata',
  ]);
  const [customOptions, setCustomOptions] = useState({
    includeTableOfContents: true,
    includePageNumbers: true,
    includeWatermark: false,
    compressionLevel: 'medium',
  });
  const [exportId, setExportId] = useState<string | null>(null);

  const createExport = useCreateExport();
  const { data: exportStatus } = useExportStatus(exportId || '', !!exportId);

  // Update selected format when initialFormat changes
  useEffect(() => {
    setSelectedFormat(initialFormat);
  }, [initialFormat]);

  const handleExport = async () => {
    if (!filename.trim()) {
      toast({
        title: 'Filename Required',
        description: 'Please enter a filename for the export.',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    const exportOptions = {
      format: selectedFormat,
      filename: filename.trim(),
      include_sections: includeSections,
      ...customOptions,
    };

    try {
      const response = await createExport.mutateAsync({
        taskId,
        options: exportOptions,
      });

      setExportId(response.export_id);
      
      toast({
        title: 'Export Started',
        description: 'Your export is being processed. You can close this dialog.',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: error instanceof Error ? error.message : 'Failed to start export',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleClose = () => {
    setExportId(null);
    setFilename('');
    setSelectedFormat(initialFormat);
    setIncludeSections(['summary', 'content', 'sources', 'metadata']);
    onClose();
  };

  const getFormatIcon = (format: ExportFormat) => {
    switch (format) {
      case 'pdf':
        return FileText;
      case 'docx':
        return FileText;
      case 'html':
        return Globe;
      case 'markdown':
        return FileText;
      case 'json':
        return Code;
      default:
        return FileText;
    }
  };

  const getFormatDescription = (format: ExportFormat) => {
    switch (format) {
      case 'pdf':
        return 'Portable Document Format - Best for sharing and printing';
      case 'docx':
        return 'Microsoft Word Document - Editable format';
      case 'html':
        return 'Web page format - Can be viewed in any browser';
      case 'markdown':
        return 'Markdown format - Plain text with formatting';
      case 'json':
        return 'JSON format - Raw data for developers';
      default:
        return '';
    }
  };

  const isExporting = exportId && (exportStatus?.status === 'generating' || exportStatus?.status === 'formatting');
  const isCompleted = exportId && exportStatus?.status === 'completed';
  const hasFailed = exportId && exportStatus?.status === 'failed';

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Export Research Report</ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <VStack spacing={6} align="stretch">
            {/* Export Progress */}
            {exportId && (
              <Alert 
                status={
                  isCompleted ? 'success' : 
                  hasFailed ? 'error' : 
                  'info'
                }
              >
                <AlertIcon />
                <AlertDescription>
                  {isCompleted && 'Export completed successfully!'}
                  {isExporting && 'Export in progress...'}
                  {hasFailed && `Export failed`}
                </AlertDescription>
              </Alert>
            )}

            {isExporting && (
              <Box>
                <Text fontSize="sm" mb={2}>Export Progress</Text>
                <Progress 
                  value={50} 
                  colorScheme="brand" 
                  size="lg"
                />
              </Box>
            )}

            {/* Format Selection */}
            <FormControl>
              <FormLabel>Export Format</FormLabel>
              <Select
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value as ExportFormat)}
                disabled={!!isExporting}
              >
                <option value="pdf">PDF</option>
                <option value="docx">Microsoft Word (DOCX)</option>
                <option value="html">HTML</option>
                <option value="markdown">Markdown</option>
                <option value="json">JSON</option>
              </Select>
              <HStack mt={2} spacing={2}>
                <Icon as={getFormatIcon(selectedFormat)} color="gray.500" />
                <Text fontSize="sm" color="gray.600">
                  {getFormatDescription(selectedFormat)}
                </Text>
              </HStack>
            </FormControl>

            {/* Filename */}
            <FormControl>
              <FormLabel>Filename</FormLabel>
              <Input
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                placeholder={`research-report.${selectedFormat}`}
                disabled={!!isExporting}
              />
              <Text fontSize="sm" color="gray.600" mt={1}>
                Don't include the file extension - it will be added automatically
              </Text>
            </FormControl>

            <Divider />

            {/* Section Selection */}
            <FormControl>
              <FormLabel>Include Sections</FormLabel>
              <CheckboxGroup
                value={includeSections}
                onChange={(values) => setIncludeSections(values as string[])}
              >
                <Stack spacing={2}>
                  <Checkbox value="summary" isDisabled={!!isExporting}>
                    Executive Summary
                  </Checkbox>
                  <Checkbox value="content" isDisabled={!!isExporting}>
                    Main Content
                  </Checkbox>
                  <Checkbox value="findings" isDisabled={!!isExporting}>
                    Key Findings
                  </Checkbox>
                  <Checkbox value="recommendations" isDisabled={!!isExporting}>
                    Recommendations
                  </Checkbox>
                  <Checkbox value="sources" isDisabled={!!isExporting}>
                    Sources & References
                  </Checkbox>
                  <Checkbox value="metadata" isDisabled={!!isExporting}>
                    Metadata
                  </Checkbox>
                </Stack>
              </CheckboxGroup>
            </FormControl>

            {/* Format-specific Options */}
            {(selectedFormat === 'pdf' || selectedFormat === 'docx') && (
              <FormControl>
                <FormLabel>Document Options</FormLabel>
                <Stack spacing={2}>
                  <Checkbox
                    isChecked={customOptions.includeTableOfContents}
                    onChange={(e) => setCustomOptions(prev => ({
                      ...prev,
                      includeTableOfContents: e.target.checked
                    }))}
                    isDisabled={!!isExporting}
                  >
                    Include Table of Contents
                  </Checkbox>
                  <Checkbox
                    isChecked={customOptions.includePageNumbers}
                    onChange={(e) => setCustomOptions(prev => ({
                      ...prev,
                      includePageNumbers: e.target.checked
                    }))}
                    isDisabled={!!isExporting}
                  >
                    Include Page Numbers
                  </Checkbox>
                  <Checkbox
                    isChecked={customOptions.includeWatermark}
                    onChange={(e) => setCustomOptions(prev => ({
                      ...prev,
                      includeWatermark: e.target.checked
                    }))}
                    isDisabled={!!isExporting}
                  >
                    Include Watermark
                  </Checkbox>
                </Stack>
              </FormControl>
            )}

            {selectedFormat === 'pdf' && (
              <FormControl>
                <FormLabel>Compression Level</FormLabel>
                <Select
                  value={customOptions.compressionLevel}
                  onChange={(e) => setCustomOptions(prev => ({
                    ...prev,
                    compressionLevel: e.target.value
                  }))}
                  disabled={!!isExporting}
                >
                  <option value="low">Low (Best Quality)</option>
                  <option value="medium">Medium (Balanced)</option>
                  <option value="high">High (Smaller File)</option>
                </Select>
              </FormControl>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <HStack spacing={3}>
            <Button variant="outline" onClick={handleClose}>
              {isCompleted ? 'Close' : 'Cancel'}
            </Button>
            {!isCompleted && (
              <Button
                colorScheme="brand"
                onClick={handleExport}
                leftIcon={<Icon as={Download} />}
                isLoading={createExport.isPending || !!isExporting}
                isDisabled={!filename.trim() || includeSections.length === 0}
              >
                {isExporting ? 'Exporting...' : 'Start Export'}
              </Button>
            )}
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
