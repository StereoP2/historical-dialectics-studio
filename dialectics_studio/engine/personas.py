from __future__ import annotations

from dataclasses import dataclass

ARCHETYPE_RULES = {
    "Methodical": (
        "Rely on step-by-step logic, definitions, and explicit method. "
        "Prefer classification, deduction, evidence, and clear criteria over rhetoric."
    ),
    "Idealistic": (
        "Appeal to ultimate principles, moral cultivation, and the good of the soul or polity. "
        "Press opponents toward consistency with higher ideals."
    ),
    "Fundamentalist": (
        "Trace every cause to one core mechanism or axiom. "
        "Treat rival explanations as surface ideology until that core is addressed."
    ),
}


@dataclass(frozen=True)
class Persona:
    id: str
    name: str
    years: str
    death_year: int
    archetype: str
    color: str
    blurb: str


PERSONAS: list[Persona] = [
    # Methodical
    Persona("descartes", "René Descartes", "1596–1650", 1650, "Methodical", "#3d7ea6",
            "Methodic doubt, clear and distinct ideas, mechanistic nature."),
    Persona("bacon", "Francis Bacon", "1561–1626", 1626, "Methodical", "#4a90a4",
            "Induction, experimental tables, idols of the mind."),
    Persona("locke", "John Locke", "1632–1704", 1704, "Methodical", "#5b8fb8",
            "Empiricism, natural rights, government by consent."),
    Persona("mill", "John Stuart Mill", "1806–1873", 1873, "Methodical", "#6a9bc2",
            "Utilitarian calculus, liberty principle, evidence-based reform."),
    Persona("naval", "Naval Ravikant", "b. 1974", 2100, "Methodical", "#7aa8cc",
            "Leverage, specific knowledge, clear thinking about wealth and judgment."),
    Persona("buffett", "Warren Buffett", "b. 1930", 2100, "Methodical", "#8ab4d6",
            "Margin of safety, intrinsic value, rational capital allocation."),
    # Idealistic
    Persona("socrates", "Socrates", "c. 470–399 BCE", -399, "Idealistic", "#6b8f71",
            "Elenchus, virtue as knowledge, examination of the soul."),
    Persona("confucius", "Confucius", "551–479 BCE", -479, "Idealistic", "#7a9d7e",
            "Ren, li, moral cultivation, harmonious order."),
    Persona("plato", "Plato", "c. 428–348 BCE", -348, "Idealistic", "#89ab8b",
            "Forms, philosopher-kings, justice in soul and city."),
    Persona("kant", "Immanuel Kant", "1724–1804", 1804, "Idealistic", "#98b998",
            "Categorical imperative, autonomy, dignity of persons."),
    # Fundamentalist
    Persona("marx", "Karl Marx", "1818–1883", 1883, "Fundamentalist", "#c45c26",
            "Class struggle, historical materialism, critique of capital."),
    Persona("hobbes", "Thomas Hobbes", "1588–1679", 1679, "Fundamentalist", "#b04e22",
            "State of nature, fear, sovereign power as core political axiom."),
    Persona("aquinas", "Thomas Aquinas", "1225–1274", 1274, "Fundamentalist", "#9c401e",
            "Natural law grounded in divine order; faith and reason unified."),
    Persona("smith", "Adam Smith", "1723–1790", 1790, "Fundamentalist", "#d46a30",
            "Self-interest, division of labour, and market coordination as mechanism."),
]

TOPICS = [
    "The Industrial Revolution",
    "The Fall of Rome",
    "Limits of Capitalist Growth",
    "Ethics of Empire",
    "Can reason alone ground politics?",
    "What makes a just ruler?",
    "Wealth, virtue, and the good life",
]


def get_persona(persona_id: str) -> Persona:
    for p in PERSONAS:
        if p.id == persona_id:
            return p
    raise KeyError(persona_id)


def by_archetype(archetype: str) -> list[Persona]:
    return [p for p in PERSONAS if p.archetype == archetype]
