"""
Application Lifecycle Hooks
Handles startup, shutdown, and lifecycle events for the Maricopa Property Search application
"""
import asyncio
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import psutil

from hook_manager import (
    Hook,
    HookContext,
    HookPriority,
    HookResult,
    HookStatus,
    get_hook_manager,
)
from logging_config import get_logger, log_exception

logger = get_logger(__name__)


class ApplicationStartupHook(Hook):
    """Hook executed during application startup"""
    def __init__(self):
        super().__init__("application_startup", HookPriority.HIGHEST)
        self.startup_time = None
        self.initialization_steps = []

    async def execute(self, context: HookContext) -> HookResult:
        """Execute startup procedures"""
        try:
            self.startup_time = datetime.now()
            startup_data = context.data

            logger.info("=== APPLICATION STARTUP INITIATED ===")
            logger.info(f"Startup Time: {self.startup_time}")
            logger.info(f"Process ID: {os.getpid()}")
            logger.info(f"Python Version: {sys.version}")

            # System resource check
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage("/")

            logger.info(
                f"System Memory: {memory_info.total / (1024**3):.1f} GB total, "
                f"{memory_info.available / (1024**3):.1f} GB available"
            )
            logger.info(
                f"Disk Space: {disk_info.total / (1024**3):.1f} GB total, "
                f"{disk_info.free / (1024**3):.1f} GB free"
            )

            # Register cleanup handlers
            self._register_cleanup_handlers()

            # Initialize application directories
            self._initialize_directories(startup_data.get("project_root"))

            # Log configuration details
            if "config_manager" in startup_data:
                self._log_configuration_info(startup_data["config_manager"])

            # Create startup metadata
            metadata = {
                "startup_time": self.startup_time.isoformat(),
                "process_id": os.getpid(),
                "system_info": {
                    "memory_total_gb": memory_info.total / (1024**3),
                    "memory_available_gb": memory_info.available / (1024**3),
                    "disk_free_gb": disk_info.free / (1024**3),
                },
                "initialization_steps": self.initialization_steps,
            }

            logger.info("=== APPLICATION STARTUP COMPLETED ===")

            return HookResult(
                status=HookStatus.SUCCESS,
                result={"startup_time": self.startup_time},
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            log_exception(logger, e, "application startup")
            return HookResult(status=HookStatus.FAILED, error=e)
def _register_cleanup_handlers(self):
        """Register signal handlers for graceful shutdown"""
def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            # Emit shutdown hook
            from hook_manager import emit_hook

            emit_hook("application.shutdown", "signal_handler", signal=signum)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.initialization_steps.append("Signal handlers registered")
def _initialize_directories(self, project_root: Optional[str]):
        """Initialize required application directories"""
        if project_root:
            dirs_to_create = ["logs", "cache", "exports", "backups", "temp"]

            for dir_name in dirs_to_create:
                dir_path = Path(project_root) / dir_name
                dir_path.mkdir(exist_ok=True)
                logger.debug(f"Ensured directory exists: {dir_path}")

            self.initialization_steps.append(
                f"Directories initialized: {dirs_to_create}"
            )
def _log_configuration_info(self, config_manager):
        """Log configuration information"""
        try:
            db_config = config_manager.get_db_config()
            api_config = config_manager.get_api_config()

            logger.info(
                f"Database: {db_config['host']}:{db_config['port']}/{db_config['database']}"
            )
            logger.info(f"API Base URL: {api_config['base_url']}")
            logger.info(f"API Timeout: {api_config['timeout']}s")

            self.initialization_steps.append("Configuration logged")

        except Exception as e:
            logger.warning(f"Could not log configuration info: {e}")


class ApplicationShutdownHook(Hook):
    """Hook executed during application shutdown"""
    def __init__(self):
        super().__init__("application_shutdown", HookPriority.HIGHEST)
        self.shutdown_time = None
        self.cleanup_results = []

    async def execute(self, context: HookContext) -> HookResult:
        """Execute shutdown procedures"""
        try:
            self.shutdown_time = datetime.now()
            shutdown_data = context.data

            logger.info("=== APPLICATION SHUTDOWN INITIATED ===")
            logger.info(f"Shutdown Time: {self.shutdown_time}")

            # Clean up temporary files
            self._cleanup_temp_files()

            # Close database connections
            if "database_manager" in shutdown_data:
                self._cleanup_database(shutdown_data["database_manager"])

            # Close API connections
            if "api_client" in shutdown_data:
                self._cleanup_api_client(shutdown_data["api_client"])

            # Generate shutdown report
            uptime = self._calculate_uptime()
            self._generate_shutdown_report(uptime)

            logger.info("=== APPLICATION SHUTDOWN COMPLETED ===")

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    "shutdown_time": self.shutdown_time,
                    "cleanup_results": self.cleanup_results,
                },
                metadata={"uptime_seconds": uptime.total_seconds() if uptime else 0},
            )

        except Exception as e:
            logger.error(f"Application shutdown error: {e}")
            log_exception(logger, e, "application shutdown")
            return HookResult(status=HookStatus.FAILED, error=e)
