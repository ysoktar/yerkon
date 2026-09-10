"""The named error sources a position carries, so each can be switched off.

A single accuracy figure says how wrong a receiver was. It does not say
what made it wrong, and a project whose whole purpose is to decide where
to spend money needs the second answer more than the first: a metre of
survey error and a metre of ranging noise cost entirely different sums to
remove, and one of them does not average out.

This module names the sources and nothing else. It imports nothing, so
the measurement code and the evaluation code can both hold one of these
without either learning about the other.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace


@dataclass(frozen=True)
class Terms:
    """Which error sources are live in a run.

    Every field defaults to on, so the ordinary path through the
    simulation is the one with everything in it. Switching one off is
    always an experiment, and it has to be asked for.
    """

    #: Delay-estimation noise, bounded below by the Cramér-Rao limit.
    waveform: bool = True
    #: The part's measured floor, where it sits above the physics.
    floor: bool = True
    #: What the two crystals do to the exchange's arithmetic.
    clock: bool = True
    #: The extra distance a signal travels over an obstruction.
    excess_path: bool = True
    #: How badly each anchor's own position is known.
    survey: bool = True
    #: The receiver moving between the ranges of one round.
    motion: bool = True
    #: Exchanges lost to everything the link budget omits.
    packet_loss: bool = True

    @classmethod
    def none(cls) -> "Terms":
        """Every source off. What is left is the model's own residue."""
        return cls(**{field.name: False for field in fields(cls)})

    @classmethod
    def only(cls, source: str) -> "Terms":
        """One source live and the rest silent."""
        return replace(cls.none(), **{_checked(source): True})

    def without(self, source: str) -> "Terms":
        """Everything but one source."""
        return replace(self, **{_checked(source): False})


def _checked(source: str) -> str:
    if source not in NAMES:
        raise ValueError(
            "no error source called {}. There are: {}".format(
                source, ", ".join(NAMES)
            )
        )
    return source


#: The sources, in the order a reader should meet them.
NAMES = tuple(field.name for field in fields(Terms))

ALL = Terms()

#: What each source is, in the report's language.
LABELS = {
    "waveform": "Dalga formu gürültüsü",
    "floor": "Donanım ölçüm tabanı",
    "clock": "Saat kayması",
    "excess_path": "Fazladan yol (engel)",
    "survey": "Direk konum ölçümü",
    "motion": "Tur içi hareket",
    "packet_loss": "Kaybolan alışveriş",
}

#: What removing each source would take, which is the point of measuring them.
REMEDIES = {
    "waveform": "daha yüksek güç, daha yakın direk, daha geniş bant",
    "floor": "daha iyi bir modül ya da düzeltilmiş bir zaman damgası",
    "clock": "TCXO ya da çift taraflı TWR",
    "excess_path": "direği yükseltmek, görüş hattını açmak",
    "survey": "direkleri GNSS ile daha iyi ölçmek",
    "motion": "daha kısa tur: daha az direk ya da daha hızlı çerçeve",
    "packet_loss": "daha temiz kanal, daha sık tekrar",
}
