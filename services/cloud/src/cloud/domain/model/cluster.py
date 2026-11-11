from dataclasses import dataclass

from shared.text import required_name


@dataclass
class Cluster:
    """A construction site. Aggregate root of its own: nodes refer to it by id."""

    name: str
    description: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = required_name(self.name, "cluster")

    def rename(self, name: str, description: str | None) -> None:
        self.name = required_name(name, "cluster")
        self.description = description
