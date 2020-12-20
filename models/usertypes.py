from enum import Enum

import functools



class NodeRole(str, Enum):
    sources = 'sources'
    sinks = 'sinks'
    transforms = 'transforms'

# class NodeType(str, Enum):
#     file = 'file'
#     lua = 'lua'
#     generator = 'generator'
#     console = 'console'
#     tokenizer = 'tokenizer'
#     sampler = "sampler"
#     elasticsearch = "elasticsearch"


    # @classmethod
    # def register_model(cls, node_type, model_class):
    #     _node_classes[node_type] = model_class


class node_subclass_registry:

    _node_classes = {}
    _codes = {}

    def __init__(self, node_role: NodeRole):
        self.node_role = node_role

    def __call__(self, node_subcls):
        registry = node_subclass_registry._node_classes
        node_role = self.node_role.value
        # node_type = self.node_type.value
        # node_type = node_subcls.type
        node_type = node_subcls.__fields__["type"].default
        roles_registry = registry.get(node_role, {})
        if node_type in roles_registry:
            raise KeyError(f'Node class for {node_type} already registered')
        roles_registry[node_type] = node_subcls
        registry[node_role] = roles_registry
        return node_subcls

    @classmethod
    def model_for_role_type(cls, node_role: NodeRole, node_type: str):
        roles_registry = cls._node_classes[node_role.value]
        try:
            subcls = roles_registry[node_type]
        except Exception as e:
            raise ValueError(f"No such type registered: {node_type}")
        return functools.partial(subcls, role=node_role)


class FileFingerprintingStrategy(str, Enum):
    checksum = 'checksum'
    device_and_inode = 'device_and_inode'

class FileMultilineParseMode(str, Enum):
    continue_through = "continue_through"
    continue_past = "continue_past"
    halt_before = "halt_before"
    halt_with = "halt_with"


class FileEncoding(str, Enum):
    ndjson = "ndjson"
    text = "text"

class TimestampFormat(str, Enum):
    rfc3339 = "rfc3339"
    unix = "unix"


class StdStream(str, Enum):
    stdout = "stdout"
    stderr = "stderr"

class VectorValueType(str, Enum):
    bool = "bool"
    float = "float"
    int = "int"
    string = "string"
    timestamp = "timestamp"


# class EncryptionScheme(str, Enum):
#     "for MP4"
#     cenc = 'cenc'
#     "for caption files"
#     aes_cbc = 'aes-cbc'

