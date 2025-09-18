"""
Hook Integration Module
Provides integration points for the Maricopa Property Search application
"""

import asyncio
import functools
import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

from hook_manager import get_hook_manager, emit_hook, emit_hook_async
from logging_config import get_logger

logger = get_logger(__name__)


class HookIntegration:
    """Main integration class for hooks in the application"""

    def __init__(self):
        self.hook_manager = get_hook_manager()
        self.integration_enabled = True
        self._session_id = None

    def enable_integration(self):
        """Enable hook integration"""
        self.integration_enabled = True
        logger.info("Hook integration enabled")

    def disable_integration(self):
        """Disable hook integration"""
        self.integration_enabled = False
        logger.info("Hook integration disabled")

    def set_session_id(self, session_id: str):
        """Set current session ID for tracking"""
        self._session_id = session_id

    @contextmanager
    def application_lifecycle(self, config_manager=None, database_manager=None, project_root=None):
        """Context manager for application lifecycle hooks"""
        if not self.integration_enabled:
            yield
            return

        try:
            # Trigger startup
            emit_hook(
                'application.startup',
                'hook_integration',
                config_manager=config_manager,
                database_manager=database_manager,
                project_root=project_root
            )
            yield

        finally:
            # Trigger shutdown
            emit_hook(
                'application.shutdown',
                'hook_integration',
                database_manager=database_manager
            )

    @contextmanager
    def search_operation(self, search_type: str, search_term: str, **kwargs):
        """Context manager for search operation hooks"""
        if not self.integration_enabled:
            yield
            return

        results = []
        error = None
        start_time = time.time()

        try:
            # Pre-search hooks
            pre_results = emit_hook(
                'search.before',
                'search_operation',
                search_type=search_type,
                search_term=search_term,
                **kwargs
            )

            # Check for validation failures
            for result in pre_results:
                if result.status.value == 'failed' and 'validation_errors' in result.metadata:
                    raise ValueError(f"Search validation failed: {result.metadata['validation_errors']}")

            yield results

        except Exception as e:
            error = e
            raise

        finally:
            # Post-search hooks
            execution_time = time.time() - start_time
            emit_hook(
                'search.after',
                'search_operation',
                search_type=search_type,
                search_term=search_term,
                results=results,
                success=error is None,
                error=str(error) if error else None,
                execution_time=execution_time,
                **kwargs
            )

    @contextmanager
    def database_connection(self, connection_id: str, database: str, host: str, port: int):
        """Context manager for database connection hooks"""
        if not self.integration_enabled:
            yield
            return

        try:
            # Connection start
            emit_hook(
                'database.connect',
                'database_connection',
                connection_id=connection_id,
                database=database,
                host=host,
                port=port
            )

            yield

            # Connection success
            emit_hook(
                'database.connected',
                'database_connection',
                connection_id=connection_id
            )

        except Exception as e:
            # Connection error
            emit_hook(
                'database.error',
                'database_connection',
                connection_id=connection_id,
                error=e
            )
            raise

        finally:
            # Disconnection
            emit_hook(
                'database.disconnect',
                'database_connection',
                connection_id=connection_id
            )

    @contextmanager
    def database_transaction(self, transaction_id: str):
        """Context manager for database transaction hooks"""
        if not self.integration_enabled:
            yield
            return

        try:
            # Transaction begin
            emit_hook(
                'database.transaction.begin',
                'database_transaction',
                transaction_id=transaction_id
            )

            yield

            # Transaction commit
            emit_hook(
                'database.transaction.commit',
                'database_transaction',
                transaction_id=transaction_id
            )

        except Exception as e:
            # Transaction rollback
            emit_hook(
                'database.transaction.rollback',
                'database_transaction',
                transaction_id=transaction_id,
                reason=str(e)
            )
            raise

    @contextmanager
    def api_request(self, request_id: str, url: str, method: str = 'GET', params: Dict = None):
        """Context manager for API request hooks"""
        if not self.integration_enabled:
            yield
            return

        start_time = time.time()
        response_data = None
        status_code = None

        try:
            # Pre-request hooks
            emit_hook(
                'api.request',
                'api_request',
                request_id=request_id,
                url=url,
                method=method,
                params=params or {}
            )

            yield

        except Exception as e:
            # API error
            emit_hook(
                'api.error',
                'api_request',
                request_id=request_id,
                error=e
            )
            raise

        finally:
            # Post-request hooks (if we have response data)
            if hasattr(self, '_api_response_data'):
                response_data = getattr(self, '_api_response_data', None)
                status_code = getattr(self, '_api_status_code', 200)
                response_time = time.time() - start_time

                emit_hook(
                    'api.response',
                    'api_request',
                    request_id=request_id,
                    status_code=status_code,
                    response_data=response_data,
                    response_time=response_time,
                    response_size=len(str(response_data)) if response_data else 0
                )

    def set_api_response(self, response_data: Any, status_code: int = 200):
        """Set API response data for hook tracking"""
        self._api_response_data = response_data
        self._api_status_code = status_code

    @contextmanager
    def performance_monitoring(self, operation_name: str, metadata: Dict = None):
        """Context manager for performance monitoring"""
        if not self.integration_enabled:
            yield
            return

        operation_id = f"{operation_name}_{int(time.time())}"

        try:
            # Start performance monitoring
            emit_hook(
                'performance.start',
                'performance_monitoring',
                operation_id=operation_id,
                operation_name=operation_name,
                metadata=metadata or {}
            )

            yield

        except Exception as e:
            success = False
            raise

        else:
            success = True

        finally:
            # End performance monitoring
            emit_hook(
                'performance.end',
                'performance_monitoring',
                operation_id=operation_id,
                success=success
            )

    def track_user_action(self, action: str, user_id: str = None, **details):
        """Track user action"""
        if not self.integration_enabled:
            return

        emit_hook(
            'user.session.activity',
            'user_action_tracking',
            session_id=self._session_id or 'default',
            user_id=user_id or 'anonymous',
            action=action,
            details=details
        )

    def handle_error(self, error: Exception, operation: Callable = None,
                    fallback: Callable = None, source: str = None):
        """Handle error with recovery hooks"""
        if not self.integration_enabled:
            return

        emit_hook(
            'error.occurred',
            source or 'error_handler',
            error=error,
            error_type=type(error).__name__,
            error_message=str(error),
            failed_operation=operation,
            fallback_operation=fallback
        )

    def trigger_health_check(self, database_manager=None, api_client=None):
        """Trigger health check"""
        if not self.integration_enabled:
            return

        return emit_hook(
            'system.health_check',
            'health_monitor',
            database_manager=database_manager,
            api_client=api_client
        )


