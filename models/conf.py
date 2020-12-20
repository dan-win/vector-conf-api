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
                node_type = attrs["type"]
                #  find class:
                node_r = NodeRole(role)
                model_factory = node_subclass_registry.model_for_role_type(node_r, node_type)
                model = model_factory(**attrs, name=name)
                self.items.append(model)
                print(model.dict())

    def serialize(self) -> str:
        d = dict(
            sources={},
            transforms={},
            sinks={}
        )
        for node in self.items:
            # attrs = node.dict()
            # # attrs["type"] = node.type.value
            # name = attrs.pop("name")
            # role = attrs.pop("role")
            # d[role.value][name] = attrs
            name = node.name
            role = node.role.value
            d[role][name] = node.dict()
        return toml.dumps(d)


class ConfLoad(BaseModel):
    text: str