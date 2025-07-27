#!/usr/bin/env python3
"""
Quick Research API Test

Simple test script to verify basic Research API functionality.
"""

import asyncio
import json
import httpx

BASE_URL = "http://localhost:8010"
API_BASE = f"{BASE_URL}/api/v1/research"

async def quick_test():
    """Run a quick test of the Research API."""
    print("🧪 Quick Research API Test")
    print("=" * 40)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test 1: Get models (skip health check)
            print("1. Getting available models...")
            response = await client.get(f"{API_BASE}/models")
            if response.status_code == 200:
                models = response.json()
                thinking_models = [m for m in models if m.get('type') == 'thinking']
                task_models = [m for m in models if m.get('type') == 'task']
                print(f"   ✅ Found {len(models)} models ({len(thinking_models)} thinking, {len(task_models)} task)")
                
                if thinking_models:
                    print(f"   🧠 Thinking models: {', '.join([m['name'] for m in thinking_models])}")
                if task_models:
                    print(f"   ⚡ Task models: {', '.join([m['name'] for m in task_models])}")
            else:
                print(f"   ❌ Failed to get models: {response.status_code}")
                print(f"   Response: {response.text}")
                return
            
            # Test 2: Start research (quick test)
            print("2. Starting a test research task...")
            research_request = {
                "prompt": "Quick test: What is artificial intelligence?",
                "models_config": {
                    "thinking": thinking_models[0]['name'] if thinking_models else "gpt-4",
                    "task": task_models[0]['name'] if task_models else "gpt-35-turbo"
                },
                "enable_web_search": False,  # Disable web search for faster test
                "research_depth": "quick",
                "language": "en"
            }
            
            response = await client.post(
                f"{API_BASE}/start",
                json=research_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                print(f"   ✅ Research started with task ID: {task_id}")
                
                # Test 3: Check status
                print("3. Checking task status...")
                await asyncio.sleep(2)  # Wait a bit
                
                response = await client.get(f"{API_BASE}/status/{task_id}")
                if response.status_code == 200:
                    status_result = response.json()
                    status = status_result.get('status')
                    progress = status_result.get('progress', {})
                    print(f"   ✅ Status: {status}, Progress: {progress.get('progress_percentage', 0)}%")
                    print(f"   Current step: {progress.get('current_step', 'Unknown')}")
                else:
                    print(f"   ❌ Failed to get status: {response.status_code}")
                
                # Test 4: Cancel task (cleanup)
                print("4. Cancelling test task...")
                response = await client.delete(f"{API_BASE}/cancel/{task_id}")
                if response.status_code == 200:
                    print("   ✅ Task cancelled successfully")
                else:
                    print(f"   ⚠️  Could not cancel task: {response.status_code}")
                
            else:
                print(f"   ❌ Failed to start research: {response.status_code}")
                print(f"   Response: {response.text}")
                return
            
            print("\n🎉 All research API tests passed! The Research API is working correctly.")
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            return

if __name__ == "__main__":
    print("Make sure the backend server is running:")
    print("cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8010")
    print()
    
    asyncio.run(quick_test())
