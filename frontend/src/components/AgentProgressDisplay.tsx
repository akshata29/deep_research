import React from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  Progress,
  Collapse,
  Card,
  CardBody,
  Icon,
  Divider,
  useColorModeValue,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Code,
  Heading,
  List,
  ListItem,
} from '@chakra-ui/react';
import { CheckCircle, Clock, AlertCircle, Play, Brain } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { OrchestrationProgress } from '@/types';

interface AgentProgressDisplayProps {
  progress: OrchestrationProgress;
  isExpanded?: boolean;
}

export const AgentProgressDisplay: React.FC<AgentProgressDisplayProps> = ({
  progress,
  isExpanded = true,
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const completedColor = useColorModeValue('green.50', 'green.900');
  const runningColor = useColorModeValue('blue.50', 'blue.900');
  const pendingColor = useColorModeValue('gray.50', 'gray.800');

  const getAgentIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return CheckCircle;
      case 'running':
        return Play;
      case 'failed':
        return AlertCircle;
      default:
        return Clock;
    }
  };

  const getAgentColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'running':
        return 'blue';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getAgentBg = (status: string) => {
    switch (status) {
      case 'completed':
        return completedColor;
      case 'running':
        return runningColor;
      case 'failed':
        return 'red.50';
      default:
        return pendingColor;
    }
  };

  const formatDuration = (timestamp?: string, execution_time_seconds?: number) => {
    if (!timestamp) return 'Not started';
    
    if (execution_time_seconds) {
      const seconds = Math.floor(execution_time_seconds);
      if (seconds < 60) return `${seconds}s`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}m ${remainingSeconds}s`;
    }
    
    // If no execution time, calculate from timestamp to now
    const start = new Date(timestamp);
    const end = new Date();
    const durationMs = end.getTime() - start.getTime();
    const seconds = Math.floor(durationMs / 1000);
    
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const completedAgents = progress.completed_agents || 0;
  const totalAgents = progress.total_agents || 0;
  const overallProgress = totalAgents > 0 ? (completedAgents / totalAgents) * 100 : 0;

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {/* Overall Progress */}
          <Box>
            <HStack justify="space-between" mb={2}>
              <HStack>
                <Icon as={Brain} color="purple.500" />
                <Text fontWeight="medium">Agent Orchestration Progress</Text>
              </HStack>
              <Badge colorScheme={progress.status === 'completed' ? 'green' : progress.status === 'in_progress' ? 'blue' : 'gray'}>
                {progress.status}
              </Badge>
            </HStack>
            
            <Progress 
              value={overallProgress} 
              colorScheme="purple" 
              size="lg" 
              mb={2}
              isIndeterminate={progress.status === 'in_progress' && overallProgress === 0}
            />
            
            <HStack justify="space-between" fontSize="sm" color="gray.600">
              <Text>{completedAgents} of {totalAgents} agents completed</Text>
              <Text>
                Duration: {formatDuration(progress.created_at)}
              </Text>
            </HStack>
          </Box>

          <Divider />

          {/* Agent Executions */}
          <Collapse in={isExpanded}>
            <VStack spacing={3} align="stretch">
              <Text fontWeight="medium" fontSize="sm" color="gray.600">
                Agent Execution Details
              </Text>
              
              {progress.agent_executions && progress.agent_executions.length > 0 ? (
                <Accordion allowToggle allowMultiple>
                  {progress.agent_executions.map((agent, index) => (
                    <AccordionItem key={index} border="1px" borderColor={borderColor} borderRadius="md" mb={2}>
                      <AccordionButton 
                        bg={getAgentBg(agent.status)}
                        _hover={{ bg: getAgentBg(agent.status) }}
                        borderRadius="md"
                      >
                        <Box flex="1" textAlign="left">
                          <HStack spacing={3}>
                            <Icon 
                              as={getAgentIcon(agent.status)} 
                              color={`${getAgentColor(agent.status)}.500`}
                            />
                            <VStack align="start" spacing={1} flex="1">
                              <HStack justify="space-between" w="100%">
                                <Text fontWeight="medium" fontSize="sm">
                                  {agent.agent_name}
                                </Text>
                                <Badge 
                                  colorScheme={getAgentColor(agent.status)} 
                                  size="sm"
                                >
                                  {agent.status}
                                </Badge>
                              </HStack>
                              <Text fontSize="xs" color="gray.600">
                                {formatDuration(agent.timestamp, agent.execution_time_seconds)}
                              </Text>
                            </VStack>
                          </HStack>
                        </Box>
                        <AccordionIcon />
                      </AccordionButton>
                      
                      <AccordionPanel pb={4}>
                        <VStack align="stretch" spacing={3}>
                          {agent.input && (
                            <Box>
                              <Text fontSize="sm" fontWeight="medium" mb={2}>Input:</Text>
                              <Box 
                                bg="blue.50" 
                                _dark={{ bg: 'blue.900' }} 
                                p={3} 
                                borderRadius="md" 
                                border="1px"
                                borderColor="blue.200"
                                _dark={{ borderColor: 'blue.700' }}
                                fontSize="sm"
                                maxH="200px"
                                overflowY="auto"
                              >
                                <ReactMarkdown
                                  components={{
                                    h1: ({ children }) => <Heading as="h1" size="sm" mb={2}>{children}</Heading>,
                                    h2: ({ children }) => <Heading as="h2" size="sm" mb={2}>{children}</Heading>,
                                    h3: ({ children }) => <Heading as="h3" size="xs" mb={1}>{children}</Heading>,
                                    p: ({ children }) => <Text mb={2} fontSize="sm">{children}</Text>,
                                    ul: ({ children }) => <List spacing={1} mb={2} fontSize="sm">{children}</List>,
                                    ol: ({ children }) => <List as="ol" spacing={1} mb={2} fontSize="sm">{children}</List>,
                                    li: ({ children }) => <ListItem fontSize="sm">{children}</ListItem>,
                                    code: ({ children }) => <Code colorScheme="blue" fontSize="xs">{children}</Code>,
                                    strong: ({ children }) => <Text as="strong" fontWeight="bold">{children}</Text>,
                                    em: ({ children }) => <Text as="em" fontStyle="italic">{children}</Text>,
                                  }}
                                >
                                  {typeof agent.input === 'string' ? agent.input : JSON.stringify(agent.input, null, 2)}
                                </ReactMarkdown>
                              </Box>
                            </Box>
                          )}
                          
                          {agent.output && (
                            <Box>
                              <Text fontSize="sm" fontWeight="medium" mb={2}>Output:</Text>
                              <Box 
                                bg="green.50" 
                                _dark={{ bg: 'green.900' }} 
                                p={3} 
                                borderRadius="md" 
                                border="1px"
                                borderColor="green.200"
                                _dark={{ borderColor: 'green.700' }}
                                fontSize="sm"
                                maxH="300px"
                                overflowY="auto"
                              >
                                <ReactMarkdown
                                  components={{
                                    h1: ({ children }) => <Heading as="h1" size="sm" mb={2}>{children}</Heading>,
                                    h2: ({ children }) => <Heading as="h2" size="sm" mb={2}>{children}</Heading>,
                                    h3: ({ children }) => <Heading as="h3" size="xs" mb={1}>{children}</Heading>,
                                    p: ({ children }) => <Text mb={2} fontSize="sm">{children}</Text>,
                                    ul: ({ children }) => <List spacing={1} mb={2} fontSize="sm">{children}</List>,
                                    ol: ({ children }) => <List as="ol" spacing={1} mb={2} fontSize="sm">{children}</List>,
                                    li: ({ children }) => <ListItem fontSize="sm">{children}</ListItem>,
                                    code: ({ children }) => <Code colorScheme="green" fontSize="xs">{children}</Code>,
                                    strong: ({ children }) => <Text as="strong" fontWeight="bold">{children}</Text>,
                                    em: ({ children }) => <Text as="em" fontStyle="italic">{children}</Text>,
                                    blockquote: ({ children }) => (
                                      <Box 
                                        borderLeft="3px solid" 
                                        borderColor="green.300" 
                                        _dark={{ borderColor: 'green.600' }}
                                        pl={3} 
                                        py={1} 
                                        bg="green.100" 
                                        _dark={{ bg: 'green.800' }}
                                        mb={2}
                                        fontSize="sm"
                                      >
                                        {children}
                                      </Box>
                                    ),
                                  }}
                                >
                                  {typeof agent.output === 'string' ? agent.output : JSON.stringify(agent.output, null, 2)}
                                </ReactMarkdown>
                              </Box>
                            </Box>
                          )}
                          
                          {agent.metadata?.error && (
                            <Box>
                              <Text fontSize="sm" fontWeight="medium" mb={1} color="red.500">Error:</Text>
                              <Code fontSize="xs" p={2} borderRadius="md" display="block" colorScheme="red">
                                {agent.metadata.error}
                              </Code>
                            </Box>
                          )}
                          
                          <HStack justify="space-between" fontSize="xs" color="gray.500">
                            <Text>Started: {agent.timestamp ? new Date(agent.timestamp).toLocaleTimeString() : 'N/A'}</Text>
                            <Text>
                              {agent.status === 'completed' ? `Duration: ${formatDuration(agent.timestamp, agent.execution_time_seconds)}` : 'Running...'}
                            </Text>
                          </HStack>
                        </VStack>
                      </AccordionPanel>
                    </AccordionItem>
                  ))}
                </Accordion>
              ) : (
                <Box textAlign="center" py={4} color="gray.500">
                  <Icon as={Clock} mb={2} />
                  <Text fontSize="sm">No agent executions yet</Text>
                </Box>
              )}
            </VStack>
          </Collapse>
        </VStack>
      </CardBody>
    </Card>
  );
};
