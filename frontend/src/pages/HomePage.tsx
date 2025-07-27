import React from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  VStack,
  HStack,
  Grid,
  GridItem,
  Card,
  CardBody,
  Icon,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  useColorModeValue,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { Brain, FileText, Zap, Users } from 'lucide-react';
import { useHealth, useResearchTasks, useExports } from '@/hooks/useApi';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  const { data: health } = useHealth();
  const { data: tasks } = useResearchTasks();
  const { data: exports } = useExports();

  const stats = [
    {
      label: 'Active Research Tasks',
      value: tasks?.tasks?.filter(t => t.status === 'processing').length || 0,
      helpText: 'Currently running',
      icon: Brain,
    },
    {
      label: 'Completed Reports',
      value: tasks?.tasks?.filter(t => t.status === 'completed').length || 0,
      helpText: 'This month',
      icon: FileText,
    },
    {
      label: 'Total Exports',
      value: exports?.total_count || 0,
      helpText: 'All time',
      icon: FileText,
    },
    {
      label: 'System Health',
      value: health?.status === 'healthy' ? '100%' : '⚠️',
      helpText: health?.status || 'Unknown',
      icon: Zap,
    },
  ];

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Hero Section */}
        <Box textAlign="center" py={8}>
          <Heading
            size="2xl"
            bgGradient="linear(to-r, brand.500, azure.500)"
            bgClip="text"
            mb={4}
          >
            Deep Research Assistant
          </Heading>
          <Text fontSize="xl" color="gray.600" _dark={{ color: 'gray.400' }} mb={8}>
            AI-powered research with multi-LLM orchestration and real-time web grounding
          </Text>
          <HStack spacing={4} justify="center">
            <Button
              size="lg"
              colorScheme="brand"
              onClick={() => navigate('/research')}
              leftIcon={<Icon as={Brain} />}
            >
              Start Research
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/exports')}
              leftIcon={<Icon as={FileText} />}
            >
              View Exports
            </Button>
          </HStack>
        </Box>

        {/* Stats Grid */}
        <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }} gap={6}>
          {stats.map((stat, index) => (
            <GridItem key={index}>
              <Card bg={bgColor} borderColor={borderColor}>
                <CardBody>
                  <Stat>
                    <HStack justify="space-between" align="start">
                      <Box>
                        <StatLabel color="gray.600" _dark={{ color: 'gray.400' }}>
                          {stat.label}
                        </StatLabel>
                        <StatNumber fontSize="2xl" fontWeight="bold">
                          {stat.value}
                        </StatNumber>
                        <StatHelpText color="gray.500">
                          {stat.helpText}
                        </StatHelpText>
                      </Box>
                      <Icon as={stat.icon} boxSize={8} color="brand.500" />
                    </HStack>
                  </Stat>
                </CardBody>
              </Card>
            </GridItem>
          ))}
        </Grid>

        {/* Features Section */}
        <Grid templateColumns={{ base: '1fr', lg: 'repeat(3, 1fr)' }} gap={6} mt={8}>
          <Card bg={bgColor} borderColor={borderColor}>
            <CardBody p={6}>
              <VStack align="start" spacing={4}>
                <Icon as={Brain} boxSize={10} color="brand.500" />
                <Heading size="md">Multi-LLM Orchestration</Heading>
                <Text color="gray.600" _dark={{ color: 'gray.400' }}>
                  Leverage multiple AI models including GPT-4, Deepseek, Grok, and Mistral 
                  for comprehensive research analysis.
                </Text>
              </VStack>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderColor={borderColor}>
            <CardBody p={6}>
              <VStack align="start" spacing={4}>
                <Icon as={Zap} boxSize={10} color="azure.500" />
                <Heading size="md">Real-time Web Grounding</Heading>
                <Text color="gray.600" _dark={{ color: 'gray.400' }}>
                  Access current information through Bing Search API integration 
                  for up-to-date research insights.
                </Text>
              </VStack>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderColor={borderColor}>
            <CardBody p={6}>
              <VStack align="start" spacing={4}>
                <Icon as={FileText} boxSize={10} color="semantic.success" />
                <Heading size="md">Multiple Export Formats</Heading>
                <Text color="gray.600" _dark={{ color: 'gray.400' }}>
                  Export research reports as Markdown, PDF, or PowerPoint 
                  presentations with professional formatting.
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Card bg={bgColor} borderColor={borderColor} mt={8}>
          <CardBody p={6}>
            <VStack spacing={4}>
              <Heading size="md">Quick Actions</Heading>
              <HStack spacing={4} wrap="wrap" justify="center">
                <Button
                  variant="outline"
                  onClick={() => navigate('/research')}
                  leftIcon={<Icon as={Brain} />}
                >
                  New Research
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate('/research')}
                  leftIcon={<Icon as={FileText} />}
                >
                  Continue Previous
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate('/exports')}
                  leftIcon={<Icon as={FileText} />}
                >
                  Manage Exports
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate('/settings')}
                  leftIcon={<Icon as={Users} />}
                >
                  Settings
                </Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};
