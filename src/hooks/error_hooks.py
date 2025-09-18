"""
Error Handling and Recovery Hooks
Comprehensive error detection, logging, recovery, and notification system
"""

import asyncio
import logging
import smtplib
import traceback
from collections import defaultdict, deque
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Set

from hook_manager import Hook, HookContext, HookResult, HookStatus, HookPriority, get_hook_manager
from logging_config import get_logger, log_exception

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """Recovery action types"""
    RETRY = "retry"
    FALLBACK = "fallback"
    RESTART = "restart"
    ALERT = "alert"
    IGNORE = "ignore"


class ErrorPattern:
    """Error pattern for classification and handling"""

    def __init__(self, name: str, pattern: str, severity: ErrorSeverity,
                 recovery_action: RecoveryAction, max_occurrences: int = 5):
        self.name = name
        self.pattern = pattern
        self.severity = severity
        self.recovery_action = recovery_action
        self.max_occurrences = max_occurrences
        self.occurrence_count = 0
        self.last_occurrence = None

    def matches(self, error_message: str) -> bool:
        """Check if error matches this pattern"""
        import re
        return bool(re.search(self.pattern, error_message, re.IGNORECASE))

    def should_suppress(self) -> bool:
        """Check if error should be suppressed due to frequency"""
        return self.occurrence_count >= self.max_occurrences

    def record_occurrence(self):
        """Record an occurrence of this error pattern"""
        self.occurrence_count += 1
        self.last_occurrence = datetime.now()


