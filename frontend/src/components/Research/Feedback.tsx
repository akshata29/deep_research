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
} from '@chakra-ui/react';
import { Loader2 } from 'lucide-react';
import { useDeepResearchContext } from '@/contexts/DeepResearchContext';
import ReactMarkdown from 'react-markdown';

const formSchema = z.object({
  feedback: z.string().min(1, 'Feedback is required'),
});

type FormData = z.infer<typeof formSchema>;

export const Feedback: React.FC = () => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const { 
    questions, 
    feedback, 
    isThinking, 
    status, 
    phase,
    writeReportPlan
  } = useDeepResearchContext();

  console.log('=== FEEDBACK COMPONENT RENDER ===');
  console.log('Questions:', questions);
  console.log('Phase:', phase);
  console.log('IsThinking:', isThinking);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      feedback: feedback,
    },
  });

  const onSubmit = async (data: FormData) => {
    await writeReportPlan(data.feedback);
  };

  if (!questions) {
    return (
      <Card bg={cardBg}>
        <CardBody>
          <Text color="gray.500">Waiting for research topic...</Text>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card bg={cardBg}>
      <CardHeader>
        <Heading size="lg">2. Ask Question</Heading>
      </CardHeader>
      <CardBody>
        <VStack spacing={6} align="stretch">
          {/* Display Questions */}
          <Box>
            <Heading size="sm" mb={3}>Questions</Heading>
            <Box
              p={4}
              bg={useColorModeValue('gray.50', 'gray.700')}
              borderRadius="md"
              borderLeft="4px solid"
              borderColor="blue.500"
            >
              <ReactMarkdown>{questions}</ReactMarkdown>
            </Box>
          </Box>

          {/* Feedback Form */}
          <form onSubmit={handleSubmit(onSubmit)}>
            <VStack spacing={4} align="stretch">
              <FormControl isInvalid={!!errors.feedback}>
                <FormLabel fontWeight="semibold">
                  Your Feedback (optional)
                </FormLabel>
                <Textarea
                  {...register('feedback')}
                  placeholder="Provide any additional context, specific focus areas, or clarifications..."
                  rows={4}
                  disabled={isThinking}
                />
                <FormErrorMessage>
                  {errors.feedback && errors.feedback.message}
                </FormErrorMessage>
              </FormControl>

              <Button
                type="submit"
                colorScheme="blue"
                size="lg"
                width="full"
                isLoading={isThinking}
                loadingText={status}
                disabled={isThinking}
              >
                {isThinking ? (
                  <>
                    <Icon as={Loader2} className="animate-spin" mr={2} />
                    {status}
                  </>
                ) : (
                  'Write Report Plan'
                )}
              </Button>
            </VStack>
          </form>
        </VStack>
      </CardBody>
    </Card>
  );
};