# Global integration instance
_hook_integration = None


def get_hook_integration() -> HookIntegration:
    """Get global hook integration instance"""
    global _hook_integration
    if _hook_integration is None:
        _hook_integration = HookIntegration()
    return _hook_integration


# Decorator functions for easy integration
def with_hooks(hook_type: str, **hook_kwargs):
    """Decorator to add hooks to functions"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            integration = get_hook_integration()

            if hook_type == 'performance':
                with integration.performance_monitoring(func.__name__, hook_kwargs):
                    return func(*args, **kwargs)

            elif hook_type == 'error_handling':
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    integration.handle_error(e, func, source=func.__name__)
                    raise

            else:
                return func(*args, **kwargs)

        return wrapper
    return decorator


def with_performance_monitoring(operation_name: str = None, **metadata):
    """Decorator for performance monitoring"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            integration = get_hook_integration()
            op_name = operation_name or func.__name__

            with integration.performance_monitoring(op_name, metadata):
                return func(*args, **kwargs)

        return wrapper
    return decorator


def with_error_handling(fallback: Callable = None):
    """Decorator for error handling"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            integration = get_hook_integration()

            try:
                return func(*args, **kwargs)
            except Exception as e:
                integration.handle_error(e, func, fallback, func.__name__)
                if fallback:
                    return fallback(*args, **kwargs)
                raise

        return wrapper
    return decorator


def track_user_action(action: str, **details):
    """Decorator to track user actions"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            integration = get_hook_integration()

            # Execute function
            result = func(*args, **kwargs)

            # Track action
            integration.track_user_action(action, details=details)

            return result

        return wrapper
    return decorator


