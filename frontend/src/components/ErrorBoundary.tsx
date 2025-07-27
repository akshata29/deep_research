import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Button,
  Heading,
  Text,
  VStack,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Code,
  Collapse,
  useDisclosure,
} from '@chakra-ui/react';
import { RefreshCw, AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

const ErrorDisplay = ({ error, errorInfo, onRetry }: {
  error?: Error;
  errorInfo?: ErrorInfo;
  onRetry: () => void;
}) => {
  const { isOpen, onToggle } = useDisclosure();

  return (
    <Box
      minH="50vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
      p={8}
    >
      <VStack spacing={6} maxW="2xl" textAlign="center">
        <Box color="red.500">
          <AlertTriangle size={48} />
        </Box>
        
        <VStack spacing={2}>
          <Heading size="lg" color="red.600">
            Something went wrong
          </Heading>
          <Text color="gray.600">
            We encountered an unexpected error. Please try refreshing the page.
          </Text>
        </VStack>

        <Button
          leftIcon={<RefreshCw size={16} />}
          colorScheme="red"
          onClick={onRetry}
        >
          Retry
        </Button>

        {(error || errorInfo) && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            <Box flex="1">
              <AlertTitle fontSize="sm">Error Details</AlertTitle>
              <AlertDescription fontSize="sm">
                <Button
                  size="xs"
                  variant="link"
                  onClick={onToggle}
                  colorScheme="red"
                >
                  {isOpen ? 'Hide' : 'Show'} technical details
                </Button>
              </AlertDescription>
            </Box>
          </Alert>
        )}

        <Collapse in={isOpen}>
          <VStack spacing={4} align="stretch" w="full">
            {error && (
              <Box>
                <Text fontSize="sm" fontWeight="semibold" mb={2}>
                  Error Message:
                </Text>
                <Code p={3} borderRadius="md" fontSize="sm" w="full">
                  {error.message}
                </Code>
              </Box>
            )}
            
            {error?.stack && (
              <Box>
                <Text fontSize="sm" fontWeight="semibold" mb={2}>
                  Stack Trace:
                </Text>
                <Code p={3} borderRadius="md" fontSize="xs" w="full" maxH="200px" overflow="auto">
                  {error.stack}
                </Code>
              </Box>
            )}
            
            {errorInfo?.componentStack && (
              <Box>
                <Text fontSize="sm" fontWeight="semibold" mb={2}>
                  Component Stack:
                </Text>
                <Code p={3} borderRadius="md" fontSize="xs" w="full" maxH="200px" overflow="auto">
                  {errorInfo.componentStack}
                </Code>
              </Box>
            )}
          </VStack>
        </Collapse>
      </VStack>
    </Box>
  );
};

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // Log to error reporting service
    // logErrorToService(error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ErrorDisplay
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onRetry={this.handleRetry}
        />
      );
    }

    return this.props.children;
  }
}

// Hook version for functional components
export const useErrorHandler = () => {
  const handleError = (error: Error, errorInfo?: ErrorInfo) => {
    console.error('Error caught by useErrorHandler:', error, errorInfo);
    // Log to error reporting service
    // logErrorToService(error, errorInfo);
  };

  return handleError;
};