class ErrorClassificationHook(Hook):
    """Hook for classifying and categorizing errors"""

    def __init__(self):
        super().__init__("error_classification", HookPriority.HIGHEST)
        self.error_patterns = self._initialize_error_patterns()
        self.error_stats = defaultdict(int)
        self.error_history = deque(maxlen=1000)

    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize common error patterns"""
        return [
            # Database errors
            ErrorPattern(
                "database_connection_failed",
                r"(connection.*failed|could not connect|timeout|connection refused)",
                ErrorSeverity.HIGH,
                RecoveryAction.RETRY
            ),
            ErrorPattern(
                "database_query_timeout",
                r"(query.*timeout|statement timeout|lock wait timeout)",
                ErrorSeverity.MEDIUM,
                RecoveryAction.RETRY
            ),
            ErrorPattern(
                "database_permission_denied",
                r"(permission denied|access denied|insufficient privileges)",
                ErrorSeverity.HIGH,
                RecoveryAction.ALERT
            ),

            # API errors
            ErrorPattern(
                "api_rate_limit",
                r"(rate limit|too many requests|429|quota exceeded)",
                ErrorSeverity.MEDIUM,
                RecoveryAction.RETRY
            ),
            ErrorPattern(
                "api_unauthorized",
                r"(unauthorized|401|forbidden|403|invalid.*token)",
                ErrorSeverity.HIGH,
                RecoveryAction.ALERT
            ),
            ErrorPattern(
                "api_service_unavailable",
                r"(service unavailable|502|503|504|bad gateway)",
                ErrorSeverity.MEDIUM,
                RecoveryAction.FALLBACK
            ),

            # Network errors
            ErrorPattern(
                "network_timeout",
                r"(connection.*timeout|read timeout|socket timeout)",
                ErrorSeverity.MEDIUM,
                RecoveryAction.RETRY
            ),
            ErrorPattern(
                "network_unreachable",
                r"(network.*unreachable|host.*unreachable|no route)",
                ErrorSeverity.HIGH,
                RecoveryAction.FALLBACK
            ),

            # Application errors
            ErrorPattern(
                "memory_error",
                r"(out of memory|memory error|cannot allocate)",
                ErrorSeverity.CRITICAL,
                RecoveryAction.RESTART
            ),
            ErrorPattern(
                "file_not_found",
                r"(file not found|no such file|path.*not.*exist)",
                ErrorSeverity.LOW,
                RecoveryAction.FALLBACK
            ),
            ErrorPattern(
                "configuration_error",
                r"(configuration.*error|config.*invalid|missing.*config)",
                ErrorSeverity.HIGH,
                RecoveryAction.ALERT
            ),

            # Generic patterns
            ErrorPattern(
                "unknown_error",
                r".*",  # Catch-all pattern
                ErrorSeverity.LOW,
                RecoveryAction.IGNORE,
                max_occurrences=10
            )
        ]

    async def execute(self, context: HookContext) -> HookResult:
        """Classify and categorize errors"""
        try:
            error_data = context.data
            error_message = str(error_data.get('error', ''))
            error_type = error_data.get('error_type', 'Unknown')

            # Find matching pattern
            matched_pattern = None
            for pattern in self.error_patterns:
                if pattern.matches(error_message):
                    matched_pattern = pattern
                    break

            if not matched_pattern:
                # Use the catch-all pattern
                matched_pattern = self.error_patterns[-1]

            # Record occurrence
            matched_pattern.record_occurrence()

            # Update statistics
            self.error_stats[matched_pattern.name] += 1

            # Create error record
            error_record = {
                'timestamp': datetime.now().isoformat(),
                'error_message': error_message,
                'error_type': error_type,
                'pattern_name': matched_pattern.name,
                'severity': matched_pattern.severity.value,
                'recovery_action': matched_pattern.recovery_action.value,
                'occurrence_count': matched_pattern.occurrence_count,
                'should_suppress': matched_pattern.should_suppress(),
                'source': context.source,
                'traceback': error_data.get('traceback', '')
            }

            # Add to history
            self.error_history.append(error_record)

            # Log based on severity
            log_level = self._get_log_level(matched_pattern.severity)
            logger.log(
                log_level,
                f"Error classified: {matched_pattern.name} ({matched_pattern.severity.value}) - {error_message}"
            )

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    'classification': error_record,
                    'pattern': {
                        'name': matched_pattern.name,
                        'severity': matched_pattern.severity.value,
                        'recovery_action': matched_pattern.recovery_action.value,
                        'should_suppress': matched_pattern.should_suppress()
                    }
                },
                metadata={'severity': matched_pattern.severity.value}
            )

        except Exception as e:
            logger.error(f"Error classification hook failed: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get appropriate log level for error severity"""
        severity_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return severity_map.get(severity, logging.ERROR)

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        total_errors = sum(self.error_stats.values())

        return {
            'total_errors': total_errors,
            'error_patterns': dict(self.error_stats),
            'recent_errors': len(self.error_history),
            'top_errors': self._get_top_errors()
        }

    def _get_top_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top error patterns by frequency"""
        sorted_errors = sorted(
            self.error_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {'pattern': pattern, 'count': count}
            for pattern, count in sorted_errors[:limit]
        ]


class ErrorRecoveryHook(Hook):
    """Hook for automated error recovery"""

    def __init__(self):
        super().__init__("error_recovery", HookPriority.HIGH)
        self.recovery_handlers = {}
        self.recovery_stats = defaultdict(int)
        self.max_retry_attempts = 3
        self.retry_delays = [1, 2, 5]  # seconds

    async def execute(self, context: HookContext) -> HookResult:
        """Execute error recovery procedures"""
        try:
            error_data = context.data
            classification = error_data.get('classification', {})
            recovery_action = classification.get('recovery_action', 'ignore')
            pattern_name = classification.get('pattern_name', 'unknown')

            logger.info(f"Attempting error recovery: {recovery_action} for {pattern_name}")

            if recovery_action == RecoveryAction.RETRY.value:
                result = await self._handle_retry_recovery(context, error_data)
            elif recovery_action == RecoveryAction.FALLBACK.value:
                result = await self._handle_fallback_recovery(context, error_data)
            elif recovery_action == RecoveryAction.RESTART.value:
                result = await self._handle_restart_recovery(context, error_data)
            elif recovery_action == RecoveryAction.ALERT.value:
                result = await self._handle_alert_recovery(context, error_data)
            else:  # IGNORE
                result = await self._handle_ignore_recovery(context, error_data)

            # Update recovery statistics
            self.recovery_stats[f"{recovery_action}_attempted"] += 1
            if result.status == HookStatus.SUCCESS:
                self.recovery_stats[f"{recovery_action}_successful"] += 1

            return result

        except Exception as e:
            logger.error(f"Error recovery hook failed: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _handle_retry_recovery(self, context: HookContext, error_data: Dict) -> HookResult:
        """Handle retry recovery strategy"""
        operation = error_data.get('failed_operation')
        retry_count = error_data.get('retry_count', 0)

        if retry_count >= self.max_retry_attempts:
            logger.warning(f"Max retry attempts ({self.max_retry_attempts}) exceeded")
            return HookResult(
                status=HookStatus.FAILED,
                result={'recovery_action': 'retry', 'max_retries_exceeded': True}
            )

        # Calculate delay
        delay = self.retry_delays[min(retry_count, len(self.retry_delays) - 1)]

        logger.info(f"Retrying operation in {delay}s (attempt {retry_count + 1}/{self.max_retry_attempts})")

        # Wait before retry
        await asyncio.sleep(delay)

        # Attempt recovery
        try:
            if operation and callable(operation):
                await operation()
                logger.info("Retry recovery successful")
                return HookResult(
                    status=HookStatus.SUCCESS,
                    result={'recovery_action': 'retry', 'retry_successful': True, 'attempt': retry_count + 1}
                )
        except Exception as e:
            logger.warning(f"Retry attempt {retry_count + 1} failed: {e}")

        return HookResult(
            status=HookStatus.FAILED,
            result={'recovery_action': 'retry', 'retry_failed': True, 'attempt': retry_count + 1}
        )

    async def _handle_fallback_recovery(self, context: HookContext, error_data: Dict) -> HookResult:
        """Handle fallback recovery strategy"""
        fallback_operation = error_data.get('fallback_operation')

        if not fallback_operation:
            logger.warning("No fallback operation available")
            return HookResult(
                status=HookStatus.FAILED,
                result={'recovery_action': 'fallback', 'no_fallback_available': True}
            )

        try:
            if callable(fallback_operation):
                result = await fallback_operation()
                logger.info("Fallback recovery successful")
                return HookResult(
                    status=HookStatus.SUCCESS,
                    result={'recovery_action': 'fallback', 'fallback_successful': True, 'fallback_result': result}
                )
        except Exception as e:
            logger.error(f"Fallback operation failed: {e}")

        return HookResult(
            status=HookStatus.FAILED,
            result={'recovery_action': 'fallback', 'fallback_failed': True}
        )

    async def _handle_restart_recovery(self, context: HookContext, error_data: Dict) -> HookResult:
        """Handle restart recovery strategy"""
        logger.critical("Critical error detected - restart recovery initiated")

        # For restart recovery, we typically need to:
        # 1. Clean up resources
        # 2. Reinitialize components
        # 3. Potentially restart the application

        restart_component = error_data.get('restart_component')

        if restart_component and hasattr(restart_component, 'restart'):
            try:
                await restart_component.restart()
                logger.info("Component restart successful")
                return HookResult(
                    status=HookStatus.SUCCESS,
                    result={'recovery_action': 'restart', 'component_restarted': True}
                )
            except Exception as e:
                logger.error(f"Component restart failed: {e}")

        # If no specific component to restart, recommend application restart
        logger.critical("Application restart recommended")
        return HookResult(
            status=HookStatus.SUCCESS,
            result={'recovery_action': 'restart', 'application_restart_recommended': True}
        )

    async def _handle_alert_recovery(self, context: HookContext, error_data: Dict) -> HookResult:
        """Handle alert recovery strategy"""
        logger.warning("Alert recovery - notifying administrators")

        # Send alerts through configured channels
        alert_sent = await self._send_alerts(error_data)

        return HookResult(
            status=HookStatus.SUCCESS,
            result={'recovery_action': 'alert', 'alert_sent': alert_sent}
        )

    async def _handle_ignore_recovery(self, context: HookContext, error_data: Dict) -> HookResult:
        """Handle ignore recovery strategy"""
        logger.debug("Error recovery: ignoring error as per configuration")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={'recovery_action': 'ignore', 'error_ignored': True}
        )

    async def _send_alerts(self, error_data: Dict) -> bool:
        """Send error alerts through configured channels"""
        try:
            # This would typically integrate with notification services
            # For now, we'll just log the alert
            logger.error(f"ALERT: Critical error detected - {error_data.get('error_message', 'Unknown error')}")

            # In a real implementation, you might:
            # - Send email notifications
            # - Post to Slack/Teams
            # - Create tickets in issue tracking systems
            # - Send SMS alerts

            return True
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False

    def register_recovery_handler(self, error_pattern: str, handler: Callable):
        """Register custom recovery handler for specific error pattern"""
        self.recovery_handlers[error_pattern] = handler
        logger.info(f"Registered recovery handler for pattern: {error_pattern}")

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        return dict(self.recovery_stats)


class ErrorNotificationHook(Hook):
    """Hook for error notifications and alerting"""

    def __init__(self):
        super().__init__("error_notification", HookPriority.LOW)
        self.notification_config = {
            'email_enabled': False,
            'slack_enabled': False,
            'severity_threshold': ErrorSeverity.HIGH
        }
        self.notification_history = deque(maxlen=100)

    async def execute(self, context: HookContext) -> HookResult:
        """Send error notifications"""
        try:
            error_data = context.data
            classification = error_data.get('classification', {})
            severity = ErrorSeverity(classification.get('severity', 'low'))

            # Check if notification should be sent
            if severity.value < self.notification_config['severity_threshold'].value:
                return HookResult(
                    status=HookStatus.SUCCESS,
                    result={'notification_sent': False, 'reason': 'Below severity threshold'}
                )

            # Check if error should be suppressed
            if classification.get('should_suppress', False):
                return HookResult(
                    status=HookStatus.SUCCESS,
                    result={'notification_sent': False, 'reason': 'Error suppressed due to frequency'}
                )

            # Send notifications
            notifications_sent = []

            if self.notification_config['email_enabled']:
                email_result = await self._send_email_notification(error_data)
                notifications_sent.append({'type': 'email', 'success': email_result})

            if self.notification_config['slack_enabled']:
                slack_result = await self._send_slack_notification(error_data)
                notifications_sent.append({'type': 'slack', 'success': slack_result})

            # Record notification
            notification_record = {
                'timestamp': datetime.now().isoformat(),
                'error_pattern': classification.get('pattern_name'),
                'severity': severity.value,
                'notifications_sent': notifications_sent
            }
            self.notification_history.append(notification_record)

            logger.info(f"Error notifications sent: {notifications_sent}")

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    'notification_sent': True,
                    'notifications': notifications_sent,
                    'notification_record': notification_record
                }
            )

        except Exception as e:
            logger.error(f"Error notification hook failed: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _send_email_notification(self, error_data: Dict) -> bool:
        """Send email notification"""
        try:
            # This would integrate with actual email service
            logger.info("Email notification would be sent here")
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    async def _send_slack_notification(self, error_data: Dict) -> bool:
        """Send Slack notification"""
        try:
            # This would integrate with Slack API
            logger.info("Slack notification would be sent here")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def configure_notifications(self, config: Dict[str, Any]):
        """Configure notification settings"""
        self.notification_config.update(config)
        logger.info(f"Notification configuration updated: {self.notification_config}")

    def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notification history"""
        return list(self.notification_history)[-limit:]


