import React, { useState } from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  HStack,
  Button,
  Card,
  CardBody,
  CardHeader,
  FormControl,
  FormLabel,
  FormHelperText,
  Input,
  Select,
  Switch,
  Textarea,
  Divider,
  Text,
  Grid,
  GridItem,
  Alert,
  AlertIcon,
  AlertDescription,
  useToast,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Icon,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SimpleGrid,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { Save, RefreshCw, Settings, User, Shield, Zap, Brain, Wrench } from 'lucide-react';
import { useSettings, useUpdateSettings, useSystemHealth, useModels, useLocalSettings } from '@/hooks/useApi';
import { UserSettings, ResearchDepth, SearchMethod } from '@/types';

interface SettingsFormData extends UserSettings {}

export const SettingsPage: React.FC = () => {
  const toast = useToast();
  const [activeTab, setActiveTab] = useState(0);

  const { data: settings, isLoading, refetch, updateSettings } = useLocalSettings();
  const { data: systemHealth } = useSystemHealth();
  const { data: models, isLoading: modelsLoading } = useModels();
  // Keep the API-based update for potential server sync in the future
  const updateSettingsAPI = useUpdateSettings();

  const { register, handleSubmit, watch, setValue, reset } = useForm<SettingsFormData>({
    defaultValues: settings || {
      defaultThinkingModel: 'chato1',
      defaultTaskModel: 'chat4omini',
      defaultResearchDepth: 'standard',
      executionMode: 'agents',
      searchMethod: 'bing',
      defaultLanguage: 'en',
      enableWebSearchByDefault: true,
      enableNotifications: true,
      autoExportFormat: 'pdf',
      maxConcurrentTasks: 3,
      defaultInstructions: '',
      themePreference: 'system',
      enableTelemetry: true,
    },
  });

  const watchedValues = watch();

  React.useEffect(() => {
    if (settings) {
      reset(settings);
    }
  }, [settings, reset]);

  const onSubmit = async (data: SettingsFormData) => {
    try {
      // Update localStorage settings
      updateSettings(data);
      
      // Optionally sync with backend in the future
      // await updateSettingsAPI.mutateAsync(data);
      
      toast({
        title: 'Settings Updated',
        description: 'Your preferences have been saved successfully.',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Failed to Update Settings',
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleReset = () => {
    reset();
    toast({
      title: 'Settings Reset',
      description: 'All settings have been reset to their default values.',
      status: 'info',
      duration: 3000,
    });
  };

  if (isLoading) {
    return (
      <Container maxW="4xl" py={8}>
        <VStack spacing={6}>
          <Heading>Loading settings...</Heading>
        </VStack>
      </Container>
    );
  }

  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>Settings</Heading>
          <Text color="gray.600" _dark={{ color: 'gray.400' }}>
            Customize your research experience and preferences
          </Text>
        </Box>

        <Tabs index={activeTab} onChange={setActiveTab} colorScheme="brand">
          <TabList>
            <Tab>
              <Icon as={Settings} mr={2} />
              General
            </Tab>
            <Tab>
              <Icon as={Zap} mr={2} />
              Models
            </Tab>
            <Tab>
              <Icon as={User} mr={2} />
              Preferences
            </Tab>
            <Tab>
              <Icon as={Shield} mr={2} />
              Advanced
            </Tab>
          </TabList>

          <TabPanels>
            {/* General Settings */}
            <TabPanel>
              <form onSubmit={handleSubmit(onSubmit)}>
                <VStack spacing={6} align="stretch">
                  <Card>
                    <CardHeader>
                      <Heading size="md">Default Research Settings</Heading>
                    </CardHeader>
                    <CardBody>
                      <VStack spacing={4}>
                        <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)' }} gap={4}>
                          <FormControl>
                            <FormLabel>Default Research Depth</FormLabel>
                            <Select {...register('defaultResearchDepth')}>
                              <option value="quick">Quick (5-10 min)</option>
                              <option value="standard">Standard (15-30 min)</option>
                              <option value="deep">Deep (45-60 min)</option>
                            </Select>
                          </FormControl>

                          <FormControl>
                            <FormLabel>Default Language</FormLabel>
                            <Select {...register('defaultLanguage')}>
                              <option value="en">English</option>
                              <option value="es">Spanish</option>
                              <option value="fr">French</option>
                              <option value="de">German</option>
                              <option value="zh">Chinese</option>
                            </Select>
                          </FormControl>
                        </Grid>

                        <FormControl display="flex" alignItems="center">
                          <FormLabel htmlFor="web-search-default" mb="0">
                            Enable Web Search by Default
                          </FormLabel>
                          <Switch
                            id="web-search-default"
                            {...register('enableWebSearchByDefault')}
                            colorScheme="brand"
                          />
                        </FormControl>

                        <FormControl>
                          <FormLabel>Search Method</FormLabel>
                          <Select {...register('searchMethod')}>
                            <option value="bing">Bing Grounding (AI with real-time search)</option>
                            <option value="tavily">Tavily Search (Direct web search API)</option>
                          </Select>
                          <FormHelperText>
                            Choose the search method for research execution. Bing Grounding uses AI with real-time search capabilities, while Tavily provides direct web search API results.
                          </FormHelperText>
                        </FormControl>

                        <FormControl>
                          <FormLabel>Default Instructions</FormLabel>
                          <Textarea
                            {...register('defaultInstructions')}
                            placeholder="Default instructions to include in all research requests..."
                            rows={3}
                            resize="vertical"
                          />
                          <FormHelperText>
                            These instructions will be automatically included in all research requests.
                          </FormHelperText>
                        </FormControl>
                      </VStack>
                    </CardBody>
                  </Card>

                  <Card>
                    <CardHeader>
                      <Heading size="md">Export Settings</Heading>
                    </CardHeader>
                    <CardBody>
                      <FormControl>
                        <FormLabel>Default Export Format</FormLabel>
                        <Select {...register('autoExportFormat')}>
                          <option value="pdf">PDF</option>
                          <option value="docx">DOCX</option>
                          <option value="html">HTML</option>
                          <option value="markdown">Markdown</option>
                          <option value="json">JSON</option>
                        </Select>
                        <FormHelperText>
                          Reports will be automatically exported in this format upon completion.
                        </FormHelperText>
                      </FormControl>
                    </CardBody>
                  </Card>
                </VStack>
              </form>
            </TabPanel>

            {/* Model Settings */}
            <TabPanel>
              <VStack spacing={6} align="stretch">
                <Card>
                  <CardHeader>
                    <Heading size="md">AI Model Configuration</Heading>
                    <Text fontSize="sm" color="gray.600">
                      Configure your preferred AI models for different research tasks
                    </Text>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={6}>
                      {/* Thinking Models Section */}
                      <Box>
                        <HStack spacing={2} mb={3}>
                          <Icon as={Brain} color="purple.500" />
                          <Text fontWeight="semibold" color="purple.600">Thinking Models</Text>
                          <Badge colorScheme="purple" size="sm">Advanced Reasoning</Badge>
                        </HStack>
                        <FormControl>
                          <FormLabel>Default Thinking Model</FormLabel>
                          <Select {...register('defaultThinkingModel')}>
                            {modelsLoading ? (
                              <option value="">Loading models...</option>
                            ) : (
                              models
                                ?.filter(model => model.type === 'thinking')
                                .map(model => (
                                  <option key={model.name} value={model.name}>
                                    {model.display_name} 
                                    {model.name.toLowerCase().includes('gpt-4.1') ? ' (Recommended)' : ''}
                                    {model.supports_agents ? ' • Agent Ready' : ''}
                                  </option>
                                ))
                            )}
                            {/* Fallback options if no models loaded */}
                            {!modelsLoading && (!models || models.filter(m => m.type === 'thinking').length === 0) && (
                              <>
                                <option value="gpt-4">GPT-4 (Recommended)</option>
                                <option value="gpt-35-turbo">GPT-3.5 Turbo</option>
                                <option value="deepseek">Deepseek</option>
                              </>
                            )}
                          </Select>
                          <FormHelperText>
                            <Icon as={Brain} color="purple.400" mr={1} />
                            Used for complex reasoning, analysis, and strategic planning. 
                            These models excel at breaking down complex problems and developing research strategies.
                          </FormHelperText>
                        </FormControl>
                      </Box>

                      <Divider />

                      {/* Task Models Section */}
                      <Box>
                        <HStack spacing={2} mb={3}>
                          <Icon as={Wrench} color="blue.500" />
                          <Text fontWeight="semibold" color="blue.600">Task Models</Text>
                          <Badge colorScheme="blue" size="sm">Fast Execution</Badge>
                        </HStack>
                        <FormControl>
                          <FormLabel>Default Task Model</FormLabel>
                          <Select {...register('defaultTaskModel')}>
                            {modelsLoading ? (
                              <option value="">Loading models...</option>
                            ) : (
                              models
                                ?.filter(model => model.type === 'task')
                                .map(model => (
                                  <option key={model.name} value={model.name}>
                                    {model.display_name} 
                                    {(model.name.toLowerCase().includes('gpt-35-turbo') || model.name.toLowerCase().includes('gpt-4o-mini')) ? ' (Recommended)' : ''}
                                    {model.supports_agents ? ' • Agent Ready' : ''}
                                  </option>
                                ))
                            )}
                            {/* Fallback options if no models loaded */}
                            {!modelsLoading && (!models || models.filter(m => m.type === 'task').length === 0) && (
                              <>
                                <option value="gpt-35-turbo">GPT-3.5 Turbo (Recommended)</option>
                                <option value="gpt-4">GPT-4</option>
                                <option value="deepseek">Deepseek</option>
                                <option value="mistral">Mistral</option>
                              </>
                            )}
                          </Select>
                          <FormHelperText>
                            <Icon as={Wrench} color="blue.400" mr={1} />
                            Used for routine tasks, information gathering, and structured queries. 
                            These models are optimized for speed and efficiency in specific tasks.
                          </FormHelperText>
                        </FormControl>
                      </Box>

                      {/* Available Models Summary */}
                      {!modelsLoading && models && models.length > 0 && (
                        <Box>
                          <Text fontWeight="semibold" mb={2}>Available Models Summary</Text>
                          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                            <Card size="sm" bg="purple.50" borderColor="purple.200">
                              <CardBody>
                                <HStack justify="space-between" mb={2}>
                                  <Text fontWeight="medium" color="purple.700">Thinking Models</Text>
                                  <Badge colorScheme="purple">{models.filter(m => m.type === 'thinking').length}</Badge>
                                </HStack>
                                <VStack align="start" spacing={1}>
                                  {models.filter(m => m.type === 'thinking').slice(0, 3).map(model => (
                                    <Text key={model.name} fontSize="sm" color="purple.600">
                                      • {model.display_name}
                                    </Text>
                                  ))}
                                  {models.filter(m => m.type === 'thinking').length > 3 && (
                                    <Text fontSize="sm" color="purple.500">
                                      +{models.filter(m => m.type === 'thinking').length - 3} more
                                    </Text>
                                  )}
                                </VStack>
                              </CardBody>
                            </Card>

                            <Card size="sm" bg="blue.50" borderColor="blue.200">
                              <CardBody>
                                <HStack justify="space-between" mb={2}>
                                  <Text fontWeight="medium" color="blue.700">Task Models</Text>
                                  <Badge colorScheme="blue">{models.filter(m => m.type === 'task').length}</Badge>
                                </HStack>
                                <VStack align="start" spacing={1}>
                                  {models.filter(m => m.type === 'task').slice(0, 3).map(model => (
                                    <Text key={model.name} fontSize="sm" color="blue.600">
                                      • {model.display_name}
                                    </Text>
                                  ))}
                                  {models.filter(m => m.type === 'task').length > 3 && (
                                    <Text fontSize="sm" color="blue.500">
                                      +{models.filter(m => m.type === 'task').length - 3} more
                                    </Text>
                                  )}
                                </VStack>
                              </CardBody>
                            </Card>
                          </SimpleGrid>
                        </Box>
                      )}

                      <Alert status="info">
                        <AlertIcon />
                        <AlertDescription>
                          Model availability depends on your Azure AI Foundry deployment and regional access.
                          Contact your administrator if you need access to specific models.
                        </AlertDescription>
                      </Alert>
                    </VStack>
                  </CardBody>
                </Card>

                {/* Execution Mode Configuration */}
                <Card>
                  <CardHeader>
                    <Heading size="md">
                      <HStack>
                        <Icon as={Settings} color="green.400" />
                        <Text>Execution Mode</Text>
                      </HStack>
                    </Heading>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <FormControl>
                        <FormLabel>
                          <HStack>
                            <Text>Research Execution Mode</Text>
                            <Badge colorScheme="green" fontSize="xs">RECOMMENDED</Badge>
                          </HStack>
                        </FormLabel>
                        <Select {...register('executionMode')} defaultValue="agents">
                          <option value="agents">Agent Mode (Recommended)</option>
                          <option value="direct">Direct Mode</option>
                        </Select>
                        <FormHelperText>
                          <VStack align="start" spacing={2}>
                            <HStack>
                              <Icon as={Brain} color="green.400" mr={1} />
                              <Text fontSize="sm">
                                <strong>Agent Mode:</strong> Uses specialized thinking and task agents for deeper analysis and more comprehensive research
                              </Text>
                            </HStack>
                            <HStack>
                              <Icon as={Zap} color="blue.400" mr={1} />
                              <Text fontSize="sm">
                                <strong>Direct Mode:</strong> Single-model approach for faster, more straightforward research tasks
                              </Text>
                            </HStack>
                          </VStack>
                        </FormHelperText>
                      </FormControl>

                      <Alert status="success" size="sm">
                        <AlertIcon />
                        <AlertDescription fontSize="sm">
                          Agent Mode leverages the O1 thinking model for complex reasoning and specialized task models for execution, 
                          providing more thorough and nuanced research outcomes.
                        </AlertDescription>
                      </Alert>
                    </VStack>
                  </CardBody>
                </Card>

                {/* System Health */}
                {systemHealth && (
                  <Card>
                    <CardHeader>
                      <Heading size="md">Model Status</Heading>
                    </CardHeader>
                    <CardBody>
                      <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
                        {Object.entries(systemHealth.models || {}).map(([model, status]) => (
                          <HStack key={model} justify="space-between">
                            <Text>{model}</Text>
                            <Badge colorScheme={status === 'healthy' ? 'green' : 'red'}>
                              {status}
                            </Badge>
                          </HStack>
                        ))}
                      </Grid>
                    </CardBody>
                  </Card>
                )}
              </VStack>
            </TabPanel>

            {/* User Preferences */}
            <TabPanel>
              <VStack spacing={6} align="stretch">
                <Card>
                  <CardHeader>
                    <Heading size="md">Interface Preferences</Heading>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={4}>
                      <FormControl>
                        <FormLabel>Theme Preference</FormLabel>
                        <Select {...register('themePreference')}>
                          <option value="system">System Default</option>
                          <option value="light">Light</option>
                          <option value="dark">Dark</option>
                        </Select>
                      </FormControl>

                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="notifications" mb="0">
                          Enable Notifications
                        </FormLabel>
                        <Switch
                          id="notifications"
                          {...register('enableNotifications')}
                          colorScheme="brand"
                        />
                      </FormControl>
                    </VStack>
                  </CardBody>
                </Card>

                <Card>
                  <CardHeader>
                    <Heading size="md">Performance Settings</Heading>
                  </CardHeader>
                  <CardBody>
                    <FormControl>
                      <FormLabel>
                        Maximum Concurrent Tasks: {watchedValues.maxConcurrentTasks}
                      </FormLabel>
                      <Slider
                        value={watchedValues.maxConcurrentTasks}
                        onChange={(val) => setValue('maxConcurrentTasks', val)}
                        min={1}
                        max={10}
                        step={1}
                        colorScheme="brand"
                      >
                        <SliderTrack>
                          <SliderFilledTrack />
                        </SliderTrack>
                        <SliderThumb />
                      </Slider>
                      <FormHelperText>
                        Higher values may impact performance. Recommended: 3-5 tasks.
                      </FormHelperText>
                    </FormControl>
                  </CardBody>
                </Card>
              </VStack>
            </TabPanel>

            {/* Advanced Settings */}
            <TabPanel>
              <VStack spacing={6} align="stretch">
                <Card>
                  <CardHeader>
                    <Heading size="md">Advanced Configuration</Heading>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={4}>
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="telemetry" mb="0">
                          Enable Usage Analytics
                        </FormLabel>
                        <Switch
                          id="telemetry"
                          {...register('enableTelemetry')}
                          colorScheme="brand"
                        />
                      </FormControl>
                      <Text fontSize="sm" color="gray.600">
                        Help us improve the service by sharing anonymous usage data.
                      </Text>

                      <Divider />

                      <Alert status="warning">
                        <AlertIcon />
                        <AlertDescription>
                          Advanced settings can affect system performance and stability.
                          Only modify these if you understand their implications.
                        </AlertDescription>
                      </Alert>
                    </VStack>
                  </CardBody>
                </Card>

                <Card>
                  <CardHeader>
                    <Heading size="md">Data Management</Heading>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <Button variant="outline" colorScheme="blue">
                        Export All Data
                      </Button>
                      <Button variant="outline" colorScheme="orange">
                        Clear Cache
                      </Button>
                      <Button variant="outline" colorScheme="red">
                        Delete All Research Data
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>

        {/* Action Buttons */}
        <HStack justify="space-between" pt={4}>
          <HStack>
            <Button
              variant="outline"
              onClick={handleReset}
              leftIcon={<Icon as={RefreshCw} />}
            >
              Reset to Defaults
            </Button>
            <Button
              variant="outline"
              onClick={() => refetch()}
              leftIcon={<Icon as={RefreshCw} />}
            >
              Reload Settings
            </Button>
          </HStack>
          
          <Button
            colorScheme="brand"
            onClick={handleSubmit(onSubmit)}
            isLoading={updateSettings.isPending}
            leftIcon={<Icon as={Save} />}
            size="lg"
          >
            Save Changes
          </Button>
        </HStack>
      </VStack>
    </Container>
  );
};
