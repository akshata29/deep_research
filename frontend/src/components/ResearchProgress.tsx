import React from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Progress,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Badge,
  Alert,
  AlertIcon,
  AlertDescription,
  Icon,
  Button,
} from '@chakra-ui/react';
import { CheckCircle, Clock, AlertCircle, Play, RefreshCw } from 'lucide-react';
import { useResearchWithUpdates } from '@/hooks/useApi';

interface ResearchProgressProps {
  taskId: string;
}

export const ResearchProgress: React.FC<ResearchProgressProps> = ({ taskId }) => {
  const research = useResearchWithUpdates(taskId);

  // Debug logging to see what data we're getting
  console.log('ResearchProgress data:', {
    status: research.status,
    progress: research.progress,
    currentStep: research.currentStep,
    isLoading: research.isLoading,
    error: research.error,
    hasReport: !!research.report
  });

  const getStatusColor = (status: string) => {
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return CheckCircle;
      case 'processing':
        return Play;
      case 'failed':
        return AlertCircle;
      default:
        return Clock;
    }
  };

  return (
    <VStack spacing={6} align="stretch">
      {/* Overall Progress */}
      <Card>
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="md">Research Progress</Heading>
            <Button 
              size="sm" 
              variant="outline" 
              leftIcon={<Icon as={RefreshCw} />}
              onClick={() => research.refetch()}
              isLoading={research.isLoading}
            >
              Refresh
            </Button>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4}>
            <Box w="full">
              <HStack justify="space-between" mb={2}>
                <Text fontSize="sm" color="gray.600">
                  Overall Progress
                </Text>
                <Text fontSize="sm" color="gray.600">
                  {research.progress}%
                </Text>
              </HStack>
              <Progress 
                value={research.progress} 
                colorScheme="brand" 
                size="lg"
                borderRadius="md"
              />
            </Box>

            <HStack justify="space-between" w="full">
              <VStack>
                <HStack>
                  <Icon 
                    as={getStatusIcon(research.status || 'pending')} 
                    color={`${getStatusColor(research.status || 'pending')}.500`}
                    boxSize={5}
                  />
                  <Text fontSize="lg" fontWeight="bold" color="blue.500">
                    {research.currentStep}
                  </Text>
                </HStack>
                <Text fontSize="sm" color="gray.600">Current Step</Text>
              </VStack>
              <VStack>
                <Badge colorScheme={getStatusColor(research.status || 'pending')} fontSize="md" p={2}>
                  {research.status || 'pending'}
                </Badge>
                <Text fontSize="sm" color="gray.600">Status</Text>
              </VStack>
            </HStack>
          </VStack>
        </CardBody>
      </Card>

      {/* Status Information */}
      <Card>
        <CardHeader>
          <Heading size="md">Current Status</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={3} align="start">
            <HStack>
              <Text fontWeight="medium" color="gray.700">Task ID:</Text>
              <Text fontSize="sm" fontFamily="mono" color="gray.600">{taskId}</Text>
            </HStack>
            <HStack>
              <Text fontWeight="medium" color="gray.700">Current Step:</Text>
              <Text color="blue.600">{research.currentStep}</Text>
            </HStack>
            <HStack>
              <Text fontWeight="medium" color="gray.700">Progress:</Text>
              <Text color="green.600">{research.progress}% complete</Text>
            </HStack>
            {research.report && (
              <HStack>
                <Text fontWeight="medium" color="gray.700">Report:</Text>
                <Badge colorScheme="green">Available</Badge>
              </HStack>
            )}
          </VStack>
        </CardBody>
      </Card>

      {/* Connection Status - Now using HTTP Polling */}
      {research.isLoading && (
        <Alert status="info">
          <AlertIcon />
          <AlertDescription>
            Fetching latest progress updates...
          </AlertDescription>
        </Alert>
      )}
      
      {research.error && (
        <Alert status="error">
          <AlertIcon />
          <AlertDescription>
            Unable to fetch progress updates. Please refresh the page.
          </AlertDescription>
        </Alert>
      )}

      {/* Polling Status Indicator */}
      <Box p={3} bg="gray.50" borderRadius="md">
        <HStack justify="space-between">
          <VStack align="start" spacing={1}>
            <Text fontSize="sm" color="gray.600">
              Using automatic refresh (every 1 second)
            </Text>
            <Text fontSize="xs" color="gray.500">
              Last update: {new Date().toLocaleTimeString()}
            </Text>
          </VStack>
          <VStack align="end" spacing={1}>
            <HStack>
              <Box w={2} h={2} bg="green.400" borderRadius="full" />
              <Text fontSize="xs" color="gray.500">Active</Text>
            </HStack>
            <Text fontSize="xs" color="gray.400">
              Status: {research.status || 'pending'}
            </Text>
          </VStack>
        </HStack>
      </Box>
    </VStack>
  );
};
