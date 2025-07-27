import React from 'react';
import { VStack, Container, Box, Text } from '@chakra-ui/react';
import { useDeepResearchContext } from '@/contexts/DeepResearchContext';
import { Topic } from './Topic';
import { Feedback } from './Feedback';
import { SearchResult } from './SearchResult';
import { FinalReport } from './FinalReport';

export const Research: React.FC = () => {
  const { 
    phase, 
    status, 
    currentTaskId, 
    isThinking, 
    isResearching, 
    isWriting,
    updateState
  } = useDeepResearchContext();

  // Debug logging - log the entire hook result
  console.log('=== RESEARCH COMPONENT DEBUG ===');
  console.log('Phase specifically:', phase);
  console.log('Type of phase:', typeof phase);
  console.log('Phase === "feedback"?', phase === 'feedback');
  console.log('=== RESEARCH COMPONENT RENDER CONDITIONS ===');
  console.log('Show Topic?', (phase === 'topic' || phase === 'questions'));
  console.log('Show Feedback?', (phase === 'feedback'));
  console.log('Show SearchResult?', (phase === 'research'));
  console.log('Show FinalReport?', (phase === 'report'));

  // Debug function to manually advance phases
  const forceNextPhase = () => {
    console.log('Manually forcing next phase from:', phase);
    switch (phase) {
      case 'questions':
        updateState({ 
          questions: 'Sample questions generated',
          phase: 'feedback',
          status: 'Questions generated successfully',
          isThinking: false,
          currentTaskId: null
        });
        break;
      case 'feedback':
        updateState({ 
          reportPlan: 'Sample report plan created',
          phase: 'research',
          status: 'Research plan created successfully',
          isThinking: false,
          currentTaskId: null
        });
        break;
      case 'research':
        updateState({ 
          searchTasks: [{
            query: 'Sample research task',
            researchGoal: 'Sample goal',
            state: 'completed' as const,
            learning: 'Sample learning content',
            sources: [],
            images: []
          }],
          phase: 'report',
          status: 'Research tasks completed successfully',
          isResearching: false,
          currentTaskId: null
        });
        break;
    }
  };

  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Debug info - remove in production */}
        <Box p={3} bg="blue.50" borderRadius="md" fontSize="sm" border="1px solid" borderColor="blue.200">
          <Text fontWeight="bold" color="blue.800">Debug Info:</Text>
          <Text color="blue.600">Phase: <strong>{phase}</strong></Text>
          <Text color="blue.600">Status: <strong>{status}</strong></Text>
          <Text color="blue.600">Task ID: {currentTaskId || 'None'}</Text>
          <Text color="blue.600">Loading States: Thinking:{isThinking} Research:{isResearching} Writing:{isWriting}</Text>
          {(phase === 'questions' || phase === 'feedback' || phase === 'research') && (
            <button 
              onClick={forceNextPhase}
              style={{ 
                marginTop: '8px', 
                padding: '4px 8px', 
                backgroundColor: '#38A169', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Force Next Phase (Debug)
            </button>
          )}
        </Box>
        
        {/* Show Topic only in 'topic' and 'questions' phases */}
        {(phase === 'topic' || phase === 'questions') && (
          <Box>
            <Topic />
            {phase === 'questions' && (
              <Box mt={4} p={4} bg="yellow.50" borderRadius="md" border="1px solid" borderColor="yellow.200">
                <Text fontWeight="bold" color="yellow.800">Processing Questions...</Text>
                <Text color="yellow.600">The AI is generating clarifying questions for your research topic.</Text>
              </Box>
            )}
          </Box>
        )}
        
        {/* Show Feedback only in feedback phase */}
        {phase === 'feedback' && (
          <Feedback />
        )}
        
        {/* Show SearchResult only in research phase */}
        {phase === 'research' && (
          <SearchResult />
        )}
        
        {/* Show FinalReport only in report phase */}
        {phase === 'report' && (
          <FinalReport />
        )}
      </VStack>
    </Container>
  );
};
