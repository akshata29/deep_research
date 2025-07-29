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
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Grid,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Tooltip,
} from '@chakra-ui/react';
import { 
  Search, 
  Download, 
  MoreVertical, 
  Eye, 
  Trash2, 
  RefreshCw, 
  BarChart3, 
  Archive, 
  FileText
} from 'lucide-react';
import { 
  useExports, 
  useDeleteExport, 
  useDownloadExport, 
  useStorageStats, 
  useCleanupOldExports 
} from '@/hooks/useApi';
import { ExportFormat } from '@/types';

interface ExportFilters {
  search: string;
  status: 'processing' | 'completed' | 'failed' | '';
  format: ExportFormat | '';
  limit: number;
  offset: number;
}

export const ExportsPage: React.FC = () => {
  const toast = useToast();
  const { isOpen: isStatsOpen, onOpen: onStatsOpen, onClose: onStatsClose } = useDisclosure();
  const { isOpen: isCleanupOpen, onOpen: onCleanupOpen, onClose: onCleanupClose } = useDisclosure();
  
  const [filters, setFilters] = useState<ExportFilters>({
    search: '',
    status: '',
    format: '',
    limit: 20,
    offset: 0,
  });
  
  const [cleanupDays, setCleanupDays] = useState<number>(30);

  // Build API params from filters
  const apiParams = {
    limit: filters.limit,
    offset: filters.offset,
    ...(filters.format && { format_filter: filters.format }),
    ...(filters.status && { status_filter: filters.status }),
  };

  const { data: exportsData, isLoading, error, refetch } = useExports(apiParams);
  const { data: storageStats, isLoading: statsLoading } = useStorageStats();
  const deleteExport = useDeleteExport();
  const downloadExport = useDownloadExport();
  const cleanupOldExports = useCleanupOldExports();

  // Filter exports by search term on client side
  const filteredExports = exportsData?.exports?.filter(exportItem => {
    if (!filters.search) return true;
    const searchLower = filters.search.toLowerCase();
    return (
      exportItem.research_topic.toLowerCase().includes(searchLower) ||
      exportItem.file_name.toLowerCase().includes(searchLower) ||
      exportItem.export_id.toLowerCase().includes(searchLower)
    );
  }) || [];

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

  const handleCleanup = async () => {
    try {
      const result = await cleanupOldExports.mutateAsync(cleanupDays);
      toast({
        title: 'Cleanup Completed',
        description: result.message,
        status: 'success',
        duration: 5000,
      });
      onCleanupClose();
    } catch (error) {
      toast({
        title: 'Cleanup Failed',
        description: error instanceof Error ? error.message : 'Failed to cleanup exports',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const getStatusColor = (status: 'processing' | 'completed' | 'failed') => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'processing':
        return 'yellow';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getFormatIcon = (format: ExportFormat) => {
    const iconProps = { size: 16 };
    switch (format) {
      case 'pdf':
        return <FileText {...iconProps} color="#d32f2f" />;
      case 'docx':
        return <FileText {...iconProps} color="#1976d2" />;
      case 'pptx':
        return <FileText {...iconProps} color="#f57c00" />;
      case 'markdown':
        return <FileText {...iconProps} color="#388e3c" />;
      case 'html':
        return <FileText {...iconProps} color="#9c27b0" />;
      case 'json':
        return <FileText {...iconProps} color="#607d8b" />;
      default:
        return <FileText {...iconProps} />;
    }
  };

  if (error) {
    return (
      <Container maxW="container.xl" py={8}>
        <Alert status="error">
          <AlertIcon />
          <AlertDescription>
            Failed to load exports: {error instanceof Error ? error.message : 'Unknown error'}
          </AlertDescription>
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between" align="flex-start">
          <Box>
            <Heading size="lg" mb={2}>
              Export Management
            </Heading>
            <Text color="gray.600">
              View and manage all your research exports
            </Text>
          </Box>
          <HStack>
            <Button
              leftIcon={<Icon as={BarChart3} />}
              variant="outline"
              onClick={onStatsOpen}
              isLoading={statsLoading}
            >
              Storage Stats
            </Button>
            <Button
              leftIcon={<Icon as={Archive} />}
              variant="outline"
              colorScheme="orange"
              onClick={onCleanupOpen}
            >
              Cleanup Old
            </Button>
            <Button
              leftIcon={<Icon as={RefreshCw} />}
              variant="outline"
              onClick={() => refetch()}
              isLoading={isLoading}
            >
              Refresh
            </Button>
          </HStack>
        </HStack>

        {/* Storage Stats Cards */}
        {storageStats?.data && (
          <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Total Exports</StatLabel>
                  <StatNumber>{storageStats.data.total_files}</StatNumber>
                  <StatHelpText>All time</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Storage Used</StatLabel>
                  <StatNumber>{storageStats.data.total_size_mb} MB</StatNumber>
                  <StatHelpText>
                    Avg: {storageStats.data.average_file_size_mb} MB per file
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Total Downloads</StatLabel>
                  <StatNumber>{storageStats.data.total_downloads}</StatNumber>
                  <StatHelpText>All exports</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </Grid>
        )}

        {/* Filters */}
        <Card>
          <CardBody>
            <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
              <FormControl>
                <FormLabel>Search</FormLabel>
                <InputGroup>
                  <InputLeftElement>
                    <Icon as={Search} color="gray.400" />
                  </InputLeftElement>
                  <Input
                    placeholder="Search exports..."
                    value={filters.search}
                    onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  />
                </InputGroup>
              </FormControl>
              <FormControl>
                <FormLabel>Status</FormLabel>
                <Select
                  value={filters.status}
                  onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value as any, offset: 0 }))}
                >
                  <option value="">All Statuses</option>
                  <option value="completed">Completed</option>
                  <option value="processing">Processing</option>
                  <option value="failed">Failed</option>
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel>Format</FormLabel>
                <Select
                  value={filters.format}
                  onChange={(e) => setFilters(prev => ({ ...prev, format: e.target.value as any, offset: 0 }))}
                >
                  <option value="">All Formats</option>
                  <option value="pdf">PDF</option>
                  <option value="docx">Word Document</option>
                  <option value="pptx">PowerPoint</option>
                  <option value="markdown">Markdown</option>
                  <option value="html">HTML</option>
                  <option value="json">JSON</option>
                </Select>
              </FormControl>
            </Grid>
          </CardBody>
        </Card>

        {/* Exports Table */}
        <Card>
          <CardHeader>
            <HStack justify="space-between">
              <Text fontWeight="medium">
                Exports ({filteredExports.length} of {exportsData?.total_count || 0})
              </Text>
              {isLoading && <Spinner size="sm" />}
            </HStack>
          </CardHeader>
          <CardBody p={0}>
            {filteredExports.length === 0 ? (
              <Box p={8} textAlign="center">
                <Text color="gray.500">
                  {filters.search || filters.status || filters.format
                    ? 'No exports match your filters'
                    : 'No exports found. Start by creating a research report and exporting it.'}
                </Text>
              </Box>
            ) : (
              <TableContainer>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Research Topic</Th>
                      <Th>Format</Th>
                      <Th>Status</Th>
                      <Th>File Size</Th>
                      <Th>Created</Th>
                      <Th>Downloads</Th>
                      <Th>Last Accessed</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredExports.map((exportItem) => (
                      <Tr key={exportItem.export_id}>
                        <Td>
                          <VStack align="start" spacing={1}>
                            <Text fontWeight="medium" fontSize="sm">
                              {exportItem.research_topic}
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              {exportItem.file_name}
                            </Text>
                            {exportItem.word_count && (
                              <Text fontSize="xs" color="gray.500">
                                {exportItem.word_count.toLocaleString()} words
                                {exportItem.sections_count && ` • ${exportItem.sections_count} sections`}
                              </Text>
                            )}
                          </VStack>
                        </Td>
                        <Td>
                          <HStack>
                            {getFormatIcon(exportItem.format)}
                            <Text fontSize="sm" textTransform="uppercase">
                              {exportItem.format}
                            </Text>
                          </HStack>
                        </Td>
                        <Td>
                          <Badge colorScheme={getStatusColor(exportItem.status)}>
                            {exportItem.status}
                          </Badge>
                        </Td>
                        <Td>
                          <Text fontSize="sm">
                            {formatFileSize(exportItem.file_size_bytes)}
                          </Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm">
                            {formatDate(exportItem.export_date)}
                          </Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm">
                            {exportItem.download_count}
                          </Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm" color="gray.500">
                            {exportItem.last_accessed
                              ? formatDate(exportItem.last_accessed)
                              : 'Never'}
                          </Text>
                        </Td>
                        <Td>
                          <HStack>
                            {exportItem.status === 'completed' && exportItem.download_url && (
                              <Tooltip label="Download">
                                <IconButton
                                  aria-label="Download"
                                  icon={<Icon as={Download} />}
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDownload(exportItem.export_id, exportItem.file_name)}
                                />
                              </Tooltip>
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
                                  icon={<Icon as={Eye} />}
                                  onClick={() => {
                                    // Could add preview functionality here
                                    toast({
                                      title: 'Export Details',
                                      description: `
                                        Topic: ${exportItem.research_topic}
                                        Format: ${exportItem.format.toUpperCase()}
                                        Size: ${formatFileSize(exportItem.file_size_bytes)}
                                        Downloads: ${exportItem.download_count}
                                      `,
                                      status: 'info',
                                      duration: 5000,
                                    });
                                  }}
                                >
                                  View Details
                                </MenuItem>
                                <MenuItem
                                  icon={<Icon as={Trash2} />}
                                  onClick={() => handleDelete(exportItem.export_id, exportItem.file_name)}
                                  color="red.500"
                                >
                                  Delete
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

        {/* Pagination */}
        {exportsData && exportsData.total_count > filters.limit && (
          <HStack justify="space-between">
            <Text fontSize="sm" color="gray.600">
              Showing {filters.offset + 1}-{Math.min(filters.offset + filters.limit, exportsData.total_count)} of{' '}
              {exportsData.total_count}
            </Text>
            <HStack>
              <Button
                size="sm"
                variant="outline"
                isDisabled={filters.offset === 0}
                onClick={() => setFilters(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
              >
                Previous
              </Button>
              <Button
                size="sm"
                variant="outline"
                isDisabled={filters.offset + filters.limit >= exportsData.total_count}
                onClick={() => setFilters(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
              >
                Next
              </Button>
            </HStack>
          </HStack>
        )}

        {/* Storage Stats Modal */}
        <Modal isOpen={isStatsOpen} onClose={onStatsClose} size="lg">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Storage Statistics</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              {storageStats?.data && (
                <VStack spacing={4} align="stretch">
                  <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                    <Stat>
                      <StatLabel>Total Files</StatLabel>
                      <StatNumber>{storageStats.data.total_files}</StatNumber>
                    </Stat>
                    <Stat>
                      <StatLabel>Total Size</StatLabel>
                      <StatNumber>{storageStats.data.total_size_mb} MB</StatNumber>
                    </Stat>
                    <Stat>
                      <StatLabel>Total Downloads</StatLabel>
                      <StatNumber>{storageStats.data.total_downloads}</StatNumber>
                    </Stat>
                    <Stat>
                      <StatLabel>Avg File Size</StatLabel>
                      <StatNumber>{storageStats.data.average_file_size_mb} MB</StatNumber>
                    </Stat>
                  </Grid>
                  
                  <Box>
                    <Text fontWeight="medium" mb={3}>Format Breakdown</Text>
                    <VStack spacing={2} align="stretch">
                      {Object.entries(storageStats.data.format_breakdown).map(([format, stats]) => (
                        <HStack key={format} justify="space-between">
                          <HStack>
                            {getFormatIcon(format as ExportFormat)}
                            <Text textTransform="uppercase">{format}</Text>
                          </HStack>
                          <HStack>
                            <Text>{stats.count} files</Text>
                            <Text color="gray.500">
                              ({formatFileSize(stats.size)})
                            </Text>
                          </HStack>
                        </HStack>
                      ))}
                    </VStack>
                  </Box>
                </VStack>
              )}
            </ModalBody>
            <ModalFooter>
              <Button onClick={onStatsClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Cleanup Modal */}
        <Modal isOpen={isCleanupOpen} onClose={onCleanupClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Cleanup Old Exports</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4} align="stretch">
                <Text>
                  This will permanently delete all exports older than the specified number of days.
                </Text>
                <FormControl>
                  <FormLabel>Delete exports older than (days)</FormLabel>
                  <NumberInput
                    value={cleanupDays}
                    onChange={(_, value) => setCleanupDays(value || 30)}
                    min={1}
                    max={365}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>
                <Alert status="warning">
                  <AlertIcon />
                  <AlertDescription>
                    This action cannot be undone. Deleted exports cannot be recovered.
                  </AlertDescription>
                </Alert>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onCleanupClose}>
                Cancel
              </Button>
              <Button
                colorScheme="red"
                onClick={handleCleanup}
                isLoading={cleanupOldExports.isPending}
              >
                Delete Old Exports
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </VStack>
    </Container>
  );
};
