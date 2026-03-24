"""
Database Models and Session Management
SQLAlchemy setup for call history and emotion logs
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Text, ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load .env file if present (allows DATABASE_URL override without editing code)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./emotion_detection.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Call(Base):
    """Call session model"""
    __tablename__ = 'calls'
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(255), unique=True, index=True)
    agent_name = Column(String(255), default='Unknown')
    customer_name = Column(String(255), default='Unknown')
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    status = Column(String(50), default='active')  # active, completed, failed
    audio_file_path = Column(String(500), nullable=True)
    
    # Summary statistics
    dominant_emotion = Column(String(50), nullable=True)
    emotion_distribution = Column(JSON, default=dict)
    avg_confidence = Column(Float, default=0.0)
    
    # Relationships
    emotion_logs = relationship("EmotionLog", back_populates="call", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'agent_name': self.agent_name,
            'customer_name': self.customer_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'status': self.status,
            'dominant_emotion': self.dominant_emotion,
            'emotion_distribution': self.emotion_distribution,
            'avg_confidence': self.avg_confidence
        }


class EmotionLog(Base):
    """Real-time emotion detection logs"""
    __tablename__ = 'emotion_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(255), ForeignKey('calls.call_id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    time_offset_seconds = Column(Float, default=0.0)
    
    # Emotion prediction
    emotion = Column(String(50))
    confidence = Column(Float)
    all_probabilities = Column(JSON)
    
    # Audio metadata
    is_speech = Column(Boolean, default=True)
    audio_energy = Column(Float, nullable=True)
    
    # Relationship
    call = relationship("Call", back_populates="emotion_logs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'time_offset_seconds': self.time_offset_seconds,
            'emotion': self.emotion,
            'confidence': self.confidence,
            'all_probabilities': self.all_probabilities,
            'is_speech': self.is_speech,
            'audio_energy': self.audio_energy
        }


class User(Base):
    """User account model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    password_hash = Column(String(255))
    role = Column(String(50), default='agent')
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Database operations
class DatabaseManager:
    """High-level database operations"""
    
    def __init__(self):
        self.Session = SessionLocal
    
    def get_session(self):
        """Get database session"""
        session = self.Session()
        try:
            yield session
        finally:
            session.close()
    
    def create_call(self, call_id: str, agent_name: str = 'Unknown', customer_name: str = 'Unknown') -> Call:
        """Create a new call record"""
        session = self.Session()
        call = Call(
            call_id=call_id,
            agent_name=agent_name,
            customer_name=customer_name,
            start_time=datetime.utcnow(),
            status='active'
        )
        session.add(call)
        session.commit()
        session.refresh(call)
        session.close()
        return call
    
    def end_call(self, call_id: str, emotion_stats: dict = None):
        """Mark call as ended with statistics"""
        session = self.Session()
        call = session.query(Call).filter(Call.call_id == call_id).first()
        if call:
            call.end_time = datetime.utcnow()
            call.status = 'completed'
            if call.start_time:
                call.duration_seconds = int((call.end_time - call.start_time).total_seconds())
            
            if emotion_stats:
                call.dominant_emotion = emotion_stats.get('dominant_emotion')
                call.emotion_distribution = emotion_stats.get('distribution', {})
                call.avg_confidence = emotion_stats.get('avg_confidence', 0.0)
            
            session.commit()
        session.close()
    
    def log_emotion(self, call_id: str, emotion_data: dict):
        """Log an emotion detection event"""
        session = self.Session()
        log = EmotionLog(
            call_id=call_id,
            time_offset_seconds=emotion_data.get('time_offset', 0),
            emotion=emotion_data.get('emotion', 'unknown'),
            confidence=emotion_data.get('confidence', 0.0),
            all_probabilities=emotion_data.get('probabilities', {}),
            is_speech=emotion_data.get('is_speech', True),
            audio_energy=emotion_data.get('audio_energy')
        )
        session.add(log)
        session.commit()
        session.close()
    
    def get_call(self, call_id: str) -> Call:
        """Get call by ID"""
        session = self.Session()
        call = session.query(Call).filter(Call.call_id == call_id).first()
        session.close()
        return call
    
    def get_call_history(self, limit: int = 100, offset: int = 0) -> list:
        """Get call history with pagination"""
        session = self.Session()
        calls = session.query(Call).order_by(Call.start_time.desc()).offset(offset).limit(limit).all()
        result = [call.to_dict() for call in calls]
        session.close()
        return result
    
    def get_call_emotions(self, call_id: str) -> list:
        """Get all emotion logs for a call"""
        session = self.Session()
        logs = session.query(EmotionLog).filter(
            EmotionLog.call_id == call_id
        ).order_by(EmotionLog.time_offset_seconds).all()
        result = [log.to_dict() for log in logs]
        session.close()
        return result
    
    def compute_agent_analytics(self, agent_name: str = None, days: int = 30) -> list:
        """Compute agent analytics from actual call data"""
        from datetime import timedelta
        session = self.Session()

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = session.query(Call).filter(
            Call.status == 'completed',
            Call.start_time >= cutoff_date
        )
        if agent_name:
            query = query.filter(Call.agent_name == agent_name)
        calls = query.all()

        agent_data: dict = {}
        for call in calls:
            agent = call.agent_name or 'Unknown'
            if agent not in agent_data:
                agent_data[agent] = {'total_calls': 0, 'total_duration': 0, 'emotion_totals': {}}
            d = agent_data[agent]
            d['total_calls'] += 1
            d['total_duration'] += call.duration_seconds or 0
            if call.emotion_distribution:
                for emotion, pct in call.emotion_distribution.items():
                    d['emotion_totals'][emotion] = d['emotion_totals'].get(emotion, 0) + (pct or 0)

        session.close()

        POSITIVE = {'happy', 'neutral', 'surprised'}
        NEGATIVE = {'angry', 'sad', 'fearful', 'disgust'}

        result = []
        for agent, d in agent_data.items():
            n = d['total_calls']
            total_emo = sum(d['emotion_totals'].values()) or 1
            pos = sum(d['emotion_totals'].get(e, 0) for e in POSITIVE) / total_emo
            neg = sum(d['emotion_totals'].get(e, 0) for e in NEGATIVE) / total_emo
            result.append({
                'agent_name': agent,
                'total_calls': n,
                'total_duration_seconds': d['total_duration'],
                'avg_call_duration': round(d['total_duration'] / n, 1) if n else 0,
                'positive_emotion_ratio': round(pos, 3),
                'negative_emotion_ratio': round(neg, 3),
                'avg_customer_satisfaction': round(pos * 100, 1)
            })
        return sorted(result, key=lambda x: x['total_calls'], reverse=True)

    def get_emotions_trend(self, days: int = 7) -> list:
        """Get daily emotion breakdown for trend charts"""
        from datetime import timedelta
        session = self.Session()
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        calls = session.query(Call).filter(
            Call.start_time >= cutoff_date
        ).order_by(Call.start_time).all()

        trends: dict = {}
        for call in calls:
            day = call.start_time.strftime('%Y-%m-%d')
            if day not in trends:
                trends[day] = {'date': day, 'call_count': 0}
            trends[day]['call_count'] += 1
            if call.emotion_distribution:
                for emotion, pct in call.emotion_distribution.items():
                    trends[day][emotion] = round(trends[day].get(emotion, 0) + (pct or 0), 3)

        session.close()
        return sorted(trends.values(), key=lambda x: x['date'])

    def get_overall_summary(self, days: int = 30) -> dict:
        """Get overall analytics summary"""
        from datetime import timedelta
        session = self.Session()
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        total_calls = session.query(Call).filter(Call.start_time >= cutoff_date).count()
        completed = session.query(Call).filter(
            Call.status == 'completed',
            Call.start_time >= cutoff_date
        ).all()

        avg_duration = 0.0
        emotion_totals: dict = {}
        if completed:
            avg_duration = sum(c.duration_seconds or 0 for c in completed) / len(completed)
            for call in completed:
                if call.emotion_distribution:
                    for emotion, pct in call.emotion_distribution.items():
                        emotion_totals[emotion] = emotion_totals.get(emotion, 0) + (pct or 0)

        total_agents = len(set(c.agent_name for c in completed)) if completed else 0
        session.close()

        total_emo = sum(emotion_totals.values()) or 1
        top_emotion = max(emotion_totals, key=emotion_totals.get) if emotion_totals else 'neutral'
        POSITIVE = {'happy', 'neutral', 'surprised'}
        pos_ratio = sum(emotion_totals.get(e, 0) for e in POSITIVE) / total_emo

        return {
            'total_calls': total_calls,
            'completed_calls': len(completed),
            'total_agents': total_agents,
            'avg_call_duration': round(avg_duration, 1),
            'top_emotion': top_emotion,
            'positive_sentiment_rate': round(pos_ratio * 100, 1),
            'emotion_distribution': {k: round(v / total_emo, 3) for k, v in emotion_totals.items()}
        }

    def update_emotion_stats(self, call_id: str, emotion_stats: dict):
        """Overwrite emotion stats on a call (used after full-recording post-analysis)"""
        session = self.Session()
        call = session.query(Call).filter(Call.call_id == call_id).first()
        if call and emotion_stats:
            call.dominant_emotion = emotion_stats.get('dominant_emotion')
            call.emotion_distribution = emotion_stats.get('distribution', {})
            call.avg_confidence = emotion_stats.get('avg_confidence', 0.0)
            session.commit()
        session.close()

    def set_audio_path(self, call_id: str, audio_path: str):
        """Store the path to the saved recording"""
        session = self.Session()
        call = session.query(Call).filter(Call.call_id == call_id).first()
        if call:
            call.audio_file_path = audio_path
            session.commit()
        session.close()

    def update_user_name(self, user_id: int, name: str):
        """Update user's display name"""
        session = self.Session()
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.name = name
            session.commit()
        session.close()

    def create_user(self, email: str, name: str, password_hash: str, role: str = 'agent') -> dict:
        """Create a new user, returns dict with all fields including password_hash"""
        session = self.Session()
        user = User(email=email, name=name, password_hash=password_hash, role=role)
        session.add(user)
        session.commit()
        result = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'password_hash': user.password_hash,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        session.close()
        return result

    def get_user_by_email(self, email: str) -> dict | None:
        """Get user by email as dict (includes password_hash for verification)"""
        session = self.Session()
        user = session.query(User).filter(User.email == email).first()
        if not user:
            session.close()
            return None
        result = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'password_hash': user.password_hash,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        session.close()
        return result

    def delete_call(self, call_id: str) -> bool:
        """Delete a call record and all associated logs"""
        session = self.Session()
        try:
            call = session.query(Call).filter(Call.call_id == call_id).first()
            if call:
                # Remove audio file if it exists
                if call.audio_file_path and os.path.exists(call.audio_file_path):
                    try:
                        os.remove(call.audio_file_path)
                    except Exception as e:
                        print(f"Error removing audio file: {e}")
                
                session.delete(call)
                session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error deleting call: {e}")
            session.rollback()
            return False
        finally:
            session.close()


# Initialize database
def init_database():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


# Global database manager instance
db_manager = DatabaseManager()

if __name__ == '__main__':
    init_database()
