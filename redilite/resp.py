"""
RESP Protocol Parser and Encoder for LiteDis (Redis Compatibility Layer).
"""

from typing import Any, List, Optional, Tuple, Union


class RESPDecoder:
    """
    Parses RESP (Redis Serialization Protocol) bytes streams into Python objects.
    """

    def __init__(self):
        self._buffer = bytearray()

    def feed(self, data: bytes):
        self._buffer.extend(data)

    def parse(self) -> Optional[Any]:
        """
        Attempts to parse one complete RESP command from the buffer.
        Returns parsed value (str, int, list, bytes, None, or Exception) if complete, or None if incomplete.
        """
        if not self._buffer:
            return None

        prefix = self._buffer[0:1]
        line_idx = self._buffer.find(b"\r\n")

        if line_idx == -1:
            return None

        line = bytes(self._buffer[1:line_idx])

        if prefix == b"+":  # Simple String
            del self._buffer[: line_idx + 2]
            return line.decode("utf-8", errors="replace")

        elif prefix == b"-":  # Error
            del self._buffer[: line_idx + 2]
            return Exception(line.decode("utf-8", errors="replace"))

        elif prefix == b":":  # Integer
            del self._buffer[: line_idx + 2]
            return int(line)

        elif prefix == b"$":  # Bulk String
            length = int(line)
            if length == -1:
                del self._buffer[: line_idx + 2]
                return None
            
            expected_total = line_idx + 2 + length + 2
            if len(self._buffer) < expected_total:
                return None  # Incomplete bulk string
            
            val_bytes = bytes(self._buffer[line_idx + 2 : line_idx + 2 + length])
            del self._buffer[:expected_total]
            return val_bytes.decode("utf-8", errors="replace")

        elif prefix == b"*":  # Array
            array_len = int(line)
            if array_len == -1:
                del self._buffer[: line_idx + 2]
                return None

            # Temporarily save buffer snapshot to restore if array elements are incomplete
            orig_buffer = bytearray(self._buffer)
            del self._buffer[: line_idx + 2]

            elements = []
            for _ in range(array_len):
                elem = self.parse()
                if elem is None and len(self._buffer) == 0:
                    # Incomplete element, restore buffer
                    self._buffer = orig_buffer
                    return None
                elements.append(elem)

            return elements

        else:
            # Inline command fallback (e.g. standard terminal ping: PING\r\n)
            line_full = bytes(self._buffer[:line_idx])
            del self._buffer[: line_idx + 2]
            parts = [p.decode("utf-8", errors="replace") for p in line_full.split()]
            return parts if parts else None


class RESPEncoder:
    """
    Encodes Python objects into RESP bytes format.
    """

    @staticmethod
    def encode_simple_string(val: str) -> bytes:
        return f"+{val}\r\n".encode("utf-8")

    @staticmethod
    def encode_error(msg: str) -> bytes:
        return f"-ERR {msg}\r\n".encode("utf-8")

    @staticmethod
    def encode_integer(val: int) -> bytes:
        return f":{val}\r\n".encode("utf-8")

    @staticmethod
    def encode_bulk_string(val: Optional[Union[str, bytes]]) -> bytes:
        if val is None:
            return b"$-1\r\n"
        if isinstance(val, str):
            val = val.encode("utf-8")
        return f"${len(val)}\r\n".encode("utf-8") + val + b"\r\n"

    @staticmethod
    def encode_array(val: Optional[List[Any]]) -> bytes:
        if val is None:
            return b"*-1\r\n"
        out = [f"*{len(val)}\r\n".encode("utf-8")]
        for item in val:
            out.append(RESPEncoder.encode(item))
        return b"".join(out)

    @classmethod
    def encode(cls, obj: Any) -> bytes:
        if obj is None:
            return b"$-1\r\n"
        elif isinstance(obj, bool):
            return cls.encode_integer(1 if obj else 0)
        elif isinstance(obj, int):
            return cls.encode_integer(obj)
        elif isinstance(obj, float):
            return cls.encode_bulk_string(str(obj))
        elif isinstance(obj, str):
            if obj.startswith("OK") or obj == "PONG":
                return cls.encode_simple_string(obj)
            return cls.encode_bulk_string(obj)
        elif isinstance(obj, bytes):
            return cls.encode_bulk_string(obj)
        elif isinstance(obj, Exception):
            return cls.encode_error(str(obj))
        elif isinstance(obj, (list, tuple, set)):
            return cls.encode_array(list(obj))
        elif isinstance(obj, dict):
            # Flatten dict to list [k1, v1, k2, v2...]
            flat = []
            for k, v in obj.items():
                flat.extend([k, v])
            return cls.encode_array(flat)
        else:
            return cls.encode_bulk_string(str(obj))
