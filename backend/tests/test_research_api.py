#!/usr/bin/env python3
"""
Test script for Research API endpoints.

This script tests the main research API functionality without requiring a UI.
Run this script to verify that the backend API is working correctly.
"""

import asyncio
import json
import time
from typing import Dict, Any

import httpx
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# API Configuration
BASE_URL = "http://localhost:8010"
API_BASE = f"{BASE_URL}/api/v1/research"

class ResearchAPITester:
    """Test runner for Research API endpoints."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all API tests and return results."""
        logger.info("Starting Research API tests", base_url=BASE_URL)
        
        # Test 1: Health check (basic connectivity)
        await self.test_health_check()
        
        # Test 2: Get available models
        await self.test_get_models()
        
        # Test 3: Start a research task
        task_id = await self.test_start_research()
        
        if task_id:
            # Test 4: Get research status
            await self.test_get_status(task_id)
            
            # Test 5: Monitor progress (brief)
            await self.test_monitor_progress(task_id)
            
            # Test 6: Cancel research task
            await self.test_cancel_research(task_id)
        
        # Test 7: List research tasks
        await self.test_list_tasks()
        
        # Test 8: Cache management
        await self.test_cache_management()
        
        # Print summary
        self.print_test_summary()
        
        await self.client.aclose()
        return self.test_results
    
    async def test_health_check(self):
        """Test basic connectivity to the API."""
        test_name = "Health Check"
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                self.log_success(test_name, "API is accessible")
            else:
                self.log_failure(test_name, f"Unexpected status code: {response.status_code}")
        except Exception as e:
            self.log_failure(test_name, f"Connection failed: {str(e)}")
    
    async def test_get_models(self):
        """Test the /models endpoint."""
        test_name = "Get Available Models"
        try:
            response = await self.client.get(f"{API_BASE}/models")
            
            if response.status_code == 200:
                models = response.json()
                if isinstance(models, list) and len(models) > 0:
                    thinking_models = [m for m in models if m.get('type') == 'thinking']
                    task_models = [m for m in models if m.get('type') == 'task']
                    
                    self.log_success(
                        test_name, 
                        f"Retrieved {len(models)} models ({len(thinking_models)} thinking, {len(task_models)} task)"
                    )
                    
                    # Log model details
                    for model in models[:3]:  # Show first 3 models
                        logger.info(
                            "Model found",
                            name=model.get('name'),
                            type=model.get('type'),
                            display_name=model.get('display_name')
                        )
                else:
                    self.log_failure(test_name, "No models returned or invalid format")
            else:
                self.log_failure(test_name, f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_failure(test_name, f"Request failed: {str(e)}")
    
    async def test_start_research(self) -> str:
        """Test starting a research task."""
        test_name = "Start Research Task"
        task_id = None
        
        try:
            # Prepare research request
            research_request = {
                "prompt": "Test research: What are the key benefits of cloud computing for small businesses?",
                "models_config": {
                    "thinking": "chat4",  # Use actual deployed model name
                    "task": "chat4omini"  # Use actual deployed model name
                },
                "enable_web_search": True,
                "research_depth": "quick",
                "language": "en",
                "custom_instructions": "This is a test research task."
            }
            
            response = await self.client.post(
                f"{API_BASE}/start",
                json=research_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                status = result.get('status')
                progress = result.get('progress', {})
                
                if task_id:
                    self.log_success(
                        test_name, 
                        f"Research started with task_id: {task_id}, status: {status}"
                    )
                    logger.info(
                        "Research task details",
                        task_id=task_id,
                        status=status,
                        current_step=progress.get('current_step'),
                        websocket_url=result.get('websocket_url')
                    )
                else:
                    self.log_failure(test_name, "No task_id returned")
            else:
                self.log_failure(test_name, f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_failure(test_name, f"Request failed: {str(e)}")
        
        return task_id
    
    async def test_get_status(self, task_id: str):
        """Test getting research task status."""
        test_name = "Get Research Status"
        
        try:
            response = await self.client.get(f"{API_BASE}/status/{task_id}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                progress = result.get('progress', {})
                
                self.log_success(
                    test_name,
                    f"Status: {status}, Progress: {progress.get('progress_percentage', 0)}%"
                )
                
                logger.info(
                    "Status details",
                    task_id=task_id,
                    status=status,
                    current_step=progress.get('current_step'),
                    tokens_used=progress.get('tokens_used', 0),
                    sources_found=progress.get('sources_found', 0)
                )
            else:
                self.log_failure(test_name, f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_failure(test_name, f"Request failed: {str(e)}")
    
    async def test_monitor_progress(self, task_id: str):
        """Monitor research progress for a short time."""
        test_name = "Monitor Progress"
        
        try:
            # Monitor for up to 30 seconds
            start_time = time.time()
            max_duration = 30
            checks = 0
            
            while time.time() - start_time < max_duration:
                response = await self.client.get(f"{API_BASE}/status/{task_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    progress = result.get('progress', {})
                    progress_pct = progress.get('progress_percentage', 0)
                    current_step = progress.get('current_step', 'Unknown')
                    
                    checks += 1
                    logger.info(
                        "Progress update",
                        check=checks,
                        status=status,
                        progress_percentage=progress_pct,
                        current_step=current_step
                    )
                    
                    # If completed or failed, break
                    if status in ['completed', 'failed', 'cancelled']:
                        break
                
                # Wait 3 seconds between checks
                await asyncio.sleep(3)
            
            self.log_success(test_name, f"Monitored for {checks} checks over {int(time.time() - start_time)} seconds")
            
        except Exception as e:
            self.log_failure(test_name, f"Monitoring failed: {str(e)}")
    
    async def test_cancel_research(self, task_id: str):
        """Test cancelling a research task."""
        test_name = "Cancel Research Task"
        
        try:
            response = await self.client.delete(f"{API_BASE}/cancel/{task_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log_success(test_name, f"Task cancelled: {result.get('message')}")
            else:
                self.log_failure(test_name, f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_failure(test_name, f"Request failed: {str(e)}")
    
    async def test_list_tasks(self):
        """Test listing research tasks."""
        test_name = "List Research Tasks"
        
        try:
            response = await self.client.get(f"{API_BASE}/list")
            
            if response.status_code == 200:
                result = response.json()
                task_count = result.get('total_count', 0)
                tasks = result.get('tasks', [])
                
                self.log_success(test_name, f"Found {task_count} tasks")
                
                # Log details of recent tasks
                for task in tasks[:3]:  # Show first 3 tasks
                    logger.info(
                        "Task found",
                        task_id=task.get('task_id'),
                        status=task.get('status'),
                        progress=task.get('progress_percentage'),
                        prompt_preview=task.get('prompt', '')[:50] + "..."
                    )
            else:
                self.log_failure(test_name, f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_failure(test_name, f"Request failed: {str(e)}")
    
    async def test_cache_management(self):
        """Test model cache management endpoints."""
        test_name = "Cache Management"
        
        try:
            # Test cache status
            response = await self.client.get(f"{API_BASE}/models/cache/status")
            if response.status_code == 200:
                cache_status = response.json()
                logger.info("Cache status", cache_status=cache_status)
                
                # Test cache refresh
                response = await self.client.post(f"{API_BASE}/models/cache/refresh")
                if response.status_code == 200:
                    refresh_result = response.json()
                    self.log_success(
                        test_name, 
                        f"Cache refreshed: {refresh_result.get('model_count')} models in {len(refresh_result.get('categories', []))} categories"
                    )
                else:
                    self.log_failure(test_name, f"Cache refresh failed: {response.status_code}")
            else:
                self.log_failure(test_name, f"Cache status failed: {response.status_code}")
                
        except Exception as e:
            self.log_failure(test_name, f"Cache management failed: {str(e)}")
    
    def log_success(self, test_name: str, message: str):
        """Log a successful test."""
        self.test_results.append({"test": test_name, "status": "PASS", "message": message})
        logger.info("TEST PASS", test=test_name, message=message)
    
    def log_failure(self, test_name: str, message: str):
        """Log a failed test."""
        self.test_results.append({"test": test_name, "status": "FAIL", "message": message})
        logger.error("TEST FAIL", test=test_name, message=message)
    
    def print_test_summary(self):
        """Print a summary of all test results."""
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        total = len(self.test_results)
        
        print("\n" + "="*60)
        print("RESEARCH API TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        print("="*60)
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"❌ {result['test']}: {result['message']}")
        
        if passed > 0:
            print("\nPASSED TESTS:")
            for result in self.test_results:
                if result["status"] == "PASS":
                    print(f"✅ {result['test']}: {result['message']}")
        
        print("\n")


async def main():
    """Main test runner."""
    print("Research API Test Runner")
    print("=" * 40)
    print(f"Testing API at: {BASE_URL}")
    print(f"Make sure the backend server is running on {BASE_URL}")
    print("=" * 40)
    
    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                print(f"❌ Server health check failed: {response.status_code}")
                return
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {str(e)}")
        print(f"   Make sure to start the backend server first:")
        print(f"   cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8010")
        return
    
    print("✅ Server is running, starting tests...\n")
    
    # Run tests
    tester = ResearchAPITester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    failed_count = len([r for r in results if r["status"] == "FAIL"])
    exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
