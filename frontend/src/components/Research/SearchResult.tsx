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
  FormErrorMessage,
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
import { Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { useDeepResearchContext } from '@/contexts/DeepResearchContext';
import ReactMarkdown from 'react-markdown';

const formSchema = z.object({
  suggestion: z.string().optional(),
});

type FormData = z.infer<typeof formSchema>;

export const SearchResult: React.FC = () => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const { 
    reportPlan,
    searchTasks,
    isResearching,
    status,
    currentTaskId,
    phase,
    runSearchTasks
  } = useDeepResearchContext();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (data: FormData) => {
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
    return (
      <Card bg={cardBg}>
        <CardBody>
          <Text color="gray.500">Waiting for research plan...</Text>
        </CardBody>
      </Card>
    );
  }

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
              <ReactMarkdown>{reportPlan}</ReactMarkdown>
            </Box>
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
              <Heading size="sm" mb={3}>Search Tasks</Heading>
              <Accordion allowToggle>
                {searchTasks.map((task, index) => (
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
                        <ReactMarkdown>{task.learning}</ReactMarkdown>
                      )}
                    </AccordionPanel>
                  </AccordionItem>
                ))}
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
        </VStack>
      </CardBody>
    </Card>
  );
};
