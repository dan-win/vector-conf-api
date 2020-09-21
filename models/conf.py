from typing import Optional, List, Union

from pydantic import \
    BaseModel, \
    PydanticValueError, \
    ValidationError, \
    validator, \
    Field, \
    UUID4

from .usertypes import \
    NodeRole, \
    NodeType, \
    FileFingerprintingStrategy, \
    FileMultilineParseMode, \
    FileEncoding, \
    TimestampFormat, \
    StdStream, \
    node_subclass_registry


from .nodes import Node

import toml

class Conf(BaseModel):
    items: List[Node] = []

    def deserialize(self, tomltext: str):
        self.items = []
        c = toml.loads(tomltext)

        #  top-level keys are: sources, transforms, sinks
        for role, items in c.items():
            for name, node in items.items():
                attrs = node.copy()
                node_type = attrs.pop("type")
                #  find class:
                node_r = NodeRole(role)
                try:
                    node_t = NodeType(node_type)
                except Exception as e:
                    raise ValueError(f"No such type for node registered: {node_type}")
                model_factory = node_subclass_registry.model_for_role_type(node_r, node_t)
                model = model_factory(**attrs, name=name)
                self.items.append(model)

    def serialize(self) -> str:
        d = dict(
            sources={},
            transforms={},
            sinks={}
        )
        for node in self.items:
            attrs = node.dict()
            attrs["type"] = node.type.value
            name = attrs.pop("name")
            role = attrs.pop("role")
            d[role.value][name] = attrs
        return toml.dumps(d)


class ConfLoad(BaseModel):
    text: str