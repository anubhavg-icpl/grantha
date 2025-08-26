"""Performance configuration and utilities for the Grantha application."""

import os
from typing import Dict, Tuple, List
from dataclasses import dataclass


@dataclass 
class PerformanceConfig:
    """Performance configuration settings."""
    
    # Rate limiting settings
    default_rate_limit: int = 100  # requests per minute
    default_window: int = 60  # seconds
    
    # Endpoint-specific rate limits (endpoint: (limit, window))
    rate_limits: Dict[str, Tuple[int, int]] = None
    
    # Caching settings  
    cache_max_size: int = 1000
    cache_default_ttl: int = 300  # 5 minutes
    
    # Endpoint-specific cache settings (endpoint: (ttl, methods))
    cache_config: Dict[str, Tuple[int, List[str]]] = None
    
    # Logging settings
    log_requests: bool = True
    log_request_body: bool = False
    log_response_body: bool = False
    log_slow_requests: bool = True
    slow_request_threshold: float = 2.0  # seconds
    
    def __post_init__(self):
        """Initialize default configurations."""
        if self.rate_limits is None:
            self.rate_limits = {
                '/chat': (20, 60),      # 20 requests per minute
                '/wiki': (50, 60),      # 50 requests per minute  
                '/research': (10, 60),  # 10 requests per minute
                '/models': (30, 60),    # 30 requests per minute
                '/auth': (10, 300),     # 10 requests per 5 minutes
            }
            
        if self.cache_config is None:
            self.cache_config = {
                '/models': (600, ['GET']),        # 10 minutes
                '/wiki/search': (300, ['GET']),   # 5 minutes
                '/health': (60, ['GET']),         # 1 minute
                '/': (3600, ['GET']),             # 1 hour
                '/metrics': (30, ['GET']),        # 30 seconds
            }


def get_performance_config() -> PerformanceConfig:
    """Get performance configuration from environment variables."""
    
    config = PerformanceConfig()
    
    # Override from environment
    config.default_rate_limit = int(os.getenv('RATE_LIMIT_DEFAULT', config.default_rate_limit))
    config.default_window = int(os.getenv('RATE_LIMIT_WINDOW', config.default_window))
    
    config.cache_max_size = int(os.getenv('CACHE_MAX_SIZE', config.cache_max_size))
    config.cache_default_ttl = int(os.getenv('CACHE_DEFAULT_TTL', config.cache_default_ttl))
    
    config.log_requests = os.getenv('LOG_REQUESTS', 'true').lower() == 'true'
    config.log_request_body = os.getenv('LOG_REQUEST_BODY', 'false').lower() == 'true'
    config.log_response_body = os.getenv('LOG_RESPONSE_BODY', 'false').lower() == 'true'
    config.log_slow_requests = os.getenv('LOG_SLOW_REQUESTS', 'true').lower() == 'true'
    config.slow_request_threshold = float(os.getenv('SLOW_REQUEST_THRESHOLD', config.slow_request_threshold))
    
    return config


# Performance monitoring utilities
class PerformanceTracker:
    """Track performance metrics across the application."""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.slow_request_count = 0
        self.total_response_time = 0.0
        self.endpoint_stats = {}
    
    def track_request(self, endpoint: str, duration: float, status_code: int):
        """Track request metrics."""
        self.request_count += 1
        self.total_response_time += duration
        
        if status_code >= 400:
            self.error_count += 1
            
        if duration > 2.0:  # Slow request threshold
            self.slow_request_count += 1
        
        # Track per-endpoint stats
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {
                'count': 0,
                'total_time': 0.0,
                'errors': 0,
                'slow_requests': 0
            }
        
        stats = self.endpoint_stats[endpoint]
        stats['count'] += 1
        stats['total_time'] += duration
        
        if status_code >= 400:
            stats['errors'] += 1
        if duration > 2.0:
            stats['slow_requests'] += 1
    
    def get_metrics(self) -> Dict:
        """Get current performance metrics."""
        avg_response_time = (self.total_response_time / self.request_count 
                           if self.request_count > 0 else 0)
        
        error_rate = (self.error_count / self.request_count * 100 
                     if self.request_count > 0 else 0)
        
        slow_request_rate = (self.slow_request_count / self.request_count * 100
                           if self.request_count > 0 else 0)
        
        # Calculate per-endpoint metrics
        endpoint_metrics = {}
        for endpoint, stats in self.endpoint_stats.items():
            endpoint_metrics[endpoint] = {
                'requests': stats['count'],
                'avg_response_time': stats['total_time'] / stats['count'] if stats['count'] > 0 else 0,
                'error_rate': stats['errors'] / stats['count'] * 100 if stats['count'] > 0 else 0,
                'slow_request_rate': stats['slow_requests'] / stats['count'] * 100 if stats['count'] > 0 else 0
            }
        
        return {
            'total_requests': self.request_count,
            'error_count': self.error_count,
            'slow_request_count': self.slow_request_count,
            'avg_response_time_ms': round(avg_response_time * 1000, 2),
            'error_rate_percent': round(error_rate, 2),
            'slow_request_rate_percent': round(slow_request_rate, 2),
            'endpoints': endpoint_metrics
        }
    
    def reset(self):
        """Reset all metrics."""
        self.request_count = 0
        self.error_count = 0
        self.slow_request_count = 0
        self.total_response_time = 0.0
        self.endpoint_stats.clear()


# Global performance tracker instance
_performance_tracker = PerformanceTracker()

def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker instance."""
    return _performance_tracker