#!/usr/bin/env python3
"""Debug script to test agent support detection logic"""

def test_agent_support():
    """Test the agent support detection with actual deployment names"""
    
    def _is_agent_supported(model_name: str) -> bool:
        """Check if a model is supported by Azure AI Agents Service."""
        print(f"Checking agent support for: '{model_name}'")
        
        model_name_lower = model_name.lower()
        print(f"Lowercase model name: '{model_name_lower}'")
        
        # Standard OpenAI model names
        standard_supported_models = [
            'gpt-4o',
            'gpt-4o-mini', 
            'gpt-4',
            'gpt-35-turbo',
            'gpt-3.5-turbo'
        ]
        
        # Custom deployment name patterns (common Azure naming conventions)
        custom_patterns = [
            'chat4o',      # GPT-4o variants
            'chat4',       # GPT-4 variants  
            'chato1',      # O1 models (GPT-4o family)
            'gpt4o',       # Alternative GPT-4o naming
            'gpt4',        # Alternative GPT-4 naming
            'gpt35',       # GPT-3.5 variants
            'turbo'        # Turbo variants
        ]
        
        # Check standard names first
        for supported in standard_supported_models:
            if supported in model_name_lower:
                print(f"  ✅ Matched standard model: '{supported}'")
                return True
        
        # Check custom deployment patterns
        for pattern in custom_patterns:
            if pattern in model_name_lower:
                print(f"  ✅ Matched custom pattern: '{pattern}'")
                return True
        
        print(f"  ❌ No match found")
        return False
    
    # Test with your deployment names
    test_models = [
        'chatds',
        'chato1',
        'chat4',
        'chat4omini',
        'chato1mini',
        'chatphi3si',
        'chatphi4mm',
        'embedding',
        # Also test potential underlying model names
        'gpt-4',
        'gpt-4o',
        'gpt-4o-mini',
        'gpt-35-turbo'
    ]
    
    print("Testing agent support detection:")
    print("="*50)
    
    for model in test_models:
        result = _is_agent_supported(model)
        status = "✅ SUPPORTED" if result else "❌ NOT SUPPORTED"
        print(f"{model:<15} → {status}")
        print()

if __name__ == "__main__":
    test_agent_support()
