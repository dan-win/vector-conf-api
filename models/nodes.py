# from datetime import datetime
import abc

from typing import Mapping, Optional, List, Union, TypeVar, Any

from typing_extensions import Literal

from pydantic import \
    BaseModel, \
    PydanticValueError, \
    ValidationError, \
    validator, \
    Field, \
    root_validator, \
    UUID4

from .usertypes import \
    NodeRole, \
    FileFingerprintingStrategy, \
    FileMultilineParseMode, \
    FileEncoding, \
    TimestampFormat, \
    StdStream, \
    VectorValueType, \
    node_subclass_registry



class FileFingerprinting(BaseModel):
    # Fingerprinting
    fingerprint_bytes: int = 256 # optional, default, bytes, relevant when strategy = "checksum"
    ignored_header_bytes: int = 0 # optional, default, bytes, relevant when strategy = "checksum"
    strategy: FileFingerprintingStrategy = FileFingerprintingStrategy.checksum # optional, default


class FileMultilineConf(BaseModel):
    "Condition regex pattern to look for"
    condition_pattern: str
    "Mode of operation, specifies how the condition_pattern is interpreted"
    mode: FileMultilineParseMode
    "Start regex pattern to look for as a beginning of the message"
    start_pattern: str
    "Once this timeout is reached, the buffered message is guaraneed to be flushed, even if incomplete"
    timeout_ms: int


# class FileEncoding(BaseModel):
#     "The encoding codec used to serialize the events before outputting."
#     codec: FileEncoding
#     "Prevent the sink from encoding the specified labels."
#     except_fileds: List[str] = []
#     "Limit the sink to only encoding the specified labels."
#     only_fileds: List[str] = []
#     "How to format event timestamps."
#     timestamp_format: TimestampFormat


class BaseSyncEncoding(BaseModel):
    "Prevent the sink from encoding the specified labels."
    except_fileds: List[str] = []
    "Limit the sink to only encoding the specified labels."
    only_fileds: List[str] = []
    "How to format event timestamps."
    timestamp_format: TimestampFormat


class FileEncoding(BaseSyncEncoding):
    codec: FileEncoding


class RuntimeHooks(BaseModel):
    "A function which is called when the first event comes, before calling hooks.process"
    init: Optional[str]
    "A function which is called for each incoming event. It can produce new events using emit function."
    process: str
    "A function which is called when Vector is stopped. It can produce new events using emit function."
    shutdown: Optional[str]


class ElasticsearchAuth(BaseModel):
    assume_role: Optional[str]
    password: Optional[str]
    strategy: Literal["aws", "basic"]
    user: Optional[str]

    @root_validator
    def check_values(cls, values):
        strategy = values.get('strategy')

        if strategy == 'basic':
            if not values.get('user'):
                raise ValueError('User field is required for basic strategy')
            if not values.get('password'):
                raise ValueError('Password field is required for basic strategy')
            if values.get('assume_role'):
                raise ValueError('assume_role field is not applicable for basic strategy')
        elif strategy == 'aws':
            pass
        return values    


class ClickHouseAuth(BaseModel):
    strategy: Literal['basic', 'bearer']
    password: Optional[str]
    token: Optional[str]
    user: Optional[str]

    @root_validator
    def check_values(cls, values):
        strategy = values.get('strategy')

        if strategy == 'basic':
            if not values.get('user'):
                raise ValueError('User field is required for basic strategy')
            if not values.get('password'):
                raise ValueError('Password field is required for basic strategy')
        elif strategy == 'bearer':
            if not values.get('token'):
                raise ValueError('token field is required for bearer strategy')
        return values    

class AwsOptions(BaseModel):
    region: str


class BatchOptions(BaseModel):
    max_bytes: int = 10490000
    max_events: Optional[int]
    timeout_secs: int = 1


class BufferOptions(BaseModel):
    type: Literal["memory", "disk"] = "memory"
    max_events: int = 500
    max_size: Optional[int]
    when_full: Literal["block", "drop_newest"]

    @root_validator
    def check_values(cls, values):
        stype = values.get('type')

        if stype == 'disk':
            if not values.get('max_size'):
                raise ValueError('max_size field is required for disk buffer')
            if values.get('max_events'):
                raise ValueError('max_events field is not applicable for disk buffer')
        elif stype == 'memory':
            pass
        return values    


class SinkRequestOptions(BaseModel):
    in_flight_limit: int = 5
    rate_limit_duration_secs: int = 1
    rate_limit_num: int = 5
    retry_attempts: int = 18446744073709552000
    retry_initial_backoff_secs: int = 1
    retry_max_duration_secs: int = 10
    timeout_secs: int = 10


