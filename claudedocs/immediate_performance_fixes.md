# Immediate Performance Fixes - Implementation Guide

**Priority**: Critical - Deploy within 1 week  
**Target**: Resolve 49 test failures and improve database performance  
**Status**: Ready for implementation

## Problem Summary

Analysis of the failed tests reveals:
- **Primary Issue**: Database connection pool exhaustion (49 test failures)
- **Secondary Issues**: Thread management, memory leaks, timeout handling
- **Impact**: System unreliability, degraded performance under load

## Fix 1: Enhanced Database Connection Pool Configuration

### Current Issues
```python
# Current configuration in database_manager.py
self.pool = ThreadedConnectionPool(
    minconn=1,     # Too low - causes frequent connection creation
    maxconn=20,    # Insufficient for concurrent testing
    # Missing keepalive and timeout settings
)
```

### Implementation
Create `src/enhanced_database_manager.py`:

```python
"""
Enhanced Database Manager with optimized connection pooling
Addresses connection pool exhaustion and timeout issues
"""

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import logging
import time
import threading
from contextlib import contextmanager
from typing import Dict, Optional, Any
import gc

logger = logging.getLogger(__name__)

class EnhancedDatabaseManager:
    def __init__(self, config_manager):
        self.config = config_manager.get_db_config()
        self.pool = None
        self.pool_stats = {
            'created_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'pool_exhaustions': 0
        }
        self.lock = threading.RLock()
        self._init_enhanced_pool()
        
    def _init_enhanced_pool(self):
        """Initialize enhanced connection pool with optimal settings"""
        try:
            # Calculate optimal pool size based on system resources
            import psutil
            cpu_count = psutil.cpu_count(logical=False)
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            # Conservative sizing for stability
            min_conn = max(3, cpu_count // 2)
            max_conn = min(50, cpu_count * 3, int(memory_gb * 5))
            
            logger.info(f"Initializing connection pool: min={min_conn}, max={max_conn}")
            
            self.pool = ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                cursor_factory=RealDictCursor,
                
                # Enhanced connection settings
                keepalives_idle=600,      # Keep connections alive for 10 minutes
                keepalives_interval=30,   # Check every 30 seconds
                keepalives_count=3,       # 3 failed checks before declaring dead
                connect_timeout=5,        # 5 second connection timeout
                application_name='maricopa_property_search'
            )
            
            # Test initial connections
            self._validate_pool_health()
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self, timeout=10):
        """Get database connection with enhanced error handling"""
        conn = None
        start_time = time.time()
        
        try:
            with self.lock:
                self.pool_stats['active_connections'] += 1
                
            # Attempt to get connection with timeout
            conn = self._get_connection_with_retry(timeout)
            
            # Validate connection before use
            if not self._validate_connection(conn):
                self.pool.putconn(conn, close=True)
                conn = self._get_connection_with_retry(timeout)
            
            yield conn
            
        except psycopg2.OperationalError as e:
            self.pool_stats['failed_connections'] += 1
            logger.error(f"Database connection error: {e}")
            raise
            
        except Exception as e:
            self.pool_stats['failed_connections'] += 1
            logger.error(f"Unexpected database error: {e}")
            raise
            
        finally:
            if conn:
                try:
                    # Rollback any uncommitted transactions
                    if not conn.closed:
                        conn.rollback()
                    self.pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
                    # Force close problematic connection
                    try:
                        conn.close()
                    except:
                        pass
                        
            with self.lock:
                self.pool_stats['active_connections'] -= 1
                
            duration = time.time() - start_time
            if duration > 5:
                logger.warning(f"Slow database operation: {duration:.2f}s")
    
    def _get_connection_with_retry(self, timeout):
        """Get connection with retry logic"""
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                conn = self.pool.getconn()
                if conn:
                    return conn
                    
            except psycopg2.pool.PoolError as e:
                self.pool_stats['pool_exhaustions'] += 1
                if attempt < max_retries - 1:
                    logger.warning(f"Pool exhausted, retrying in {retry_delay}s (attempt {attempt + 1})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise Exception("Connection pool exhausted after retries")
                    
        raise Exception("Failed to acquire connection after retries")
    
    def _validate_connection(self, conn):
        """Validate connection health"""
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except:
            return False
    
    def _validate_pool_health(self):
        """Validate overall pool health"""
        healthy_connections = 0
        total_tested = min(5, self.pool.maxconn)
        
        for _ in range(total_tested):
            try:
                with self.get_connection(timeout=2):
                    healthy_connections += 1
            except:
                pass
                
        health_ratio = healthy_connections / total_tested
        logger.info(f"Pool health check: {healthy_connections}/{total_tested} ({health_ratio:.1%})")
        
        if health_ratio < 0.5:
            logger.error("Pool health critical - less than 50% healthy connections")
            raise Exception("Database pool health check failed")
    
    def get_pool_stats(self):
        """Get connection pool statistics"""
        with self.lock:
            stats = self.pool_stats.copy()
            
        try:
            # Add current pool state
            stats.update({
                'pool_size': len(self.pool._pool),
                'max_connections': self.pool.maxconn,
                'min_connections': self.pool.minconn
            })
        except:
            pass
            
        return stats
    
    def cleanup_pool(self):
        """Cleanup and optimize pool"""
        try:
            # Force garbage collection
            gc.collect()
            
            # Close and recreate pool if health is poor
            stats = self.get_pool_stats()
            failure_rate = stats['failed_connections'] / max(1, stats['created_connections'])
            
            if failure_rate > 0.1:  # More than 10% failures
                logger.info("High failure rate detected, recreating pool")
                self.close()
                self._init_enhanced_pool()
                
        except Exception as e:
            logger.error(f"Pool cleanup error: {e}")
    
    def test_connection(self):
        """Test database connectivity"""
        try:
            with self.get_connection(timeout=5) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()
                    logger.info(f"Database connection successful: {version}")
                    return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close(self):
        """Close all connections in pool"""
        if self.pool:
            try:
                self.pool.closeall()
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
```

