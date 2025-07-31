import React, { useState } from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  Select,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  IconButton,
  useToast,
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
  Textarea,
  SimpleGrid,
  Card,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  Tooltip,
  Alert,
  AlertIcon,
  Spinner,
  Flex,
  Tag,
  TagLabel,
  TagCloseButton,
} from '@chakra-ui/react';
import {
  Plus,
  Play,
  Edit,
  Trash2,
  Archive,
  BarChart3,
  RefreshCw,
} from 'lucide-react';
import {
  useListSessions,
  useCreateSession,
  useUpdateSession,
  useDeleteSession,
  useRestoreSession,
  useSessionStorageStats,
  useCleanupOldSessions,
} from '@/hooks/useApi';
import { ResearchSession, SessionCreateRequest, SessionUpdateRequest } from '@/types';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/services/api';

export const SessionsPage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  
  // State for filters and pagination
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  
  // Modal states
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure();
  const { isOpen: isStatsOpen, onOpen: onStatsOpen, onClose: onStatsClose } = useDisclosure();
  const [selectedSession, setSelectedSession] = useState<ResearchSession | null>(null);
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    topic: '',
    tags: [] as string[],
    notes: '',
    status: 'active'
  });
  const [newTag, setNewTag] = useState('');
  
  // API hooks
  const { data: sessionsData, isLoading, refetch } = useListSessions({
    page,
    page_size: pageSize,
    status_filter: statusFilter || undefined,
    search_query: searchQuery || undefined,
  });
  
  const { data: storageStats } = useSessionStorageStats();
  const createSessionMutation = useCreateSession();
  const updateSessionMutation = useUpdateSession();
  const deleteSessionMutation = useDeleteSession();
  const restoreSessionMutation = useRestoreSession();
  const cleanupMutation = useCleanupOldSessions();
  
  const sessions = sessionsData?.sessions || [];
  const totalCount = sessionsData?.total_count || 0;
  
  // Reset form
  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      topic: '',
      tags: [],
      notes: '',
      status: 'active'
    });
    setNewTag('');
    setSelectedSession(null);
  };
  
  // Handle create session
  const handleCreateSession = async () => {
    try {
      const request: SessionCreateRequest = {
        title: formData.title,
        description: formData.description,
        topic: formData.topic,
        tags: formData.tags,
      };
      
      await createSessionMutation.mutateAsync(request);
      
      toast({
        title: 'Session Created',
        description: 'Research session created successfully',
        status: 'success',
        duration: 3000,
      });
      
      resetForm();
      onCreateClose();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create session',
        status: 'error',
        duration: 3000,
      });
    }
  };
  
  // Handle update session
  const handleUpdateSession = async () => {
    if (!selectedSession) return;
    
    try {
      const request: SessionUpdateRequest = {
        title: formData.title,
        description: formData.description,
        tags: formData.tags,
        notes: formData.notes,
        status: formData.status,
      };
      
      await updateSessionMutation.mutateAsync({
        sessionId: selectedSession.session_id,
        request,
      });
      
      toast({
        title: 'Session Updated',
        description: 'Research session updated successfully',
        status: 'success',
        duration: 3000,
      });
      
      resetForm();
      onEditClose();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update session',
        status: 'error',
        duration: 3000,
      });
    }
  };
  
  // Handle delete session
  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) return;
    
    try {
      await deleteSessionMutation.mutateAsync(sessionId);
      
      toast({
        title: 'Session Deleted',
        description: 'Research session deleted successfully',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete session',
        status: 'error',
        duration: 3000,
      });
    }
  };
  
  // Handle restore session
  const handleRestoreSession = async (session: ResearchSession) => {
    try {
      // Check if this is an orchestration session
      if (session.session_type === 'orchestration') {
        // Restore orchestration session
        const result = await apiClient.restoreOrchestrationSession(session.session_id);
        
        toast({
          title: 'Orchestration Session Restored',
          description: `Session ${session.session_id.slice(0, 8)} restored successfully`,
          status: 'success',
          duration: 3000,
        });
        
        // Navigate to orchestration page with restored data
        navigate(`/orchestration/${session.session_id}`, { 
          state: { 
            restoredSession: result.restoration_data,
            sessionId: session.session_id
          } 
        });
      } else {
        // Restore regular research session
        const result = await restoreSessionMutation.mutateAsync({
          sessionId: session.session_id,
          request: { session_id: session.session_id },
        });
        
        toast({
          title: 'Session Restored',
          description: `Session restored to ${result.restoration_data.phase} phase`,
          status: 'success',
          duration: 3000,
        });
        
        // Navigate to research page with restored state and session ID
        navigate('/research', { 
          state: { 
            restoredSession: result.restoration_data,
            sessionId: session.session_id
          } 
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to restore session',
        status: 'error',
        duration: 3000,
      });
    }
  };
  
  // Handle cleanup old sessions
  const handleCleanup = async () => {
    try {
      const result = await cleanupMutation.mutateAsync(90); // Archive sessions older than 90 days
      
      toast({
        title: 'Cleanup Complete',
        description: result.message,
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to cleanup sessions',
        status: 'error',
        duration: 3000,
      });
    }
  };
  
  // Open edit modal with session data
  const openEditModal = (session: ResearchSession) => {
    setSelectedSession(session);
    setFormData({
      title: session.title,
      description: session.description,
      topic: session.topic,
      tags: session.tags,
      notes: session.notes,
      status: session.status,
    });
    onEditOpen();
  };
  
  // Add tag
  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };
  
  // Remove tag
  const removeTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };
  
  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'completed': return 'blue';
      case 'archived': return 'gray';
      default: return 'gray';
    }
  };
  
  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Flex align="center" justify="space-between">
          <Box>
            <Heading size="lg" color="gray.800">
              Session History
            </Heading>
            <Text color="gray.600" mt={1}>
              Manage and restore your research sessions
            </Text>
          </Box>
          <HStack spacing={3}>
            <Button
              leftIcon={<BarChart3 size={16} />}
              variant="outline"
              size="sm"
              onClick={onStatsOpen}
            >
              Statistics
            </Button>
            <Button
              leftIcon={<Archive size={16} />}
              variant="outline"
              size="sm"
              onClick={handleCleanup}
              isLoading={cleanupMutation.isPending}
            >
              Cleanup
            </Button>
            <Button
              leftIcon={<Plus size={16} />}
              colorScheme="blue"
              size="sm"
              onClick={onCreateOpen}
            >
              New Session
            </Button>
          </HStack>
        </Flex>
        
        {/* Storage Stats Summary */}
        {storageStats?.data && (
          <SimpleGrid columns={4} spacing={4}>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Total Sessions</StatLabel>
                  <StatNumber>{storageStats.data.total_sessions}</StatNumber>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Active Sessions</StatLabel>
                  <StatNumber>{storageStats.data.active_sessions}</StatNumber>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Completed</StatLabel>
                  <StatNumber>{storageStats.data.completed_sessions}</StatNumber>
                </Stat>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <Stat>
                  <StatLabel>Archived</StatLabel>
                  <StatNumber>{storageStats.data.archived_sessions}</StatNumber>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>
        )}
        
        {/* Filters */}
        <HStack spacing={4}>
          <Input
            placeholder="Search sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            maxW="300px"
          />
          <Select
            placeholder="All statuses"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            maxW="150px"
          >
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="archived">Archived</option>
          </Select>
          <Button
            leftIcon={<RefreshCw size={16} />}
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            isLoading={isLoading}
          >
            Refresh
          </Button>
        </HStack>
        
        {/* Sessions Table */}
        {isLoading ? (
          <Flex justify="center" py={8}>
            <Spinner size="lg" />
          </Flex>
        ) : sessions.length === 0 ? (
          <Alert status="info">
            <AlertIcon />
            No sessions found. Create your first research session to get started.
          </Alert>
        ) : (
          <Box overflowX="auto">
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>Title</Th>
                  <Th>Phase</Th>
                  <Th>Status</Th>
                  <Th>Progress</Th>
                  <Th>Updated</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {sessions.map((session) => (
                  <Tr key={session.session_id}>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <HStack spacing={2}>
                          <Text fontWeight="medium">{session.title}</Text>
                          {session.session_type === 'orchestration' && (
                            <Badge colorScheme="blue" variant="solid" size="sm">
                              Multi-Agent
                            </Badge>
                          )}
                        </HStack>
                        {session.description && (
                          <Text fontSize="sm" color="gray.600" noOfLines={1}>
                            {session.description}
                          </Text>
                        )}
                        {session.tags.length > 0 && (
                          <HStack spacing={1}>
                            {session.tags.slice(0, 3).map((tag) => (
                              <Tag key={tag} size="sm" colorScheme={session.session_type === 'orchestration' ? 'blue' : 'gray'}>
                                <TagLabel>{tag}</TagLabel>
                              </Tag>
                            ))}
                            {session.tags.length > 3 && (
                              <Text fontSize="sm" color="gray.500">
                                +{session.tags.length - 3} more
                              </Text>
                            )}
                          </HStack>
                        )}
                      </VStack>
                    </Td>
                    <Td>
                      <Badge colorScheme="purple" variant="subtle">
                        {session.current_phase}
                      </Badge>
                    </Td>
                    <Td>
                      <Badge colorScheme={getStatusColor(session.status)} variant="subtle">
                        {session.status}
                      </Badge>
                    </Td>
                    <Td>
                      <Text fontSize="sm">
                        {Math.round(session.completion_percentage)}%
                      </Text>
                    </Td>
                    <Td>
                      <VStack align="start" spacing={0}>
                        <Text fontSize="sm">{formatDate(session.updated_at)}</Text>
                        <Text fontSize="xs" color="gray.500">
                          Created {formatDate(session.created_at)}
                        </Text>
                      </VStack>
                    </Td>
                    <Td>
                      <HStack spacing={1}>
                        <Tooltip label="Restore Session">
                          <IconButton
                            aria-label="Restore session"
                            icon={<Play size={14} />}
                            size="sm"
                            variant="ghost"
                            colorScheme="green"
                            onClick={() => handleRestoreSession(session)}
                            isLoading={restoreSessionMutation.isPending}
                          />
                        </Tooltip>
                        <Tooltip label="Edit Session">
                          <IconButton
                            aria-label="Edit session"
                            icon={<Edit size={14} />}
                            size="sm"
                            variant="ghost"
                            colorScheme="blue"
                            onClick={() => openEditModal(session)}
                          />
                        </Tooltip>
                        <Tooltip label="Delete Session">
                          <IconButton
                            aria-label="Delete session"
                            icon={<Trash2 size={14} />}
                            size="sm"
                            variant="ghost"
                            colorScheme="red"
                            onClick={() => handleDeleteSession(session.session_id)}
                            isLoading={deleteSessionMutation.isPending}
                          />
                        </Tooltip>
                      </HStack>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        )}
        
        {/* Pagination */}
        {totalCount > pageSize && (
          <HStack justify="center" spacing={4}>
            <Button
              size="sm"
              onClick={() => setPage(page - 1)}
              isDisabled={page === 1}
            >
              Previous
            </Button>
            <Text fontSize="sm">
              Page {page} of {Math.ceil(totalCount / pageSize)}
            </Text>
            <Button
              size="sm"
              onClick={() => setPage(page + 1)}
              isDisabled={page >= Math.ceil(totalCount / pageSize)}
            >
              Next
            </Button>
          </HStack>
        )}
      </VStack>
      
      {/* Create Session Modal */}
      <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create New Session</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Title</FormLabel>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Enter session title"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>Description</FormLabel>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Enter session description"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>Initial Topic</FormLabel>
                <Input
                  value={formData.topic}
                  onChange={(e) => setFormData(prev => ({ ...prev, topic: e.target.value }))}
                  placeholder="Enter research topic (optional)"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>Tags</FormLabel>
                <HStack>
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="Add a tag"
                    onKeyPress={(e) => e.key === 'Enter' && addTag()}
                  />
                  <Button size="sm" onClick={addTag}>Add</Button>
                </HStack>
                {formData.tags.length > 0 && (
                  <HStack mt={2} wrap="wrap">
                    {formData.tags.map((tag) => (
                      <Tag key={tag} size="sm" colorScheme="blue">
                        <TagLabel>{tag}</TagLabel>
                        <TagCloseButton onClick={() => removeTag(tag)} />
                      </Tag>
                    ))}
                  </HStack>
                )}
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onCreateClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleCreateSession}
              isLoading={createSessionMutation.isPending}
              isDisabled={!formData.title.trim()}
            >
              Create Session
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
      
      {/* Edit Session Modal */}
      <Modal isOpen={isEditOpen} onClose={onEditClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Edit Session</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Title</FormLabel>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Enter session title"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>Description</FormLabel>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Enter session description"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>Status</FormLabel>
                <Select
                  value={formData.status}
                  onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                >
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="archived">Archived</option>
                </Select>
              </FormControl>
              
              <FormControl>
                <FormLabel>Notes</FormLabel>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="Add notes about this session"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel>Tags</FormLabel>
                <HStack>
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="Add a tag"
                    onKeyPress={(e) => e.key === 'Enter' && addTag()}
                  />
                  <Button size="sm" onClick={addTag}>Add</Button>
                </HStack>
                {formData.tags.length > 0 && (
                  <HStack mt={2} wrap="wrap">
                    {formData.tags.map((tag) => (
                      <Tag key={tag} size="sm" colorScheme="blue">
                        <TagLabel>{tag}</TagLabel>
                        <TagCloseButton onClick={() => removeTag(tag)} />
                      </Tag>
                    ))}
                  </HStack>
                )}
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onEditClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleUpdateSession}
              isLoading={updateSessionMutation.isPending}
              isDisabled={!formData.title.trim()}
            >
              Update Session
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
      
      {/* Storage Stats Modal */}
      <Modal isOpen={isStatsOpen} onClose={onStatsClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Storage Statistics</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {storageStats?.data && (
              <VStack spacing={4} align="stretch">
                <SimpleGrid columns={2} spacing={4}>
                  <Card>
                    <CardBody>
                      <Stat>
                        <StatLabel>Total Sessions</StatLabel>
                        <StatNumber>{storageStats.data.total_sessions}</StatNumber>
                      </Stat>
                    </CardBody>
                  </Card>
                  <Card>
                    <CardBody>
                      <Stat>
                        <StatLabel>Active Sessions</StatLabel>
                        <StatNumber>{storageStats.data.active_sessions}</StatNumber>
                      </Stat>
                    </CardBody>
                  </Card>
                  <Card>
                    <CardBody>
                      <Stat>
                        <StatLabel>Completed Sessions</StatLabel>
                        <StatNumber>{storageStats.data.completed_sessions}</StatNumber>
                      </Stat>
                    </CardBody>
                  </Card>
                  <Card>
                    <CardBody>
                      <Stat>
                        <StatLabel>Archived Sessions</StatLabel>
                        <StatNumber>{storageStats.data.archived_sessions}</StatNumber>
                      </Stat>
                    </CardBody>
                  </Card>
                </SimpleGrid>
                
                <Card>
                  <CardBody>
                    <Stat>
                      <StatLabel>Storage Size</StatLabel>
                      <StatNumber>
                        {(storageStats.data.total_size_bytes / 1024).toFixed(1)} KB
                      </StatNumber>
                    </Stat>
                  </CardBody>
                </Card>
                
                {storageStats.data.unique_tags.length > 0 && (
                  <Box>
                    <Text fontWeight="medium" mb={2}>Available Tags</Text>
                    <HStack wrap="wrap">
                      {storageStats.data.unique_tags.map((tag) => (
                        <Tag key={tag} size="sm" colorScheme="blue">
                          <TagLabel>{tag}</TagLabel>
                        </Tag>
                      ))}
                    </HStack>
                  </Box>
                )}
                
                <Box>
                  <Text fontWeight="medium" mb={1}>Storage Location</Text>
                  <Text fontSize="sm" color="gray.600" fontFamily="mono">
                    {storageStats.data.storage_location}
                  </Text>
                </Box>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button onClick={onStatsClose}>Close</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  );
};
