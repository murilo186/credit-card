import pytest
from pydantic import ValidationError

from app.schemas.card import CardCreate
from app.schemas.customer import CustomerCreate
from app.schemas.transaction import TransactionCreate


@pytest.mark.parametrize("name", ["", "   "])
def test_rn02_rejects_empty_customer_name(name: str) -> None:
    with pytest.raises(ValidationError):
        CustomerCreate(name=name)


def test_rn02_trims_customer_name() -> None:
    assert CustomerCreate(name="  Cliente Fictício  ").name == "Cliente Fictício"


@pytest.mark.parametrize("total_limit_cents", [0, -1])
def test_rn04_rejects_non_positive_total_limit(total_limit_cents: int) -> None:
    with pytest.raises(ValidationError):
        CardCreate(last_four_digits="1234", total_limit_cents=total_limit_cents)


@pytest.mark.parametrize("last_four_digits", ["123", "12345", "12a4"])
def test_rn12_rejects_invalid_last_four_digits(last_four_digits: str) -> None:
    with pytest.raises(ValidationError):
        CardCreate(last_four_digits=last_four_digits, total_limit_cents=100)


@pytest.mark.parametrize("amount_cents", [0, -1])
def test_rn13_rejects_non_positive_transaction_amount(amount_cents: int) -> None:
    with pytest.raises(ValidationError):
        TransactionCreate(merchant="Loja Fictícia", amount_cents=amount_cents)


@pytest.mark.parametrize("merchant", ["", "   "])
def test_rn14_rejects_empty_merchant(merchant: str) -> None:
    with pytest.raises(ValidationError):
        TransactionCreate(merchant=merchant, amount_cents=100)
