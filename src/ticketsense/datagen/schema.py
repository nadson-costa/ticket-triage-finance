from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Urgency = Literal["alta", "normal"]
Length = Literal["curto", "medio", "longo"]
Generator = Literal["A", "B"]
UrgencyCriterion = Annotated[int, Field(ge=1, le=5)]


class Ficha(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: Annotated[str, Field(pattern=r"^[a-z_]+-\d{5}$")]
    split: str
    generator: Generator
    true_category: str
    subtopic: str
    urgency: Urgency
    urgency_criterion: UrgencyCriterion | None = Field(
        description="Critério 1 a 5 da seção 6 da taxonomia; None quando a urgência é normal."
    )
    uses_urgent_word: bool
    length: Length
    persona: str
    tone: str
    style_noise: tuple[str, ...]
    overlap_with: str | None = Field(
        description="Categoria com a qual o ticket deve poder ser confundido, ou None."
    )
    is_vague: bool
    is_multi_topic: bool

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if not self.id.startswith(f"{self.split}-"):
            raise ValueError(f"id '{self.id}' não começa com o split '{self.split}-'")
        if (self.urgency == "alta") != (self.urgency_criterion is not None):
            raise ValueError("urgency_criterion deve existir se, e somente se, urgency for 'alta'")
        if self.is_vague and self.length != "curto":
            raise ValueError("ticket vago deve ter length 'curto'")
        if self.overlap_with == self.true_category:
            raise ValueError("overlap_with não pode ser igual a true_category")
        return self


class Ticket(Ficha):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    category: str
    label_noisy: bool

    @model_validator(mode="after")
    def _check_label_noise(self) -> Self:
        if self.label_noisy != (self.category != self.true_category):
            raise ValueError(
                "label_noisy deve ser verdadeiro se, e somente se, category != true_category"
            )
        return self

    @classmethod
    def from_ficha(cls, ficha: Ficha, text: str, category: str | None = None) -> Self:
        category = category or ficha.true_category
        return cls(
            **ficha.model_dump(),
            text=text,
            category=category,
            label_noisy=category != ficha.true_category,
        )
