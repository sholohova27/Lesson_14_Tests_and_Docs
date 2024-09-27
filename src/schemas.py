from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class ContactBase(BaseModel):
    """
    Базовая модель для контакта.
    Атрибуты:
        first_name (str): Имя контакта.
        last_name (str): Фамилия контакта.
        email (EmailStr): Электронная почта контакта.
        phone_number (str): Номер телефона контакта.
        birthday (date): Дата рождения контакта.
        additional_info (Optional[str]): Дополнительная информация о контакте (по желанию).
    """
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: Optional[str] = None


class ContactCreate(ContactBase):
    """
    Модель для создания нового контакта. Унаследована от ContactBase.
    """
    pass


class ContactUpdate(ContactBase):
    """
    Модель для обновления информации о контакте. Унаследована от ContactBase.
    """
    pass


class ContactResponse(ContactBase):
    """
    Модель для представления контакта в ответе API.
    Атрибуты: id (int): Уникальный идентификатор контакта.
    """
    id: int
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """
    Модель для создания нового пользователя.
    Атрибуты:
        email (EmailStr): Электронная почта пользователя.
        password (str): Пароль пользователя.
    """
    email: EmailStr
    password: str


class Token(BaseModel):
    """
    Модель для представления токенов аутентификации.
    Атрибуты:
        access_token (str): Токен доступа.
        refresh_token (str): Токен обновления.
        token_type (str): Тип токена (по умолчанию "bearer").
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    """
    Модель для входа пользователя.
    Атрибуты:
        email (EmailStr): Электронная почта пользователя.
        password (str): Пароль пользователя.
    """
    email: EmailStr
    password: str
