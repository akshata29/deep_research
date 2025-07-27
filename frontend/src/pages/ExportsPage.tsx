import React, { useState } from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  HStack,
  Button,
  Card,
  CardBody,
  CardHeader,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Badge,
  Text,
  Input,
  Select,
  InputGroup,
  InputLeftElement,
  Icon,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useToast,
  Alert,
  AlertIcon,
  AlertDescription,
  Spinner,
} from '@chakra-ui/react';
import { Search, Download, MoreVertical, Eye, Trash2, RefreshCw } from 'lucide-react';
import { useExports, useDeleteExport, useDownloadExport } from '@/hooks/useApi';
import { ExportStatus, ExportFormat } from '@/types';

interface ExportFilters {
  search: string;
  status: ExportStatus | '';
  format: ExportFormat | '';
}

export const ExportsPage: React.FC = () => {
  const toast = useToast();
  const [filters, setFilters] = useState<ExportFilters>({
    search: '',
    status: '',
    format: '',
  });

  const { data: exports, isLoading, error, refetch } = useExports(filters);
  const deleteExport = useDeleteExport();
  const downloadExport = useDownloadExport();

  const handleDownload = async (exportId: string, filename: string) => {
    try {
      await downloadExport.mutateAsync({ exportId, filename });
      toast({
        title: 'Download Started',
        description: `${filename} is being downloaded.`,
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Download Failed',
        description: error instanceof Error ? error.message : 'Failed to download file',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleDelete = async (exportId: string, filename: string) => {
    try {
      await deleteExport.mutateAsync(exportId);
      toast({
        title: 'Export Deleted',
        description: `${filename} has been deleted.`,
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Delete Failed',
        description: error instanceof Error ? error.message : 'Failed to delete export',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const getStatusColor = (status: ExportStatus) => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'processing':
        return 'blue';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const filteredExports = exports?.filter(exportItem => {
    const matchesSearch = !filters.search || 
      exportItem.filename.toLowerCase().includes(filters.search.toLowerCase()) ||
      exportItem.task_id.toLowerCase().includes(filters.search.toLowerCase());
    
    const matchesStatus = !filters.status || exportItem.status === filters.status;
    const matchesFormat = !filters.format || exportItem.format === filters.format;
    
    return matchesSearch && matchesStatus && matchesFormat;
  }) || [];

  if (error) {
    return (
      <Container maxW="6xl" py={8}>
        <Alert status="error">
          <AlertIcon />
          <AlertDescription>
            Failed to load exports. Please try again later.
          </AlertDescription>
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxW="6xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Box>
            <Heading size="lg" mb={2}>Export Management</Heading>
            <Text color="gray.600" _dark={{ color: 'gray.400' }}>
              Manage and download your research exports
            </Text>
          </Box>
          <Button
            leftIcon={<Icon as={RefreshCw} />}
            onClick={() => refetch()}
            isLoading={isLoading}
          >
            Refresh
          </Button>
        </HStack>

        {/* Filters */}
        <Card>
          <CardBody>
            <HStack spacing={4} wrap="wrap">
              <InputGroup maxW="300px">
                <InputLeftElement pointerEvents="none">
                  <Icon as={Search} color="gray.400" />
                </InputLeftElement>
                <Input
                  placeholder="Search exports..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                />
              </InputGroup>

              <Select
                placeholder="All statuses"
                maxW="200px"
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value as ExportStatus | '' }))}
              >
                <option value="pending">Pending</option>
                <option value="processing">Processing</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </Select>

              <Select
                placeholder="All formats"
                maxW="200px"
                value={filters.format}
                onChange={(e) => setFilters(prev => ({ ...prev, format: e.target.value as ExportFormat | '' }))}
              >
                <option value="pdf">PDF</option>
                <option value="docx">DOCX</option>
                <option value="html">HTML</option>
                <option value="markdown">Markdown</option>
                <option value="json">JSON</option>
              </Select>

              {(filters.search || filters.status || filters.format) && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setFilters({ search: '', status: '', format: '' })}
                >
                  Clear Filters
                </Button>
              )}
            </HStack>
          </CardBody>
        </Card>

        {/* Exports Table */}
        <Card>
          <CardHeader>
            <HStack justify="space-between">
              <Heading size="md">Exports ({filteredExports.length})</Heading>
              {isLoading && <Spinner size="sm" />}
            </HStack>
          </CardHeader>
          <CardBody>
            {isLoading ? (
              <VStack py={8}>
                <Spinner size="lg" />
                <Text>Loading exports...</Text>
              </VStack>
            ) : filteredExports.length === 0 ? (
              <VStack spacing={4} py={12} textAlign="center">
                <Icon as={Download} boxSize={12} color="gray.400" />
                <VStack spacing={2}>
                  <Heading size="md" color="gray.600">
                    No exports found
                  </Heading>
                  <Text color="gray.500" maxW="md">
                    {filters.search || filters.status || filters.format
                      ? "No exports match your current filters."
                      : "You haven't created any exports yet. Start a research task to generate reports."}
                  </Text>
                </VStack>
              </VStack>
            ) : (
              <TableContainer>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Filename</Th>
                      <Th>Task ID</Th>
                      <Th>Format</Th>
                      <Th>Status</Th>
                      <Th>Size</Th>
                      <Th>Created</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredExports.map((exportItem) => (
                      <Tr key={exportItem.export_id}>
                        <Td>
                          <VStack align="start" spacing={1}>
                            <Text fontWeight="medium">{exportItem.filename}</Text>
                            {exportItem.error_message && (
                              <Text fontSize="sm" color="red.500">
                                {exportItem.error_message}
                              </Text>
                            )}
                          </VStack>
                        </Td>
                        <Td>
                          <Text fontSize="sm" fontFamily="mono">
                            {exportItem.task_id}
                          </Text>
                        </Td>
                        <Td>
                          <Badge variant="subtle" colorScheme="blue">
                            {exportItem.format.toUpperCase()}
                          </Badge>
                        </Td>
                        <Td>
                          <Badge colorScheme={getStatusColor(exportItem.status)}>
                            {exportItem.status}
                          </Badge>
                        </Td>
                        <Td>
                          {exportItem.file_size ? formatFileSize(exportItem.file_size) : 'N/A'}
                        </Td>
                        <Td>
                          <Text fontSize="sm">
                            {formatDate(exportItem.created_at)}
                          </Text>
                        </Td>
                        <Td>
                          <HStack spacing={2}>
                            {exportItem.status === 'completed' && (
                              <>
                                <IconButton
                                  aria-label="View export"
                                  icon={<Icon as={Eye} />}
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDownload(exportItem.export_id, exportItem.filename)}
                                />
                                <IconButton
                                  aria-label="Download export"
                                  icon={<Icon as={Download} />}
                                  size="sm"
                                  colorScheme="blue"
                                  variant="ghost"
                                  onClick={() => handleDownload(exportItem.export_id, exportItem.filename)}
                                  isLoading={downloadExport.isPending}
                                />
                              </>
                            )}
                            <Menu>
                              <MenuButton
                                as={IconButton}
                                aria-label="More options"
                                icon={<Icon as={MoreVertical} />}
                                variant="ghost"
                                size="sm"
                              />
                              <MenuList>
                                <MenuItem
                                  icon={<Icon as={Trash2} />}
                                  color="red.500"
                                  onClick={() => handleDelete(exportItem.export_id, exportItem.filename)}
                                  isDisabled={deleteExport.isPending}
                                >
                                  Delete Export
                                </MenuItem>
                              </MenuList>
                            </Menu>
                          </HStack>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </TableContainer>
            )}
          </CardBody>
        </Card>

        {/* Summary Stats */}
        {filteredExports.length > 0 && (
          <Card>
            <CardBody>
              <HStack spacing={8} justify="center">
                <VStack>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">
                    {filteredExports.filter(e => e.status === 'completed').length}
                  </Text>
                  <Text fontSize="sm" color="gray.600">Completed</Text>
                </VStack>
                <VStack>
                  <Text fontSize="2xl" fontWeight="bold" color="blue.500">
                    {filteredExports.filter(e => e.status === 'processing').length}
                  </Text>
                  <Text fontSize="sm" color="gray.600">Processing</Text>
                </VStack>
                <VStack>
                  <Text fontSize="2xl" fontWeight="bold" color="red.500">
                    {filteredExports.filter(e => e.status === 'failed').length}
                  </Text>
                  <Text fontSize="sm" color="gray.600">Failed</Text>
                </VStack>
                <VStack>
                  <Text fontSize="2xl" fontWeight="bold" color="gray.500">
                    {filteredExports.reduce((sum, e) => sum + (e.file_size || 0), 0) > 0 
                      ? formatFileSize(filteredExports.reduce((sum, e) => sum + (e.file_size || 0), 0))
                      : 'N/A'
                    }
                  </Text>
                  <Text fontSize="sm" color="gray.600">Total Size</Text>
                </VStack>
              </HStack>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Container>
  );
};
