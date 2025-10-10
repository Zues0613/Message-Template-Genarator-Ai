"""
Standalone Usage Example
========================

This example shows how to use the MessageTemplateGenerator
programmatically in your Python code, without FastAPI.

Usage:
    python examples/standalone_usage.py
"""

import asyncio
from message_template_component import MessageTemplateGenerator, ComponentConfig


async def basic_usage():
    """Basic usage with context manager."""
    print("\n=== Basic Usage ===")
    
    # Create configuration
    config = ComponentConfig.from_env()
    
    # Use as context manager (automatically handles initialization and cleanup)
    async with MessageTemplateGenerator(config) as generator:
        result = await generator.generate(
            prompt="Birthday wishes for premium customers",
            tone="formal",
            length="medium"
        )
        
        print(f"Success: {result['source'] != 'error'}")
        print(f"Message: {result['message']}")
        print(f"Source: {result['source']}")
        if result['error']:
            print(f"Error: {result['error']}")


async def manual_lifecycle():
    """Manual initialization and cleanup."""
    print("\n=== Manual Lifecycle ===")
    
    config = ComponentConfig(
        api_key="your-api-key",  # Or use from_env()
        model="deepseek/deepseek-r1-0528",
        temperature=0.7
    )
    
    generator = MessageTemplateGenerator(config)
    
    # Initialize manually
    await generator.initialize()
    
    try:
        # Generate multiple messages
        prompts = [
            "Diwali greetings",
            "New year wishes",
            "Product launch announcement"
        ]
        
        for prompt in prompts:
            result = await generator.generate(
                prompt=prompt,
                tone="informal",
                length="short"
            )
            print(f"\nPrompt: {prompt}")
            print(f"Message: {result['message']}")
    
    finally:
        # Cleanup manually
        await generator.cleanup()


async def advanced_usage():
    """Advanced usage with custom configuration."""
    print("\n=== Advanced Usage ===")
    
    config = ComponentConfig(
        api_key="your-api-key",
        model="deepseek/deepseek-r1-0528",
        temperature=0.6,
        max_tokens=1500,
        system_prompt="You are a professional marketing copywriter...",
        enable_fallback_templates=True
    )
    
    async with MessageTemplateGenerator(config) as generator:
        # Generate with custom placeholders
        result = await generator.generate(
            prompt="Exclusive discount offer for VIP members",
            tone="formal",
            length="medium",
            placeholders="name,discount,code,expiry",
            audience="VIP members who made purchases in last 30 days"
        )
        
        print(f"Message: {result['message']}")
        print(f"Metadata: {result['metadata']}")


async def batch_generation():
    """Generate multiple messages in batch."""
    print("\n=== Batch Generation ===")
    
    config = ComponentConfig.from_env()
    
    async with MessageTemplateGenerator(config) as generator:
        messages_to_generate = [
            {
                "prompt": "Welcome message for new customers",
                "tone": "informal",
                "length": "short"
            },
            {
                "prompt": "Follow-up after purchase",
                "tone": "formal",
                "length": "medium"
            },
            {
                "prompt": "Re-engagement for inactive users",
                "tone": "informal",
                "length": "medium",
                "audience": "Users inactive for 60+ days"
            }
        ]
        
        results = []
        for params in messages_to_generate:
            result = await generator.generate(**params)
            results.append(result)
            
            print(f"\nPrompt: {params['prompt']}")
            print(f"Message: {result['message'][:100]}...")
        
        # Summary
        success_count = sum(1 for r in results if r['source'] != 'error')
        print(f"\n✅ Successfully generated {success_count}/{len(results)} messages")


async def error_handling():
    """Example of error handling."""
    print("\n=== Error Handling ===")
    
    # Invalid configuration (will fail validation)
    try:
        config = ComponentConfig(
            api_key=None,  # No API key
            enable_fallback_templates=False  # No fallback
        )
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
    
    # Generate with fallback
    config = ComponentConfig.from_env()
    config.enable_fallback_templates = True
    
    async with MessageTemplateGenerator(config) as generator:
        # Even if AI fails, we get a fallback
        result = await generator.generate(
            prompt="Birthday wishes",
            tone="informal"
        )
        
        print(f"Message: {result['message']}")
        print(f"Source: {result['source']}")


async def main():
    """Run all examples."""
    print("🚀 Message Template Generator - Standalone Usage Examples")
    print("=" * 60)
    
    # Check if API key is set
    import os
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\n⚠️  WARNING: OPENROUTER_API_KEY not found in environment!")
        print("Set it in your .env file or export it:")
        print("export OPENROUTER_API_KEY='your-key-here'\n")
    
    try:
        # Run examples
        await basic_usage()
        # await manual_lifecycle()
        # await advanced_usage()
        # await batch_generation()
        # await error_handling()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

