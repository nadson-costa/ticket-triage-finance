import json
from typing import Any

import pytest
from pydantic import ValidationError

from ticketsense.datagen.schema import Ficha, Ticket


def ficha_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "train-00001",
        "split": "train",
        "generator": "A",
        "true_category": "pix",
        "subtopic": "Pix enviado para chave errada",
        "urgency": "alta",
        "urgency_criterion": 3,
        "uses_urgent_word": False,
        "length": "medio",
        "persona": "cliente_comum",
        "tone": "informal",
        "style_noise": ["abreviacoes"],
        "overlap_with": "fraude_seguranca",
        "is_vague": False,
        "is_multi_topic": False,
    }
    return {**base, **overrides}


def ticket_kwargs(**overrides: Any) -> dict[str, Any]:
    base = {
        **ficha_kwargs(),
        "text": "mandei um pix pra chave errada, preciso cancelar hoje",
        "category": "pix",
        "label_noisy": False,
    }
    return {**base, **overrides}


# --------------------------------------------------------------------------- #
# Ficha
# --------------------------------------------------------------------------- #


def test_valid_ficha_is_created():
    ficha = Ficha(**ficha_kwargs())

    assert ficha.id == "train-00001"
    assert ficha.urgency == "alta"
    assert ficha.urgency_criterion == 3


def test_style_noise_list_becomes_tuple():
    ficha = Ficha(**ficha_kwargs(style_noise=["abreviacoes", "sem_acentos"]))

    assert ficha.style_noise == ("abreviacoes", "sem_acentos")


def test_normal_ficha_without_criterion_is_valid():
    ficha = Ficha(**ficha_kwargs(urgency="normal", urgency_criterion=None))

    assert ficha.urgency == "normal"
    assert ficha.urgency_criterion is None


def test_vague_ficha_with_short_length_is_valid():
    ficha = Ficha(**ficha_kwargs(is_vague=True, length="curto"))

    assert ficha.is_vague is True


def test_overlap_with_none_is_valid():
    ficha = Ficha(**ficha_kwargs(overlap_with=None))

    assert ficha.overlap_with is None


INVALID_FICHA_CASES = [
    pytest.param({"urgency": "urgente"}, "Input should be", id="urgencia-invalida"),
    pytest.param({"urgency_criterion": 7}, "less than or equal to 5", id="criterio-acima-de-5"),
    pytest.param({"urgency_criterion": 0}, "greater than or equal to 1", id="criterio-abaixo-de-1"),
    pytest.param({"urgency": "normal"}, "urgency_criterion deve existir", id="normal-com-criterio"),
    pytest.param(
        {"urgency_criterion": None}, "urgency_criterion deve existir", id="alta-sem-criterio"
    ),
    pytest.param({"is_vague": True}, "ticket vago", id="vago-com-tamanho-medio"),
    pytest.param({"overlap_with": "pix"}, "overlap_with não pode", id="overlap-igual-a-categoria"),
    pytest.param({"id": "val-00001"}, "não começa com o split", id="id-com-split-errado"),
    pytest.param({"id": "train-1"}, "should match pattern", id="id-mal-formado"),
    pytest.param({"lavel_noisy": True}, "Extra inputs are not permitted", id="campo-desconhecido"),
    pytest.param({"generator": "C"}, "Input should be", id="gerador-invalido"),
    pytest.param({"length": "grande"}, "Input should be", id="tamanho-invalido"),
]


@pytest.mark.parametrize(("overrides", "message"), INVALID_FICHA_CASES)
def test_invalid_ficha_is_rejected(overrides: dict[str, Any], message: str):
    with pytest.raises(ValidationError, match=message):
        Ficha(**ficha_kwargs(**overrides))


def test_missing_required_field_is_rejected():
    kwargs = ficha_kwargs()
    del kwargs["persona"]

    with pytest.raises(ValidationError, match="Field required"):
        Ficha(**kwargs)


def test_ficha_is_immutable():
    ficha = Ficha(**ficha_kwargs())

    with pytest.raises(ValidationError, match="frozen"):
        ficha.persona = "outra_persona"


def test_equal_fichas_are_equal_and_hashable():
    first = Ficha(**ficha_kwargs())
    second = Ficha(**ficha_kwargs())

    assert first == second
    assert len({first, second}) == 1


# --------------------------------------------------------------------------- #
# Ticket
# --------------------------------------------------------------------------- #


def test_valid_ticket_is_created():
    ticket = Ticket(**ticket_kwargs())

    assert ticket.category == ticket.true_category == "pix"
    assert ticket.label_noisy is False


def test_ticket_text_is_stripped():
    ticket = Ticket(**ticket_kwargs(text="  preciso de ajuda  "))

    assert ticket.text == "preciso de ajuda"


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_empty_ticket_text_is_rejected(text: str):
    with pytest.raises(ValidationError, match="at least 1 character"):
        Ticket(**ticket_kwargs(text=text))


def test_ticket_with_label_noise_is_valid():
    ticket = Ticket(**ticket_kwargs(category="fraude_seguranca", label_noisy=True))

    assert ticket.category == "fraude_seguranca"
    assert ticket.true_category == "pix"


def test_label_noisy_must_match_categories():
    with pytest.raises(ValidationError, match="label_noisy deve ser verdadeiro"):
        Ticket(**ticket_kwargs(category="pix", label_noisy=True))

    with pytest.raises(ValidationError, match="label_noisy deve ser verdadeiro"):
        Ticket(**ticket_kwargs(category="fraude_seguranca", label_noisy=False))


def test_ticket_inherits_ficha_rules():
    with pytest.raises(ValidationError, match="urgency_criterion deve existir"):
        Ticket(**ticket_kwargs(urgency="normal"))


def test_from_ficha_defaults_to_true_category():
    ficha = Ficha(**ficha_kwargs())

    ticket = Ticket.from_ficha(ficha, "texto do ticket")

    assert ticket.category == "pix"
    assert ticket.label_noisy is False
    assert ticket.id == ficha.id


def test_from_ficha_with_other_category_marks_noise():
    ficha = Ficha(**ficha_kwargs())

    ticket = Ticket.from_ficha(ficha, "texto do ticket", category="fraude_seguranca")

    assert ticket.category == "fraude_seguranca"
    assert ticket.true_category == "pix"
    assert ticket.label_noisy is True


def test_ticket_json_round_trip():
    ficha = Ficha(**ficha_kwargs())
    ticket = Ticket.from_ficha(ficha, "texto do ticket", category="fraude_seguranca")

    data = ticket.model_dump(mode="json")
    restored = Ticket.model_validate(json.loads(json.dumps(data)))

    assert isinstance(data["style_noise"], list)
    assert restored == ticket
