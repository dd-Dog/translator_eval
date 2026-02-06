"""
请求队列管理器
实现单线程处理，避免并发请求导致服务器压力过大
"""

import threading
import queue
import time
import uuid
from typing import Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class RequestStatus(Enum):
    """请求状态"""
    QUEUED = "queued"  # 排队中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    TIMEOUT = "timeout"  # 超时
    CANCELLED = "cancelled"  # 已取消


@dataclass
class QueuedRequest:
    """排队请求"""
    request_id: str
    request_data: Dict[str, Any]
    status: RequestStatus = RequestStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    queue_position: int = 0


class RequestQueue:
    """请求队列管理器"""
    
    def __init__(self, max_queue_size: int = 100, request_timeout: int = 300):
        """
        初始化请求队列
        
        Args:
            max_queue_size: 最大队列长度
            request_timeout: 请求超时时间（秒）
        """
        self.max_queue_size = max_queue_size
        self.request_timeout = request_timeout
        
        # 请求队列
        self.queue = queue.Queue(maxsize=max_queue_size)
        
        # 请求状态跟踪
        self.requests: Dict[str, QueuedRequest] = {}
        self.requests_lock = threading.Lock()
        
        # 处理锁（确保单线程处理）
        self.processing_lock = threading.Lock()
        
        # 当前处理的请求ID
        self.current_request_id: Optional[str] = None
        
        # 后台处理线程
        self.processing_thread: Optional[threading.Thread] = None
        self.running = False
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "timeout_requests": 0,
            "current_queue_size": 0
        }
    
    def start(self):
        """启动队列处理线程"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.processing_thread.start()
            print(f"✅ 请求队列已启动 (最大队列长度: {self.max_queue_size}, 超时: {self.request_timeout}秒)")
    
    def stop(self):
        """停止队列处理线程"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
    
    def submit_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提交请求到队列
        
        Args:
            request_data: 请求数据
            
        Returns:
            Dict: 包含request_id和status的字典
        """
        # 检查队列是否已满
        if self.queue.full():
            return {
                "success": False,
                "error": "服务器队列已满，请稍后重试",
                "queue_full": True,
                "max_queue_size": self.max_queue_size
            }
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 创建排队请求
        queued_request = QueuedRequest(
            request_id=request_id,
            request_data=request_data,
            queue_position=self.queue.qsize() + 1
        )
        
        # 添加到队列和状态跟踪
        try:
            self.queue.put(queued_request, timeout=1)
            with self.requests_lock:
                self.requests[request_id] = queued_request
                self.stats["total_requests"] += 1
                self.stats["current_queue_size"] = self.queue.qsize()
            
            return {
                "success": True,
                "request_id": request_id,
                "status": "queued",
                "queue_position": queued_request.queue_position,
                "message": f"请求已加入队列，当前排队位置: {queued_request.queue_position}"
            }
        except queue.Full:
            return {
                "success": False,
                "error": "服务器队列已满，请稍后重试",
                "queue_full": True
            }
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        获取请求状态
        
        Args:
            request_id: 请求ID
            
        Returns:
            Dict: 请求状态信息，如果不存在返回None
        """
        with self.requests_lock:
            if request_id not in self.requests:
                return None
            
            req = self.requests[request_id]
            
            # 计算等待时间
            wait_time = None
            if req.status == RequestStatus.QUEUED:
                wait_time = (datetime.now() - req.created_at).total_seconds()
            elif req.status == RequestStatus.PROCESSING and req.started_at:
                wait_time = (datetime.now() - req.started_at).total_seconds()
            
            # 计算队列位置
            queue_position = 0
            if req.status == RequestStatus.QUEUED:
                # 计算在当前请求之前的排队请求数
                queue_position = sum(
                    1 for r in self.requests.values()
                    if r.status == RequestStatus.QUEUED and r.created_at < req.created_at
                ) + 1
            
            return {
                "request_id": request_id,
                "status": req.status.value,
                "queue_position": queue_position,
                "created_at": req.created_at.isoformat(),
                "started_at": req.started_at.isoformat() if req.started_at else None,
                "completed_at": req.completed_at.isoformat() if req.completed_at else None,
                "wait_time": wait_time,
                "result": req.result,
                "error": req.error
            }
    
    def _process_queue(self):
        """后台处理队列（单线程）"""
        while self.running:
            try:
                # 从队列获取请求（阻塞，最多等待1秒）
                try:
                    queued_request = self.queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # 使用锁确保单线程处理
                with self.processing_lock:
                    self.current_request_id = queued_request.request_id
                    
                    # 更新状态
                    with self.requests_lock:
                        queued_request.status = RequestStatus.PROCESSING
                        queued_request.started_at = datetime.now()
                        queued_request.queue_position = 0
                        self.stats["current_queue_size"] = self.queue.qsize()
                    
                    # 处理请求（由外部提供处理函数）
                    result = None
                    error = None
                    
                    try:
                        # 检查超时
                        elapsed = (datetime.now() - queued_request.created_at).total_seconds()
                        if elapsed > self.request_timeout:
                            raise TimeoutError(f"请求在队列中等待超时 ({elapsed:.1f}秒)")
                        
                        # 调用处理函数（通过回调）
                        if hasattr(self, '_process_callback') and self._process_callback:
                            result = self._process_callback(queued_request.request_data)
                        else:
                            # 默认处理（应该由外部设置回调）
                            result = {"error": "处理回调未设置"}
                        
                        # 更新状态
                        with self.requests_lock:
                            queued_request.status = RequestStatus.COMPLETED
                            queued_request.completed_at = datetime.now()
                            queued_request.result = result
                            self.stats["completed_requests"] += 1
                            self.stats["current_queue_size"] = self.queue.qsize()
                    
                    except TimeoutError as e:
                        error = str(e)
                        with self.requests_lock:
                            queued_request.status = RequestStatus.TIMEOUT
                            queued_request.completed_at = datetime.now()
                            queued_request.error = error
                            self.stats["timeout_requests"] += 1
                            self.stats["current_queue_size"] = self.queue.qsize()
                    
                    except Exception as e:
                        error = str(e)
                        with self.requests_lock:
                            queued_request.status = RequestStatus.FAILED
                            queued_request.completed_at = datetime.now()
                            queued_request.error = error
                            self.stats["failed_requests"] += 1
                            self.stats["current_queue_size"] = self.queue.qsize()
                    
                    finally:
                        self.current_request_id = None
                        self.queue.task_done()
            
            except Exception as e:
                print(f"⚠️  队列处理异常: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)  # 避免异常循环
    
    def set_process_callback(self, callback):
        """设置请求处理回调函数"""
        self._process_callback = callback
    
    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        with self.requests_lock:
            return {
                "queue_size": self.queue.qsize(),
                "current_processing": self.current_request_id,
                "total_requests": self.stats["total_requests"],
                "completed_requests": self.stats["completed_requests"],
                "failed_requests": self.stats["failed_requests"],
                "timeout_requests": self.stats["timeout_requests"],
                "max_queue_size": self.max_queue_size,
                "request_timeout": self.request_timeout
            }
    
    def cleanup_old_requests(self, max_age_seconds: int = 3600):
        """清理旧的已完成请求（释放内存）"""
        with self.requests_lock:
            now = datetime.now()
            to_remove = []
            for request_id, req in self.requests.items():
                if req.status in [RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.TIMEOUT]:
                    if req.completed_at:
                        age = (now - req.completed_at).total_seconds()
                        if age > max_age_seconds:
                            to_remove.append(request_id)
            
            for request_id in to_remove:
                del self.requests[request_id]
            
            if to_remove:
                print(f"🧹 清理了 {len(to_remove)} 个旧请求记录")
