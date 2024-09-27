from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import os
from dotenv import load_dotenv

from src.database import models
from src import schemas
from src.schemas import UserCreate
from src.database.models import get_password_hash
from src.database.db import get_db


def get_contact(db: Session, contact_id: int):
    """
    Получает контакт по его уникальному идентификатору.
    Args: db (Session): Сессия базы данных.
          contact_id (int): Уникальный идентификатор контакта.
    Returns: models.Contact: Объект контакта, если найден, иначе None.
    """
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()


def get_contacts(db: Session, skip: int = 0, limit: int = 10):
    """
    Получает список контактов с поддержкой пагинации.
    Args: db (Session): Сессия базы данных.
          skip (int): Количество пропущенных записей (по умолчанию 0).
          limit (int): Максимальное количество возвращаемых записей (по умолчанию 10).
    Returns: List[models.Contact]: Список контактов.
    """
    return db.query(models.Contact).offset(skip).limit(limit).all()


def create_contact(db: Session, contact: schemas.ContactCreate):
    """
    Создает новый контакт.
    Args: db (Session): Сессия базы данных.
          contact (schemas.ContactCreate): Данные для создания нового контакта.
    Returns: models.Contact: Созданный контакт.
    """
    db_contact = models.Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def update_contact(db: Session, contact_id: int, contact: schemas.ContactUpdate):
    """
    Обновляет существующий контакт.
    Args: db (Session): Сессия базы данных.
          contact_id (int): Уникальный идентификатор контакта.
          contact (schemas.ContactUpdate): Данные для обновления контакта.
    Returns: models.Contact: Обновленный контакт, если найден, иначе None.
    """
    db_contact = get_contact(db, contact_id)
    if db_contact:
        for key, value in contact.model_dump(exclude_unset=True).items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, contact_id: int):
    """
    Удаляет контакт по его уникальному идентификатору.
    Args: db (Session): Сессия базы данных.
          contact_id (int): Уникальный идентификатор контакта.
    Returns: models.Contact: Удаленный контакт, если найден, иначе None.
    """
    db_contact = get_contact(db, contact_id)
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact


def search_contacts(db: Session, name: str = None, surname: str = None, email: str = None):
    """
    Ищет контакты по имени, фамилии или электронной почте.
    Args: db (Session): Сессия базы данных.
         name (str, optional): Имя контакта для поиска.
         surname (str, optional): Фамилия контакта для поиска.
         email (str, optional): Электронная почта контакта для поиска.
    Returns: List[models.Contact]: Список найденных контактов.
    """
    query = db.query(models.Contact)
    if name:
        query = query.filter(models.Contact.first_name.ilike(f"%{name}%"))
    if surname:
        query = query.filter(models.Contact.last_name.ilike(f"%{surname}%"))
    if email:
        query = query.filter(models.Contact.email.ilike(f"%{email}%"))
    return query.all()


def get_upcoming_birthdays(db: Session):
    """
    Получает список контактов с днями рождения в ближайшую неделю.
    Args:db (Session): Сессия базы данных.
    Returns: List[models.Contact]: Список контактов с предстоящими днями рождения.
    """
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    return db.query(models.Contact).filter(
        func.date_trunc('day', models.Contact.birthday) >= today,
        func.date_trunc('day', models.Contact.birthday) <= next_week
    ).all()


def create_user(db: Session, user: UserCreate):
    """
    Создает нового пользователя.
    Args: db (Session): Сессия базы данных.
          user (UserCreate): Данные для создания нового пользователя.
    Raises: HTTPException: Если электронная почта уже зарегистрирована.
    Returns: models.User: Созданный пользователь.
    """
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


SECRET_KEY = "my_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Создает токен доступа.
    Args: data (dict): Данные, которые будут закодированы в токен.
          expires_delta (timedelta, optional): Время истечения токена.
    Returns: str: Закодированный токен доступа.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(days=30)) -> str:
    """
    Создает токен обновления.
    Args: data (dict): Данные, которые будут закодированы в токен.
          expires_delta (timedelta, optional): Время истечения токена обновления.
    Returns: str: Закодированный токен обновления.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Получает текущего пользователя на основе предоставленного токена.
    Args: db (Session, optional): Сессия базы данных.
          token (str): Токен доступа.
    Raises: HTTPException: Если токен недействителен или пользователь не найден.
    Returns: models.User: Текущий пользователь.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


def get_user_by_email(db: Session, email: str):
    """
    Получает пользователя по его электронной почте.
    Args: db (Session): Сессия базы данных.
          email (str): Электронная почта пользователя.
    Returns: models.User: Объект пользователя, если найден, иначе None.
    """
    return db.query(models.User).filter(models.User.email == email).first()


load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_USERNAME"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME="Your App",
    MAIL_STARTTLS=os.getenv('MAIL_USE_TLS') == 'True',
    MAIL_SSL_TLS=os.getenv('MAIL_USE_SSL') == 'True',
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


async def send_verification_email(email: EmailStr, background_tasks: BackgroundTasks):
    """
    Отправляет электронное письмо для верификации.
    Args: email (EmailStr): Электронная почта получателя.
          background_tasks (BackgroundTasks): Задачи для выполнения в фоне.
    Returns: None
    """
    token_data = {"sub": email}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"Please verify your email: http://127.0.0.1:8000/verify?token={token}",
        subtype="html"
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
