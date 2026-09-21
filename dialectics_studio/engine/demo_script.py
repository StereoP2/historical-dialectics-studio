"""Offline sample debate: Marx vs Descartes on the Industrial Revolution."""

from __future__ import annotations

DEMO_ROUNDS = [
    {
        "speaker": "marx",
        "text": (
            "Gentlemen, spare me your crystal clear ideas. The steam-engine and the mule "
            "did not arise from pure thought; they arose from the needs of accumulation. "
            "Where the handicraftsman once owned his tools, the mill now owns the worker. "
            "[Source: Capital, Vol. I, Ch. 15, 1867] The Industrial Revolution is not a hymn "
            "to method — it is the violent divorce of producer from means of production. "
            "Your 'progress' is surplus value dressed as Providence."
        ),
    },
    {
        "speaker": "historiographer",
        "text": (
            "• Severity Med — Marx's framing is powerful but compresses a long, uneven process "
            "(proto-industrialization, regional variation) into a single rupture.\n"
            "• Nuance: Enclosure and colonial markets also mattered; machinery alone does not "
            "explain timing. [Suggested: Deane, The First Industrial Revolution; Allen, The British Industrial Revolution in Global Perspective]"
        ),
    },
    {
        "speaker": "descartes",
        "text": (
            "I shall proceed in order. First, distinguish nature's mechanisms from men's passions. "
            "Machines amplify clear operations on matter; that they are misused by greed does not "
            "indict method itself. [Source: Discourse on the Method, Parts II–VI, 1637] "
            "If we would reform industry, let us begin by doubting confused slogans — 'capital', "
            "'class' — until each is defined by clear and distinct marks, as one defines a figure in geometry."
        ),
    },
    {
        "speaker": "historiographer",
        "text": (
            "• Severity Low — Descartes cannot historically 'reply' to 19th-century industry; "
            "this is a constructed dialogue. Flag as anachronistic framing, not a quote from Descartes.\n"
            "• Nuance: His mechanistic science later informed engineering culture, but he did not "
            "theorize factories. [Suggested: Dear, Revolutionizing the Sciences]"
        ),
    },
    {
        "speaker": "marx",
        "text": (
            "Definition without history is a scholastic game. The factory's 'clear operations' "
            "are purchased with the lengthening of the working day and the cheapening of labour. "
            "[Source: Capital, Vol. I, Ch. 10] Demand that the bourgeoisie state whose clarity "
            "is served — the ledger's, or the child's in the mill?"
        ),
    },
    {
        "speaker": "historiographer",
        "text": (
            "• Severity Low — Child labour and long hours are well attested for early mills; "
            "Marx's polemic here tracks parliamentary Blue Books he used.\n"
            "• Nuance: Conditions varied by sector and decade; reform acts also belong in the "
            "picture. [Suggested: Factory Inquiry Commission reports, 1830s; Humphries on child labour]"
        ),
    },
]
