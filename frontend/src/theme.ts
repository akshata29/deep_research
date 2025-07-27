import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: true,
};

const theme = extendTheme({
  config,
  fonts: {
    heading: `'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
    body: `'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
  },
  colors: {
    brand: {
      50: '#e3f2fd',
      100: '#bbdefb',
      200: '#90caf9',
      300: '#64b5f6',
      400: '#42a5f5',
      500: '#2196f3',
      600: '#1e88e5',
      700: '#1976d2',
      800: '#1565c0',
      900: '#0d47a1',
    },
    azure: {
      50: '#e8f4f8',
      100: '#d1e7ee',
      200: '#a2cedd',
      300: '#74b6cc',
      400: '#459dbb',
      500: '#1684aa',
      600: '#126a88',
      700: '#0d4f66',
      800: '#093544',
      900: '#041a22',
    },
    semantic: {
      success: '#38a169',
      warning: '#d69e2e',
      error: '#e53e3e',
      info: '#3182ce',
    }
  },
  components: {
    Button: {
      defaultProps: {
        colorScheme: 'brand',
      },
      variants: {
        solid: {
          bg: 'brand.500',
          color: 'white',
          _hover: {
            bg: 'brand.600',
          },
        },
        outline: {
          borderColor: 'brand.500',
          color: 'brand.500',
          _hover: {
            bg: 'brand.50',
          },
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          borderRadius: 'lg',
          boxShadow: 'sm',
          border: '1px solid',
          borderColor: 'gray.200',
          _dark: {
            borderColor: 'gray.700',
          },
        },
      },
    },
    Progress: {
      defaultProps: {
        colorScheme: 'brand',
      },
    },
    Spinner: {
      defaultProps: {
        colorScheme: 'brand',
      },
    },
    Tag: {
      variants: {
        status: {
          container: {
            borderRadius: 'full',
            px: 3,
            py: 1,
            fontSize: 'sm',
            fontWeight: 'medium',
          },
        },
      },
    },
  },
  styles: {
    global: {
      body: {
        bg: 'gray.50',
        _dark: {
          bg: 'gray.900',
        },
      },
    },
  },
  semanticTokens: {
    colors: {
      'bg-canvas': {
        default: 'white',
        _dark: 'gray.800',
      },
      'bg-surface': {
        default: 'gray.50',
        _dark: 'gray.900',
      },
      'text-primary': {
        default: 'gray.900',
        _dark: 'gray.100',
      },
      'text-secondary': {
        default: 'gray.600',
        _dark: 'gray.400',
      },
      'border-subtle': {
        default: 'gray.200',
        _dark: 'gray.700',
      },
    },
  },
});

export { theme };
