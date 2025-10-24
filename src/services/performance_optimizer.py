"""
Performance Optimization Service
Implements model quantization, caching, and latency optimizations for AgentGuard.

October 2025 Enhancement: Sub-50ms response times with intelligent caching.
"""

import logging
import asyncio
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
import redis
from functools import wraps, lru_cache
import pickle
import zlib

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for caching system."""
    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 3600  # 1 hour
    max_cache_size: int = 1000  # Max items in memory cache
    compression_threshold: int = 1024  # Compress items larger than 1KB
    enable_memory_cache: bool = True
    enable_redis_cache: bool = True


@dataclass
class OptimizationConfig:
    """Configuration for performance optimizations."""
    enable_quantization: bool = True
    quantization_bits: int = 8  # 8-bit quantization
    enable_model_caching: bool = True
    enable_result_caching: bool = True
    batch_size_optimization: bool = True
    memory_optimization: bool = True
    cpu_optimization: bool = True


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time_ms: float = 0.0
    quantized_model_speedup: float = 1.0
    memory_usage_mb: float = 0.0
    cpu_utilization: float = 0.0


class ModelQuantizer:
    """
    Model quantization for faster inference and reduced memory usage.
    
    Supports dynamic quantization for CPU and static quantization for production.
    """
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.quantized_models = {}
        
    def quantize_model(self, model: nn.Module, model_name: str) -> nn.Module:
        """
        Quantize a PyTorch model for faster inference.
        
        Args:
            model: PyTorch model to quantize
            model_name: Name for caching quantized model
            
        Returns:
            Quantized model
        """
        try:
            if not self.config.enable_quantization:
                return model
            
            # Check if already quantized
            if model_name in self.quantized_models:
                logger.info(f"Using cached quantized model: {model_name}")
                return self.quantized_models[model_name]
            
            logger.info(f"Quantizing model: {model_name} to {self.config.quantization_bits}-bit")
            
            # Dynamic quantization (good for CPU inference)
            if self.config.quantization_bits == 8:
                quantized_model = torch.quantization.quantize_dynamic(
                    model,
                    {nn.Linear, nn.Conv1d, nn.Conv2d},
                    dtype=torch.qint8
                )
            else:
                # For other bit widths, use post-training quantization
                model.eval()
                quantized_model = torch.quantization.quantize_dynamic(
                    model,
                    {nn.Linear},
                    dtype=torch.qint8
                )
            
            # Cache quantized model
            self.quantized_models[model_name] = quantized_model
            
            # Measure speedup
            speedup = self._measure_quantization_speedup(model, quantized_model)
            logger.info(f"Quantization speedup for {model_name}: {speedup:.2f}x")
            
            return quantized_model
            
        except Exception as e:
            logger.error(f"Model quantization error for {model_name}: {e}")
            return model  # Return original model on error

    def _measure_quantization_speedup(self, original_model: nn.Module, quantized_model: nn.Module) -> float:
        """Measure speedup from quantization."""
        try:
            # Create dummy input
            dummy_input = torch.randn(1, 512, 768)  # Typical transformer input
            
            # Warm up
            with torch.no_grad():
                original_model(dummy_input)
                quantized_model(dummy_input)
            
            # Measure original model
            start_time = time.time()
            with torch.no_grad():
                for _ in range(10):
                    original_model(dummy_input)
            original_time = time.time() - start_time
            
            # Measure quantized model
            start_time = time.time()
            with torch.no_grad():
                for _ in range(10):
                    quantized_model(dummy_input)
            quantized_time = time.time() - start_time
            
            speedup = original_time / quantized_time if quantized_time > 0 else 1.0
            return speedup
            
        except Exception as e:
            logger.error(f"Speedup measurement error: {e}")
            return 1.0


class IntelligentCache:
    """
    Multi-layer caching system with Redis and in-memory caching.
    
    Features:
    - LRU memory cache for hot data
    - Redis cache for persistence
    - Compression for large items
    - TTL-based expiration
    - Cache warming and preloading
    """
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.memory_cache = {}
        self.cache_access_times = {}
        self.redis_client = None
        
        # Initialize Redis connection
        if config.enable_redis_cache:
            try:
                import redis
                self.redis_client = redis.from_url(config.redis_url)
                self.redis_client.ping()  # Test connection
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis initialization failed: {e}")
                self.redis_client = None

    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        """Generate a consistent cache key from data."""
        try:
            # Create hash from data
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            
            hash_obj = hashlib.sha256(data_str.encode())
            return f"{prefix}:{hash_obj.hexdigest()[:16]}"
            
        except Exception as e:
            logger.error(f"Cache key generation error: {e}")
            return f"{prefix}:error_{int(time.time())}"

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data if it exceeds threshold."""
        if len(data) > self.config.compression_threshold:
            return zlib.compress(data)
        return data

    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data if it was compressed."""
        try:
            return zlib.decompress(data)
        except zlib.error:
            # Data wasn't compressed
            return data

    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache (memory first, then Redis)."""
        try:
            # Check memory cache first
            if self.config.enable_memory_cache and key in self.memory_cache:
                self.cache_access_times[key] = time.time()
                logger.debug(f"Memory cache hit: {key}")
                return self.memory_cache[key]
            
            # Check Redis cache
            if self.redis_client:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        # Decompress and deserialize
                        decompressed = self._decompress_data(data)
                        item = pickle.loads(decompressed)
                        
                        # Store in memory cache for next time
                        if self.config.enable_memory_cache:
                            self._store_in_memory(key, item)
                        
                        logger.debug(f"Redis cache hit: {key}")
                        return item
                except Exception as e:
                    logger.error(f"Redis get error for {key}: {e}")
            
            logger.debug(f"Cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set item in cache (both memory and Redis)."""
        try:
            ttl = ttl or self.config.default_ttl
            
            # Store in memory cache
            if self.config.enable_memory_cache:
                self._store_in_memory(key, value)
            
            # Store in Redis cache
            if self.redis_client:
                try:
                    # Serialize and compress
                    serialized = pickle.dumps(value)
                    compressed = self._compress_data(serialized)
                    
                    # Store with TTL
                    self.redis_client.setex(key, ttl, compressed)
                    logger.debug(f"Stored in Redis cache: {key}")
                    
                except Exception as e:
                    logger.error(f"Redis set error for {key}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False

    def _store_in_memory(self, key: str, value: Any):
        """Store item in memory cache with LRU eviction."""
        try:
            # Check if cache is full
            if len(self.memory_cache) >= self.config.max_cache_size:
                # Remove least recently used item
                lru_key = min(self.cache_access_times.keys(), 
                             key=lambda k: self.cache_access_times[k])
                del self.memory_cache[lru_key]
                del self.cache_access_times[lru_key]
            
            # Store new item
            self.memory_cache[key] = value
            self.cache_access_times[key] = time.time()
            
        except Exception as e:
            logger.error(f"Memory cache store error: {e}")

    async def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        try:
            # Clear from memory cache
            keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.memory_cache[key]
                if key in self.cache_access_times:
                    del self.cache_access_times[key]
            
            # Clear from Redis cache
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(f"*{pattern}*")
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.error(f"Redis invalidation error: {e}")
                    
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_max_size': self.config.max_cache_size,
            'redis_connected': self.redis_client is not None,
            'compression_threshold': self.config.compression_threshold,
            'default_ttl': self.config.default_ttl
        }


class PerformanceOptimizer:
    """
    Main performance optimization service.
    
    Coordinates model quantization, caching, and other optimizations
    to achieve sub-50ms response times.
    """
    
    def __init__(self, 
                 cache_config: Optional[CacheConfig] = None,
                 optimization_config: Optional[OptimizationConfig] = None):
        """
        Initialize performance optimizer.
        
        Args:
            cache_config: Caching configuration
            optimization_config: Optimization settings
        """
        self.cache_config = cache_config or CacheConfig()
        self.optimization_config = optimization_config or OptimizationConfig()
        
        # Initialize components
        self.cache = IntelligentCache(self.cache_config)
        self.quantizer = ModelQuantizer(self.optimization_config)
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.request_times = []
        
        logger.info("Performance optimizer initialized")

    def cache_result(self, cache_prefix: str, ttl: Optional[int] = None):
        """
        Decorator for caching function results.
        
        Args:
            cache_prefix: Prefix for cache keys
            ttl: Time to live in seconds
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_data = {'args': args, 'kwargs': kwargs}
                cache_key = self.cache._generate_cache_key(cache_prefix, cache_data)
                
                # Try to get from cache
                start_time = time.time()
                cached_result = await self.cache.get(cache_key)
                
                if cached_result is not None:
                    self.metrics.cache_hits += 1
                    response_time = (time.time() - start_time) * 1000
                    self._update_response_time(response_time)
                    logger.debug(f"Cache hit for {func.__name__}: {response_time:.2f}ms")
                    return cached_result
                
                # Cache miss - execute function
                self.metrics.cache_misses += 1
                result = await func(*args, **kwargs)
                
                # Store result in cache
                await self.cache.set(cache_key, result, ttl)
                
                response_time = (time.time() - start_time) * 1000
                self._update_response_time(response_time)
                logger.debug(f"Cache miss for {func.__name__}: {response_time:.2f}ms")
                
                return result
            
            return wrapper
        return decorator

    def optimize_model(self, model: nn.Module, model_name: str) -> nn.Module:
        """
        Apply all model optimizations.
        
        Args:
            model: PyTorch model to optimize
            model_name: Name for caching
            
        Returns:
            Optimized model
        """
        try:
            optimized_model = model
            
            # Apply quantization
            if self.optimization_config.enable_quantization:
                optimized_model = self.quantizer.quantize_model(optimized_model, model_name)
            
            # Set to evaluation mode
            optimized_model.eval()
            
            # Enable CPU optimizations
            if self.optimization_config.cpu_optimization:
                torch.set_num_threads(torch.get_num_threads())  # Use all available threads
            
            logger.info(f"Model optimization complete for {model_name}")
            return optimized_model
            
        except Exception as e:
            logger.error(f"Model optimization error for {model_name}: {e}")
            return model

    async def warm_cache(self, warm_up_data: List[Dict[str, Any]]):
        """
        Warm up cache with common requests.
        
        Args:
            warm_up_data: List of common request patterns to pre-cache
        """
        try:
            logger.info(f"Warming cache with {len(warm_up_data)} items")
            
            for item in warm_up_data:
                cache_key = self.cache._generate_cache_key("warmup", item)
                # Store dummy result for warming
                await self.cache.set(cache_key, {"warmed": True}, ttl=3600)
            
            logger.info("Cache warming complete")
            
        except Exception as e:
            logger.error(f"Cache warming error: {e}")

    def _update_response_time(self, response_time_ms: float):
        """Update response time metrics."""
        self.metrics.total_requests += 1
        self.request_times.append(response_time_ms)
        
        # Keep only recent requests for moving average
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
        
        # Update average
        self.metrics.avg_response_time_ms = np.mean(self.request_times)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        cache_hit_rate = (
            self.metrics.cache_hits / (self.metrics.cache_hits + self.metrics.cache_misses)
            if (self.metrics.cache_hits + self.metrics.cache_misses) > 0 else 0.0
        )
        
        return {
            'total_requests': self.metrics.total_requests,
            'cache_hit_rate': cache_hit_rate,
            'cache_hits': self.metrics.cache_hits,
            'cache_misses': self.metrics.cache_misses,
            'avg_response_time_ms': self.metrics.avg_response_time_ms,
            'quantized_models': len(self.quantizer.quantized_models),
            'quantization_enabled': self.optimization_config.enable_quantization,
            'cache_stats': self.cache.get_stats(),
            'p95_response_time_ms': np.percentile(self.request_times, 95) if self.request_times else 0.0,
            'p99_response_time_ms': np.percentile(self.request_times, 99) if self.request_times else 0.0,
        }

    async def optimize_batch_processing(self, 
                                      items: List[Any], 
                                      process_func: callable,
                                      optimal_batch_size: int = 8) -> List[Any]:
        """
        Optimize batch processing with dynamic batch sizing.
        
        Args:
            items: Items to process
            process_func: Function to process each batch
            optimal_batch_size: Starting batch size
            
        Returns:
            List of processed results
        """
        try:
            if not self.optimization_config.batch_size_optimization:
                # Process individually
                results = []
                for item in items:
                    result = await process_func([item])
                    results.extend(result)
                return results
            
            # Process in optimized batches
            results = []
            batch_size = optimal_batch_size
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                start_time = time.time()
                batch_results = await process_func(batch)
                processing_time = time.time() - start_time
                
                results.extend(batch_results)
                
                # Adjust batch size based on performance
                if processing_time > 0.1:  # If batch takes >100ms
                    batch_size = max(1, batch_size // 2)
                elif processing_time < 0.05:  # If batch takes <50ms
                    batch_size = min(32, batch_size * 2)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch optimization error: {e}")
            # Fallback to individual processing
            results = []
            for item in items:
                result = await process_func([item])
                results.extend(result)
            return results

    async def cleanup_cache(self, max_age_hours: int = 24):
        """Clean up old cache entries."""
        try:
            # This would typically involve Redis SCAN and TTL checking
            # For now, we'll just clear memory cache of old items
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            old_keys = [
                key for key, access_time in self.cache.cache_access_times.items()
                if current_time - access_time > max_age_seconds
            ]
            
            for key in old_keys:
                if key in self.cache.memory_cache:
                    del self.cache.memory_cache[key]
                if key in self.cache.cache_access_times:
                    del self.cache.cache_access_times[key]
            
            logger.info(f"Cleaned up {len(old_keys)} old cache entries")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")


# Global performance optimizer instance
_performance_optimizer = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get or create performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


# Convenience decorators
def cache_result(cache_prefix: str, ttl: Optional[int] = None):
    """Convenience decorator for caching results."""
    optimizer = get_performance_optimizer()
    return optimizer.cache_result(cache_prefix, ttl)


if __name__ == "__main__":
    # Example usage
    async def test_performance_optimizer():
        optimizer = PerformanceOptimizer()
        
        # Test caching
        @optimizer.cache_result("test", ttl=300)
        async def expensive_function(x: int) -> int:
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x * 2
        
        # First call - cache miss
        start = time.time()
        result1 = await expensive_function(5)
        time1 = time.time() - start
        
        # Second call - cache hit
        start = time.time()
        result2 = await expensive_function(5)
        time2 = time.time() - start
        
        print(f"First call: {result1} in {time1*1000:.2f}ms")
        print(f"Second call: {result2} in {time2*1000:.2f}ms")
        print(f"Speedup: {time1/time2:.2f}x")
        
        # Print metrics
        metrics = optimizer.get_performance_metrics()
        print(f"Performance metrics: {json.dumps(metrics, indent=2)}")
    
    # Run test
    # asyncio.run(test_performance_optimizer())
