from .models import init_db, Activity, ActivityLog, ActivityDescriptionLog, Setting
from datetime import datetime, timedelta
import os
from sqlalchemy import func

class StorageManager:
    def __init__(self, db_path="gainhour.db"):
        self.Session = init_db(db_path)
    
    def get_session(self):
        return self.Session()
    
    def get_activity_by_name(self, name, activity_type='app'):
        session = self.get_session()
        try:
            return session.query(Activity).filter_by(name=name, type=activity_type).first()
        finally:
            session.close()

    def get_activity_by_id(self, activity_id):
        session = self.get_session()
        try:
            return session.query(Activity).get(activity_id)
        finally:
            session.close()

    def get_activity_by_id(self, activity_id):
        session = self.get_session()
        try:
            return session.query(Activity).get(activity_id)
        finally:
            session.close()


    def get_or_create_activity(self, name, activity_type='app', description=None, icon_path=None):
        session = self.get_session()
        try:
            activity = session.query(Activity).filter_by(name=name, type=activity_type).first()
            if not activity:
                # Force description to None if type is 'app'
                if activity_type == 'app':
                    description = None
                    
                activity = Activity(name=name, type=activity_type, description=description, icon_path=icon_path)
                session.add(activity)
                session.commit()
                # Refresh to get ID
                session.refresh(activity)
            elif icon_path and not activity.icon_path:
                # Update icon if missing
                activity.icon_path = icon_path
                session.commit()
                session.refresh(activity)
            return activity
        finally:
            session.close()

    def start_logging(self, activity_id):
        session = self.get_session()
        try:
            log = ActivityLog(activity_id=activity_id, start_time=datetime.now())
            session.add(log)
            session.commit()
            session.refresh(log)
            return log.id
        finally:
            session.close()

    def stop_logging(self, log_id):
        session = self.get_session()
        try:
            log = session.query(ActivityLog).get(log_id)
            if log:
                # Always update end_time (Heartbeat approach)
                log.end_time = datetime.now()
                log.duration_seconds = int((log.end_time - log.start_time).total_seconds())
                session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()
            
    def get_all_activities(self):
        session = self.get_session()
        try:
            return session.query(Activity).all()
        finally:
            session.close()

    def update_activity_visibility(self, activity_id, visible):
        session = self.get_session()
        try:
            activity = session.query(Activity).get(activity_id)
            if activity:
                activity.discord_visible = visible
                session.commit()
        finally:
            session.close()

    def update_activity(self, activity_id, description=None, icon_path=None):
        session = self.get_session()
        try:
            activity = session.query(Activity).get(activity_id)
            if activity:
                if description is not None:
                     # Only update description if NOT app, or if explicit override logic exists?
                     # User said: "make sure description wont be automaticly recorded here... only for irl tags"
                     # Since this method might be used by UI for manual edits, we should probably allow manual edits?
                     # But user request implies rigid rule. 
                     # Let's assume this method is general purpose. 
                     # Actually, safe to just allow it here, as tracker calls are the main source of auto-updates.
                     # But let's add a guard if it's 'app' and we want to enforce the rule strictly.
                     if activity.type != 'app':
                        activity.description = description
                if icon_path is not None:
                    activity.icon_path = icon_path
                session.commit()
        finally:
            session.close()


    def get_activity_stats(self):
        session = self.get_session()
        try:
            # Query to sum duration for each activity
            # We filter out logs with 0 duration or no end_time (still running)
            # For simplicity, we just look at closed logs
            activities = session.query(Activity).all()
            stats = []
            for activity in activities:
                total_seconds = sum(log.duration_seconds for log in activity.logs if log.duration_seconds)
                if total_seconds > 0:
                     stats.append({
                        "name": activity.name,
                        "type": activity.type,
                        "total_seconds": total_seconds,
                        "icon_path": activity.icon_path
                    })
            # Sort by duration
            stats.sort(key=lambda x: x['total_seconds'], reverse=True)
            return stats
        finally:
            session.close()

    def get_activity_duration(self, name, activity_type='app'):
        session = self.get_session()
        try:
            activity = session.query(Activity).filter_by(name=name, type=activity_type).first()
            if not activity:
                return 0
            
            # Use SQL sum for efficiency
            total = session.query(func.sum(ActivityLog.duration_seconds)).filter(
                ActivityLog.activity_id == activity.id
            ).scalar()
            return total if total else 0
        finally:
            session.close()

    def get_today_duration(self, name, activity_type='app'):
        session = self.get_session()
        try:
            activity = session.query(Activity).filter_by(name=name, type=activity_type).first()
            if not activity:
                return 0
            
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            total = session.query(func.sum(ActivityLog.duration_seconds)).filter(
                ActivityLog.activity_id == activity.id,
                ActivityLog.start_time >= today_start
            ).scalar()
            return total if total else 0
        finally:
            session.close()

    def get_total_today_duration(self):
        session = self.get_session()
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            total = session.query(func.sum(ActivityLog.duration_seconds)).filter(
                ActivityLog.start_time >= today_start
            ).scalar()
            return total if total else 0
        finally:
            session.close()

    def get_today_stats(self):
        session = self.get_session()
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            # We need to sum durations for logs starting today, grouped by activity
            # But straightforward way: get all activities, sum their logs for today
            activities = session.query(Activity).all()
            stats = []
            
            for activity in activities:
                # Calculate total seconds for today ONLY
                # We could do a join query but this is simpler for now
                total_seconds = sum(
                    log.duration_seconds for log in activity.logs 
                    if log.start_time >= today_start and log.duration_seconds
                )
                
                if total_seconds > 0:
                    stats.append({
                        "name": activity.name,
                        "type": activity.type,
                        "total_seconds": total_seconds,
                        "icon_path": activity.icon_path
                    })
            
            stats.sort(key=lambda x: x['total_seconds'], reverse=True)
            stats.sort(key=lambda x: x['total_seconds'], reverse=True)
            return stats
        finally:
            session.close()

    def get_daily_stats(self, target_date):
        """Get stats for a specific date (date object)."""
        session = self.get_session()
        try:
            # Range: target_date 00:00:00 to target_date 23:59:59
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            
            activities = session.query(Activity).all()
            stats = []
            
            for activity in activities:
                # Sum logs that STARTED within the range
                # Or cover the range? Simple approach: start_time in range.
                total_seconds = sum(
                    log.duration_seconds for log in activity.logs 
                    if log.start_time >= start_dt and log.start_time <= end_dt and log.duration_seconds
                )
                
                if total_seconds > 0:
                    stats.append({
                        "name": activity.name,
                        "type": activity.type,
                        "total_seconds": total_seconds,
                        "icon_path": activity.icon_path
                    })
            
            stats.sort(key=lambda x: x['total_seconds'], reverse=True)
            return stats
        finally:
            session.close()


    def clean_explorer_data(self):
        session = self.get_session()
        try:
            # Find explorer activity
            activity = session.query(Activity).filter_by(name="explorer.exe").first()
            if activity:
                # Delete logs first
                session.query(ActivityLog).filter_by(activity_id=activity.id).delete()
                # Delete activity
                session.delete(activity)
                session.commit()
        except Exception as e:
            print(f"Error cleaning explorer data: {e}")
            session.rollback()
        finally:
            session.close()

    def start_description_log(self, activity_id, description):
        session = self.get_session()
        try:
            log = ActivityDescriptionLog(activity_id=activity_id, description=description, start_time=datetime.now())
            session.add(log)
            session.commit()
            session.refresh(log)
            return log.id
        finally:
            session.close()

    def stop_description_log(self, log_id):
        session = self.get_session()
        try:
            log = session.query(ActivityDescriptionLog).get(log_id)
            if log:
                # Always update end_time (Heartbeat approach)
                log.end_time = datetime.now()
                log.duration_seconds = int((log.end_time - log.start_time).total_seconds())
                session.commit()
        finally:
            session.close()

    def update_log_heartbeat(self, log_id):
        """Update end_time of a log to now without closing it conceptually (keeps it valid)."""
        self.stop_logging(log_id) # Re-use stop logic as it just updates timestamp

    def update_desc_heartbeat(self, log_id):
        self.stop_description_log(log_id)

    def cleanup_incomplete_logs(self):
        """Close any logs that were left open (NULL end_time) due to crashes."""
        session = self.get_session()
        try:
            # 1. Activity Logs
            incomplete_logs = session.query(ActivityLog).filter(ActivityLog.end_time == None).all()
            count = 0
            for log in incomplete_logs:
                # Set end_time to start_time (0 duration) or maybe 1 minute later?
                # User asked to fix nulls. Closing them at start_time is safest "cleaning".
                # Or we could assume they lasted 1 min?
                log.end_time = log.start_time
                log.duration_seconds = 0
                count += 1
            
            # 2. Description Logs
            incomplete_desc = session.query(ActivityDescriptionLog).filter(ActivityDescriptionLog.end_time == None).all()
            d_count = 0
            for log in incomplete_desc:
                log.end_time = log.start_time
                log.duration_seconds = 0
                d_count += 1
                
            session.commit()
            print(f"Cleanup: Closed {count} logs and {d_count} desc logs.")
        finally:
            session.close()

    def get_description_stats(self, activity_id, description):
        session = self.get_session()
        try:
            count = session.query(func.count(ActivityDescriptionLog.id)).filter_by(activity_id=activity_id, description=description).scalar()
            total_duration = session.query(func.sum(ActivityDescriptionLog.duration_seconds)).filter_by(activity_id=activity_id, description=description).scalar()
            return {
                "count": count if count else 0,
                "total_seconds": total_duration if total_duration else 0
            }
        finally:
            session.close()

    def get_activity_description_logs(self, activity_id, today_only=False):
        """
        Fetch description logs for an activity. 
        Returns a list of dicts:
        {
            'description': str,
            'start_time': datetime,
            'end_time': datetime,
            'duration': int (seconds),
            'count': int (total times this desc used),
            'total_usage': int (total seconds this desc used)
        }
        """
        session = self.get_session()
        try:
            query = session.query(ActivityDescriptionLog).filter_by(activity_id=activity_id)
            
            if today_only:
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(ActivityDescriptionLog.start_time >= today_start)
            
            logs = query.order_by(ActivityDescriptionLog.start_time.desc()).all()
            
            # To get "Count" and "Total Usage" for each description efficiently:
            # We can pre-calculate stats for ALL descriptions of this activity (not just today's if today_only is set? 
            # User asked: "how many times this description used. total time of usege of this description."
            # Usually this implies "Total Historical Stats" even if viewing today's logs.
            # So let's fetch global stats for the descriptions present in the logs.
            
            # 1. Get unique descriptions from the fetched logs to optimize
            unique_descs = set(log.description for log in logs if log.description)
            
            stats_map = {}
            if unique_descs:
                # Group by description to get global stats
                stat_query = session.query(
                    ActivityDescriptionLog.description, 
                    func.count(ActivityDescriptionLog.id), 
                    func.sum(ActivityDescriptionLog.duration_seconds)
                ).filter(
                    ActivityDescriptionLog.activity_id == activity_id,
                    ActivityDescriptionLog.description.in_(unique_descs)
                ).group_by(ActivityDescriptionLog.description).all()
                
                for desc, count, total_sec in stat_query:
                    stats_map[desc] = {
                        'count': count,
                        'total_seconds': total_sec if total_sec else 0
                    }
            
            result = []
            for log in logs:
                desc = log.description if log.description else "(No Description)"
                s = stats_map.get(log.description, {'count': 0, 'total_seconds': 0})
                
                result.append({
                    'description': desc,
                    'start_time': log.start_time,
                    'end_time': log.end_time,
                    'duration': log.duration_seconds if log.duration_seconds else 0,
                    'count': s['count'],
                    'total_usage': s['total_seconds']
                })
                
            return result
        finally:
            session.close()
    

    def delete_activity(self, activity_id):
        """Cascading delete for an activity."""
        session = self.get_session()
        try:
            activity = session.query(Activity).get(activity_id)
            if not activity:
                return False
            
            # 1. Delete Icon File if custom
            if activity.icon_path and os.path.exists(activity.icon_path):
                # Try to delete file
                try:
                    os.remove(activity.icon_path)
                except Exception as e:
                    print(f"Error deleting icon file: {e}")

            # 2. Delete Logs (Cascade usually handles this if set up, but safer to do explicit)
            session.query(ActivityLog).filter_by(activity_id=activity_id).delete()
            session.query(ActivityDescriptionLog).filter_by(activity_id=activity_id).delete()
            
            # 3. Delete Activity
            session.delete(activity)
            session.commit()
            return True
        except Exception as e:
            print(f"Error deleting activity {activity_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_setting(self, key, default=None):
        session = self.get_session()
        try:
            from src.database.models import Setting
            setting = session.query(Setting).get(key)
            return setting.value if setting else default
        finally:
            session.close()

    def set_setting(self, key, value):
        session = self.get_session()
        try:
            from src.database.models import Setting
            setting = session.query(Setting).get(key)
            if not setting:
                setting = Setting(key=key, value=str(value)) # Store as string
                session.add(setting)
            else:
                setting.value = str(value)
            session.commit()
        finally:
            session.close()

    def cleanup_old_description_logs(self):
        """Deletes all description logs that started before today (00:00:00)."""
        session = self.get_session()
        try:
            from src.database.models import ActivityDescriptionLog
            # Get start of today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Delete older logs
            deleted = session.query(ActivityDescriptionLog).filter(ActivityDescriptionLog.start_time < today_start).delete()
            session.commit()
            print(f"Cleanup: Deleted {deleted} old description logs.")
            return deleted
        except Exception as e:
            print(f"Error cleaning old logs: {e}")
            session.rollback()
        finally:
            session.close()

    def get_daily_activity_breakdown(self):
        """
        Returns { date_obj: { activity_name: total_seconds } }
        Aggregates duration per activity per day.
        """
        session = self.get_session()
        try:
            # Group by Date and Activity
            # SQLite returns date string 'YYYY-MM-DD'
            data = session.query(
                func.date(ActivityLog.start_time),
                Activity.name,
                func.sum(ActivityLog.duration_seconds)
            ).join(Activity).group_by(func.date(ActivityLog.start_time), Activity.name).all()
            
            result = {}
            for day_str, act_name, duration in data:
                if not day_str or not duration: 
                    continue
                
                try:
                    day = datetime.strptime(day_str, "%Y-%m-%d").date()
                except ValueError:
                    continue # Skip invalid dates
                    
                if day not in result:
                    result[day] = {}
                # Handle potentially None duration (though we filtered)
                result[day][act_name] = duration
                
            return result
        finally:
            session.close()

    def wipe_data(self):
        """Hard resets the database by wiping all tables."""
        session = self.get_session()
        try:
            from src.database.models import Activity, ActivityLog, ActivityDescriptionLog, Setting
            # Clear logs first due to foreign keys
            session.query(ActivityDescriptionLog).delete()
            session.query(ActivityLog).delete()
            session.query(Activity).delete()
            session.query(Setting).delete()
            session.commit()
            print("Database wiped successfully.")
            return True
        except Exception as e:
            print(f"Error wiping database: {e}")
            session.rollback()
            return False
        finally:
            session.close()
