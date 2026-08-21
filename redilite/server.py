"""
Async RESP TCP Server for RediLite - Allows redis-cli and standard Redis drivers to connect.
"""

import asyncio
import logging
from typing import Optional
from .core import RediLite
from .resp import RESPDecoder, RESPEncoder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class RediLiteServer:
    """
    Async TCP server serving RediLite over Redis Serialization Protocol (RESP).
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 6379, db_path: str = "mydb.redilite"):
        self.host = host
        self.port = port
        self.db_path = db_path
        self.db = RediLite(db_path)
        self.server: Optional[asyncio.AbstractServer] = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        decoder = RESPDecoder()
        peer = writer.get_extra_info('peername')
        logging.info(f"Client connected from {peer}")

        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break

                decoder.feed(data)
                while True:
                    parsed = decoder.parse()
                    if parsed is None:
                        break

                    if isinstance(parsed, list):
                        if not parsed:
                            continue
                        cmd = str(parsed[0])
                        args = [str(x) for x in parsed[1:]]

                        if cmd.upper() == "QUIT":
                            writer.write(RESPEncoder.encode_simple_string("OK"))
                            await writer.drain()
                            writer.close()
                            await writer.wait_closed()
                            return

                        result = self.db.execute_command(cmd, *args)
                        response_bytes = RESPEncoder.encode(result)
                    elif isinstance(parsed, str):
                        parts = parsed.split()
                        cmd = parts[0]
                        args = parts[1:]
                        result = self.db.execute_command(cmd, *args)
                        response_bytes = RESPEncoder.encode(result)
                    else:
                        response_bytes = RESPEncoder.encode_error("ERR syntax error")

                    writer.write(response_bytes)
                    await writer.drain()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"Error handling client {peer}: {e}")
        finally:
            logging.info(f"Client disconnected from {peer}")
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass  # nosec B110

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = self.server.sockets[0].getsockname()
        logging.info(f"RediLite Server running on {addr[0]}:{addr[1]} (backed by '{self.db_path}')")
        async with self.server:
            await self.server.serve_forever()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logging.info("RediLite Server stopped.")
        finally:
            self.db.close()


# Backwards compatibility alias
LiteDisServer = RediLiteServer


if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "mydb.redilite"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 6379
    server = RediLiteServer(port=port, db_path=db)
    server.run()
