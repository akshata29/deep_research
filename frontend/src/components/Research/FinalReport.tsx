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
  UnorderedList,
  OrderedList,
  ListItem,
  Code
} from '@chakra-ui/react';
import { Loader2, FileText } from 'lucide-react';
import { useDeepResearchContext } from '@/contexts/DeepResearchContext';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { parseFinalReportToMarkdown } from '../../utils/jsonContentParser';
import { ExportDropdown } from '../ExportDropdown';

const formSchema = z.object({
  requirement: z.string().optional(),
});

type FormData = z.infer<typeof formSchema>;

export const FinalReport: React.FC = () => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const reportBg = useColorModeValue('gray.50', 'gray.700');
  const { 
    searchTasks,
    finalReport,
    currentTaskId,
    isWriting,
    status,
    writeFinalReport
  } = useDeepResearchContext();

  const {
    register,
    handleSubmit,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (data: FormData) => {
    await writeFinalReport(data.requirement);
  };

  const taskFinished = searchTasks.length > 0 && searchTasks.every(task => task.state === 'completed');

  if (searchTasks.length === 0) {
    return (
      <Card bg={cardBg}>
        <CardBody>
          <Text color="gray.500">Waiting for data to be collected...</Text>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card bg={cardBg}>
      <CardHeader>
        <Heading size="lg">4. Final Report</Heading>
      </CardHeader>
      <CardBody>
        <VStack spacing={6} align="stretch">
          {/* Final Report Display */}
          {finalReport && (
            <Box>
              <HStack justify="space-between" mb={4}>
                <Heading size="sm">Research Report</Heading>
                <ExportDropdown 
                  taskId={currentTaskId || 'temp-task-id'} 
                  reportContent={parseFinalReportToMarkdown(finalReport)}
                  reportTitle="research-report"
                  isDisabled={!finalReport}
                />
              </HStack>
              <Box
                p={6}
                bg={reportBg}
                borderRadius="md"
                maxH="500px"
                overflowY="auto"
              >
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    table: ({ children }) => (
                      <Box overflowX="auto" mb={4}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                          {children}
                        </table>
                      </Box>
                    ),
                    th: ({ children }) => (
                      <th style={{ 
                        border: '1px solid #e2e8f0', 
                        padding: '8px', 
                        backgroundColor: '#f7fafc',
                        fontWeight: '600',
                        textAlign: 'left'
                      }}>
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td style={{ 
                        border: '1px solid #e2e8f0', 
                        padding: '8px'
                      }}>
                        {children}
                      </td>
                    ),
                    h1: ({ children }) => (
                      <Heading as="h1" size="xl" color="blue.600" mt={6} mb={4}>
                        {children}
                      </Heading>
                    ),
                    h2: ({ children }) => (
                      <Heading as="h2" size="lg" color="blue.500" mt={5} mb={3}>
                        {children}
                      </Heading>
                    ),
                    h3: ({ children }) => (
                      <Heading as="h3" size="md" color="gray.700" mt={4} mb={2}>
                        {children}
                      </Heading>
                    ),
                    p: ({ children }) => (
                      <Text mb={3} lineHeight="1.7">
                        {children}
                      </Text>
                    ),
                    ul: ({ children }) => (
                      <UnorderedList mb={4} pl={6}>
                        {children}
                      </UnorderedList>
                    ),
                    ol: ({ children }) => (
                      <OrderedList mb={4} pl={6}>
                        {children}
                      </OrderedList>
                    ),
                    li: ({ children }) => (
                      <ListItem mb={1}>
                        {children}
                      </ListItem>
                    ),
                    strong: ({ children }) => (
                      <Text as="strong" fontWeight="semibold" color="gray.800">
                        {children}
                      </Text>
                    ),
                    blockquote: ({ children }) => (
                      <Box
                        borderLeft="4px solid"
                        borderColor="blue.200"
                        pl={4}
                        ml={4}
                        fontStyle="italic"
                        mb={4}
                      >
                        {children}
                      </Box>
                    ),
                    code: ({ children, className }) => {
                      const isBlock = className?.includes('language-');
                      if (isBlock) {
                        return (
                          <Box
                            as="pre"
                            bg="gray.100"
                            p={4}
                            borderRadius="md"
                            overflowX="auto"
                            mb={4}
                          >
                            <code>{children}</code>
                          </Box>
                        );
                      }
                      return (
                        <Code bg="gray.100" px={1} borderRadius="sm" fontSize="sm">
                          {children}
                        </Code>
                      );
                    }
                  }}
                >
                  {parseFinalReportToMarkdown(finalReport)}
                </ReactMarkdown>
              </Box>
            </Box>
          )}

          {/* Write Report Form */}
          {taskFinished && !finalReport && (
            <form onSubmit={handleSubmit(onSubmit)}>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel fontWeight="semibold">
                    Writing Requirements (optional)
                  </FormLabel>
                  <Textarea
                    {...register('requirement')}
                    placeholder="Specific format, style, or content requirements for the final report..."
                    rows={3}
                    disabled={isWriting}
                  />
                </FormControl>

                <Button
                  type="submit"
                  colorScheme="blue"
                  size="lg"
                  width="full"
                  isLoading={isWriting}
                  loadingText={status}
                  disabled={isWriting}
                >
                  {isWriting ? (
                    <>
                      <Icon as={Loader2} className="animate-spin" mr={2} />
                      {status}
                    </>
                  ) : finalReport ? (
                    'Rewrite Report'
                  ) : (
                    'Write Report'
                  )}
                </Button>
              </VStack>
            </form>
          )}

          {/* Regenerate Report Button */}
          {finalReport && (
            <form onSubmit={handleSubmit(onSubmit)}>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel fontWeight="semibold">
                    Regeneration Requirements (optional)
                  </FormLabel>
                  <Textarea
                    {...register('requirement')}
                    placeholder="How would you like to modify or improve the report..."
                    rows={3}
                    disabled={isWriting}
                  />
                </FormControl>

                <Button
                  type="submit"
                  colorScheme="orange"
                  size="lg"
                  width="full"
                  isLoading={isWriting}
                  loadingText={status}
                  disabled={isWriting}
                >
                  {isWriting ? (
                    <>
                      <Icon as={Loader2} className="animate-spin" mr={2} />
                      {status}
                    </>
                  ) : (
                    'Regenerate Report'
                  )}
                </Button>
              </VStack>
            </form>
          )}

          {/* Empty State */}
          {!taskFinished && (
            <Box textAlign="center" py={8}>
              <Icon as={FileText} boxSize={12} color="gray.400" mb={4} />
              <Text color="gray.500">
                Complete all research tasks to generate the final report
              </Text>
            </Box>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};
