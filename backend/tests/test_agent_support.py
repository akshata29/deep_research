#!/usr/bin/env python3
import httpx
import asyncio

async def test_models():
    async with httpx.AsyncClient() as client:
        response = await client.get('http://localhost:8010/api/v1/research/models')
        models = response.json()
        
        print("Model Agent Support:")
        print("=" * 50)
        for model in models:
            support_text = "✅ AGENTS" if model['supports_agents'] else "❌ DIRECT ONLY"
            print(f"{model['name']:<15} -> {support_text}")

if __name__ == "__main__":
    asyncio.run(test_models())
