import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ChakraProvider, ColorModeScript } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { theme } from './theme';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { ResearchPage } from './pages/ResearchPage';
import { OrchestrationPage } from './pages/OrchestrationPage';
import { ExportsPage } from './pages/ExportsPage';
import { SessionsPage } from './pages/SessionsPage';
import { SettingsPage } from './pages/SettingsPage';
import { ErrorBoundary } from './components/ErrorBoundary';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

function App() {
  return (
    <>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      <ChakraProvider theme={theme}>
        <QueryClientProvider client={queryClient}>
          <ErrorBoundary>
            <Router>
              <Layout>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/research" element={<ResearchPage />} />
                  <Route path="/research/:taskId" element={<ResearchPage />} />
                  <Route path="/orchestration" element={<OrchestrationPage />} />
                  <Route path="/orchestration/:sessionId" element={<OrchestrationPage />} />
                  <Route path="/exports" element={<ExportsPage />} />
                  <Route path="/sessions" element={<SessionsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </Layout>
            </Router>
          </ErrorBoundary>
        </QueryClientProvider>
      </ChakraProvider>
    </>
  );
}

export default App;
