#!/usr/bin/env python
"""
User Action Logger for Maricopa Property Search
Logs all user actions comprehensively for debugging and issue resolution
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading

# Set up module logger
logger = logging.getLogger(__name__)


class UserActionLogger:
    """Comprehensive user action logger that maintains a persistent action history"""

    def __init__(self, log_dir: str = None):
        """Initialize the user action logger"""
        # Determine log directory
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs" / "user_actions"
        else:
            log_dir = Path(log_dir)

        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with timestamp
        self.session_start = datetime.now()
        self.log_file = (
            self.log_dir
            / f"user_actions_{self.session_start.strftime('%Y%m%d_%H%M%S')}.jsonl"
        )
        self.summary_file = self.log_dir / "user_actions_summary.log"

        # Thread lock for concurrent access
        self.lock = threading.Lock()

        # Session info
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")
        self.action_count = 0

        # Initialize log files
        self._initialize_logs()

        logger.info(f"User action logger initialized - Session: {self.session_id}")

    def _initialize_logs(self):
        """Initialize log files with session information"""
        self.log_action(
            action_type="SESSION_START",
            details={
                "session_id": self.session_id,
                "start_time": self.session_start.isoformat(),
                "log_file": str(self.log_file),
            },
        )

    def log_action(
        self,
        action_type: str,
        details: Dict[str, Any],
        user_input: Optional[str] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """
        Log a user action with comprehensive details

        Args:
            action_type: Type of action (e.g., SEARCH, VIEW_DETAILS, COLLECT_DATA)
            details: Dictionary of action-specific details
            user_input: Raw user input if applicable
            result: Result of the action
            error: Error message if action failed
        """
        with self.lock:
            self.action_count += 1

            # Create action record
            action_record = {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "action_number": self.action_count,
                "action_type": action_type,
                "details": details,
                "user_input": user_input,
                "result": result,
                "error": error,
            }

            # Write to JSON Lines file (one JSON object per line)
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(action_record, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.error(f"Failed to write to action log: {e}")

            # Also write human-readable summary
            self._write_summary(action_record)

    def _write_summary(self, action_record: Dict[str, Any]):
        """Write human-readable summary to summary file"""
        try:
            with open(self.summary_file, "a", encoding="utf-8") as f:
                timestamp = action_record["timestamp"]
                action_type = action_record["action_type"]
                details = action_record.get("details", {})

                # Format summary line
                summary = f"[{timestamp}] [{self.session_id}] {action_type}"

                # Add key details based on action type
                if action_type == "SEARCH":
                    search_type = details.get("search_type", "unknown")
                    search_value = details.get("search_value", "")
                    result_count = details.get("result_count", 0)
                    summary += f" - Type: {search_type}, Value: {search_value}, Results: {result_count}"

                elif action_type == "VIEW_DETAILS":
                    apn = details.get("apn", "unknown")
                    summary += f" - APN: {apn}"

                elif action_type == "COLLECT_DATA":
                    apn = details.get("apn", "unknown")
                    data_type = details.get("data_type", "all")
                    summary += f" - APN: {apn}, Type: {data_type}"

                elif action_type == "EXPORT_DATA":
                    export_type = details.get("export_type", "unknown")
                    count = details.get("count", 0)
                    summary += f" - Type: {export_type}, Count: {count}"

                elif action_type == "ERROR":
                    error_type = details.get("error_type", "unknown")
                    summary += f" - Error: {error_type}"

                # Add result or error if present
                if action_record.get("result"):
                    summary += f" [SUCCESS]"
                if action_record.get("error"):
                    summary += f" [ERROR: {action_record['error'][:100]}]"

                f.write(summary + "\n")
                f.flush()  # Ensure immediate write

        except Exception as e:
            logger.error(f"Failed to write summary: {e}")

    def log_search(self, search_type: str, search_value: str, result_count: int = 0):
        """Log a search action"""
        self.log_action(
            action_type="SEARCH",
            details={
                "search_type": search_type,
                "search_value": search_value,
                "result_count": result_count,
            },
            user_input=f"{search_type}: {search_value}",
            result=f"Found {result_count} results",
        )

    def log_view_details(self, apn: str, property_data: Dict[str, Any] = None):
        """Log viewing property details"""
        self.log_action(
            action_type="VIEW_DETAILS",
            details={
                "apn": apn,
                "has_data": property_data is not None,
                "data_fields": list(property_data.keys()) if property_data else [],
            },
        )

    def log_collect_data(self, apn: str, data_type: str = "all", success: bool = True):
        """Log data collection action"""
        self.log_action(
            action_type="COLLECT_DATA",
            details={"apn": apn, "data_type": data_type, "success": success},
            result=(
                "Data collected successfully" if success else "Data collection failed"
            ),
        )

    def log_export(self, export_type: str, file_path: str, record_count: int):
        """Log data export action"""
        self.log_action(
            action_type="EXPORT_DATA",
            details={
                "export_type": export_type,
                "file_path": file_path,
                "count": record_count,
            },
            result=f"Exported {record_count} records to {file_path}",
        )

    def log_error(
        self, error_type: str, error_message: str, context: Dict[str, Any] = None
    ):
        """Log an error"""
        self.log_action(
            action_type="ERROR",
            details={"error_type": error_type, "context": context or {}},
            error=error_message,
        )

    def log_batch_operation(self, operation: str, apn_list: list, status: str):
        """Log batch operations"""
        self.log_action(
            action_type="BATCH_OPERATION",
            details={
                "operation": operation,
                "apn_count": len(apn_list),
                "apns": apn_list[:10],  # Log first 10 APNs
                "status": status,
            },
        )

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "action_count": self.action_count,
            "log_file": str(self.log_file),
            "summary_file": str(self.summary_file),
        }

    def export_full_log(self, output_path: Optional[str] = None) -> str:
        """
        Export full log for sharing/debugging

        Returns:
            Path to exported log file
        """
        if output_path is None:
            output_path = self.log_dir / f"export_{self.session_id}.txt"
        else:
            output_path = Path(output_path)

        try:
            with open(output_path, "w", encoding="utf-8") as out_file:
                # Write header
                out_file.write("=" * 80 + "\n")
                out_file.write("MARICOPA PROPERTY SEARCH - USER ACTION LOG EXPORT\n")
                out_file.write(f"Session: {self.session_id}\n")
                out_file.write(f"Exported: {datetime.now().isoformat()}\n")
                out_file.write("=" * 80 + "\n\n")

                # Write summary
                if self.summary_file.exists():
                    out_file.write("ACTION SUMMARY:\n")
                    out_file.write("-" * 40 + "\n")
                    with open(self.summary_file, "r", encoding="utf-8") as f:
                        out_file.write(f.read())
                    out_file.write("\n")

                # Write detailed log
                out_file.write("DETAILED ACTION LOG:\n")
                out_file.write("-" * 40 + "\n")
                if self.log_file.exists():
                    with open(self.log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                record = json.loads(line)
                                out_file.write(json.dumps(record, indent=2) + "\n")
                            except json.JSONDecodeError:
                                out_file.write(line)

                logger.info(f"Exported full log to {output_path}")
                return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export log: {e}")
            return None

    def close(self):
        """Close the logger and finalize session"""
        self.log_action(
            action_type="SESSION_END",
            details={
                "session_id": self.session_id,
                "end_time": datetime.now().isoformat(),
                "total_actions": self.action_count,
            },
        )
        logger.info(f"User action logger closed - Total actions: {self.action_count}")


# Global instance for easy access
_global_logger = None


def get_user_action_logger() -> UserActionLogger:
    """Get or create global user action logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = UserActionLogger()
    return _global_logger


def log_user_action(action_type: str, **kwargs):
    """Convenience function to log user actions"""
    logger = get_user_action_logger()
    logger.log_action(action_type, **kwargs)