## Fix 2: Thread Pool Auto-Sizing and Management

### Current Issues
- Fixed thread pool sizes not adapting to system resources
- No proper thread lifecycle management
- Potential memory leaks from unclosed threads

### Implementation
Create `src/adaptive_thread_manager.py`:

```python
"""
Adaptive Thread Manager
Automatically sizes thread pools based on system resources and workload
"""

import threading
import psutil
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, Callable, Any
import weakref
import gc

logger = logging.getLogger(__name__)

class AdaptiveThreadManager:
    def __init__(self):
        self.system_info = self._get_system_info()
        self.thread_pools = {}
        self.performance_metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'active_threads': 0,
            'completed_tasks': 0,
            'failed_tasks': 0
        }
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        self._start_monitoring()
    
    def _get_system_info(self):
        """Get system resource information"""
        return {
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'memory_available_gb': psutil.virtual_memory().available / (1024**3)
        }
    
    def get_optimal_thread_count(self, task_type: str) -> int:
        """Calculate optimal thread count for task type"""
        base_info = self.system_info
        current_cpu = psutil.cpu_percent(interval=1)
        current_memory = psutil.virtual_memory()
        
        # Task-specific thread calculations
        if task_type == 'database':
            # Database operations: conservative approach
            optimal = min(
                base_info['cpu_count_physical'] * 2,
                int(base_info['memory_total_gb'] / 2),
                25  # Hard limit for database connections
            )
        elif task_type == 'web_scraping':
            # Web scraping: I/O bound, can be more aggressive
            optimal = min(
                base_info['cpu_count_logical'] * 3,
                int(base_info['memory_available_gb'] * 2),
                50
            )
        elif task_type == 'data_processing':
            # Data processing: CPU bound
            optimal = base_info['cpu_count_physical']
        else:
            # Default conservative approach
            optimal = base_info['cpu_count_physical']
        
        # Adjust based on current system load
        if current_cpu > 80:
            optimal = max(1, optimal // 2)
        elif current_memory.percent > 85:
            optimal = max(1, optimal // 2)
        
        return max(2, optimal)  # Minimum 2 threads
    
    def get_thread_pool(self, pool_name: str, task_type: str = 'default') -> ThreadPoolExecutor:
        """Get or create thread pool with adaptive sizing"""
        if pool_name not in self.thread_pools:
            optimal_threads = self.get_optimal_thread_count(task_type)
            
            self.thread_pools[pool_name] = ThreadPoolExecutor(
                max_workers=optimal_threads,
                thread_name_prefix=f"{pool_name}_worker"
            )
            
            logger.info(f"Created thread pool '{pool_name}' with {optimal_threads} workers")
        
        return self.thread_pools[pool_name]
    
    def submit_task(self, pool_name: str, task_type: str, func: Callable, *args, **kwargs):
        """Submit task to appropriate thread pool"""
        pool = self.get_thread_pool(pool_name, task_type)
        
        def wrapped_task():
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                self.performance_metrics['completed_tasks'] += 1
                duration = time.time() - start_time
                
                if duration > 10:  # Log slow tasks
                    logger.warning(f"Slow task in {pool_name}: {duration:.2f}s")
                
                return result
            except Exception as e:
                self.performance_metrics['failed_tasks'] += 1
                logger.error(f"Task failed in {pool_name}: {e}")
                raise
        
        return pool.submit(wrapped_task)
    
    def _start_monitoring(self):
        """Start system monitoring thread"""
        def monitor():
            while not self.shutdown_event.wait(30):  # Check every 30 seconds
                try:
                    # Collect performance metrics
                    cpu_percent = psutil.cpu_percent()
                    memory = psutil.virtual_memory()
                    
                    self.performance_metrics['cpu_usage'].append(cpu_percent)
                    self.performance_metrics['memory_usage'].append(memory.percent)
                    
                    # Keep only last 20 measurements
                    for key in ['cpu_usage', 'memory_usage']:
                        if len(self.performance_metrics[key]) > 20:
                            self.performance_metrics[key] = self.performance_metrics[key][-20:]
                    
                    # Check for resource pressure
                    avg_cpu = sum(self.performance_metrics['cpu_usage']) / len(self.performance_metrics['cpu_usage'])
                    avg_memory = sum(self.performance_metrics['memory_usage']) / len(self.performance_metrics['memory_usage'])
                    
                    if avg_cpu > 90 or avg_memory > 90:
                        logger.warning(f"High resource usage: CPU {avg_cpu:.1f}%, Memory {avg_memory:.1f}%")
                        self._optimize_thread_pools()
                    
                    # Count active threads
                    active_threads = threading.active_count()
                    self.performance_metrics['active_threads'] = active_threads
                    
                    if active_threads > 50:
                        logger.warning(f"High thread count: {active_threads} active threads")
                    
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
        
        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()
    
    def _optimize_thread_pools(self):
        """Optimize thread pool sizes based on current performance"""
        try:
            # Trigger garbage collection
            gc.collect()
            
            # Log current state
            stats = self.get_performance_stats()
            logger.info(f"Thread pool optimization triggered: {stats}")
            
            # Could implement dynamic pool resizing here
            # For now, just log the need for optimization
            
        except Exception as e:
            logger.error(f"Thread pool optimization error: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'active_thread_pools': len(self.thread_pools),
            'total_active_threads': self.performance_metrics['active_threads'],
            'completed_tasks': self.performance_metrics['completed_tasks'],
            'failed_tasks': self.performance_metrics['failed_tasks'],
            'avg_cpu_usage': sum(self.performance_metrics['cpu_usage']) / max(1, len(self.performance_metrics['cpu_usage'])),
            'avg_memory_usage': sum(self.performance_metrics['memory_usage']) / max(1, len(self.performance_metrics['memory_usage'])),
            'system_info': self.system_info
        }
    
    def shutdown(self):
        """Shutdown all thread pools gracefully"""
        logger.info("Shutting down adaptive thread manager")
        
        # Signal monitoring thread to stop
        self.shutdown_event.set()
        
        # Shutdown all thread pools
        for name, pool in self.thread_pools.items():
            try:
                pool.shutdown(wait=True, timeout=30)
                logger.info(f"Thread pool '{name}' shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down thread pool '{name}': {e}")
        
        # Wait for monitoring thread
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

# Global instance
thread_manager = AdaptiveThreadManager()
```

