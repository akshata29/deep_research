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
} from '@chakra-ui/react';
import { Loader2, Download, FileText } from 'lucide-react';
import { useDeepResearchContext } from '@/contexts/DeepResearchContext';
import ReactMarkdown from 'react-markdown';

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

  const handleExport = () => {
    if (!finalReport) return;
    
    const blob = new Blob([finalReport], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'research-report.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
                <HStack>
                  <Button
                    size="sm"
                    variant="outline"
                    leftIcon={<Icon as={Download} />}
                    onClick={handleExport}
                  >
                    Export
                  </Button>
                </HStack>
              </HStack>
              <Box
                p={6}
                bg={reportBg}
                borderRadius="md"
                maxH="500px"
                overflowY="auto"
              >
                <ReactMarkdown>{finalReport}</ReactMarkdown>
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