class TlsOptions(BaseModel):
    ca_file: Optional[str]
    crt_file: Optional[str]
    key_file: Optional[str]
    key_pass: Optional[str]
    verify_certificate: bool = True
    verify_hostname: bool = True




class Node(BaseModel, abc.ABC):
    type: str
    role: NodeRole
    # type: NodeType = NodeType.file
    name: str

    def dict(self) -> Mapping[str, Any]:
        d = super().dict()
        name = d.pop("name")
        role = d.pop("role")
        d["type"] = str(d["type"])
        return d

    def get_key(self):
        return f"{self.role.value}.{self.name}"
    
    def display_dict(self) -> Mapping[str, Any]:
        d = self.dict()
        return dict(**d, 
            id=self.get_key(),
            role = self.role.value
            )

class DescendantNode(Node):
    """ Transforms and sinks which have inputs"""
    inputs: Optional[List[str]]

class CRUDNode(DescendantNode):
    key: str


class HasVersions:
    @classmethod
    def detect_version_tag(cls, values) -> str:
        return ""


@node_subclass_registry(NodeRole.sources)
class SourceFile(Node):
    """The Vector file source ingests data through one or more local files and outputs log events. Reference: https://vector.dev/docs/reference/sources/file/"""
    type: Literal['file'] = 'file'
    "The directory used to persist file checkpoint positions"
    data_dir: Optional[str]
    exclude: List[str] = []
    file_key: str = 'file'
    "The number of bytes read off the head of the file to generate a unique fingerprint"
    fingerprinting: Optional[FileFingerprinting]
    "Delay (ms) between file discovery calls."
    glob_minimum_cooldown: int = 1000
    "The key name added to each event representing the current host"
    host_key: Optional[str]
    "Ignore files with a data modification date that does not exceed this age (sec)."
    ignore_older: Optional[int]
    "Array of file patterns to include. Globbing is supported.  e.g: include = ['/var/log/nginx/*log']"
    include: List[str]
    "The maximum number of a bytes a line can contain before being discarded. This protects against malformed lines or tailing incorrect files."
    max_line_bytes: int = 102400
    "An approximate limit on the amount of data read from a single file at a given time."
    max_read_bytes: int = 2048
    "Multiline parsing configuration (per file). If not speicified, multiline parsing is disabled"
    multiline: Optional[FileMultilineConf]
    "Instead of balancing read capacity fairly across all watched files, prioritize draining the oldest files before moving on to read data from younger files"
    oldest_first: bool = False
    "Timeout from reaching eof after which file will be removed from filesystem, unless new data is written in the meantime. If not specified, files will not be removed."
    remove_after: Optional[int]
    "For files with a stored checkpoint at startup, setting this option to true will tell Vector to read from the beginning of the file instead of the stored checkpoint"
    start_at_beginning: bool = False


@node_subclass_registry(NodeRole.sources)
class SourceGenerator(Node):
    """The Vector generator source ingests data through an internal data generator and outputs log events. Reference: https://vector.dev/docs/reference/sources/generator/"""
    type: Literal['generator'] = 'generator'
    "The amount of time, in seconds, to pause between each batch of output lines. If not set, there will be no delay."
    batch_interval: Optional[float]
    "The number of times to repeat outputting the lines."
    count: Union[str, float] = "infinite"
    "The list of lines to output."
    lines: List[str]
    "If true, each output line will start with an increasing sequence number."
    sequence: bool = False


@node_subclass_registry(NodeRole.sinks)
class SinkFile(DescendantNode):
    type: Literal['file'] = 'file'
    "Configures the encoding specific sink behavior."
    encoding: FileEncoding
    "Enables/disables the sink healthcheck upon start."
    healthcheck: bool = True
    "The amount of time a file can be idle and stay open."
    idle_timeout_secs: int = 30
    "File name to write events, e.g. application-{{ application_id }}-%Y-%m-%d.log"
    path: str

@node_subclass_registry(NodeRole.sinks)
class SinkConsole(DescendantNode):
    """The Vector console sink streams log and metric events to standard output streams, such as STDOUT and STDERR. Reference: https://vector.dev/docs/reference/sinks/console/"""
    type: Literal['console'] = 'console'
    "Configures the encoding specific sink behavior."
    encoding: FileEncoding
    "The standard stream to write to."
    target: StdStream = StdStream.stdout


@node_subclass_registry(NodeRole.transforms)
class TransformLua(DescendantNode):
    type: Literal['lua'] = 'lua'
    hooks: RuntimeHooks
    search_dirs: Optional[List[str]]


