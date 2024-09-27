from sqlalchemy import Column, Integer, String, Date
from src.database.db import Base
from passlib.context import CryptContext
from sqlalchemy.orm import Session



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Contact(Base):
    """
    Модель БД для контактов.
    Атрибуты:
        id (int): Уникальный идентификатор контакта.
        first_name (str): Имя контакта.
        last_name (str): Фамилия контакта.
        email (str): Электронная почта контакта.
        phone_number (str): Номер телефона контакта.
        birthday (str): Дата рождения контакта.
        additional_info (str, optional): Дополнительная информация о контакте.
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    birthday = Column(Date)
    additional_info = Column(String, nullable=True)


class User(Base):
    """
    Модель БД для хранения и верификации креденшиалов пользователя.
    Атрибуты:
        id (int): Уникальный идентификатор пользователя.
        email (str): Электронная почта пользователя (логин).
        hashed_password (str): Хэшированный пароль.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    def verify_password(self, password: str):
        """
        Проверяет, совпадает ли предоставленный пароль с хэшированным паролем.
        Параметры: password (str): Пароль для проверки.
        Возвращает: bool: True, если пароль совпадает, иначе False.
        """
        return pwd_context.verify(password, self.hashed_password)


def get_password_hash(password: str) -> str:
    """
    Генерирует хэш пароля.
    Параметры: password (str): Пароль для хэширования.
    Возвращает: str: Хэшированный пароль.
    """
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """
     Проверяет, совпадает ли открытый пароль с хэшированным паролем.
     Параметры: plain_password (str): Открытый пароль.
                hashed_password (str): Хэшированный пароль.
     Возвращает: bool: True, если пароль совпадает, иначе False.
     """
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, email: str, password: str):
    """
     Аутентифицирует пользователя по электронной почте и паролю.
     Параметры: db (Session): Сессия базы данных.
                email (str): Электронная почта пользователя.
                password (str): Пароль пользователя.
     Возвращает: User: Пользователь, если аутентификация успешна, иначе None.
     """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user