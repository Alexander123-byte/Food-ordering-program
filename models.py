"""
models.py
Модели данных для системы ресторана
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    id: int
    name: str
    description: str = ""


@dataclass
class MenuItem:
    id: int
    name: str
    description: str
    price: float
    category_id: int
    category_name: str = ""
    is_available: bool = True
    calories: Optional[int] = None
    cooking_time: Optional[int] = None

    def display(self) -> str:
        available = "✓" if self.is_available else "✗"
        return f"{self.id}. {available} {self.name} - {self.price}₽\n   {self.description}"


@dataclass
class Customer:
    id: int
    name: str
    phone: str = ""
    email: str = ""
    address: str = ""


@dataclass
class OrderItem:
    menu_item_id: int
    quantity: int
    price_at_order: float
    menu_item_name: str = ""

    @property
    def subtotal(self) -> float:
        return self.quantity * self.price_at_order
