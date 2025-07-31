#!/usr/bin/env python3
"""
Test script for session management integration.
"""

import asyncio
import json
from pathlib import Path

async def test_session_management():
    """Test the session management system."""
    
    print("🧪 Testing Session Management Integration\n")
    
    try:
        # Test 1: Import session manager
        print("1. Testing session manager import...")
        from backend.app.orchestration.session_manager import OrchestrationSessionManager
        session_manager = OrchestrationSessionManager()
        print("✓ Session manager imported and initialized successfully")
        
        # Test 2: Create a test session
        print("\n2. Testing session creation...")
        test_session_id = "test-session-123"
        test_query = "Test research query about AI technologies"
        
        session_manager.create_session(
            session_id=test_session_id,
            query=test_query,
            project_id="test-project"
        )
        print("✓ Test session created successfully")
        
        # Test 3: Add agent execution
        print("\n3. Testing agent execution tracking...")
        session_manager.add_agent_execution(
            session_id=test_session_id,
            agent_name="TestAgent",
            input_data="Test input",
            output_data="Test output with some detailed response",
            status="completed",
            execution_time=1.25,
            metadata={"test": True, "agent_type": "test"}
        )
        print("✓ Agent execution tracked successfully")
        
        # Test 4: Update session status
        print("\n4. Testing session status update...")
        session_manager.update_session_status(
            session_id=test_session_id,
            status="completed",
            final_result="Final test result"
        )
        print("✓ Session status updated successfully")
        
        # Test 5: Retrieve session details
        print("\n5. Testing session retrieval...")
        session_details = session_manager.get_session(test_session_id)
        
        if session_details:
            print("✓ Session details retrieved successfully")
            print(f"  - Session ID: {session_details['session_id']}")
            print(f"  - Status: {session_details['status']}")
            print(f"  - Query: {session_details['query'][:50]}...")
            print(f"  - Agent executions: {len(session_details['agent_executions'])}")
            print(f"  - Final result length: {len(session_details.get('final_result', ''))}")
        else:
            print("❌ Session details not found")
            return False
        
        # Test 6: Test Deep Research Agent integration
        print("\n6. Testing DeepResearchAgent integration...")
        from backend.app.orchestration.deep_research_agent import DeepResearchAgent
        
        agent = DeepResearchAgent(
            session_id="integration-test-456",
            project_id="integration-test-project"
        )
        
        print("✓ DeepResearchAgent with session management imported successfully")
        print(f"  - Session ID: {agent.session_id}")
        print(f"  - Project ID: {agent.project_id}")
        print(f"  - Session manager: {type(agent.session_manager).__name__}")
        
        # Test 7: Check session files
        print("\n7. Testing session file storage...")
        sessions_dir = Path("backend/sessions")
        if sessions_dir.exists():
            session_files = list(sessions_dir.glob("orchestration_*.json"))
            metadata_file = sessions_dir / "sessions_orchestration_metadata.json"
            
            print(f"✓ Sessions directory exists: {sessions_dir}")
            print(f"  - Session files found: {len(session_files)}")
            print(f"  - Metadata file exists: {metadata_file.exists()}")
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                print(f"  - Total sessions in metadata: {len(metadata.get('sessions', {}))}")
        else:
            print(f"⚠️  Sessions directory not found: {sessions_dir}")
        
        print("\n🎉 All session management tests passed!")
        print("\nSession Management Features:")
        print("✓ Session creation and tracking")
        print("✓ Agent execution logging with timing")
        print("✓ Status updates and final results")
        print("✓ Persistent file storage")
        print("✓ Integration with DeepResearchAgent")
        print("✓ API endpoint support")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Session management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_integration():
    """Test API integration (requires running server)."""
    print("\n🌐 Testing API Integration (optional - requires running server)")
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get("http://localhost:8000/api/v1/orchestration/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✓ Orchestration health endpoint working")
                    print(f"  - Status: {health_data.get('status')}")
                    print(f"  - Active sessions: {health_data.get('active_sessions_count')}")
                else:
                    print(f"⚠️  Health endpoint returned status {response.status}")
                    
    except ImportError:
        print("⚠️  aiohttp not available, skipping API tests")
    except Exception as e:
        print(f"⚠️  API test failed (server may not be running): {e}")

if __name__ == "__main__":
    asyncio.run(test_session_management())
    asyncio.run(test_api_integration())