def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
import tempfile

            temp_dir = Path(tempfile.gettempdir())
            app_temp_files = list(temp_dir.glob("maricopa_*"))

            for temp_file in app_temp_files:
                try:
                    if temp_file.is_file():
                        temp_file.unlink()
                        logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Could not clean up {temp_file}: {e}")

            self.cleanup_results.append(f"Cleaned up {len(app_temp_files)} temp files")

        except Exception as e:
            logger.warning(f"Temp file cleanup failed: {e}")
def _cleanup_database(self, database_manager):
        """Clean up database connections"""
        try:
            if hasattr(database_manager, "pool") and database_manager.pool:
                database_manager.pool.closeall()
                logger.info("Database connection pool closed")
                self.cleanup_results.append("Database connections closed")
        except Exception as e:
            logger.warning(f"Database cleanup error: {e}")
def _cleanup_api_client(self, api_client):
        """Clean up API client connections"""
        try:
            if hasattr(api_client, "session"):
                api_client.session.close()
                logger.info("API client session closed")
                self.cleanup_results.append("API client closed")
        except Exception as e:
            logger.warning(f"API client cleanup error: {e}")
    def _calculate_uptime(self) -> Optional[timedelta]:
        """Calculate application uptime"""
        try:
            # Try to get startup time from hook manager history
            hook_manager = get_hook_manager()
            history = hook_manager.get_event_history(1000)

            for event_name, timestamp, source in history:
                if event_name == "application.startup":
                    return self.shutdown_time - timestamp

        except Exception as e:
            logger.debug(f"Could not calculate uptime: {e}")

        return None
def _generate_shutdown_report(self, uptime: Optional[timedelta]):
        """Generate final shutdown report"""
        try:
            hook_manager = get_hook_manager()
            stats = hook_manager.get_hook_stats()

            report_lines = [
                "=== APPLICATION SHUTDOWN REPORT ===",
                f"Shutdown Time: {self.shutdown_time}",
                f"Uptime: {uptime}" if uptime else "Uptime: Unknown",
                f"Process ID: {os.getpid()}",
                "",
                "Cleanup Results:",
            ]

            for result in self.cleanup_results:
                report_lines.append(f"  - {result}")

            if stats:
                report_lines.extend(["", "Hook Execution Summary:"])
                for hook_name, hook_stats in stats.items():
                    report_lines.append(
                        f"  - {hook_name}: {hook_stats.get('total_executions', 0)} executions, "
                        f"avg {hook_stats.get('avg_time', 0):.3f}s"
                    )

            logger.info("\n".join(report_lines))

        except Exception as e:
            logger.warning(f"Could not generate shutdown report: {e}")


