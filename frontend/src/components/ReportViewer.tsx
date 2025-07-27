import React from 'react';
import ReactMarkdown from 'react-markdown';
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
  Badge,
  Code,
  List,
  ListItem,
  Icon,
  useColorModeValue,
} from '@chakra-ui/react';
import { Download } from 'lucide-react';
import { ResearchReport } from '@/types';

interface ReportViewerProps {
  report: ResearchReport;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({ report }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const codeBg = useColorModeValue('gray.50', 'gray.900');

  // Custom markdown component with Chakra UI styling
  const MarkdownContent = ({ content }: { content: string }) => {
    return (
      <Box className="markdown-content">
        <ReactMarkdown
          components={{
            h1: ({ children }) => <Heading as="h1" size="xl" mb={4} color="gray.800">{children}</Heading>,
            h2: ({ children }) => <Heading as="h2" size="lg" mb={3} color="gray.700">{children}</Heading>,
            h3: ({ children }) => <Heading as="h3" size="md" mb={2} color="gray.600">{children}</Heading>,
            p: ({ children }) => <Text mb={3} lineHeight="tall" color={useColorModeValue('gray.700', 'gray.300')}>{children}</Text>,
            ul: ({ children }) => <List spacing={1} mb={3}>{children}</List>,
            ol: ({ children }) => <List as="ol" spacing={1} mb={3}>{children}</List>,
            li: ({ children }) => <ListItem>{children}</ListItem>,
            strong: ({ children }) => <Text as="strong" fontWeight="bold" color={useColorModeValue('gray.800', 'gray.200')}>{children}</Text>,
            em: ({ children }) => <Text as="em" fontStyle="italic">{children}</Text>,
            code: ({ children, className }) => {
              const isInline = !className;
              if (isInline) {
                return <Code colorScheme="gray" fontSize="sm">{children}</Code>;
              }
              return (
                <Box bg={codeBg} p={3} borderRadius="md" mb={3} overflow="auto">
                  <Code colorScheme="gray" fontSize="sm" whiteSpace="pre">{children}</Code>
                </Box>
              );
            },
            blockquote: ({ children }) => (
              <Box 
                borderLeft="4px solid" 
                borderColor="blue.500" 
                pl={4} 
                py={2} 
                bg={useColorModeValue('blue.50', 'blue.900')} 
                borderRadius="md"
                mb={3}
              >
                {children}
              </Box>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </Box>
    );
  };

  return (
    <VStack spacing={6} align="stretch">
      {/* Report Header */}
      <Card bg={cardBg}>
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="lg">{report.title}</Heading>
            <Button size="sm" leftIcon={<Icon as={Download} />}>
              Export
            </Button>
          </HStack>
        </CardHeader>
      </Card>

      {/* Individual Section Cards - One card per section with title, content, and stats */}
      {report.sections && report.sections.length > 0 && (
        <>
          {report.sections.map((section, index) => (
            <Card key={index} bg={cardBg}>
              <CardHeader>
                <HStack justify="space-between">
                  <Heading size="md">{section.title}</Heading>
                  <HStack spacing={2}>
                    <Badge colorScheme="blue" variant="subtle">
                      {section.word_count} words
                    </Badge>
                    <Badge colorScheme="green" variant="subtle">
                      {Math.round(section.confidence_score * 100)}% confidence
                    </Badge>
                  </HStack>
                </HStack>
              </CardHeader>
              <CardBody>
                <MarkdownContent content={section.content} />
              </CardBody>
            </Card>
          ))}
        </>
      )}
    </VStack>
  );
};