FieldTypeMapping = TypeVar("FieldTypeMapping", bound=Mapping[str, VectorValueType])

@node_subclass_registry(NodeRole.transforms)
class TransformTokenizer(DescendantNode):
    type: Literal['tokenizer'] = 'tokenizer'
    "If true the field will be dropped after parsing."
    drop_field: bool = True
    "The log field to tokenize. "
    field: str = "message"
    "The log field names assigned to the resulting tokens, in order"
    field_names: List[str]
    "Key/value pairs representing mapped log field names and types"
    types: Optional[FieldTypeMapping]


@node_subclass_registry(NodeRole.transforms)
class TransformSampler(DescendantNode):
    type: Literal['sampler'] = 'sampler'
    "The name of the log field to use to determine if the event should be passed."
    key_field: Optional[str]
    "A list of regular expression patterns to exclude events from sampling"
    pass_list: Optional[List[str]]
    "The rate at which events will be forwarded, expressed as 1/N"
    rate: int


@node_subclass_registry(NodeRole.sinks)
class SinkElasticsearch(DescendantNode):
    type: Literal['elasticsearch'] = 'elasticsearch'
    auth: Optional[ElasticsearchAuth]
    aws: Optional[AwsOptions]
    batch: Optional[BatchOptions]
    buffer: Optional[BufferOptions]
    compression: Literal["none", "gzip"] = "none"
    doc_type: str = "_doc"
    encoding: Optional[BaseSyncEncoding]
    headers: Optional[Mapping[str, str]]
    healthcheck: bool = True
    host: Optional[str]
    id_key: Optional[str]
    index: Optional[str]
    query: Optional[Mapping[str,str]]
    request: Optional[SinkRequestOptions]
    tls: Optional[TlsOptions]


@node_subclass_registry(NodeRole.sinks)
class SinkInfluxDbLogs(DescendantNode):
    type: Literal['influxdb_logs'] = 'influxdb_logs'
    batch: Optional[BatchOptions]
    buffer: Optional[BufferOptions]
    bucket: Optional[str] # Ver 2, req
    consistency: Optional[str] # Ver 1
    database: Optional[str] # Ver 1, req
    encoding: Optional[BaseSyncEncoding]
    endpoint: str
    healthcheck: bool = True
    namespace: str
    org: Optional[str] # Ver 2, req
    password: Optional[str] # Ver 1
    request: Optional[SinkRequestOptions]
    retention_policy_name: Optional[str] # Ver 1
    tags: Optional[List[str]]
    token: Optional[str] # Ver 2, req
    username: Optional[str] # Ver 1


@node_subclass_registry(NodeRole.sinks)
class SinkInfluxDbMetrics(DescendantNode):
    type: Literal['influxdb_metrics'] = 'influxdb_metrics'
    batch: Optional[BatchOptions]
    # buffer: Optional[BufferOptions]
    bucket: Optional[str] # Ver 2, req
    consistency: Optional[str] # Ver 1
    database: Optional[str] # Ver 1, req
    # encoding: Optional[BaseSyncEncoding]
    endpoint: str
    healthcheck: bool = True
    namespace: str
    org: Optional[str] # Ver 2, req
    password: Optional[str] # Ver 1
    request: Optional[SinkRequestOptions]
    retention_policy_name: Optional[str] # Ver 1
    # tags: Optional[List[str]]
    token: Optional[str] # Ver 2, req
    username: Optional[str] # Ver 1


@node_subclass_registry(NodeRole.sinks)
class SinkClickHouse(DescendantNode):
    type: Literal['clickhouse'] = 'clickhouse'
    auth: Optional[ClickHouseAuth]
    batch: Optional[BatchOptions]
    buffer: Optional[BufferOptions]
    compression: Literal["none", "gzip"] = "none"
    database: Optional[str] 
    encoding: Optional[BaseSyncEncoding]
    healthcheck: bool = True
    host: Optional[str]
    table: str
    healthcheck: bool = True
    host: Optional[str]
    request: Optional[SinkRequestOptions]
    tls: Optional[TlsOptions]



@node_subclass_registry(NodeRole.sinks)
class SinkBlackhole(DescendantNode):
    type: Literal['blackhole'] = 'blackhole'
    print_amount: int


class SourceJournalD(Node):
    type: Literal['journald'] = 'journald'
    batch_size: int = 16
    current_boot_only: bool = True
    data_dir: Optional[str]
    exclude_units: List[str] = []
    include_units: List[str] = []
    journalctl_path: str = "journalctl"
    remap_priority: bool = False

