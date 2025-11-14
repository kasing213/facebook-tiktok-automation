#!/usr/bin/env python3
"""
Example usage of the rate limiting module.

This file demonstrates how to use the various rate limiters
for different scenarios and platforms.
"""
import asyncio
import httpx
from app.core.rate_limit import (
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    CompositeRateLimiter,
    PlatformRateLimiters,
)


async def example_token_bucket():
    """Example: Using token bucket for bursty API calls."""
    print("\n=== Token Bucket Example ===")

    # Allow 100 requests per minute, with burst capacity of 20
    limiter = TokenBucketRateLimiter(
        max_requests=100,
        time_window=60,
        burst_size=20
    )

    # Make rapid requests (will use burst capacity)
    for i in range(5):
        async with limiter:
            print(f"Request {i+1} - Available tokens: {limiter.get_available_tokens():.2f}")
            # Your API call here
            await asyncio.sleep(0.1)  # Simulate API call


async def example_sliding_window():
    """Example: Using sliding window for strict rate limiting."""
    print("\n=== Sliding Window Example ===")

    # Allow exactly 10 requests per minute
    limiter = SlidingWindowRateLimiter(
        max_requests=10,
        time_window=60
    )

    # Make requests
    for i in range(5):
        async with limiter:
            remaining = limiter.get_remaining_requests()
            print(f"Request {i+1} - Remaining: {remaining}")
            # Your API call here
            await asyncio.sleep(0.1)


async def example_facebook_api():
    """Example: Using Facebook Graph API rate limiter."""
    print("\n=== Facebook API Example ===")

    limiter = PlatformRateLimiters.facebook_graph_api()

    # Simulate making Facebook API calls
    async with httpx.AsyncClient() as client:
        for i in range(5):
            async with limiter:
                print(f"Making Facebook API call {i+1}...")
                # Example: Get user profile
                # response = await client.get(
                #     f"https://graph.facebook.com/v18.0/me",
                #     params={"access_token": "YOUR_TOKEN"}
                # )
                await asyncio.sleep(0.1)


async def example_tiktok_api():
    """Example: Using TikTok API rate limiter."""
    print("\n=== TikTok API Example ===")

    limiter = PlatformRateLimiters.tiktok_api()

    # Simulate making TikTok API calls
    async with httpx.AsyncClient() as client:
        for i in range(5):
            async with limiter:
                print(f"Making TikTok API call {i+1}...")
                # Example: Get user info
                # response = await client.get(
                #     "https://open-api.tiktok.com/user/info/",
                #     headers={"Authorization": f"Bearer {access_token}"}
                # )
                await asyncio.sleep(0.1)


async def example_custom_multi_tier():
    """Example: Custom multi-tier rate limiting."""
    print("\n=== Multi-Tier Rate Limiting Example ===")

    # Create a custom limiter with multiple tiers
    limiter = CompositeRateLimiter([
        SlidingWindowRateLimiter(max_requests=5, time_window=1),      # 5 per second
        SlidingWindowRateLimiter(max_requests=100, time_window=60),   # 100 per minute
        TokenBucketRateLimiter(max_requests=1000, time_window=3600, burst_size=50),  # 1000/hr with burst
    ])

    print("Making 10 requests with multi-tier limiting...")
    for i in range(10):
        async with limiter:
            print(f"Request {i+1} completed")
            await asyncio.sleep(0.3)  # Space out requests


async def example_manual_acquire():
    """Example: Manual token acquisition (without context manager)."""
    print("\n=== Manual Acquisition Example ===")

    limiter = SlidingWindowRateLimiter(max_requests=3, time_window=1)

    # Try to acquire without waiting
    for i in range(5):
        if await limiter.acquire():
            print(f"Request {i+1}: Acquired successfully")
        else:
            print(f"Request {i+1}: Rate limit exceeded, waiting...")
            await limiter.wait_for_slot()
            print(f"Request {i+1}: Acquired after waiting")


async def main():
    """Run all examples."""
    print("Rate Limiter Examples")
    print("=" * 50)

    await example_token_bucket()
    await example_sliding_window()
    await example_facebook_api()
    await example_tiktok_api()
    await example_custom_multi_tier()
    await example_manual_acquire()

    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