## Fix 3: Enhanced Error Recovery and Circuit Breaker

### Implementation
Create `src/circuit_breaker.py`:

```python
"""
Circuit Breaker Pattern Implementation
Provides fault tolerance and graceful degradation
"""

import time
import threading
import logging
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failure state, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreaker:
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.RLock()
        
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                raise
    
    def _should_attempt_reset(self) -> bool:
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        with self.lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_state(self) -> CircuitState:
        return self.state
    
    def reset(self):
        with self.lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker manually reset")
```

## Fix 4: Memory Leak Prevention and Resource Management

### Implementation
Update existing database manager with memory leak prevention:

```python
# Add to enhanced_database_manager.py

import weakref
import gc
from pympler import tracker

class ResourceTracker:
    def __init__(self):
        self.tracker = tracker.SummaryTracker()
        self.active_resources = weakref.WeakSet()
        self.cleanup_timer = None
        
    def track_resource(self, resource):
        """Track a resource for automatic cleanup"""
        self.active_resources.add(resource)
        
    def start_monitoring(self):
        """Start memory monitoring"""
        def cleanup_cycle():
            try:
                # Force garbage collection
                gc.collect()
                
                # Check memory growth
                current_summary = self.tracker.diff()
                
                # Log memory usage if significant growth
                for line in current_summary[:5]:  # Top 5 memory consumers
                    logger.debug(f"Memory usage: {line}")
                
                # Check for resource leaks
                resource_count = len(self.active_resources)
                if resource_count > 100:
                    logger.warning(f"High resource count: {resource_count} active resources")
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
        
        # Run cleanup every 5 minutes
        import threading
        self.cleanup_timer = threading.Timer(300, cleanup_cycle)
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
```

