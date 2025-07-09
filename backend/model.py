from sqlalchemy import Column, Integer, String, DateTime, ForeignKey,Enum,Text
from sqlalchemy.orm import relationship,declarative_base
import datetime,enum
from passlib import hash

Base = declarative_base()
class UserRole(str, enum.Enum):
    student = 'student'
    lecturer = "lecturer"
    admin = "admin"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    student_id = Column(String(50),unique=True,nullable=False )
    name = Column(String(50),nullable=False )
    email = Column(String(255),unique=True,nullable=False )
    hashed_password = Column(String(255),nullable=False )
    role = Column(Enum(UserRole),nullable=False,default=UserRole.admin)

    def verify_password(self,password:str):
        return hash.bcrypt.verify(password,self.hashed_password)
    # Relationships
    reviews = relationship("Review", back_populates="author")
    taught_courses = relationship("CourseUnit", back_populates="lecturer")


class CourseUnit(Base):
    __tablename__ = 'course_units'
    id = Column(Integer, primary_key=True,index=True)
    title = Column(String(100),nullable=False )
    code = Column(String(20), unique=True, nullable=False)
    lecturer_id = Column(Integer,ForeignKey('users.id'),nullable=False )

    # Relationships
    lecturer = relationship("User", back_populates="taught_courses")
    reviews = relationship("Review", back_populates="course")


class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True,index=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer,ForeignKey('course_units.id'),nullable=False)
    text = Column(Text, nullable=False)  # Original review text
    clean_text = Column(Text, nullable=True)  # Preprocessed text for ML
    sentiment = Column(String,nullable=False)
    create_at = Column(DateTime,default=datetime.datetime.utcnow)

    # Relationships
    author = relationship("User", back_populates="reviews")
    course = relationship("CourseUnit", back_populates="reviews")