# Register error hooks
def register_error_hooks():
    """Register all error hooks with the hook manager"""
    hook_manager = get_hook_manager()

    # Register hooks
    hook_manager.register_hook('error.occurred', ErrorClassificationHook())
    hook_manager.register_hook('error.occurred', ErrorRecoveryHook())
    hook_manager.register_hook('error.occurred', ErrorNotificationHook())

    logger.info("Error handling hooks registered successfully")


# Convenience functions for triggering error events
def trigger_error_occurred(error: Exception, error_type: str = None, source: str = None,
                          failed_operation: Callable = None, fallback_operation: Callable = None,
                          retry_count: int = 0, **kwargs):
    """Trigger error occurred hook"""
    from hook_manager import emit_hook

    error_data = {
        'error': error,
        'error_type': error_type or type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        'failed_operation': failed_operation,
        'fallback_operation': fallback_operation,
        'retry_count': retry_count,
        **kwargs
    }

    return emit_hook(
        'error.occurred',
        source or 'error_handler',
        **error_data
    )


def handle_error_with_recovery(error: Exception, operation: Callable = None,
                             fallback: Callable = None, source: str = None):
    """Handle error with automatic recovery"""
    return trigger_error_occurred(
        error=error,
        failed_operation=operation,
        fallback_operation=fallback,
        source=source or 'auto_recovery'
    )