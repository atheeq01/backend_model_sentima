import fastapi
import fastapi.security as security
import sqlalchemy.orm as orm
from fastapi import FastAPI,Depends

import services,schemas

app = FastAPI()

# register
@app.post("/auth/register")
async def create_user(
        user: schemas.UserCreate,
        db: orm.Session = Depends(services.get_db)):
    data_user = await services.get_user_by_email(email=str(user.email),db=db)
    if data_user:
        raise fastapi.HTTPException(status_code=400, detail="Email already registered")
    user_create= await services.create_user(user,db)
    return await services.create_token(user_create)

# authenticate
@app.post("/auth/token")
async def generate_token(
        form_data: security.OAuth2PasswordRequestForm = Depends(),
        db: orm.Session = Depends(services.get_db)):
    user = await services.authenticate_user(email=form_data.username,password=form_data.password, db=db)
    if not user:
        raise fastapi.HTTPException(status_code=400, detail="invalid credentials")
    return await services.create_token(user)

# get the current user
@app.get("/auth/user/me",response_model=schemas.UserResponse)
async def get_current_user(user:schemas.UserResponse=Depends(services.get_current_user)):
    return user

# student
@app.get("/student/courses",response_model=list[schemas.CourseResponse])
async def get_all_courses(
        db: orm.Session = Depends(services.get_db),
        user: schemas.UserResponse = Depends(services.require_student)):
    return await services.get_all_courses(db=db)

@app.post("/student/course/{course_id}/submit", response_model=schemas.ReviewResponse)
async def submit_review(
    course_id: int,
    review: schemas.ReviewCreate,
    db: orm.Session = fastapi.Depends(services.get_db),
    user: schemas.UserResponse = fastapi.Depends(services.require_student)
):
    return await services.create_review(db, review, user.id, course_id)

@app.get("student/courses/{course_id}",response_model=schemas.SentimentSummary)
async def get_course_summary(
        course_id: int,
        db: orm.Session = fastapi.Depends(services.get_db),
        user: schemas.UserResponse = fastapi.Depends(services.require_student)):
    return await services.get_course_sentiment_summary(db,course_id)

# lecturer
@app.get("/lesson/courses",response_model=list[schemas.CourseResponse])
async def get_lecture_courses(
        db: orm.Session = fastapi.Depends(services.get_db),
        user: schemas.UserResponse = fastapi.Depends(services.require_lecturer)
):
    return await services.get_all(db=db,user.id)


