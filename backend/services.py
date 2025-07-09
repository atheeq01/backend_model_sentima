import jwt
import sqlalchemy.orm as orm
from fastapi import HTTPException

import database,model,schemas
from passlib import hash
import fastapi
import fastapi.security as security

import ml_util

JWT_SECRET = "myJwtSecret"

def create_database():
    return database.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_user_by_email(email:str,db : orm.Session):
    return db.query(model.User).filter(model.User.email == email).first()

async def create_user(user:schemas.UserCreate,db : orm.Session,):
    user_obj = model.User(
        student_id=user.student_id,
        name=user.name,
        email=str(user.email),
        hashed_password= hash.bcrypt.hash(user.password),
        role=user.role
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj


async def authenticate_user(email:str,password:str,db : orm.Session):
    user = await get_user_by_email(email=email,db=db)
    if not user:
        return False
    if not user.verify_password(password):
        return False

    return user

async def create_token(user:model.User):
    user_obj = schemas.UserResponse.from_orm(user)

    token= jwt.encode(user_obj.dict(),JWT_SECRET)
    return dict(access_token=token,token_type="bearer")

# get the current user
async def get_current_user(db: orm.Session = fastapi.Depends(get_db),token:str = fastapi.Depends(security.OAuth2PasswordBearer(tokenUrl="/auth/token"))):
    try:
        payload = jwt.decode(token,JWT_SECRET,algorithms=["HS256"])
        user = db.query(model.User).get(payload["id"])
    except:
        raise fastapi.HTTPException(status_code=404,detail="invalid Email or password")

    return schemas.UserResponse.from_orm(user)

# check the user is admin or not
async def require_admin(user:schemas.UserResponse = fastapi.Depends(get_current_user)):
    if user.role != "admin":
        raise fastapi.HTTPException(status_code=403,detail="you are not an admin")
    return user

# check the user is lecturer or not
async def require_lecturer(user:schemas.UserResponse = fastapi.Depends(get_current_user)):
    if user.role != "lecturer":
        raise fastapi.HTTPException(status_code=403,detail="you are not an Student")
    return user

# check the user is student or not
async def require_student(user:schemas.UserResponse = fastapi.Depends(get_current_user)):
    if user.role != "student":
        raise fastapi.HTTPException(status_code=403,detail="you are not an Student")
    return user

# -------------------------- course ----------------------------------
# get all courses
async def get_all_courses(db: orm.Session):
    return db.query(model.CourseUnit).all()

# create course
async def create_course(course:schemas.CourseCreate,db:orm.Session):
    course_obj = model.CourseUnit(
        title=course.title,
        code=course.code,
        lecturer_id=course.lecturer_id
    )
    db.add(course_obj)
    db.commit()
    db.refresh(course_obj)
    return course_obj

# delete course
async def delete_course(db: orm.Session, course_id: int):
    course = db.query(model.CourseUnit).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()

# update course() change the course lecturer
async def change_course_lecturer(db:orm.Session, course_id: int, lecturer_id: int):
    course = db.query(model.CourseUnit).get(course_id)
    if not course_id:
        raise HTTPException(status_code=404, detail="Course not found")
    lecturer_id = db.query(model.User).get(lecturer_id)
    if not lecturer_id or lecturer_id.role != "lecturer":
        raise HTTPException(status_code=403, detail="you are not a lecturer or invalid Lecturer ID")
    course.lecturer_id = lecturer_id
    db.commit()
    return course


# -------------------------- review ----------------------------------
# create review
# Review Operations with Sentiment Analysis
async def create_review(
        db: orm.Session,
        review: schemas.ReviewCreate,
        student_id: int,
        course_id: int
):

    result = ml_util.predict_sentiment(review.txt)

    review_obj = model.Review(
        student_id=student_id,
        course_id=course_id,
        text=review.txt,
        clean_text=result['lemmatize'],
        sentiment=result['sentiment']
    )
    db.add(review_obj)
    db.commit()
    db.refresh(review_obj)
    return review_obj

# delete review
async def delete_review(db: orm.Session, review_id: int):
    review=db.query(model.Review).get(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()

# -------------------------- users ----------------------------------

# get all user
async def get_all_users(db: orm.Session):
    return db.query(model.User).all()

# delete user
async def delete_user(db: orm.Session, user_id: int):
    user = db.query(model.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()

# update user
async def update_user(db: orm.Session, user_id: int, user_data: schemas.UserUpdate):
    user = db.query(model.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = hash.bcrypt.hash(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


async def get_course_sentiment_summary(db: orm.Session, course_id: int):
    reviews = db.query(model.Review).filter(model.Review.course_id == course_id).all()

    # Calculate sentiment distribution
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    for review in reviews:
        sentiment = str(review.sentiment)
        sentiment_counts[sentiment] += 1

    total = len(reviews)
    distribution = {
        "positive": sentiment_counts["positive"] / total if total else 0,
        "negative": sentiment_counts["negative"] / total if total else 0,
        "neutral": sentiment_counts["neutral"] / total if total else 0
    }

    return {
        "course_id": course_id,
        "positive": sentiment_counts["positive"],
        "negative": sentiment_counts["negative"],
        "neutral": sentiment_counts["neutral"],
        "total": total,
        "sentiment_distribution": distribution
    }

# overview
async def get_admin_overview(db: orm.Session):
    # Implement system-wide statistics
    return {
        "total_courses": db.query(model.CourseUnit).count(),
        "total_reviews": db.query(model.Review).count(),
        "total_students": db.query(model.User).filter(model.User.role == "student").count(),
        "total_lecturers": db.query(model.User).filter(model.User.role == "lecturer").count(),
        "sentiment_distribution": await get_system_sentiment(db)
    }


async def get_system_sentiment(db: orm.Session):
    reviews = db.query(model.Review).all()
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

    for review in reviews:
        sentiment = str(review.sentiment)
        sentiment_counts[sentiment] += 1

    total = len(reviews)
    return {
        "positive": sentiment_counts["positive"] / total if total else 0,
        "negative": sentiment_counts["negative"] / total if total else 0,
        "neutral": sentiment_counts["neutral"] / total if total else 0
    }