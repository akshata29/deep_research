import React, { useState, useEffect, useRef } from 'react';
import { 
  VStack, 
  Container, 
  Box, 
  Text, 
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Badge,
  HStack,
  Icon,
  Grid,
  GridItem,
  useColorModeValue,
  Divider,
  Progress,
  Flex
} from '@chakra-ui/react';
import { CheckCircle, Circle, Clock, Zap, Brain, Search, FileText } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { useDeepResearchContext } from '@/contexts/DeepResearchContext';
import { Topic } from './Topic';
import { Feedback } from './Feedback';
import { SearchResult } from './SearchResult';
import { FinalReport } from './FinalReport';

export const Research: React.FC = () => {
  const location = useLocation();
  const { 
    phase, 
    status, 
    isThinking, 
    isResearching, 
    isWriting,
    finalReport,
    sessionId,
    topic,
    questions,
    feedback,
    reportPlan,
    searchTasks,
    setSessionId,
    updateState
  } = useDeepResearchContext();

  console.log('Research component render - Current phase:', phase, 'SessionId:', sessionId);

  // State for managing which accordion panels are expanded
  const [expandedIndexes, setExpandedIndexes] = useState<number[]>([]);
  
  // Track if session has been restored to prevent infinite loops
  const hasRestoredSession = useRef<string | null>(null);

  // Handle session restoration from navigation state
  useEffect(() => {
    console.log('Session restoration useEffect triggered');
    console.log('Location state:', location.state);
    console.log('Current sessionId:', sessionId);
    console.log('hasRestoredSession.current:', hasRestoredSession.current);
    
    const { restoredSession, sessionId: navSessionId } = location.state || {};
    
    console.log('restoredSession:', restoredSession);
    console.log('navSessionId:', navSessionId);
    
    // If we have session data and the current component phase doesn't match the restored phase,
    // then we need to restore regardless of whether we've restored before
    let restoredPhase = restoredSession?.current_phase || restoredSession?.phase;
    
    // Override phase detection: if we have a final_report, the session is actually complete
    if (restoredSession?.final_report && restoredSession.final_report.trim() !== '') {
      restoredPhase = 'completed';
    }
    
    const shouldRestore = restoredSession && navSessionId && 
      restoredPhase && 
      (restoredPhase !== phase || hasRestoredSession.current !== navSessionId);
    
    console.log('Should restore check:', {
      hasRestoredSession: !!restoredSession,
      hasNavSessionId: !!navSessionId,
      hasPhase: !!restoredPhase,
      currentPhase: phase,
      restoredPhase: restoredPhase,
      phasesDifferent: restoredPhase !== phase,
      alreadyRestoredThisSession: hasRestoredSession.current === navSessionId,
      shouldRestore
    });
    
    // Only restore if:
    // 1. We have session data from navigation
    // 2. The restored phase is different from current phase
    // 3. We have a valid session to restore
    if (shouldRestore) {
      console.log('CONDITIONS MET - Starting session restoration');
      console.log('Restoring session:', navSessionId, restoredSession);
      hasRestoredSession.current = navSessionId;
      
      // Set the session ID
      setSessionId(navSessionId);
      
      // Restore the research state based on the restoration data
      let actualPhase = restoredPhase;
      
      const restorationUpdates: any = {
        phase: actualPhase || 'topic'
      };
      
      // Phase-specific restoration logic
      if (actualPhase === 'topic') {
        // Populate topic and expand Research Topic & Questions
        if (restoredSession.topic) {
          restorationUpdates.topic = restoredSession.topic;
        } else if (restoredSession.description) {
          restorationUpdates.topic = restoredSession.description;
        }
      } else if (actualPhase === 'feedback') {
        // Populate questions & feedback and move to and expand Review & Feedback
        if (restoredSession.topic) {
          restorationUpdates.topic = restoredSession.topic;
        } else if (restoredSession.description) {
          restorationUpdates.topic = restoredSession.description;
        }
        if (restoredSession.questions) {
          restorationUpdates.questions = restoredSession.questions;
        }
        if (restoredSession.feedback) {
          restorationUpdates.feedback = restoredSession.feedback;
        }
      } else if (actualPhase === 'research') {
        // Populate report_plan into Research Plan and expand Execute Research Tasks
        if (restoredSession.topic) {
          restorationUpdates.topic = restoredSession.topic;
        } else if (restoredSession.description) {
          restorationUpdates.topic = restoredSession.description;
        }
        if (restoredSession.questions) {
          restorationUpdates.questions = restoredSession.questions;
        }
        if (restoredSession.feedback) {
          restorationUpdates.feedback = restoredSession.feedback;
        }
        if (restoredSession.reportPlan) {
          restorationUpdates.reportPlan = restoredSession.reportPlan;
        }
      } else if (actualPhase === 'report') {
        // Populate Search Tasks and Expand Final Report
        if (restoredSession.topic) {
          restorationUpdates.topic = restoredSession.topic;
        } else if (restoredSession.description) {
          restorationUpdates.topic = restoredSession.description;
        }
        if (restoredSession.questions) {
          restorationUpdates.questions = restoredSession.questions;
        }
        if (restoredSession.feedback) {
          restorationUpdates.feedback = restoredSession.feedback;
        }
        if (restoredSession.reportPlan) {
          restorationUpdates.reportPlan = restoredSession.reportPlan;
        }
        if (restoredSession.searchTasks) {
          restorationUpdates.searchTasks = restoredSession.searchTasks;
        }
      } else if (actualPhase === 'completed') {
        // Populate everything and expand all sections
        if (restoredSession.topic) {
          restorationUpdates.topic = restoredSession.topic;
        } else if (restoredSession.description) {
          restorationUpdates.topic = restoredSession.description;
        }
        if (restoredSession.questions) {
          restorationUpdates.questions = restoredSession.questions;
        }
        if (restoredSession.feedback) {
          restorationUpdates.feedback = restoredSession.feedback;
        }
        if (restoredSession.reportPlan) {
          restorationUpdates.reportPlan = restoredSession.reportPlan;
        }
        if (restoredSession.searchTasks) {
          restorationUpdates.searchTasks = restoredSession.searchTasks;
        }
        if (restoredSession.finalReport) {
          restorationUpdates.finalReport = typeof restoredSession.finalReport === 'string' 
            ? restoredSession.finalReport 
            : JSON.stringify(restoredSession.finalReport, null, 2);
        }
      }
      
      // Always populate currentTaskId if available
      if (restoredSession.currentTaskId) {
        restorationUpdates.currentTaskId = restoredSession.currentTaskId;
      }
      
      // Apply the restoration updates
      console.log('About to apply restoration updates:', restorationUpdates);
      console.log('Current state before restoration:', { phase, sessionId });
      updateState(restorationUpdates);
      console.log('State update called, current state should be updated');
      
      // Force accordion expansion after a short delay to ensure state is updated
      setTimeout(() => {
        const getActiveIndex = () => {
          const currentPhase = actualPhase;
          console.log('Force expanding accordion for phase:', currentPhase);
          if (currentPhase === 'topic') {
            return [0]; // Research Topic & Questions panel
          } else if (currentPhase === 'feedback') {
            return [1]; // Review & Feedback panel
          } else if (currentPhase === 'research') {
            return [2]; // Execute Research Tasks panel
          } else if (currentPhase === 'report') {
            return [3]; // Final Report panel
          } else if (currentPhase === 'completed') {
            return [0, 1, 2, 3]; // Expand all sections
          }
          return [0]; // Default to first panel
        };
        
        const forcedIndexes = getActiveIndex();
        console.log('Forcing accordion expansion to indexes:', forcedIndexes);
        setExpandedIndexes(forcedIndexes);
      }, 100);
      
      console.log('Session restored successfully', {
        sessionId: navSessionId,
        phase: actualPhase,
        topic: restorationUpdates.topic,
        questions: restorationUpdates.questions,
        reportPlan: restorationUpdates.reportPlan,
        searchTasks: restorationUpdates.searchTasks,
        finalReport: restorationUpdates.finalReport ? 'Present' : 'Not present'
      });
    } else {
      console.log('SESSION RESTORATION CONDITIONS NOT MET:');
      console.log('- Has restoredSession:', !!restoredSession);
      console.log('- Has navSessionId:', !!navSessionId);
      console.log('- restoredSession.current_phase:', restoredSession?.current_phase);
      console.log('- Current phase:', phase);
      console.log('- shouldRestore:', shouldRestore);
    }
  }, [location.state, phase, setSessionId, updateState]);

  // Update expanded indexes when phase changes
  useEffect(() => {
    const getActiveIndex = () => {
      console.log('Getting active index for phase:', phase);
      if (phase === 'topic' || phase === 'questions') {
        console.log('Returning index 0 for topic/questions phase');
        return [0]; // Topic & Questions panel
      } else if (phase === 'feedback') {
        console.log('Returning index 1 for feedback phase');
        return [1]; // Feedback panel
      } else if (phase === 'research') {
        console.log('Returning index 2 for research phase');
        return [2]; // Research panel
      } else if (phase === 'report' || phase === 'completed') {
        console.log('Returning index 3 for report/completed phase');
        return [3]; // Report panel
      }
      console.log('Returning default index 0');
      return [0]; // Default to first panel
    };

    const newIndexes = getActiveIndex();
    console.log('Phase changed to:', phase, '- Expanding accordion panel:', newIndexes);
    console.log('Current expandedIndexes before update:', expandedIndexes);
    setExpandedIndexes(newIndexes);
  }, [phase]);

  const bgGradient = useColorModeValue(
    'linear(to-br, blue.50, purple.50, pink.50)',
    'linear(to-br, gray.900, blue.900, purple.900)'
  );
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const cardShadow = useColorModeValue('xl', 'dark-lg');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'gray.100');
  const subtitleColor = useColorModeValue('gray.600', 'gray.400');
  const processingBg = useColorModeValue('blue.50', 'blue.900');
  const processingBorder = useColorModeValue('blue.200', 'blue.600');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const disabledBg = useColorModeValue('gray.50', 'gray.800');
  const emptyStateBg = useColorModeValue('gray.50', 'gray.700');

  // Helper function to get phase status and styling
  const getPhaseInfo = (phaseName: string) => {
    const phaseOrder = ['topic', 'questions', 'feedback', 'research', 'report', 'completed'];
    const currentIndex = phaseOrder.indexOf(phase);
    const targetIndex = phaseOrder.indexOf(phaseName);
    
    console.log(`getPhaseInfo for ${phaseName}: currentPhase=${phase}, currentIndex=${currentIndex}, targetIndex=${targetIndex}`);
    
    if (targetIndex < currentIndex || (phaseName === 'topic' && (phase === 'questions' || currentIndex > 0))) {
      console.log(`${phaseName}: returning completed/enabled`);
      return { status: 'completed', icon: CheckCircle, color: 'green', isEnabled: true };
    } else if (targetIndex === currentIndex || (phaseName === 'topic' && phase === 'questions')) {
      // Special case for report phase: check if final report is completed
      if (phaseName === 'report' && (phase === 'report' || phase === 'completed') && finalReport && !isWriting) {
        console.log(`${phaseName}: returning completed/enabled (final report case)`);
        return { status: 'completed', icon: CheckCircle, color: 'green', isEnabled: true };
      }
      console.log(`${phaseName}: returning active/enabled`);
      return { status: 'active', icon: Clock, color: 'blue', isEnabled: true };
    } else {
      console.log(`${phaseName}: returning pending/disabled`);
      return { status: 'pending', icon: Circle, color: 'gray', isEnabled: false };
    }
  };

  // Calculate progress percentage
  const getProgressPercentage = () => {
    const phaseOrder = ['topic', 'questions', 'feedback', 'research', 'report', 'completed'];
    const currentIndex = phaseOrder.indexOf(phase);
    if (phase === 'completed') return 100;
    return ((currentIndex + 1) / (phaseOrder.length - 1)) * 100; // Exclude completed from calculation
  };

  const phaseIcons = [
    { icon: Zap, title: 'Topic & Questions', desc: 'Define research scope' },
    { icon: Brain, title: 'Review & Feedback', desc: 'Refine approach (optional)' },
    { icon: Search, title: 'Research Execution', desc: 'Gather insights' },
    { icon: FileText, title: 'Final Report', desc: 'Generate deliverable' }
  ];

  return (
    <Box minH="100vh" bgGradient={bgGradient}>
      <Container maxW="full" px={8} py={8}>
        <Grid templateColumns={{ base: '1fr', lg: '300px 1fr' }} gap={8} minH="calc(100vh - 4rem)">
          {/* Left Sidebar - Progress Overview */}
          <GridItem>
            <Box
              bg={cardBg}
              shadow={cardShadow}
              borderRadius="2xl"
              p={6}
              border="1px solid"
              borderColor={borderColor}
              position="sticky"
              top={8}
            >
              <VStack spacing={6} align="stretch">
                <Box textAlign="center">
                  <Text fontSize="xl" fontWeight="bold" mb={2} color={textColor}>
                    Research Pipeline
                  </Text>
                  <Text fontSize="sm" color={subtitleColor} mb={4}>
                    AI-powered deep research
                  </Text>
                  <Box>
                    <Progress 
                      value={getProgressPercentage()} 
                      colorScheme="blue" 
                      size="lg" 
                      borderRadius="full"
                      bg={useColorModeValue('gray.100', 'gray.700')}
                    />
                    <Text fontSize="xs" color={subtitleColor} mt={2}>
                      {Math.round(getProgressPercentage())}% Complete
                    </Text>
                  </Box>
                </Box>

                <Divider />

                <VStack spacing={4} align="stretch">
                  {phaseIcons.map((item, index) => {
                    const phaseNames = ['topic', 'feedback', 'research', 'report'];
                    const phaseName = phaseNames[index];
                    const phaseInfo = getPhaseInfo(phaseName);
                    const isCurrentPhase = (phase === phaseName) || 
                                         (phase === 'questions' && phaseName === 'topic') ||
                                         (phase === 'completed' && phaseName === 'report');
                    
                    return (
                      <Flex
                        key={index}
                        align="center"
                        p={3}
                        borderRadius="lg"
                        bg={isCurrentPhase ? processingBg : 'transparent'}
                        border={isCurrentPhase ? '1px solid' : '1px solid transparent'}
                        borderColor={isCurrentPhase ? processingBorder : 'transparent'}
                        transition="all 0.2s"
                        _hover={{ bg: hoverBg }}
                      >
                        <Icon
                          as={phaseInfo.icon}
                          w={5}
                          h={5}
                          color={`${phaseInfo.color}.500`}
                          mr={3}
                        />
                        <Box flex={1}>
                          <Text fontSize="sm" fontWeight="semibold" color={textColor}>
                            {item.title}
                          </Text>
                          <Text fontSize="xs" color={subtitleColor}>
                            {item.desc}
                          </Text>
                        </Box>
                        <Badge
                          size="sm"
                          colorScheme={phaseInfo.color}
                          variant={phaseInfo.status === 'active' ? 'solid' : 'subtle'}
                        >
                          {phaseInfo.status === 'completed' ? '✓' : 
                           phaseInfo.status === 'active' ? '●' : '○'}
                        </Badge>
                      </Flex>
                    );
                  })}
                </VStack>

                {(isThinking || isResearching || isWriting) && (
                  <>
                    <Divider />
                    <Box textAlign="center" p={3} bg={processingBg} borderRadius="lg" border="1px solid" borderColor={processingBorder}>
                      <HStack justify="center" mb={2}>
                        <Icon as={Clock} color="blue.500" className="animate-spin" w={4} h={4} />
                        <Text fontSize="sm" fontWeight="semibold" color="blue.500">
                          Processing...
                        </Text>
                      </HStack>
                      <Text fontSize="xs" color={subtitleColor}>
                        {status || 'Working on your research'}
                      </Text>
                    </Box>
                  </>
                )}
              </VStack>
            </Box>
          </GridItem>

          {/* Main Content Area */}
          <GridItem>
            <Box
              bg={cardBg}
              shadow={cardShadow}
              borderRadius="2xl"
              border="1px solid"
              borderColor={borderColor}
              overflow="hidden"
            >
              <Accordion 
                allowMultiple 
                index={expandedIndexes}
                onChange={(indexes) => setExpandedIndexes(Array.isArray(indexes) ? indexes : [indexes])}
                variant="unstyled"
              >
                {/* Phase 1: Topic & Questions */}
                <AccordionItem>
                  {({ isExpanded }) => {
                    const topicInfo = getPhaseInfo('topic');
                    return (
                      <>
                        <AccordionButton 
                          p={6}
                          _hover={{ bg: hoverBg }}
                          bg={isExpanded ? hoverBg : 'transparent'}
                          borderBottom={isExpanded ? '1px solid' : 'none'}
                          borderColor={borderColor}
                          cursor="pointer"
                        >
                          <Flex flex="1" align="center" textAlign="left">
                            <Box
                              w={12}
                              h={12}
                              borderRadius="xl"
                              bg={`${topicInfo.color}.100`}
                              display="flex"
                              alignItems="center"
                              justifyContent="center"
                              mr={4}
                            >
                              <Icon 
                                as={Zap} 
                                color={`${topicInfo.color}.600`}
                                w={6} 
                                h={6} 
                              />
                            </Box>
                            <Box flex={1}>
                              <HStack justify="space-between" align="center">
                                <VStack align="start" spacing={1}>
                                  <Text fontWeight="bold" fontSize="lg" color={textColor}>
                                    Research Topic & Questions
                                  </Text>
                                  <Text fontSize="sm" color={subtitleColor}>
                                    Define your research scope and generate clarifying questions
                                    {topicInfo.status === 'completed' && ' • Click to review'}
                                  </Text>
                                </VStack>
                                <VStack align="end" spacing={2}>
                                  <Badge 
                                    colorScheme={topicInfo.color}
                                    variant={topicInfo.status === 'active' ? 'solid' : 'subtle'}
                                    fontSize="xs"
                                    px={3}
                                    py={1}
                                    borderRadius="full"
                                  >
                                    {topicInfo.status === 'completed' ? '✓ Completed' :
                                     phase === 'topic' ? 'Enter Topic' : 
                                     phase === 'questions' ? 'Generating Questions' : 'Pending'}
                                  </Badge>
                                  {(phase === 'questions' && isThinking) && (
                                    <Text fontSize="xs" color="blue.600" fontWeight="medium">
                                      {status}
                                    </Text>
                                  )}
                                </VStack>
                              </HStack>
                            </Box>
                          </Flex>
                          <AccordionIcon ml={4} />
                        </AccordionButton>
                        <AccordionPanel p={6} pt={0}>
                          <Topic />
                          {phase === 'questions' && (
                            <Box mt={6} p={4} bg="blue.50" borderRadius="xl" border="1px solid" borderColor="blue.200">
                              <HStack mb={2}>
                                <Icon as={Clock} color="blue.500" className="animate-spin" w={5} h={5} />
                                <Text fontWeight="bold" color="blue.800">Generating Questions...</Text>
                              </HStack>
                              <Text color="blue.600" fontSize="sm">
                                {status || 'The AI is creating clarifying questions for your research topic.'}
                              </Text>
                            </Box>
                          )}
                        </AccordionPanel>
                      </>
                    );
                  }}
                </AccordionItem>

                {/* Phase 2: Feedback */}
                <AccordionItem>
                  {({ isExpanded }) => {
                    const feedbackInfo = getPhaseInfo('feedback');
                    return (
                      <>
                        <AccordionButton 
                          p={6}
                          _hover={{ bg: feedbackInfo.isEnabled ? hoverBg : disabledBg }}
                          bg={isExpanded ? hoverBg : 'transparent'}
                          cursor={feedbackInfo.isEnabled ? 'pointer' : 'not-allowed'}
                          opacity={feedbackInfo.isEnabled ? 1 : 0.6}
                          borderBottom={isExpanded ? '1px solid' : 'none'}
                          borderColor={borderColor}
                          disabled={!feedbackInfo.isEnabled}
                        >
                          <Flex flex="1" align="center" textAlign="left">
                            <Box
                              w={12}
                              h={12}
                              borderRadius="xl"
                              bg={`${feedbackInfo.color}.100`}
                              display="flex"
                              alignItems="center"
                              justifyContent="center"
                              mr={4}
                            >
                              <Icon 
                                as={Brain} 
                                color={`${feedbackInfo.color}.600`}
                                w={6} 
                                h={6} 
                              />
                            </Box>
                            <Box flex={1}>
                              <HStack justify="space-between" align="center">
                                <VStack align="start" spacing={1}>
                                  <Text fontWeight="bold" fontSize="lg" color={textColor}>
                                    Review Questions & Provide Feedback (Optional)
                                  </Text>
                                  <Text fontSize="sm" color={subtitleColor}>
                                    Review generated questions and provide your insights or skip to continue
                                    {feedbackInfo.status === 'completed' && ' • Click to review'}
                                  </Text>
                                </VStack>
                                <Badge 
                                  colorScheme={feedbackInfo.color}
                                  variant={feedbackInfo.status === 'active' ? 'solid' : 'subtle'}
                                  fontSize="xs"
                                  px={3}
                                  py={1}
                                  borderRadius="full"
                                >
                                  {feedbackInfo.status === 'completed' ? 'Completed' : 
                                   feedbackInfo.status === 'active' ? 'Active' : 'Pending'}
                                </Badge>
                              </HStack>
                            </Box>
                          </Flex>
                          <AccordionIcon ml={4} />
                        </AccordionButton>
                        <AccordionPanel p={6} pt={0}>
                          {feedbackInfo.isEnabled ? (
                            <Feedback />
                          ) : (
                            <Box p={8} bg={emptyStateBg} borderRadius="xl" textAlign="center">
                              <Icon as={Circle} w={8} h={8} color="gray.400" mb={3} />
                              <Text color={subtitleColor} fontWeight="medium">
                                Complete the topic and questions phase first
                              </Text>
                              <Text fontSize="sm" color={subtitleColor} mt={1}>
                                Generate questions before proceeding to feedback
                              </Text>
                            </Box>
                          )}
                        </AccordionPanel>
                      </>
                    );
                  }}
                </AccordionItem>

                {/* Phase 3: Research Execution */}
                <AccordionItem>
                  {({ isExpanded }) => {
                    const researchInfo = getPhaseInfo('research');
                    return (
                      <>
                        <AccordionButton 
                          p={6}
                          _hover={{ bg: researchInfo.isEnabled ? hoverBg : disabledBg }}
                          bg={isExpanded ? hoverBg : 'transparent'}
                          cursor={researchInfo.isEnabled ? 'pointer' : 'not-allowed'}
                          opacity={researchInfo.isEnabled ? 1 : 0.6}
                          borderBottom={isExpanded ? '1px solid' : 'none'}
                          borderColor={borderColor}
                          disabled={!researchInfo.isEnabled}
                        >
                          <Flex flex="1" align="center" textAlign="left">
                            <Box
                              w={12}
                              h={12}
                              borderRadius="xl"
                              bg={`${researchInfo.color}.100`}
                              display="flex"
                              alignItems="center"
                              justifyContent="center"
                              mr={4}
                            >
                              <Icon 
                                as={Search} 
                                color={`${researchInfo.color}.600`}
                                w={6} 
                                h={6} 
                              />
                            </Box>
                            <Box flex={1}>
                              <HStack justify="space-between" align="center">
                                <VStack align="start" spacing={1}>
                                  <Text fontWeight="bold" fontSize="lg" color={textColor}>
                                    Execute Research Tasks
                                  </Text>
                                  <Text fontSize="sm" color={subtitleColor}>
                                    AI conducts comprehensive research with real-time data
                                    {researchInfo.status === 'completed' && ' • Click to review'}
                                  </Text>
                                </VStack>
                                <VStack align="end" spacing={2}>
                                  <Badge 
                                    colorScheme={researchInfo.color}
                                    variant={researchInfo.status === 'active' ? 'solid' : 'subtle'}
                                    fontSize="xs"
                                    px={3}
                                    py={1}
                                    borderRadius="full"
                                  >
                                    {researchInfo.status === 'completed' ? '✓ Completed' : 
                                     researchInfo.status === 'active' ? 'Researching' : 'Pending'}
                                  </Badge>
                                  {(phase === 'research' && isResearching) && (
                                    <Text fontSize="xs" color="blue.600" fontWeight="medium">
                                      {status}
                                    </Text>
                                  )}
                                </VStack>
                              </HStack>
                            </Box>
                          </Flex>
                          <AccordionIcon ml={4} />
                        </AccordionButton>
                        <AccordionPanel p={6} pt={0}>
                          {researchInfo.isEnabled ? (
                            <SearchResult />
                          ) : (
                            <Box p={8} bg={emptyStateBg} borderRadius="xl" textAlign="center">
                              <Icon as={Circle} w={8} h={8} color="gray.400" mb={3} />
                              <Text color={subtitleColor} fontWeight="medium">
                                Complete the feedback phase first
                              </Text>
                              <Text fontSize="sm" color={subtitleColor} mt={1}>
                                Provide feedback before starting research execution
                              </Text>
                            </Box>
                          )}
                        </AccordionPanel>
                      </>
                    );
                  }}
                </AccordionItem>

                {/* Phase 4: Final Report */}
                <AccordionItem>
                  {({ isExpanded }) => {
                    const reportInfo = getPhaseInfo('report');
                    return (
                      <>
                        <AccordionButton 
                          p={6}
                          _hover={{ bg: reportInfo.isEnabled ? hoverBg : disabledBg }}
                          bg={isExpanded ? hoverBg : 'transparent'}
                          cursor={reportInfo.isEnabled ? 'pointer' : 'not-allowed'}
                          opacity={reportInfo.isEnabled ? 1 : 0.6}
                          disabled={!reportInfo.isEnabled}
                        >
                          <Flex flex="1" align="center" textAlign="left">
                            <Box
                              w={12}
                              h={12}
                              borderRadius="xl"
                              bg={`${reportInfo.color}.100`}
                              display="flex"
                              alignItems="center"
                              justifyContent="center"
                              mr={4}
                            >
                              <Icon 
                                as={FileText} 
                                color={`${reportInfo.color}.600`}
                                w={6} 
                                h={6} 
                              />
                            </Box>
                            <Box flex={1}>
                              <HStack justify="space-between" align="center">
                                <VStack align="start" spacing={1}>
                                  <Text fontWeight="bold" fontSize="lg" color={textColor}>
                                    Generate Final Report
                                  </Text>
                                  <Text fontSize="sm" color={subtitleColor}>
                                    Create comprehensive report with insights and analysis
                                    {reportInfo.status === 'completed' && ' • Click to review'}
                                  </Text>
                                </VStack>
                                <VStack align="end" spacing={2}>
                                  <Badge 
                                    colorScheme={reportInfo.color}
                                    variant={reportInfo.status === 'active' ? 'solid' : 'subtle'}
                                    fontSize="xs"
                                    px={3}
                                    py={1}
                                    borderRadius="full"
                                  >
                                    {reportInfo.status === 'completed' ? '✓ Completed' : 
                                     reportInfo.status === 'active' ? 'Generating' : 'Pending'}
                                  </Badge>
                                  {(phase === 'report' && isWriting) && (
                                    <Text fontSize="xs" color="blue.500" fontWeight="medium">
                                      {status}
                                    </Text>
                                  )}
                                </VStack>
                              </HStack>
                            </Box>
                          </Flex>
                          <AccordionIcon ml={4} />
                        </AccordionButton>
                        <AccordionPanel p={6} pt={0}>
                          {reportInfo.isEnabled ? (
                            <FinalReport />
                          ) : (
                            <Box p={8} bg={emptyStateBg} borderRadius="xl" textAlign="center">
                              <Icon as={Circle} w={8} h={8} color="gray.400" mb={3} />
                              <Text color={subtitleColor} fontWeight="medium">
                                Complete the research execution phase first
                              </Text>
                              <Text fontSize="sm" color={subtitleColor} mt={1}>
                                Execute research tasks before generating the final report
                              </Text>
                            </Box>
                          )}
                        </AccordionPanel>
                      </>
                    );
                  }}
                </AccordionItem>
              </Accordion>
            </Box>
          </GridItem>
        </Grid>
      </Container>
    </Box>
  );
};
