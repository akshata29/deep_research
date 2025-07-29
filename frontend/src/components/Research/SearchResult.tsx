import React from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Card,
  CardBody,
  CardHeader,
  Button,
  Textarea,
  FormControl,
  FormLabel,
  Icon,
  useColorModeValue,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Badge,
  Progress,
} from '@chakra-ui/react';
import { Loader2, CheckCircle, AlertCircle, Clock, Search } from 'lucide-react';
import { useDeepResearchContext } from '@/contexts/DeepResearchContext';
import { useLocalSettings } from '@/hooks/useApi';
import ReactMarkdown from 'react-markdown';
import { parsePlanToMarkdown, parseFindingsToMarkdown } from '@/utils/jsonContentParser';

const formSchema = z.object({
  suggestion: z.string().optional(),
});

type FormData = z.infer<typeof formSchema>;

export const SearchResult: React.FC = () => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const { data: settings } = useLocalSettings();
  const { 
    reportPlan,
    searchTasks,
    isResearching,
    status,
    runSearchTasks
  } = useDeepResearchContext();

  // Debug logs to check what data is actually being passed
  console.log('SearchResult component render:');
  console.log('- reportPlan:', reportPlan);
  console.log('- searchTasks:', searchTasks);
  console.log('- searchTasks.length:', searchTasks.length);
  console.log('- isResearching:', isResearching);

  const {
    register,
    handleSubmit,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async () => {
    await runSearchTasks();
  };

  const getTaskStatusIcon = (taskState: string) => {
    switch (taskState) {
      case 'completed':
        return <Icon as={CheckCircle} color="green.500" />;
      case 'processing':
        return <Icon as={Loader2} className="animate-spin" color="blue.500" />;
      case 'failed':
        return <Icon as={AlertCircle} color="red.500" />;
      default:
        return <Icon as={Clock} color="gray.500" />;
    }
  };

  const getTaskStatusColor = (taskState: string) => {
    switch (taskState) {
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

  if (!reportPlan) {
    console.log('SearchResult: NO reportPlan found, showing waiting message');
    return (
      <Card bg={cardBg}>
        <CardBody>
          <Text color="gray.500">Waiting for research plan...</Text>
        </CardBody>
      </Card>
    );
  }

  console.log('SearchResult: reportPlan exists, rendering component');
  console.log('SearchResult: About to parse reportPlan with parsePlanToMarkdown:', reportPlan);
  const parsedPlan = parsePlanToMarkdown(reportPlan);
  console.log('SearchResult: Parsed plan result:', parsedPlan);

  return (
    <Card bg={cardBg}>
      <CardHeader>
        <Heading size="lg">3. Information Collection</Heading>
      </CardHeader>
      <CardBody>
        <VStack spacing={6} align="stretch">
          {/* Research Plan Display */}
          <Box>
            <Heading size="sm" mb={3}>Research Plan</Heading>
            <Box
              p={4}
              bg={useColorModeValue('gray.50', 'gray.700')}
              borderRadius="md"
              borderLeft="4px solid"
              borderColor="green.500"
            >
              <ReactMarkdown>{parsedPlan}</ReactMarkdown>
            </Box>
          </Box>

          {/* Search Method Indicator */}
          <Box>
            <HStack spacing={3} align="center">
              <Icon as={Search} color="blue.500" />
              <Text fontSize="sm" fontWeight="medium">
                Search Method: 
              </Text>
              <Badge 
                colorScheme={settings?.searchMethod === 'tavily' ? 'purple' : 'blue'}
                variant="subtle"
              >
                {settings?.searchMethod === 'tavily' ? 'Tavily Search API' : 'Bing Grounding'}
              </Badge>
            </HStack>
            <Text fontSize="xs" color="gray.600" mt={1} ml={8}>
              {settings?.searchMethod === 'tavily' 
                ? 'Using direct web search API for comprehensive results'
                : 'Using AI with real-time search grounding capabilities'
              }
            </Text>
          </Box>

          {/* Progress Indicator */}
          {isResearching && (
            <Box>
              <HStack justify="space-between" mb={2}>
                <Text fontWeight="semibold">Research Progress</Text>
                <Loader2 className="animate-spin" size={16} />
              </HStack>
              <Progress isIndeterminate colorScheme="blue" size="sm" mb={2} />
              <Text fontSize="sm" color="gray.600">Executing research tasks...</Text>
            </Box>
          )}

          {/* Search Tasks */}
          {searchTasks.length > 0 && (
            <Box>
              <HStack justify="space-between" mb={3}>
                <Heading size="sm">Search Tasks</Heading>
                {searchTasks.every(task => task.state === 'completed') && (
                  <Badge colorScheme="green" variant="subtle">
                    All tasks completed
                  </Badge>
                )}
              </HStack>
              <Accordion allowToggle>
                {searchTasks.map((task, index) => {
                  console.log(`SearchResult: Rendering search task ${index}:`, task);
                  return (
                  <AccordionItem key={index}>
                    <AccordionButton>
                      <HStack flex="1" textAlign="left">
                        {getTaskStatusIcon(task.state)}
                        <Text>{task.query}</Text>
                        <Badge colorScheme={getTaskStatusColor(task.state)} ml="auto">
                          {task.state}
                        </Badge>
                      </HStack>
                      <AccordionIcon />
                    </AccordionButton>
                    <AccordionPanel pb={4}>
                      <Box
                        p={4}
                        bg={useColorModeValue('blue.50', 'blue.900')}
                        borderRadius="md"
                        mb={4}
                      >
                        <Text fontSize="sm" fontStyle="italic">
                          {task.researchGoal}
                        </Text>
                      </Box>
                      {task.learning && (
                        <Box>
                          <Text fontWeight="semibold" mb={2}>Research Findings:</Text>
                          <ReactMarkdown>{parseFindingsToMarkdown(task.learning)}</ReactMarkdown>
                        </Box>
                      )}
                      {!task.learning && (
                        <Text color="gray.500" fontSize="sm">No research findings available</Text>
                      )}
                    </AccordionPanel>
                  </AccordionItem>
                )})}
              </Accordion>
            </Box>
          )}

          {/* Start Research Button */}
          {searchTasks.length === 0 && (
            <form onSubmit={handleSubmit(onSubmit)}>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel fontWeight="semibold">
                    Research Suggestions (optional)
                  </FormLabel>
                  <Textarea
                    {...register('suggestion')}
                    placeholder="Any specific suggestions for the research process..."
                    rows={3}
                    disabled={isResearching}
                  />
                </FormControl>

                <Button
                  type="submit"
                  colorScheme="blue"
                  size="lg"
                  width="full"
                  isLoading={isResearching}
                  loadingText={status}
                  disabled={isResearching}
                >
                  {isResearching ? (
                    <>
                      <Icon as={Loader2} className="animate-spin" mr={2} />
                      {status}
                    </>
                  ) : (
                    'Start Research'
                  )}
                </Button>
              </VStack>
            </form>
          )}

          {/* Resubmit Research Button - Show when tasks are completed */}
          {searchTasks.length > 0 && searchTasks.every(task => task.state === 'completed') && (
            <form onSubmit={handleSubmit(onSubmit)}>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel fontWeight="semibold">
                    Research Refinement (optional)
                  </FormLabel>
                  <Textarea
                    {...register('suggestion')}
                    placeholder="Any changes or refinements for the research process..."
                    rows={3}
                    disabled={isResearching}
                  />
                </FormControl>

                <Button
                  type="submit"
                  colorScheme="orange"
                  size="lg"
                  width="full"
                  isLoading={isResearching}
                  loadingText={status}
                  disabled={isResearching}
                >
                  {isResearching ? (
                    <>
                      <Icon as={Loader2} className="animate-spin" mr={2} />
                      {status}
                    </>
                  ) : (
                    'Resubmit Research'
                  )}
                </Button>
              </VStack>
            </form>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};
