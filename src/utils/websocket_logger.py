import asyncio
import json
import sys
import threading
from datetime import datetime
from typing import Optional

import websockets
from tqdm import tqdm as original_tqdm


class WebSocketLogger:
    """WebSocket日志管理器"""
    _instance = None
    _clients = set()
    _server = None
    _loop = None
    _server_thread = None
    _recursion_guard = False
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebSocketLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """延迟初始化，避免递归"""
        if not self._initialized:
            self._initialized = True
            self._start_server()

    def _start_server(self):
        """启动WebSocket服务器 - 使用主事件循环"""
        # 获取或创建主事件循环
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        # 如果循环已经在运行，直接启动服务器
        if self._loop.is_running():
            asyncio.create_task(self._start_server_async())
        else:
            # 在新线程中运行事件循环
            def run_loop():
                asyncio.set_event_loop(self._loop)
                self._loop.run_until_complete(self._start_server_async())
                self._loop.run_forever()

            self._server_thread = threading.Thread(target=run_loop, daemon=True)
            self._server_thread.start()

    async def _start_server_async(self):
        """异步启动服务器"""
        try:
            self._server = await websockets.serve(
                self._websocket_handler,
                "localhost",
                8765
            )
            print("WebSocket服务器已启动在 localhost:8765")
        except Exception as e:
            print(f"WebSocket服务器启动失败: {e}")

    async def _websocket_handler(self, websocket):
        """WebSocket连接处理器"""
        self._clients.add(websocket)
        client_info = f"{websocket.remote_address}"
        print(f"新客户端连接: {client_info}")

        try:
            await self._send_to_client(websocket, {
                "type": "system",
                "message": "已连接到Python日志服务器",
                "level": "info",
                "timestamp": self._get_timestamp()
            })

            # 保持连接
            async for message in websocket:
                pass

        except websockets.exceptions.ConnectionClosed:
            print(f"客户端断开: {client_info}")
        finally:
            self._clients.remove(websocket)

    async def _send_to_client(self, websocket, data):
        """发送消息到指定客户端"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            if websocket in self._clients:
                self._clients.remove(websocket)

    async def _broadcast_async(self, data):
        """异步广播消息到所有客户端"""
        if not self._clients:
            return

        disconnected_clients = []
        for client in list(self._clients):  # 创建副本避免修改时迭代
            try:
                await client.send(json.dumps(data))
            except (websockets.exceptions.ConnectionClosed, Exception):
                disconnected_clients.append(client)

        for client in disconnected_clients:
            if client in self._clients:
                self._clients.remove(client)

    @staticmethod
    def _get_timestamp():
        """获取时间戳"""
        return datetime.now().strftime("%H:%M:%S")

    def log(self, message: str, level: str = "info"):
        """记录日志 - 超轻量版本"""
        if self._recursion_guard:
            return

        self._recursion_guard = True
        try:
            # 只输出到控制台，不发送WebSocket
            timestamp = self._get_timestamp()
            sys.__stdout__.write(f"[{timestamp}] {message}\n")
            sys.__stdout__.flush()
        finally:
            self._recursion_guard = False

    def progress(self, current: int, total: int, description: str = ""):
        """发送进度信息 - 简化版本"""
        if self._recursion_guard:
            return

        self._recursion_guard = True
        try:
            percentage = int((current / total) * 100) if total > 0 else 0
            data = {
                "type": "progress",
                "current": current,
                "total": total,
                "percentage": percentage,
                "description": description,
                "timestamp": self._get_timestamp()
            }

            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._broadcast_async(data),
                    self._loop
                )
        finally:
            self._recursion_guard = False

    def complete(self, message: str = "任务完成"):
        """发送完成消息"""
        self.log(message, "success")

    def error(self, message: str):
        """发送错误消息"""
        self.log(message, "error")


class WebSocketTqdm:
    """tqdm的WebSocket包装器"""

    def __init__(self, iterable=None, total: Optional[int] = None, desc: str = ""):
        self.websocket_logger = WebSocketLogger()
        self.desc = desc
        self.total = total if total is not None else len(iterable) if iterable is not None else 0
        self.current = 0

        # 创建原始tqdm实例
        self._tqdm = original_tqdm(
            iterable=iterable,
            total=total,
            desc=desc
        )

        # 初始进度
        self.websocket_logger.progress(0, self.total, desc)

    def __iter__(self):
        return self._tqdm.__iter__()

    def __next__(self):
        try:
            value = next(self._tqdm)
            self.current += 1
            self.websocket_logger.progress(self.current, self.total, self.desc)
            return value
        except StopIteration:
            self.websocket_logger.complete(f"{self.desc} 完成")
            raise

    def update(self, n: int = 1):
        """更新进度"""
        self._tqdm.update(n)
        self.current += n
        self.websocket_logger.progress(self.current, self.total, self.desc)

    def set_description(self, desc: str):
        """设置描述"""
        self._tqdm.set_description(desc)
        self.desc = desc

    def close(self):
        """关闭进度条"""
        self._tqdm.close()


class WebSocketStdout:
    """重定向stdout到WebSocket"""

    def __init__(self):
        self.websocket_logger = WebSocketLogger()
        self.original_stdout = sys.stdout
        self._recursion_guard = False

    def write(self, text):
        """写入文本"""
        if self._recursion_guard or not text.strip() or text.isspace():
            self.original_stdout.write(text)
            return

        self._recursion_guard = True
        try:
            self.websocket_logger.log(text.strip(), "info")
            self.original_stdout.write(text)
        finally:
            self._recursion_guard = False

    def flush(self):
        """刷新缓冲区"""
        self.original_stdout.flush()


# 创建全局实例
websocket_logger = WebSocketLogger()

def get_websocket_logger():
    """获取WebSocket日志器实例"""
    return websocket_logger

def tqdm_websocket(iterable=None, total=None, desc=""):
    """创建带WebSocket的tqdm进度条"""
    return WebSocketTqdm(iterable=iterable, total=total, desc=desc)

# 可选：应用重定向
# sys.stdout = WebSocketStdout()