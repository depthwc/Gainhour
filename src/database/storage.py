from .models import init_db, Activity, ActivityLog, Setting
from datetime import datetime, timedelta
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

    def get_or_create_activity(self, name, activity_type='app', description=None, icon_path=None):
        session = self.get_session()
        try:
            activity = session.query(Activity).filter_by(name=name, type=activity_type).first()
            if not activity:
                activity = Activity(name=name, type=activity_type, description=description, icon_path=icon_path)
                session.add(activity)
                session.commit()
                # Refresh to get ID
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
            if log and log.end_time is None:
                log.end_time = datetime.now()
                log.duration_seconds = int((log.end_time - log.start_time).total_seconds())
                session.commit()
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