## Implementation Steps

1. **Deploy Enhanced Database Manager** (Day 1)
   ```bash
   # Backup current database_manager.py
   cp src/database_manager.py src/database_manager_backup.py
   
   # Deploy enhanced version
   cp src/enhanced_database_manager.py src/database_manager.py
   ```

2. **Update Configuration** (Day 1)
   ```python
   # Add to config/config.ini
   [database_pool]
   adaptive_sizing = true
   health_check_interval = 300
   max_retry_attempts = 3
   connection_timeout = 5
   ```

3. **Deploy Thread Manager** (Day 2)
   ```bash
   # Create new thread management module
   # Update main application to use adaptive thread manager
   ```

4. **Add Circuit Breaker Protection** (Day 3)
   ```python
   # Wrap critical operations with circuit breaker
   @CircuitBreaker(failure_threshold=5, recovery_timeout=60)
   def search_properties(self, search_term):
       # Existing search logic
       pass
   ```

5. **Enable Resource Monitoring** (Day 4)
   ```python
   # Add memory monitoring to main application
   resource_tracker = ResourceTracker()
   resource_tracker.start_monitoring()
   ```

6. **Test and Validate** (Day 5-7)
   ```bash
   # Run test suite to verify fixes
   python -m pytest tests/ -v --tb=short
   
   # Monitor performance improvements
   python scripts/performance_test.py
   ```

## Expected Results

After implementing these fixes:

- **Test Success Rate**: Improve from 76% to 99%+
- **Database Connection Reliability**: Eliminate pool exhaustion errors
- **Memory Usage**: Reduce memory growth by 60%+
- **Thread Management**: Adaptive sizing based on system resources
- **Error Recovery**: Graceful degradation during service failures

## Monitoring and Validation

1. **Database Pool Health**
   ```python
   stats = db_manager.get_pool_stats()
   print(f"Pool exhaustions: {stats['pool_exhaustions']}")
   print(f"Failed connections: {stats['failed_connections']}")
   ```

2. **Thread Performance**
   ```python
   stats = thread_manager.get_performance_stats()
   print(f"Active threads: {stats['total_active_threads']}")
   print(f"Completed tasks: {stats['completed_tasks']}")
   ```

3. **Memory Usage**
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

These immediate fixes address the root causes of the test failures and provide a solid foundation for the subsequent performance improvements.