# Initialization function to register all hooks
def initialize_hooks():
    """Initialize and register all hook modules"""
    try:
        # Import and register all hook modules
        from hooks.lifecycle_hooks import register_lifecycle_hooks
        from hooks.search_hooks import register_search_hooks
        from hooks.database_hooks import register_database_hooks
        from hooks.api_hooks import register_api_hooks
        from hooks.error_hooks import register_error_hooks
        from hooks.performance_hooks import register_performance_hooks
        from hooks.user_action_hooks import register_user_action_hooks

        # Register all hooks
        register_lifecycle_hooks()
        register_search_hooks()
        register_database_hooks()
        register_api_hooks()
        register_error_hooks()
        register_performance_hooks()
        register_user_action_hooks()

        logger.info("All hooks initialized and registered successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize hooks: {e}")
        return False


# Enhanced database manager integration
class HookedDatabaseManager:
    """Database manager wrapper with hook integration"""

    def __init__(self, original_db_manager):
        self.db_manager = original_db_manager
        self.integration = get_hook_integration()

    def get_connection(self):
        """Get database connection with hooks"""
        connection_id = f"conn_{int(time.time())}"
        config = self.db_manager.config

        with self.integration.database_connection(
            connection_id=connection_id,
            database=config['database'],
            host=config['host'],
            port=config['port']
        ):
            return self.db_manager.get_connection()

    def __getattr__(self, name):
        """Delegate other methods to original manager"""
        return getattr(self.db_manager, name)


# Enhanced API client integration
class HookedAPIClient:
    """API client wrapper with hook integration"""

    def __init__(self, original_api_client):
        self.api_client = original_api_client
        self.integration = get_hook_integration()

    def _make_request(self, endpoint: str, params: Dict = None, **kwargs):
        """Make API request with hooks"""
        request_id = f"req_{int(time.time())}"
        url = f"{self.api_client.base_url}/{endpoint.lstrip('/')}"

        with self.integration.api_request(
            request_id=request_id,
            url=url,
            method=kwargs.get('method', 'GET'),
            params=params
        ):
            result = self.api_client._make_request(endpoint, params, **kwargs)

            # Set response data for hooks
            if result:
                self.integration.set_api_response(result, 200)
            else:
                self.integration.set_api_response(None, 500)

            return result

    def __getattr__(self, name):
        """Delegate other methods to original client"""
        return getattr(self.api_client, name)


# Helper functions for common integration patterns
def enable_hooks_for_database(database_manager):
    """Enable hooks for database manager"""
    return HookedDatabaseManager(database_manager)


def enable_hooks_for_api_client(api_client):
    """Enable hooks for API client"""
    return HookedAPIClient(api_client)


def start_user_session(user_id: str = None, **metadata) -> str:
    """Start a user session with hooks"""
    import uuid
    session_id = str(uuid.uuid4())

    integration = get_hook_integration()
    integration.set_session_id(session_id)

    emit_hook(
        'user.session.start',
        'session_manager',
        session_id=session_id,
        user_id=user_id or 'anonymous',
        metadata=metadata
    )

    return session_id


def end_user_session(session_id: str = None, reason: str = 'explicit'):
    """End a user session with hooks"""
    integration = get_hook_integration()

    if not session_id:
        session_id = integration._session_id

    if session_id:
        emit_hook(
            'user.session.end',
            'session_manager',
            session_id=session_id,
            end_reason=reason
        )

        # Clear session from integration
        if integration._session_id == session_id:
            integration.set_session_id(None)


def get_hook_stats() -> Dict[str, Any]:
    """Get comprehensive hook statistics"""
    hook_manager = get_hook_manager()

    return {
        'hook_stats': hook_manager.get_hook_stats(),
        'registered_hooks': hook_manager.get_registered_hooks(),
        'event_history': hook_manager.get_event_history(50)
    }