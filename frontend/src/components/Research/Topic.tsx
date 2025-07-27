import React, { useRef } from 'react';
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
import { Plus, FileText, Loader2 } from 'lucide-react';
import { useDeepResearchContext } from '@/contexts/DeepResearchContext';

const formSchema = z.object({
  topic: z.string().min(1, 'Research topic is required'),
});

type FormData = z.infer<typeof formSchema>;

export const Topic: React.FC = () => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { 
    isThinking, 
    status,
    askQuestions, 
    createNewResearch 
  } = useDeepResearchContext();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (data: FormData) => {
    await askQuestions(data.topic);
  };

  const handleNewResearch = () => {
    createNewResearch();
    reset();
  };

  return (
    <Card bg={cardBg}>
      <CardHeader>
        <HStack justify="space-between">
          <Heading size="lg">1. Research Topics</Heading>
          <Button
            size="sm"
            variant="ghost"
            leftIcon={<Icon as={Plus} />}
            onClick={handleNewResearch}
            title="Start New Research"
          >
            New
          </Button>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          <Box>
            <Text fontWeight="semibold" mb={2}>
              1.1 Research topics
            </Text>
            <form onSubmit={handleSubmit(onSubmit)}>
              <VStack spacing={4} align="stretch">
                <FormControl isInvalid={!!errors.topic}>
                  <Textarea
                    {...register('topic')}
                    placeholder="Any questions you want to know..."
                    rows={4}
                    disabled={isThinking}
                  />
                  <FormErrorMessage>
                    {errors.topic && errors.topic.message}
                  </FormErrorMessage>
                </FormControl>

                <FormControl>
                  <FormLabel fontWeight="semibold">
                    1.2 Local research resources (optional)
                  </FormLabel>
                  <Button
                    size="sm"
                    variant="outline"
                    leftIcon={<Icon as={FileText} />}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Add Resource
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    hidden
                    accept=".txt,.pdf,.doc,.docx"
                  />
                </FormControl>

                <Button
                  type="submit"
                  colorScheme="blue"
                  size="lg"
                  width="full"
                  isLoading={isThinking}
                  loadingText={status || "Thinking..."}
                  disabled={isThinking}
                >
                  {isThinking ? (
                    <>
                      <Icon as={Loader2} className="animate-spin" mr={2} />
                      {status || 'Start Thinking'}
                    </>
                  ) : (
                    'Start Thinking'
                  )}
                </Button>

                {/* Simple loading indicator */}
                {isThinking && (
                  <Box p={4} bg="blue.50" borderRadius="md" textAlign="center">
                    <Text color="blue.600" fontSize="sm">
                      <Icon as={Loader2} className="animate-spin mr-2" />
                      {status || 'Processing...'}
                    </Text>
                  </Box>
                )}
              </VStack>
            </form>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
};
