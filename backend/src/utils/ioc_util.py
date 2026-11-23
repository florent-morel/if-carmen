"""
Minimal inversion-of-control registry for resolving CarbonService implementations.
"""

from __future__ import annotations


class IocRegistrationModel:
    """Maps an (abstract_type, ioc_key) pair to a concrete service class."""

    def __init__(self, ioc_key: str, abstract_type: type, concrete_type: type) -> None:
        self.ioc_key = ioc_key
        self.abstract_type = abstract_type
        self.concrete_type = concrete_type


def resolve(abstract_type: type, ioc_key: str, duration: int) -> object | None:
    """Instantiate the registered concrete service matching abstract_type and ioc_key."""
    for ioc_registered_item in ioc_registered_models:
        abstract_type_name = ioc_registered_item.abstract_type.__name__

        if (ioc_registered_item.ioc_key == ioc_key) & (
            abstract_type_name == abstract_type.__name__
        ):
            return ioc_registered_item.concrete_type(duration)
    return None


ioc_registered_models: list[IocRegistrationModel] | None = []
