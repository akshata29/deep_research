import React from 'react';
import { Research } from '@/components/Research/Research';
import { DeepResearchProvider } from '@/contexts/DeepResearchContext';

export const ResearchPage: React.FC = () => {
  return (
    <DeepResearchProvider>
      <Research />
    </DeepResearchProvider>
  );
};
