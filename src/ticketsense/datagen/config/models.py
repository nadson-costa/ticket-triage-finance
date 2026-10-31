import hashlib
import json
import math
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Probability = Annotated[float, Field(ge=0, le=1)]
PositiveInt = Annotated[int, Field(gt=0)]
PositiveFloat = Annotated[float, Field(gt=0)]
NonNegativeFloat = Annotated[float, Field(ge=0)]
Placeholder = Annotated[str, Field(pattern=r"^<[A-Z_]+>$")]

LENGTH_NAMES = ("curto", "medio", "longo")


class _Base(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# --------------------------------------------------------------------------- #
# taxonomy.yaml
# --------------------------------------------------------------------------- #


class Weighted(_Base):
    id: str
    weight: PositiveFloat


class GeneratorStyle(_Base):
    personas: Annotated[list[Weighted], Field(min_length=1)]
    tones: Annotated[list[Weighted], Field(min_length=1)]
    lengths: Annotated[list[Weighted], Field(min_length=1)]
    style_noise: Annotated[list[Weighted], Field(min_length=1)]

    @model_validator(mode="after")
    def _check_options(self) -> Self:
        problems: list[str] = []
        for field in ("personas", "tones", "lengths", "style_noise"):
            ids = [option.id for option in getattr(self, field)]
            duplicated = sorted({i for i in ids if ids.count(i) > 1})
            if duplicated:
                problems.append(f"'{field}' tem ids repetidos: {duplicated}")
        unknown_lengths = sorted({o.id for o in self.lengths} - set(LENGTH_NAMES))
        if unknown_lengths:
            problems.append(f"'lengths' tem ids inválidos {unknown_lengths}; use {LENGTH_NAMES}")
        if problems:
            raise ValueError("; ".join(problems))
        return self


class CategoryConfig(_Base):
    name: str
    share: Probability
    urgency_prior: Probability
    definition: str
    not_this: str
    subtopics: Annotated[list[str], Field(min_length=1)]
    urgency_criteria: Annotated[list[int], Field(min_length=1)]
    confusable_with: list[str] = Field(default_factory=list)


class TaxonomyConfig(_Base):
    version: str
    urgency_criteria: dict[int, str]
    categories: dict[str, CategoryConfig]
    generators: dict[str, GeneratorStyle]
    allowed_placeholders: list[Placeholder]
    blocked_brand_names: list[str]

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        problems: list[str] = []

        total_share = sum(c.share for c in self.categories.values())
        if not math.isclose(total_share, 1.0, abs_tol=1e-6):
            problems.append(
                f"a soma dos 'share' das categorias é {total_share:.4f}, deveria ser 1.0"
            )

        names = set(self.categories)
        known_criteria = set(self.urgency_criteria)
        for name, category in self.categories.items():
            for other in category.confusable_with:
                if other not in names:
                    problems.append(f"categoria '{name}': confusable_with '{other}' não existe")
                elif other == name:
                    problems.append(
                        f"categoria '{name}': confusable_with não pode incluir ela mesma"
                    )
            for criterion in category.urgency_criteria:
                if criterion not in known_criteria:
                    problems.append(
                        f"categoria '{name}': critério de urgência {criterion} "
                        "não está em urgency_criteria"
                    )

        if problems:
            raise ValueError("\n".join(problems))
        return self


# --------------------------------------------------------------------------- #
# generation.yaml
# --------------------------------------------------------------------------- #


class Rates(_Base):
    vague: Probability
    overlap: Probability
    multi_topic: Probability
    label_noise_train: Probability


class UrgentWordProb(_Base):
    alta: Probability
    normal: Probability


class LengthWords(_Base):
    curto: tuple[PositiveInt, PositiveInt]
    medio: tuple[PositiveInt, PositiveInt]
    longo: tuple[PositiveInt, PositiveInt]

    @model_validator(mode="after")
    def _check_ranges(self) -> Self:
        for name in LENGTH_NAMES:
            low, high = getattr(self, name)
            if low > high:
                raise ValueError(f"length_words.{name}: mínimo {low} maior que máximo {high}")
        if not (self.curto[1] < self.medio[0] and self.medio[1] < self.longo[0]):
            raise ValueError("length_words: as faixas curto, medio e longo não podem se sobrepor")
        return self


class SplitConfig(_Base):
    n: PositiveInt
    generator: Literal["A", "B"]
    seed_offset: int
    priority: int
    label_noise: bool
    frozen: bool = False


class DedupConfig(_Base):
    threshold: Annotated[float, Field(gt=0, le=1)]
    cross_split: bool


class ModelRef(_Base):
    name: Annotated[str, Field(min_length=1)]


class Price(_Base):
    input: NonNegativeFloat
    output: NonNegativeFloat


class ClientConfig(_Base):
    max_retries: Annotated[int, Field(ge=0)]
    timeout_seconds: PositiveFloat
    concurrency: PositiveInt
    cache_dir: str


class Paths(_Base):
    data_dir: str
    manifest: str


class GenerationConfig(_Base):
    seed: int
    oversample: Annotated[float, Field(ge=1)]
    fichas_per_call: PositiveInt
    rates: Rates
    urgent_word_prob: UrgentWordProb
    length_words: LengthWords
    vague_max_words: PositiveInt
    splits: Annotated[dict[str, SplitConfig], Field(min_length=1)]
    dedup: DedupConfig
    models: dict[str, ModelRef]
    prices_usd_per_mtok: dict[str, Price]
    budget_usd: PositiveFloat
    client: ClientConfig
    paths: Paths

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        priorities = [s.priority for s in self.splits.values()]
        if len(priorities) != len(set(priorities)):
            raise ValueError(
                "splits: 'priority' deve ser único, para a remoção de duplicatas ser determinística"
            )
        return self


class Config(_Base):
    taxonomy: TaxonomyConfig
    generation: GenerationConfig

    @model_validator(mode="after")
    def _check_cross_file(self) -> Self:
        problems: list[str] = []
        generators = self.taxonomy.generators
        models = self.generation.models
        prices = self.generation.prices_usd_per_mtok

        for split_name, split in self.generation.splits.items():
            if split.generator not in generators:
                problems.append(
                    f"split '{split_name}': o gerador '{split.generator}' "
                    "não existe em taxonomy.generators"
                )
            model = models.get(split.generator)
            if model is None:
                problems.append(
                    f"split '{split_name}': o gerador '{split.generator}' "
                    "não tem modelo em generation.models"
                )
            elif model.name not in prices:
                problems.append(
                    f"split '{split_name}': o modelo '{model.name}' "
                    "não tem preço em prices_usd_per_mtok"
                )

        if problems:
            raise ValueError("\n".join(problems))
        return self

    def fingerprint(self) -> str:
        canonical = json.dumps(self.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
