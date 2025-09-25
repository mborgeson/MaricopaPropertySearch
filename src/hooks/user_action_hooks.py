"""
User Action Tracking Hooks
Comprehensive user behavior analytics, session tracking, and usage patterns
"""
import hashlib
import json
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

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


class UserSessionTrackingHook(Hook):
    """Hook for tracking user sessions and activity"""
    def __init__(self):
        super().__init__("user_session_tracking", HookPriority.NORMAL)
        self.active_sessions = {}
        self.session_history = deque(maxlen=1000)
        self.session_timeout = 3600  # 1 hour
        self.session_stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "total_actions": 0,
            "unique_users": set(),
        }

    async def execute(self, context: HookContext) -> HookResult:
        """Track user sessions"""
        try:
            event_type = context.event_name.split(".")[-1]
            session_data = context.data

            if event_type == "start":
                return await self._handle_session_start(context, session_data)
            elif event_type == "activity":
                return await self._handle_session_activity(context, session_data)
            elif event_type == "end":
                return await self._handle_session_end(context, session_data)
            else:
                return HookResult(status=HookStatus.SUCCESS, result={"skipped": True})

        except Exception as e:
            logger.error(f"User session tracking hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _handle_session_start(
        self, context: HookContext, session_data: Dict
    ) -> HookResult:
        """Handle session start"""
        session_id = session_data.get("session_id") or str(uuid.uuid4())
        user_id = session_data.get("user_id", "anonymous")
        start_time = time.time()

        # Create session record
        session_record = {
            "session_id": session_id,
            "user_id": user_id,
            "start_time": start_time,
            "last_activity": start_time,
            "actions": [],
            "user_agent": session_data.get("user_agent", ""),
            "ip_address": self._hash_ip(session_data.get("ip_address", "")),
            "metadata": session_data.get("metadata", {}),
        }

        # Store active session
        self.active_sessions[session_id] = session_record

        # Update statistics
        self.session_stats["total_sessions"] += 1
        self.session_stats["active_sessions"] = len(self.active_sessions)
        self.session_stats["unique_users"].add(user_id)

        logger.info(f"User session started: {session_id} (user: {user_id})")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "session_id": session_id,
                "user_id": user_id,
                "session_started": True,
            },
        )

    async def _handle_session_activity(
        self, context: HookContext, session_data: Dict
    ) -> HookResult:
        """Handle session activity"""
        session_id = session_data.get("session_id")
        action = session_data.get("action", "unknown")
        current_time = time.time()

        if not session_id or session_id not in self.active_sessions:
            # Create implicit session if none exists
            if session_id:
                session_result = await self._handle_session_start(context, session_data)
                if session_result.status != HookStatus.SUCCESS:
                    return session_result
            else:
                logger.warning("Session activity without session ID")
                return HookResult(
                    status=HookStatus.SUCCESS, result={"warning": "No session ID"}
                )

        session_record = self.active_sessions[session_id]

        # Update last activity
        session_record["last_activity"] = current_time

        # Record action
        action_record = {
            "timestamp": current_time,
            "action": action,
            "details": session_data.get("details", {}),
            "source": context.source,
        }
        session_record["actions"].append(action_record)

        # Update statistics
        self.session_stats["total_actions"] += 1

        logger.debug(f"User action recorded: {action} in session {session_id}")

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "session_id": session_id,
                "action_recorded": True,
                "action_count": len(session_record["actions"]),
            },
        )

    async def _handle_session_end(
        self, context: HookContext, session_data: Dict
    ) -> HookResult:
        """Handle session end"""
        session_id = session_data.get("session_id")

        if not session_id or session_id not in self.active_sessions:
            logger.warning(f"Session end for unknown session: {session_id}")
            return HookResult(
                status=HookStatus.SUCCESS, result={"warning": "Unknown session"}
            )

        session_record = self.active_sessions[session_id]
        end_time = time.time()

        # Finalize session record
        session_record.update(
            {
                "end_time": end_time,
                "duration": end_time - session_record["start_time"],
                "total_actions": len(session_record["actions"]),
                "end_reason": session_data.get("end_reason", "explicit"),
            }
        )

        # Move to history
        self.session_history.append(session_record.copy())

        # Remove from active sessions
        del self.active_sessions[session_id]

        # Update statistics
        self.session_stats["active_sessions"] = len(self.active_sessions)

        logger.info(
            f"User session ended: {session_id} (duration: {session_record['duration']:.1f}s, actions: {session_record['total_actions']})"
        )

        return HookResult(
            status=HookStatus.SUCCESS,
            result={
                "session_id": session_id,
                "session_ended": True,
                "duration": session_record["duration"],
                "total_actions": session_record["total_actions"],
            },
        )
    def _hash_ip(self, ip_address: str) -> str:
        """Hash IP address for privacy"""
        if not ip_address:
            return ""
        return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = time.time()
        expired_sessions = []

        for session_id, session_record in self.active_sessions.items():
            if current_time - session_record["last_activity"] > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            session_record = self.active_sessions[session_id]
            session_record.update(
                {
                    "end_time": session_record["last_activity"],
                    "duration": session_record["last_activity"]
                    - session_record["start_time"],
                    "total_actions": len(session_record["actions"]),
                    "end_reason": "timeout",
                }
            )

            # Move to history
            self.session_history.append(session_record)
            del self.active_sessions[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        self.session_stats["active_sessions"] = len(self.active_sessions)
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        # Clean up expired sessions first
        self.cleanup_expired_sessions()

        recent_sessions = [
            s
            for s in self.session_history
            if datetime.fromtimestamp(s["start_time"])
            > datetime.now() - timedelta(days=1)
        ]

        avg_duration = 0
        avg_actions = 0
        if recent_sessions:
            avg_duration = sum(s.get("duration", 0) for s in recent_sessions) / len(
                recent_sessions
            )
            avg_actions = sum(s.get("total_actions", 0) for s in recent_sessions) / len(
                recent_sessions
            )

        return {
            "total_sessions": self.session_stats["total_sessions"],
            "active_sessions": self.session_stats["active_sessions"],
            "total_actions": self.session_stats["total_actions"],
            "unique_users": len(self.session_stats["unique_users"]),
            "recent_sessions_24h": len(recent_sessions),
            "avg_session_duration": avg_duration,
            "avg_actions_per_session": avg_actions,
        }


class UserBehaviorAnalyticsHook(Hook):
    """Hook for analyzing user behavior patterns"""
    def __init__(self):
        super().__init__("user_behavior_analytics", HookPriority.LOW)
        self.action_patterns = defaultdict(lambda: defaultdict(int))
        self.user_journeys = defaultdict(list)
        self.feature_usage = defaultdict(int)
        self.error_patterns = defaultdict(int)
        self.search_patterns = defaultdict(int)

    async def execute(self, context: HookContext) -> HookResult:
        """Analyze user behavior patterns"""
        try:
            action_data = context.data
            user_id = action_data.get("user_id", "anonymous")
            action = action_data.get("action", "unknown")
            details = action_data.get("details", {})

            # Record action pattern
            self.action_patterns[user_id][action] += 1

            # Track user journey
            journey_entry = {
                "timestamp": time.time(),
                "action": action,
                "details": details,
                "source": context.source,
            }
            self.user_journeys[user_id].append(journey_entry)

            # Keep only recent journey entries (last 100 per user)
            if len(self.user_journeys[user_id]) > 100:
                self.user_journeys[user_id] = self.user_journeys[user_id][-100:]

            # Analyze specific action types
            await self._analyze_specific_action(action, details)

            # Feature usage tracking
            feature = self._extract_feature_from_action(action, details)
            if feature:
                self.feature_usage[feature] += 1

            logger.debug(f"User behavior analyzed: {user_id} -> {action}")

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    "user_id": user_id,
                    "action": action,
                    "behavior_recorded": True,
                },
            )

        except Exception as e:
            logger.error(f"User behavior analytics hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)

    async def _analyze_specific_action(self, action: str, details: Dict):
        """Analyze specific action types"""
        if action == "search":
            search_type = details.get("search_type", "unknown")
            self.search_patterns[search_type] += 1

        elif action == "error":
            error_type = details.get("error_type", "unknown")
            self.error_patterns[error_type] += 1
    def _extract_feature_from_action(self, action: str, details: Dict) -> Optional[str]:
        """Extract feature name from action"""
        feature_map = {
            "search": "property_search",
            "export": "data_export",
            "view_property": "property_viewer",
            "view_tax_history": "tax_history",
            "view_sales_history": "sales_history",
            "batch_search": "batch_processing",
            "api_help": "api_documentation",
        }

        return feature_map.get(action)
    def get_behavior_insights(self, user_id: str = None) -> Dict[str, Any]:
        """Get behavior insights for specific user or all users"""
        if user_id:
            return self._get_user_insights(user_id)
        else:
            return self._get_global_insights()
    def _get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights for specific user"""
        if user_id not in self.action_patterns:
            return {"user_found": False}

        actions = self.action_patterns[user_id]
        journey = self.user_journeys[user_id]

        # Calculate user metrics
        total_actions = sum(actions.values())
        most_used_action = (
            max(actions.items(), key=lambda x: x[1]) if actions else ("none", 0)
        )

        # Analyze session patterns
        session_analysis = self._analyze_user_sessions(journey)

        return {
            "user_found": True,
            "total_actions": total_actions,
            "unique_actions": len(actions),
            "most_used_action": most_used_action[0],
            "most_used_action_count": most_used_action[1],
            "action_distribution": dict(actions),
            "session_analysis": session_analysis,
            "recent_journey": journey[-10:],  # Last 10 actions
        }
    def _get_global_insights(self) -> Dict[str, Any]:
        """Get global behavior insights"""
        # Aggregate all user actions
        all_actions = defaultdict(int)
        for user_actions in self.action_patterns.values():
            for action, count in user_actions.items():
                all_actions[action] += count

        # Get top actions
        top_actions = sorted(all_actions.items(), key=lambda x: x[1], reverse=True)[:10]

        # Feature usage insights
        top_features = sorted(
            self.feature_usage.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_users": len(self.action_patterns),
            "total_actions": sum(all_actions.values()),
            "unique_actions": len(all_actions),
            "top_actions": top_actions,
            "top_features": top_features,
            "search_patterns": dict(self.search_patterns),
            "error_patterns": dict(self.error_patterns),
        }
    def _analyze_user_sessions(self, journey: List[Dict]) -> Dict[str, Any]:
        """Analyze user session patterns from journey"""
        if not journey:
            return {"no_data": True}

        # Group actions by session (assuming 30-minute session timeout)
        sessions = []
        current_session = []
        session_timeout = 1800  # 30 minutes

        for action in journey:
            if (
                current_session
                and action["timestamp"] - current_session[-1]["timestamp"]
                > session_timeout
            ):
                # Start new session
                sessions.append(current_session)
                current_session = [action]
            else:
                current_session.append(action)

        if current_session:
            sessions.append(current_session)

        # Analyze sessions
        session_lengths = [len(session) for session in sessions]
        session_durations = [
            session[-1]["timestamp"] - session[0]["timestamp"]
            for session in sessions
            if len(session) > 1
        ]

        return {
            "total_sessions": len(sessions),
            "avg_session_length": (
                sum(session_lengths) / len(session_lengths) if session_lengths else 0
            ),
            "avg_session_duration": (
                sum(session_durations) / len(session_durations)
                if session_durations
                else 0
            ),
            "max_session_length": max(session_lengths) if session_lengths else 0,
            "total_actions": sum(session_lengths),
        }


class UsageMetricsHook(Hook):
    """Hook for collecting usage metrics and KPIs"""
    def __init__(self):
        super().__init__("usage_metrics", HookPriority.LOW)
        self.daily_metrics = defaultdict(lambda: defaultdict(int))
        self.hourly_metrics = defaultdict(lambda: defaultdict(int))
        self.feature_metrics = defaultdict(
            lambda: {
                "usage_count": 0,
                "unique_users": set(),
                "total_time": 0,
                "error_count": 0,
            }
        )

    async def execute(self, context: HookContext) -> HookResult:
        """Collect usage metrics"""
        try:
            metrics_data = context.data
            current_time = datetime.now()
            date_key = current_time.strftime("%Y-%m-%d")
            hour_key = current_time.strftime("%Y-%m-%d-%H")

            action = metrics_data.get("action", "unknown")
            user_id = metrics_data.get("user_id", "anonymous")
            feature = metrics_data.get("feature")
            duration = metrics_data.get("duration", 0)
            success = metrics_data.get("success", True)

            # Update daily metrics
            self.daily_metrics[date_key]["total_actions"] += 1
            self.daily_metrics[date_key]["unique_users"] = len(
                set(list(self.daily_metrics[date_key].get("users", set())) + [user_id])
            )

            # Update hourly metrics
            self.hourly_metrics[hour_key]["total_actions"] += 1
            self.hourly_metrics[hour_key][action] += 1

            # Update feature metrics
            if feature:
                feature_stats = self.feature_metrics[feature]
                feature_stats["usage_count"] += 1
                feature_stats["unique_users"].add(user_id)
                feature_stats["total_time"] += duration

                if not success:
                    feature_stats["error_count"] += 1

            logger.debug(f"Usage metrics updated: {action} (feature: {feature})")

            return HookResult(
                status=HookStatus.SUCCESS,
                result={
                    "metrics_updated": True,
                    "date_key": date_key,
                    "action": action,
                    "feature": feature,
                },
            )

        except Exception as e:
            logger.error(f"Usage metrics hook error: {e}")
            return HookResult(status=HookStatus.FAILED, error=e)
    def get_usage_report(self, days: int = 7) -> Dict[str, Any]:
        """Get usage report for specified number of days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Collect daily metrics for the period
        period_metrics = {}
        for i in range(days):
            date = start_date + timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")
            period_metrics[date_key] = dict(self.daily_metrics.get(date_key, {}))

        # Calculate feature usage summary
        feature_summary = {}
        for feature, stats in self.feature_metrics.items():
            avg_time = stats["total_time"] / max(1, stats["usage_count"])
            error_rate = (stats["error_count"] / max(1, stats["usage_count"])) * 100

            feature_summary[feature] = {
                "usage_count": stats["usage_count"],
                "unique_users": len(stats["unique_users"]),
                "avg_usage_time": avg_time,
                "error_rate": error_rate,
            }

        # Get top features
        top_features = sorted(
            feature_summary.items(), key=lambda x: x[1]["usage_count"], reverse=True
        )[:10]

        return {
            "report_period_days": days,
            "daily_metrics": period_metrics,
            "feature_summary": feature_summary,
            "top_features": [{"feature": f[0], **f[1]} for f in top_features],
            "total_actions": sum(
                stats["usage_count"] for stats in self.feature_metrics.values()
            ),
            "total_features_used": len(self.feature_metrics),
        }


# Register user action hooks
def register_user_action_hooks():
    """Register all user action hooks with the hook manager"""
    hook_manager = get_hook_manager()

    # Register hooks
    hook_manager.register_hook("user.session.start", UserSessionTrackingHook())
    hook_manager.register_hook("user.session.activity", UserSessionTrackingHook())
    hook_manager.register_hook("user.session.end", UserSessionTrackingHook())

    hook_manager.register_hook("user.action", UserBehaviorAnalyticsHook())
    hook_manager.register_hook("user.action", UsageMetricsHook())

    logger.info("User action tracking hooks registered successfully")


# Convenience functions for triggering user events
def track_user_session_start(session_id: str, user_id: str = None, **metadata):
    """Track user session start"""
    from hook_manager import emit_hook

    return emit_hook(
        "user.session.start",
        "user_tracker",
        session_id=session_id,
        user_id=user_id or "anonymous",
        metadata=metadata,
    )
def track_user_action(session_id: str, action: str, user_id: str = None, **details):
    """Track user action"""
    from hook_manager import emit_hook

    return emit_hook(
        "user.session.activity",
        "user_tracker",
        session_id=session_id,
        user_id=user_id or "anonymous",
        action=action,
        details=details,
    )
def track_user_session_end(session_id: str, reason: str = "explicit"):
    """Track user session end"""
    from hook_manager import emit_hook

    return emit_hook(
        "user.session.end", "user_tracker", session_id=session_id, end_reason=reason
    )
    def track_feature_usage(
    feature: str, user_id: str = None, duration: float = 0, success: bool = True
):
    """Track feature usage"""
    from hook_manager import emit_hook

    return emit_hook(
        "user.action",
        "feature_tracker",
        action="feature_usage",
        feature=feature,
        user_id=user_id or "anonymous",
        duration=duration,
        success=success,
    )
