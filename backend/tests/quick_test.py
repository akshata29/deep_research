#!/usr/bin/env python3
import httpx
import asyncio
import json

async def test_api():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test models endpoint
        try:
            response = await client.get('http://localhost:8010/api/v1/research/models')
            print(f'Models endpoint: {response.status_code}')
            if response.status_code == 200:
                models = response.json()
                print(f'Found {len(models)} models')
                for model in models[:3]:
                    print(f"  - {model.get('name')} ({model.get('type')})")
            else:
                print(f'Error: {response.text}')
        except Exception as e:
            print(f'Models request failed: {e}')
        
        # Test research start endpoint
        try:
            research_request = {
                "prompt": "Quick test: What is cloud computing?",
                "models_config": {
                    "thinking": "chat4",
                    "task": "chat4omini"
                },
                "enable_web_search": True,
                "research_depth": "quick"
            }
            
            response = await client.post(
                'http://localhost:8010/api/v1/research/start',
                json=research_request,
                headers={"Content-Type": "application/json"}
            )
            print(f'\nResearch start: {response.status_code}')
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                print(f'Task started: {task_id}')
                print(f'Status: {result.get("status")}')
                
                # Check status after a moment
                if task_id:
                    print('\nWaiting 3 seconds, then checking status...')
                    await asyncio.sleep(3)
                    
                    status_response = await client.get(f'http://localhost:8010/api/v1/research/status/{task_id}')
                    print(f'Status check: {status_response.status_code}')
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        print(f'Current status: {status_result.get("status")}')
                        progress = status_result.get("progress", {})
                        print(f'Progress: {progress.get("progress_percentage", 0)}%')
                        print(f'Current step: {progress.get("current_step", "Unknown")}')
                    else:
                        print(f'Status error: {status_response.text}')
            else:
                print(f'Error: {response.text}')
        except Exception as e:
            print(f'Research start failed: {e}')

if __name__ == "__main__":
    asyncio.run(test_api())
