"""
Test script for the orchestration system.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend app to the path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.orchestration.config import get_orchestration_config, get_project_config


async def test_configuration():
    """Test configuration loading."""
    print("Testing configuration...")
    
    try:
        # Test orchestration config
        config = get_orchestration_config()
        print(f"✓ Orchestration config loaded")
        print(f"  - Azure OpenAI Endpoint: {config.azure_openai_endpoint or 'Not set'}")
        print(f"  - Embedding Deployment: {config.azure_embedding_deployment}")
        print(f"  - Company: {config.company}")
        
        # Test project config
        project_config = get_project_config()
        print(f"✓ Project config loaded")
        print(f"  - Company: {project_config.system.get('company', 'Not set')}")
        print(f"  - Agent count: {len(project_config.agents)}")
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False
    
    return True


async def test_memory_import():
    """Test memory module imports."""
    print("\nTesting memory module imports...")
    
    try:
        from app.orchestration.memory import MemoryManager, MemoryPlugin
        print("✓ Memory modules imported successfully")
    except Exception as e:
        print(f"✗ Memory import failed: {e}")
        return False
    
    return True


async def test_search_import():
    """Test search module imports."""
    print("\nTesting search module imports...")
    
    try:
        from app.orchestration.search import ModularSearchPlugin, WebSearchProvider, AzureSearchProvider
        print("✓ Search modules imported successfully")
    except Exception as e:
        print(f"✗ Search import failed: {e}")
        return False
    
    return True


async def test_agent_import():
    """Test agent module imports."""
    print("\nTesting agent module imports...")
    
    try:
        from app.orchestration.agent_factory import create_agents_with_memory
        from app.orchestration.deep_research_agent import DeepResearchAgent
        print("✓ Agent modules imported successfully")
    except Exception as e:
        print(f"✗ Agent import failed: {e}")
        return False
    
    return True


async def test_api_import():
    """Test API module imports."""
    print("\nTesting API module imports...")
    
    try:
        from app.api.orchestration import router
        print("✓ API orchestration module imported successfully")
    except Exception as e:
        print(f"✗ API import failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("🧪 Running Orchestration System Tests\n")
    
    tests = [
        test_configuration,
        test_memory_import,
        test_search_import,
        test_agent_import,
        test_api_import
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results:")
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Orchestration system is ready.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and dependencies.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
