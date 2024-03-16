from ipaddress import IPv4Address, IPv6Address
from os import PathLike
from typing import Any, AnyStr, IO, Mapping, Optional, Sequence, Text, Tuple, Union

from maxminddb import MODE_AUTO
from maxminddb.errors import InvalidDatabaseError as InvalidDatabaseError
from maxminddb.types import Record

class Reader:
    closed: bool = ...
    def __init__(
        self, database: Union[AnyStr, int, PathLike, IO], mode: int = MODE_AUTO
    ) -> None: ...
    def close(self) -> None: ...
    def get(
        self, ip_address: Union[str, IPv6Address, IPv4Address]
    ) -> Optional[Record]: ...
    def get_with_prefix_len(
        self, ip_address: Union[str, IPv6Address, IPv4Address]
    ) -> Tuple[Optional[Record], int]: ...
    def metadata(self) -> "Metadata": ...
    def __enter__(self) -> "Reader": ...
    def __exit__(self, *args) -> None: ...

class Metadata:
    @property
    def node_count(self) -> int: ...
    @property
    def record_size(self) -> int: ...
    @property
    def ip_version(self) -> int: ...
    @property
    def database_type(self) -> Text: ...
    @property
    def languages(self) -> Sequence[Text]: ...
    @property
    def binary_format_major_version(self) -> int: ...
    @property
    def binary_format_minor_version(self) -> int: ...
    @property
    def build_epoch(self) -> int: ...
    @property
    def description(self) -> Mapping[Text, Text]: ...
    def __init__(self, **kwargs: Any) -> None: ...
