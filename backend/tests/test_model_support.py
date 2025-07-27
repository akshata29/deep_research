#!/usr/bin/env python3
import asyncio
import httpx

async def test_model_support():
    """Test model agent support detection"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get('http://localhost:8010/api/v1/research/models')
            print(f'Models endpoint: {response.status_code}')
            
            if response.status_code == 200:
                models = response.json()
                print(f'\nFound {len(models)} models:')
                print('='*60)
                
                for model in models:
                    name = model.get('name', 'Unknown')
                    display_name = model.get('display_name', 'Unknown')
                    model_type = model.get('type', 'Unknown')
                    agent_supported = model.get('agent_supported', False)
                    
                    status = "✅ Agents Supported" if agent_supported else "❌ Direct Only"
                    print(f"{name:<15} | {display_name:<20} | {model_type:<10} | {status}")
                
                print('='*60)
                
                # Check specific models
                agent_models = [m for m in models if m.get('agent_supported', False)]
                direct_models = [m for m in models if not m.get('agent_supported', False)]
                
                print(f"\n📊 Summary:")
                print(f"   Models supporting Azure AI Agents: {len(agent_models)}")
                print(f"   Models requiring Direct API: {len(direct_models)}")
                
                if agent_models:
                    print(f"\n✅ Azure AI Agents Compatible:")
                    for model in agent_models:
                        print(f"   - {model['name']} ({model['display_name']})")
                
                if direct_models:
                    print(f"\n🔗 Direct API Only:")
                    for model in direct_models:
                        print(f"   - {model['name']} ({model['display_name']})")
                        
            else:
                print(f'Error: {response.text}')
                
        except Exception as e:
            print(f'Request failed: {e}')

if __name__ == "__main__":
    asyncio.run(test_model_support())