class ResourceMonitorHook(Hook):
    """Hook for monitoring system resources"""
    def __init__(self):
        super().__init__("resource_monitor", HookPriority.LOW)
        self.last_check = None
        self.monitoring_enabled = True

    async def execute(self, context: HookContext) -> HookResult:
        """Monitor system resources"""
        try:
            if not self.monitoring_enabled:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

            current_time = datetime.now()
            process = psutil.Process()

            # Get resource usage
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()

            # System-wide info
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent()

            resource_data = {
                "timestamp": current_time.isoformat(),
                "process": {
                    "memory_rss_mb": memory_info.rss / (1024 * 1024),
                    "memory_vms_mb": memory_info.vms / (1024 * 1024),
                    "cpu_percent": cpu_percent,
                    "pid": os.getpid(),
                },
                "system": {
                    "memory_percent": system_memory.percent,
                    "memory_available_gb": system_memory.available / (1024**3),
                    "cpu_percent": system_cpu,
                },
            }

            # Check for resource warnings
            warnings = []
            if system_memory.percent > 85:
                warnings.append(
                    f"High system memory usage: {system_memory.percent:.1f}%"
                )

            if memory_info.rss / (1024**3) > 1:  # More than 1GB
                warnings.append(
                    f"High process memory usage: {memory_info.rss / (1024**3):.1f} GB"
                )

            if warnings:
                logger.warning("Resource usage warnings: " + "; ".join(warnings))
                resource_data["warnings"] = warnings

            self.last_check = current_time

            return HookResult(
                status=HookStatus.SUCCESS,
                result=resource_data,
                metadata={"warnings_count": len(warnings)},
            )

        except Exception as e:
            logger.error(f"Resource monitoring failed: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)


class HealthCheckHook(Hook):
    """Hook for application health checks"""
    def __init__(self):
        super().__init__("health_check", HookPriority.NORMAL)
        self.last_health_check = None
        self.health_status = {}

    async def execute(self, context: HookContext) -> HookResult:
        """Perform application health check"""
        try:
            current_time = datetime.now()
            health_data = context.data
            health_results = {}

            # Check database connectivity
            if "database_manager" in health_data:
                db_health = self._check_database_health(health_data["database_manager"])
                health_results["database"] = db_health

            # Check API connectivity
            if "api_client" in health_data:
                api_health = self._check_api_health(health_data["api_client"])
                health_results["api"] = api_health

            # Check disk space
            disk_health = self._check_disk_space()
            health_results["disk"] = disk_health

            # Overall health status
            overall_healthy = all(
                result.get("healthy", False) for result in health_results.values()
            )

            self.health_status = {
                "timestamp": current_time.isoformat(),
                "overall_healthy": overall_healthy,
                "components": health_results,
            }
            self.last_health_check = current_time

            status_level = "INFO" if overall_healthy else "WARNING"
            logger.log(
                getattr(logging, status_level),
                f"Health check completed - Overall: {'HEALTHY' if overall_healthy else 'UNHEALTHY'}",
            )

            return HookResult(
                status=HookStatus.SUCCESS,
                result=self.health_status,
                metadata={"overall_healthy": overall_healthy},
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)
    def _check_database_health(self, database_manager) -> Dict[str, Any]:
        """Check database connectivity and health"""
        try:
            start_time = time.time()
            is_healthy = database_manager.test_connection()
            response_time = time.time() - start_time

            return {
                "healthy": is_healthy,
                "response_time_ms": response_time * 1000,
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }
    def _check_api_health(self, api_client) -> Dict[str, Any]:
        """Check API connectivity and health"""
        try:
            start_time = time.time()
            is_healthy = api_client.test_connection()
            response_time = time.time() - start_time

            return {
                "healthy": is_healthy,
                "response_time_ms": response_time * 1000,
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            disk_usage = psutil.disk_usage("/")
            free_percent = (disk_usage.free / disk_usage.total) * 100

            is_healthy = free_percent > 10  # At least 10% free space

            return {
                "healthy": is_healthy,
                "free_percent": free_percent,
                "free_gb": disk_usage.free / (1024**3),
                "total_gb": disk_usage.total / (1024**3),
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }


# Register lifecycle hooks
def register_lifecycle_hooks():
    """Register all lifecycle hooks with the hook manager"""
    hook_manager = get_hook_manager()

    # Register hooks
    hook_manager.register_hook("application.startup", ApplicationStartupHook())
    hook_manager.register_hook("application.shutdown", ApplicationShutdownHook())
    hook_manager.register_hook("system.resource_monitor", ResourceMonitorHook())
    hook_manager.register_hook("system.health_check", HealthCheckHook())

    logger.info("Lifecycle hooks registered successfully")


# Convenience functions for triggering lifecycle events
def trigger_startup(config_manager=None, database_manager=None, project_root=None):
    """Trigger application startup hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "application.startup",
        "lifecycle_manager",
        config_manager=config_manager,
        database_manager=database_manager,
        project_root=project_root,
    )
def trigger_shutdown(database_manager=None, api_client=None):
    """Trigger application shutdown hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "application.shutdown",
        "lifecycle_manager",
        database_manager=database_manager,
        api_client=api_client,
    )
def trigger_health_check(database_manager=None, api_client=None):
    """Trigger health check hook"""
    from hook_manager import emit_hook

    return emit_hook(
        "system.health_check",
        "lifecycle_manager",
        database_manager=database_manager,
        api_client=api_client,
    )
def trigger_resource_monitor():
    """Trigger resource monitoring hook"""
    from hook_manager import emit_hook

    return emit_hook("system.resource_monitor", "lifecycle_manager")
