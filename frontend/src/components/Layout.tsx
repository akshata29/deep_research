import { ReactNode } from 'react';
import {
  Box,
  Flex,
  HStack,
  VStack,
  IconButton,
  Button,
  useColorMode,
  useColorModeValue,
  Text,
  Avatar,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Divider,
  Container,
  useDisclosure,
  Drawer,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  DrawerHeader,
  DrawerBody,
} from '@chakra-ui/react';
import { Link, useLocation } from 'react-router-dom';
import {
  Search,
  FileText,
  Settings,
  Moon,
  Sun,
  Menu as MenuIcon,
  Home,
  BarChart3,
  User,
  LogOut,
  Users,
} from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

const NavItem = ({ 
  to, 
  icon, 
  children, 
  isActive = false,
  onClick
}: { 
  to: string; 
  icon: React.ReactElement; 
  children: ReactNode; 
  isActive?: boolean;
  onClick?: () => void;
}) => {
  return (
    <Button
      as={Link}
      to={to}
      variant={isActive ? 'solid' : 'ghost'}
      leftIcon={icon}
      justifyContent="flex-start"
      width="full"
      size="sm"
      fontWeight={isActive ? 'semibold' : 'normal'}
      onClick={onClick}
    >
      {children}
    </Button>
  );
};

const Navigation = ({ onClose }: { onClose?: () => void }) => {
  const location = useLocation();
  
  const navItems = [
    { to: '/', icon: <Home size={16} />, label: 'Home' },
    { to: '/research', icon: <Search size={16} />, label: 'Research' },
    { to: '/orchestration', icon: <Users size={16} />, label: 'Orchestration' },
    { to: '/exports', icon: <FileText size={16} />, label: 'Exports' },
    { to: '/sessions', icon: <BarChart3 size={16} />, label: 'Sessions' },
    { to: '/settings', icon: <Settings size={16} />, label: 'Settings' },
  ];

  return (
    <VStack spacing={2} align="stretch">
      {navItems.map((item) => (
        <NavItem
          key={item.to}
          to={item.to}
          icon={item.icon}
          isActive={location.pathname === item.to}
          onClick={onClose}
        >
          {item.label}
        </NavItem>
      ))}
    </VStack>
  );
};

export const Layout = ({ children }: LayoutProps) => {
  const { colorMode, toggleColorMode } = useColorMode();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Flex minH="100vh" bg="bg-surface">
      {/* Desktop Sidebar */}
      <Box
        display={{ base: 'none', md: 'block' }}
        w="240px"
        bg={bg}
        borderRight="1px solid"
        borderColor={borderColor}
        p={4}
      >
        <VStack spacing={6} align="stretch">
          {/* Logo */}
          <Box>
            <Text fontSize="xl" fontWeight="bold" color="brand.500">
              Deep Research
            </Text>
            <Text fontSize="sm" color="text-secondary">
              AI-Powered Research
            </Text>
          </Box>

          <Divider />

          {/* Navigation */}
          <Navigation />

          {/* Spacer */}
          <Box flex={1} />

          {/* User Menu */}
          <Menu>
            <MenuButton
              as={Button}
              variant="ghost"
              leftIcon={<Avatar size="sm" name="User" />}
              justifyContent="flex-start"
              width="full"
              size="sm"
            >
              <Text fontSize="sm" isTruncated>
                John Doe
              </Text>
            </MenuButton>
            <MenuList>
              <MenuItem icon={<User size={16} />}>
                Profile
              </MenuItem>
              <MenuItem icon={<BarChart3 size={16} />}>
                Analytics
              </MenuItem>
              <Divider />
              <MenuItem icon={<LogOut size={16} />} color="red.500">
                Sign Out
              </MenuItem>
            </MenuList>
          </Menu>
        </VStack>
      </Box>

      {/* Mobile Drawer */}
      <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>
            <Text fontSize="lg" fontWeight="bold" color="brand.500">
              Deep Research
            </Text>
          </DrawerHeader>
          <DrawerBody>
            <Navigation onClose={onClose} />
          </DrawerBody>
        </DrawerContent>
      </Drawer>

      {/* Main Content */}
      <Flex flex={1} direction="column">
        {/* Top Bar */}
        <Flex
          h="60px"
          px={4}
          bg={bg}
          borderBottom="1px solid"
          borderColor={borderColor}
          align="center"
          justify="space-between"
        >
          {/* Mobile Menu Button */}
          <IconButton
            display={{ base: 'flex', md: 'none' }}
            icon={<MenuIcon size={20} />}
            variant="ghost"
            aria-label="Open menu"
            onClick={onOpen}
          />

          {/* Spacer */}
          <Box flex={1} />

          {/* Right Actions */}
          <HStack spacing={2}>
            <IconButton
              icon={colorMode === 'light' ? <Moon size={16} /> : <Sun size={16} />}
              variant="ghost"
              aria-label="Toggle color mode"
              onClick={toggleColorMode}
            />
          </HStack>
        </Flex>

        {/* Page Content */}
        <Box flex={1} overflow="auto">
          <Container maxW="7xl" py={6}>
            {children}
          </Container>
        </Box>
      </Flex>
    </Flex>
  );
};
