import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  VStack,
  HStack,
  Card,
  CardBody,
  CardHeader,
  Textarea,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Badge,
  Icon,
  useToast,
  Spinner,
  Progress,
  Grid,
  GridItem,
  Stat,
  StatLabel,
  StatNumber,
  useColorModeValue,
  Code,
  List,
  ListItem,
} from '@chakra-ui/react';
import { 
  Users, 
  Brain, 
  Search, 
  FileText, 
  CheckCircle, 
  XCircle,
  ArrowLeft
} from 'lucide-react';
import { useOrchestrationResearch, useOrchestrationHealth, useSessionSummary, useSessionProgress } from '../hooks/useOrchestrationApi';
import { ExportDropdown } from '@/components/ExportDropdown';
import { AgentProgressDisplay } from '../components/AgentProgressDisplay';
import { OrchestrationProgress } from '../types';

export const OrchestrationPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  
  const [query, setQuery] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionId || null);
  const [progress, setProgress] = useState<OrchestrationProgress | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [restorationData, setRestorationData] = useState<any>(null);
  const [mockSessionSummary, setMockSessionSummary] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  // API hooks
  const { data: healthData } = useOrchestrationHealth();
  // Load session summary only for active sessions, not restored ones
  const { data: sessionSummary, refetch: refetchSummary, isLoading: sessionLoading } = useSessionSummary(
    currentSessionId || undefined,
    { 
      enabled: !!currentSessionId && !restorationData // Only fetch if not a restored session
    }
  );
  
  // Debug session loading
  console.log('Session summary hook:', {
    currentSessionId,
    sessionLoading,
    hasSessionSummary: !!sessionSummary,
    sessionSummaryData: sessionSummary
  });
  
  const { 
    mutate: startResearch, 
    isPending: isResearching, 
    data: researchResult,
    error: researchError 
  } = useOrchestrationResearch({
    onMutate: () => {
      // Clear previous progress when starting new research
      setProgress(null);
    },
    onSuccess: (data: any) => {
      console.log('Research started with session ID:', data.session_id);
      setCurrentSessionId(data.session_id);
      
      // Don't show completion toast immediately since research runs in background
      toast({
        title: 'Research Started',
        description: 'Multi-agent research orchestration started. Watch the progress below!',
        status: 'info',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Research Failed to Start',
        description: error.message || 'Failed to start research orchestration',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  });

  // Load progress for restored sessions
  const { data: savedProgress, refetch: refetchProgress } = useSessionProgress(
    currentSessionId || undefined,
    { 
      enabled: !!currentSessionId && !restorationData, // Always fetch for active sessions, regardless of other conditions
      refetchInterval: isResearching ? 2000 : 10000, // Refresh every 2s while researching, every 10s otherwise
      staleTime: 1000 // Consider data stale after 1 second
    }
  );

  // Debug logging
  console.log('OrchestrationPage state:', {
    sessionId,
    currentSessionId,
    hasProgress: !!progress,
    progressData: progress,
    hasSavedProgress: !!savedProgress,
    savedProgressData: savedProgress,
    isResearching,
    sessionSummary: sessionSummary ? sessionSummary.session_id : null,
    locationState: location.state
  });

  // Additional detailed logging for debugging
  if (progress) {
    console.log('Current progress details:', {
      session_id: progress.session_id,
      status: progress.status,
      progress_percentage: progress.progress_percentage,
      total_agents: progress.total_agents,
      completed_agents: progress.completed_agents,
      agent_executions_count: progress.agent_executions?.length || 0,
      agent_executions: progress.agent_executions
    });
  }
  
  if (savedProgress) {
    console.log('Saved progress details:', {
      session_id: savedProgress.session_id,
      status: savedProgress.status,
      progress_percentage: savedProgress.progress_percentage,
      total_agents: savedProgress.total_agents,
      completed_agents: savedProgress.completed_agents,
      agent_executions_count: savedProgress.agent_executions?.length || 0,
      agent_executions: savedProgress.agent_executions
    });
  }

  // Handle URL parameter changes (for restored sessions)
  useEffect(() => {
    console.log('URL sessionId parameter changed:', sessionId);
    if (sessionId && sessionId !== currentSessionId) {
      console.log('Setting currentSessionId from URL:', sessionId);
      setCurrentSessionId(sessionId);
    }
    
    // Check if there's restoration data in location state
    const state = location.state as any;
    if (state?.restoredSession && state?.sessionId) {
      console.log('Found restoration data in location state:', state);
      setRestorationData(state.restoredSession);
      if (state.restoredSession.query) {
        setQuery(state.restoredSession.query);
      }
    }
  }, [sessionId, currentSessionId, location.state]);

  // Set query from session summary when it becomes available
  useEffect(() => {
    if (sessionSummary && sessionSummary.query && !query) {
      console.log('Setting query from session summary:', sessionSummary.query);
      setQuery(sessionSummary.query);
    }
  }, [sessionSummary, query]);

  // Convert restoration data to progress format
  useEffect(() => {
    if (restorationData && restorationData.agentExecutions && !progress) {
      console.log('Converting restoration data to progress format:', restorationData);
      
      const restoredProgress: OrchestrationProgress = {
        session_id: restorationData.sessionId,
        status: 'completed', // Restored sessions are always completed
        progress_percentage: 100,
        total_agents: restorationData.agentExecutions.length,
        completed_agents: restorationData.agentExecutions.length,
        failed_agents: restorationData.agentExecutions.filter((exec: any) => exec.status === 'failed').length,
        agent_executions: restorationData.agentExecutions.map((exec: any) => ({
          agent_name: exec.agent_name,
          status: exec.status,
          input: exec.input,
          output: exec.output,
          metadata: exec.metadata,
          execution_time_seconds: exec.execution_time_seconds,
          timestamp: exec.timestamp || exec.start_time || restorationData.createdAt
        })),
        final_result: restorationData.finalResult,
        created_at: restorationData.createdAt,
        updated_at: restorationData.updatedAt,
        metadata: restorationData.metadata
      };
      
      setProgress(restoredProgress);
      
      // Also create a mock session summary for UI consistency
      const mockSummary = {
        session_id: restorationData.sessionId,
        status: 'completed',
        query: restorationData.query,
        start_time: restorationData.createdAt,
        end_time: restorationData.updatedAt,
        result: restorationData.finalResult,
        agents_used: restorationData.agentExecutions.map((exec: any) => exec.agent_name),
        memory_collections: []
      };
      
      setMockSessionSummary(mockSummary);
    }
  }, [restorationData, progress]);
  useEffect(() => {
    console.log('Progress effect triggered:', {
      currentSessionId,
      isResearching,
      hasProgress: !!progress,
      hasSavedProgress: !!savedProgress
    });
    
    if (currentSessionId && savedProgress) {
      console.log('Setting progress from saved data:', savedProgress);
      setProgress(savedProgress);
    }
  }, [currentSessionId, savedProgress]); // Removed other dependencies to always update when savedProgress changes

  // WebSocket connection for real-time progress
  useEffect(() => {
    if (currentSessionId && (isResearching || (!progress && !restorationData))) {
      console.log('Setting up WebSocket connection for session:', currentSessionId);
      
      // Use backend server directly for WebSocket connection
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const backendPort = '8010';
      const wsUrl = `${protocol}//localhost:${backendPort}/api/v1/orchestration/ws/${currentSessionId}`;
      
      console.log('Connecting to WebSocket:', wsUrl);
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        setWsConnected(true);
        console.log('WebSocket connected for session:', currentSessionId);
        
        // Send a ping to request current progress
        if (wsRef.current) {
          wsRef.current.send(JSON.stringify({ type: 'get_progress' }));
        }
        
        // Set up heartbeat to keep connection alive
        const heartbeat = setInterval(() => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // Send ping every 30 seconds
        
        // Store heartbeat for cleanup
        (wsRef.current as any).heartbeat = heartbeat;
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('WebSocket message received:', message);
          
          switch (message.type) {
            case 'connection_established':
              console.log('WebSocket connection established');
              break;
            case 'progress_update':
              // Handle enhanced progress update from backend
              if (message.session_id === currentSessionId) {
                const progressData: OrchestrationProgress = {
                  session_id: message.session_id,
                  status: message.status || 'running',
                  progress_percentage: message.progress_percentage || 0,
                  total_agents: message.total_agents || 0,
                  completed_agents: message.completed_agents || 0,
                  failed_agents: message.failed_agents || 0,
                  agent_executions: message.agent_executions || [],
                  final_result: message.final_result || '',
                  created_at: message.created_at || '',
                  updated_at: message.updated_at || '',
                  metadata: message.metadata || {}
                };
                console.log('Setting progress from WebSocket update:', progressData);
                
                // Force refresh the saved progress query
                console.log('Forcing query refetch after progress update');
                refetchProgress();
                
                // Check if research just completed
                const wasCompleted = progress?.status === 'completed';
                const isNowCompleted = progressData.status === 'completed';
                
                if (!wasCompleted && isNowCompleted) {
                  toast({
                    title: 'Research Completed',
                    description: 'Multi-agent research orchestration completed successfully!',
                    status: 'success',
                    duration: 5000,
                    isClosable: true,
                  });
                  // Refetch session summary when completed
                  refetchSummary();
                }
                
                setProgress(progressData);
              }
              break;
            case 'agent_progress':
              // Handle legacy format for backward compatibility
              if (message.data || message.session_id) {
                const progressData: OrchestrationProgress = {
                  session_id: message.session_id || currentSessionId,
                  status: message.data?.status || message.status || 'running',
                  progress_percentage: message.data?.progress_percentage || 0,
                  total_agents: message.data?.total_agents || 0,
                  completed_agents: message.data?.completed_agents || 0,
                  failed_agents: message.data?.failed_agents || 0,
                  agent_executions: message.data?.agent_executions || message.agent_executions || [],
                  final_result: message.data?.final_result || message.final_result || '',
                  created_at: message.data?.created_at || '',
                  updated_at: message.data?.updated_at || '',
                  metadata: message.data?.metadata || {}
                };
                console.log('Setting progress from legacy WebSocket format:', progressData);
                
                // Force refresh the saved progress query
                console.log('Forcing query refetch after legacy progress update');
                refetchProgress();
                
                setProgress(progressData);
              }
              break;
            case 'session_progress':
              // Handle session progress updates
              if (message.agent_executions) {
                const totalAgents = message.agent_executions.length;
                const completedAgents = message.agent_executions.filter((exec: any) => exec.status === 'completed').length;
                const failedAgents = message.agent_executions.filter((exec: any) => exec.status === 'failed').length;
                
                const progressData: OrchestrationProgress = {
                  session_id: message.session_id,
                  status: message.status,
                  progress_percentage: totalAgents > 0 ? (completedAgents / totalAgents) * 100 : 0,
                  total_agents: totalAgents,
                  completed_agents: completedAgents,
                  failed_agents: failedAgents,
                  agent_executions: message.agent_executions,
                  final_result: '',
                  created_at: '',
                  updated_at: '',
                  metadata: {}
                };
                setProgress(progressData);
              }
              break;
            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        setWsConnected(false);
        console.log('WebSocket disconnected');
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };
    }
    
    return () => {
      if (wsRef.current) {
        // Clear heartbeat
        if ((wsRef.current as any).heartbeat) {
          clearInterval((wsRef.current as any).heartbeat);
        }
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [currentSessionId, isResearching, progress, restorationData]);

  // Load progress for restored sessions
  useEffect(() => {
    if (currentSessionId && !isResearching && !progress && savedProgress) {
      setProgress(savedProgress);
    }
  }, [currentSessionId, isResearching, progress, savedProgress]);

  // Clear progress when starting new session
  useEffect(() => {
    if (!currentSessionId) {
      setProgress(null);
      setWsConnected(false);
      setRestorationData(null);
      setMockSessionSummary(null);
    }
  }, [currentSessionId]);

  const handleStartResearch = () => {
    if (!query.trim()) {
      toast({
        title: 'Query Required',
        description: 'Please enter a research query',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    startResearch({
      query: query.trim(),
      session_id: currentSessionId || undefined,
    });
  };

  const handleNewSession = () => {
    setCurrentSessionId(null);
    setQuery('');
    setProgress(null);
    setWsConnected(false);
    setRestorationData(null);
    setMockSessionSummary(null);
  };

  // Health status indicators
  const getHealthStatus = () => {
    if (!healthData || !healthData.configuration) return { status: 'unknown', color: 'gray' };
    
    const config = healthData.configuration;
    const requiredServices = [
      config.azure_openai_configured,
      config.embedding_configured
    ];
    
    const optionalServices = [
      config.azure_search_configured,
      config.web_search_configured
    ];
    
    const allRequired = requiredServices.every(Boolean);
    const someOptional = optionalServices.some(Boolean);
    
    if (allRequired && someOptional) {
      return { status: 'optimal', color: 'green' };
    } else if (allRequired) {
      return { status: 'basic', color: 'yellow' };
    } else {
      return { status: 'limited', color: 'red' };
    }
  };

  const healthStatus = getHealthStatus();

  return (
    <Container maxW="6xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <Box>
          <HStack spacing={4} mb={4}>
            <Button
              variant="ghost"
              leftIcon={<Icon as={ArrowLeft} />}
              onClick={() => navigate('/')}
            >
              Back to Home
            </Button>
          </HStack>
          
          <Heading
            size="xl"
            bgGradient="linear(to-r, purple.500, blue.500)"
            bgClip="text"
            mb={2}
          >
            Multi-Agent Research Orchestration
          </Heading>
          <Text fontSize="lg" color="gray.600" _dark={{ color: 'gray.400' }}>
            Advanced research using specialized AI agents coordinated through Semantic Kernel
          </Text>
        </Box>

        {/* System Status */}
        <Card bg={bgColor} borderColor={borderColor}>
          <CardHeader>
            <HStack justify="space-between">
              <Heading size="md">System Status</Heading>
              <Badge colorScheme={healthStatus.color} size="lg">
                {healthStatus.status.toUpperCase()}
              </Badge>
            </HStack>
          </CardHeader>
          <CardBody>
            <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }} gap={4}>
              <GridItem>
                <Stat>
                  <StatLabel>Azure OpenAI</StatLabel>
                  <StatNumber>
                    <Icon 
                      as={healthData?.configuration.azure_openai_configured ? CheckCircle : XCircle} 
                      color={healthData?.configuration.azure_openai_configured ? 'green.500' : 'red.500'}
                    />
                  </StatNumber>
                </Stat>
              </GridItem>
              <GridItem>
                <Stat>
                  <StatLabel>Internal Search</StatLabel>
                  <StatNumber>
                    <Icon 
                      as={healthData?.configuration.azure_search_configured ? CheckCircle : XCircle} 
                      color={healthData?.configuration.azure_search_configured ? 'green.500' : 'red.500'}
                    />
                  </StatNumber>
                </Stat>
              </GridItem>
              <GridItem>
                <Stat>
                  <StatLabel>Web Search</StatLabel>
                  <StatNumber>
                    <Icon 
                      as={healthData?.configuration.web_search_configured ? CheckCircle : XCircle} 
                      color={healthData?.configuration.web_search_configured ? 'green.500' : 'red.500'}
                    />
                  </StatNumber>
                </Stat>
              </GridItem>
              <GridItem>
                <Stat>
                  <StatLabel>Active Sessions</StatLabel>
                  <StatNumber>{healthData?.active_sessions_count || 0}</StatNumber>
                </Stat>
              </GridItem>
            </Grid>
          </CardBody>
        </Card>

        {/* Research Input */}
        <Card bg={bgColor} borderColor={borderColor}>
          <CardHeader>
            <HStack justify="space-between">
              <Heading size="md">Research Query</Heading>
              {currentSessionId && (
                <Button size="sm" variant="outline" onClick={handleNewSession}>
                  New Session
                </Button>
              )}
            </HStack>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {currentSessionId && (
                <Alert status="info" borderRadius="md">
                  <AlertIcon />
                  <Box>
                    <AlertTitle>Active Session</AlertTitle>
                    <AlertDescription>
                      Session ID: {currentSessionId.slice(0, 8)}...
                    </AlertDescription>
                  </Box>
                </Alert>
              )}
              
              <Textarea
                placeholder="Enter your research query here... (e.g., 'Analyze the latest developments in AI orchestration technologies and their enterprise applications')"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                minH="120px"
                resize="vertical"
                disabled={isResearching}
              />
              
              <HStack justify="space-between">
                <Text fontSize="sm" color="gray.500">
                  The system will deploy multiple specialized agents for comprehensive research
                </Text>
                <HStack>
                  <Button
                    colorScheme="purple"
                    leftIcon={<Icon as={Users} />}
                    onClick={handleStartResearch}
                    isLoading={isResearching}
                    loadingText="Orchestrating Research..."
                    size="lg"
                    disabled={!query.trim()}
                  >
                    Start Orchestration
                  </Button>
                  <Button 
                    onClick={() => {
                      console.log('Manual refresh triggered');
                      refetchProgress();
                    }} 
                    colorScheme="gray" 
                    size="sm"
                    disabled={!currentSessionId}
                  >
                    Refresh
                  </Button>
                </HStack>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Research Progress */}
        {(isResearching || progress) && (
          <VStack spacing={4}>
            {/* Basic Progress Indicator */}
            {isResearching && !progress && (
              <Card bg={bgColor} borderColor={borderColor}>
                <CardBody>
                  <VStack spacing={4}>
                    <HStack>
                      <Spinner color="purple.500" />
                      <Text fontWeight="medium">Multi-Agent Research in Progress...</Text>
                      {wsConnected && (
                        <Badge colorScheme="green" size="sm">WebSocket Connected</Badge>
                      )}
                    </HStack>
                    <Progress colorScheme="purple" size="lg" isIndeterminate w="100%" />
                    <Text fontSize="sm" color="gray.600" textAlign="center">
                      Specialized agents are researching, analyzing, and synthesizing information
                    </Text>
                  </VStack>
                </CardBody>
              </Card>
            )}
            
            {/* Detailed Progress Display */}
            {progress && (
              <AgentProgressDisplay progress={progress} isExpanded={true} />
            )}
          </VStack>
        )}

        {/* Session Summary */}
        {(sessionSummary || mockSessionSummary) && (
          <Card bg={bgColor} borderColor={borderColor}>
            <CardHeader>
              <Heading size="md">Session Summary</Heading>
            </CardHeader>
            <CardBody>
              <Grid templateColumns={{ base: '1fr', md: 'repeat(3, 1fr)' }} gap={4}>
                <GridItem>
                  <Stat>
                    <StatLabel>Session Status</StatLabel>
                    <StatNumber>
                      <Badge colorScheme={(sessionSummary || mockSessionSummary)?.status === 'active' ? 'green' : 'blue'}>
                        {(sessionSummary || mockSessionSummary)?.status}
                      </Badge>
                    </StatNumber>
                  </Stat>
                </GridItem>
                <GridItem>
                  <Stat>
                    <StatLabel>Agents Used</StatLabel>
                    <StatNumber>{(sessionSummary || mockSessionSummary)?.total_agents?.length || 0}</StatNumber>
                  </Stat>
                </GridItem>
                <GridItem>
                  <Stat>
                    <StatLabel>Session ID</StatLabel>
                    <StatNumber fontSize="sm">{(sessionSummary || mockSessionSummary)?.session_id}</StatNumber>
                  </Stat>
                </GridItem>
              </Grid>
            </CardBody>
          </Card>
        )}

        {/* Research Error */}
        {researchError && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            <Box>
              <AlertTitle>Research Failed</AlertTitle>
              <AlertDescription>
                {researchError.message || 'An error occurred during research orchestration'}
              </AlertDescription>
            </Box>
          </Alert>
        )}

        {/* Research Results */}
        {(researchResult && researchResult.status === 'completed') || (sessionSummary && sessionSummary.result) || (mockSessionSummary && mockSessionSummary.result) ? (
          <Card bg={bgColor} borderColor={borderColor}>
            <CardHeader>
              <HStack justify="space-between">
                <Heading size="md">Research Results</Heading>
                <ExportDropdown
                  taskId={currentSessionId || 'orchestration-research'}
                  reportContent={(researchResult?.result || sessionSummary?.result || mockSessionSummary?.result) || ''}
                  reportTitle={`Orchestration Research - ${currentSessionId?.slice(0, 8) || 'Report'}`}
                  isDisabled={false}
                />
              </HStack>
            </CardHeader>
            <CardBody>
              <Box
                bg="gray.50"
                _dark={{ bg: 'gray.900' }}
                p={6}
                borderRadius="md"
                border="1px"
                borderColor={borderColor}
                maxH="500px"
                overflowY="auto"
              >
                <ReactMarkdown 
                  components={{
                    h1: ({ children }) => <Heading as="h1" size="xl" mb={4}>{children}</Heading>,
                    h2: ({ children }) => <Heading as="h2" size="lg" mb={3}>{children}</Heading>,
                    h3: ({ children }) => <Heading as="h3" size="md" mb={2}>{children}</Heading>,
                    p: ({ children }) => <Text mb={3} lineHeight="tall">{children}</Text>,
                    ul: ({ children }) => <List spacing={1} mb={3}>{children}</List>,
                    ol: ({ children }) => <List as="ol" spacing={1} mb={3}>{children}</List>,
                    li: ({ children }) => <ListItem>{children}</ListItem>,
                    code: ({ children }) => <Code colorScheme="gray" fontSize="sm">{children}</Code>,
                    blockquote: ({ children }) => (
                      <Box 
                        borderLeft="4px solid" 
                        borderColor="gray.300" 
                        pl={4} 
                        py={2} 
                        bg="gray.50" 
                        _dark={{ bg: 'gray.800', borderColor: 'gray.600' }}
                        mb={3}
                      >
                        {children}
                      </Box>
                    ),
                  }}
                >
                  {researchResult?.result || sessionSummary?.result || mockSessionSummary?.result || ''}
                </ReactMarkdown>
              </Box>
            </CardBody>
          </Card>
        ) : null}

        {/* Features Info */}
        <Card bg={bgColor} borderColor={borderColor}>
          <CardHeader>
            <Heading size="md">Orchestration Features</Heading>
          </CardHeader>
          <CardBody>
            <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)' }} gap={6}>
              <VStack align="start" spacing={3}>
                <HStack>
                  <Icon as={Brain} color="purple.500" />
                  <Text fontWeight="medium">Specialized Agents</Text>
                </HStack>
                <Text fontSize="sm" color="gray.600">
                  Lead Researcher, Technical Analysts, Credibility Critics, Report Writers, and more
                </Text>
              </VStack>
              
              <VStack align="start" spacing={3}>
                <HStack>
                  <Icon as={Search} color="blue.500" />
                  <Text fontWeight="medium">Multi-Source Research</Text>
                </HStack>
                <Text fontSize="sm" color="gray.600">
                  Combines internal document search with web research for comprehensive coverage
                </Text>
              </VStack>
              
              <VStack align="start" spacing={3}>
                <HStack>
                  <Icon as={CheckCircle} color="green.500" />
                  <Text fontWeight="medium">Quality Validation</Text>
                </HStack>
                <Text fontSize="sm" color="gray.600">
                  Built-in credibility assessment and reflection critics for reliable results
                </Text>
              </VStack>
              
              <VStack align="start" spacing={3}>
                <HStack>
                  <Icon as={FileText} color="orange.500" />
                  <Text fontWeight="medium">Professional Reports</Text>
                </HStack>
                <Text fontSize="sm" color="gray.600">
                  Enterprise-grade reports with proper citations and structured analysis
                </Text>
              </VStack>
            </Grid>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};
