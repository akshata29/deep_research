import React from 'react';
import {
  VStack,
  Text,
  Icon,
  Box,
  useColorModeValue,
} from '@chakra-ui/react';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
}) => {
  const iconColor = useColorModeValue('gray.400', 'gray.500');
  const titleColor = useColorModeValue('gray.600', 'gray.400');
  const descriptionColor = useColorModeValue('gray.500', 'gray.500');

  return (
    <Box py={16}>
      <VStack spacing={4} textAlign="center">
        <Icon as={icon} boxSize={12} color={iconColor} />
        <VStack spacing={2}>
          <Text fontSize="lg" fontWeight="medium" color={titleColor}>
            {title}
          </Text>
          <Text fontSize="sm" color={descriptionColor} maxW="md">
            {description}
          </Text>
        </VStack>
      </VStack>
    </Box>
  );
};
