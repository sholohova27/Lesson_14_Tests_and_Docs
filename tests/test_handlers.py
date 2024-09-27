import unittest
from unittest.mock import MagicMock
from datetime import datetime
from sqlalchemy.orm import Session
from src.database.models import Contact
from src.schemas import ContactCreate, ContactUpdate
from src.handler import (
    get_contact,
    get_contacts,
    create_contact,
    update_contact,
    delete_contact,
    search_contacts
)


class TestContactHandlers(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.contact_data = {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "phone_number": "1234567890",  # Добавлено поле
            "birthday": datetime(1990, 1, 1)
        }
        self.contact = Contact(**self.contact_data)

    def test_get_contact(self):
        self.db.query().filter().first.return_value = self.contact
        result = get_contact(self.db, contact_id=1)
        self.db.query().filter().first.assert_called_once()
        self.assertEqual(result.first_name, "John")
        self.assertEqual(result.email, "johndoe@example.com")

    def test_get_contacts(self):
        contacts = [self.contact]
        self.db.query().offset().limit().all.return_value = contacts
        result = get_contacts(self.db, skip=0, limit=10)
        self.db.query().offset().limit().all.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].first_name, "John")

    def test_create_contact(self):
        contact_create = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            phone_number="1234567890",  # Добавлено поле
            birthday=datetime(1990, 1, 1)
        )
        self.db.add = MagicMock()
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()
        result = create_contact(self.db, contact_create)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
        self.assertEqual(result.first_name, "John")

    def test_update_contact(self):
        contact_update = ContactUpdate(
            first_name="John Updated",
            last_name="Doe",  # Добавлены необходимые поля
            email="johndoe@example.com",
            phone_number="1234567890",
            birthday=datetime(1990, 1, 1)
        )
        self.db.query().filter().first.return_value = self.contact
        self.db.commit = MagicMock()
        self.db.refresh = MagicMock()
        result = update_contact(self.db, contact_id=1, contact=contact_update)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once()
        self.assertEqual(result.first_name, "John Updated")

    def test_delete_contact(self):
        self.db.query().filter().first.return_value = self.contact
        self.db.delete = MagicMock()
        self.db.commit = MagicMock()
        result = delete_contact(self.db, contact_id=1)
        self.db.delete.assert_called_once()
        self.db.commit.assert_called_once()
        self.assertEqual(result.id, 1)

    def test_search_contacts(self):
        contacts = [self.contact]
        self.db.query().filter().all.return_value = contacts
        result = search_contacts(self.db, name="John", surname=None, email=None)
        self.db.query().filter().all.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].first_name, "John")


if __name__ == '__main__':
    unittest.main()
