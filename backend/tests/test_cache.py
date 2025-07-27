import asyncio
from app.core.config import get_settings
from app.core.azure_config import AzureServiceManager

async def test_cache():
    settings = get_settings()
    azure_manager = AzureServiceManager(settings)
    await azure_manager.initialize()
    
    print('=== Initial cache status ===')
    status = azure_manager.get_models_cache_status()
    print(f"Cached: {status['cached']}")
    print(f"Valid: {status['is_valid']}")
    
    print('\n=== First call (should hit API) ===')
    models1 = await azure_manager.get_deployed_models()
    print(f'Retrieved {len(models1)} model categories: {list(models1.keys())}')
    
    status = azure_manager.get_models_cache_status()
    print(f"Cache age: {status['cache_age_minutes']} minutes")
    print(f"Cache TTL: {status['cache_ttl_minutes']} minutes")
    print(f"Valid: {status['is_valid']}")
    
    print('\n=== Second call (should use cache) ===')
    models2 = await azure_manager.get_deployed_models()
    print(f'Retrieved {len(models2)} model categories')
    print(f'Same data: {models1 == models2}')
    
    status = azure_manager.get_models_cache_status()
    print(f"Cache age: {status['cache_age_minutes']} minutes")
    
    print('\n=== Force refresh ===')
    models3 = await azure_manager.get_deployed_models(force_refresh=True)
    print(f'Retrieved {len(models3)} model categories')
    
    status = azure_manager.get_models_cache_status()
    print(f"Cache age after refresh: {status['cache_age_minutes']} minutes")
    
    print('\n=== Invalidate cache ===')
    azure_manager.invalidate_models_cache()
    status = azure_manager.get_models_cache_status()
    print(f"Cached after invalidation: {status['cached']}")
    
    print('\n=== Set new TTL ===')
    azure_manager.set_models_cache_ttl(60)  # 1 hour
    status = azure_manager.get_models_cache_status()
    print(f"New TTL: {status['cache_ttl_minutes']} minutes")

if __name__ == "__main__":
    asyncio.run(test_cache())
