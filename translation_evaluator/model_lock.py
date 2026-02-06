"""
模型加载锁机制
避免多个进程同时加载大型模型导致系统卡死
"""

import os
import time
import fcntl
import tempfile
from pathlib import Path


class ModelLock:
    """模型加载文件锁"""
    
    def __init__(self, lock_name: str, timeout: int = 300, wait_interval: float = 1.0):
        """
        初始化模型锁
        
        Args:
            lock_name: 锁名称（用于区分不同的模型）
            timeout: 超时时间（秒），超过此时间自动释放锁
            wait_interval: 等待锁的间隔时间（秒）
        """
        self.lock_name = lock_name
        self.timeout = timeout
        self.wait_interval = wait_interval
        
        # 使用临时目录存放锁文件
        lock_dir = os.path.join(tempfile.gettempdir(), "translation_evaluator_locks")
        os.makedirs(lock_dir, exist_ok=True)
        
        self.lock_file = os.path.join(lock_dir, f"{lock_name}.lock")
        self.lock_fd = None
    
    def acquire(self, timeout: int = None):
        """
        获取锁
        
        Args:
            timeout: 等待超时时间（秒），None表示使用默认超时
            
        Returns:
            bool: 是否成功获取锁
        """
        if timeout is None:
            timeout = self.timeout
        
        start_time = time.time()
        max_wait_time = timeout
        
        while True:
            try:
                # 尝试打开锁文件（创建模式）
                self.lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
                
                # 尝试获取排他锁（非阻塞）
                try:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    
                    # 写入进程ID和时间戳
                    pid = os.getpid()
                    timestamp = time.time()
                    os.write(self.lock_fd, f"{pid}:{timestamp}\n".encode())
                    os.fsync(self.lock_fd)
                    
                    print(f"🔒 [ModelLock] 已获取锁: {self.lock_name} (PID: {pid})")
                    return True
                    
                except BlockingIOError:
                    # 锁被其他进程持有，检查是否超时
                    elapsed = time.time() - start_time
                    if elapsed >= max_wait_time:
                        print(f"⚠️  [ModelLock] 获取锁超时: {self.lock_name} (等待了 {elapsed:.1f}秒)")
                        os.close(self.lock_fd)
                        self.lock_fd = None
                        return False
                    
                    # 检查锁文件是否过期（可能是进程崩溃留下的）
                    if os.path.exists(self.lock_file):
                        try:
                            with open(self.lock_file, 'r') as f:
                                content = f.read().strip()
                                if content:
                                    parts = content.split(':')
                                    if len(parts) >= 2:
                                        lock_pid = int(parts[0])
                                        lock_time = float(parts[1])
                                        
                                        # 检查进程是否还在运行
                                        try:
                                            os.kill(lock_pid, 0)  # 信号0用于检查进程是否存在
                                        except (OSError, ProcessLookupError):
                                            # 进程不存在，删除过期锁
                                            print(f"🔓 [ModelLock] 检测到过期锁，清理: {self.lock_name} (PID: {lock_pid})")
                                            os.remove(self.lock_file)
                                            os.close(self.lock_fd)
                                            self.lock_fd = None
                                            continue
                                        
                                        # 检查锁是否超时
                                        if time.time() - lock_time > self.timeout:
                                            print(f"🔓 [ModelLock] 检测到超时锁，清理: {self.lock_name}")
                                            os.remove(self.lock_file)
                                            os.close(self.lock_fd)
                                            self.lock_fd = None
                                            continue
                        except Exception:
                            pass
                    
                    os.close(self.lock_fd)
                    self.lock_fd = None
                    
                    # 等待一段时间后重试
                    print(f"⏳ [ModelLock] 等待锁释放: {self.lock_name} (已等待 {elapsed:.1f}秒)")
                    time.sleep(self.wait_interval)
                    
            except Exception as e:
                print(f"⚠️  [ModelLock] 获取锁异常: {e}")
                if self.lock_fd is not None:
                    try:
                        os.close(self.lock_fd)
                    except:
                        pass
                    self.lock_fd = None
                return False
    
    def release(self):
        """释放锁"""
        if self.lock_fd is not None:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                os.close(self.lock_fd)
                self.lock_fd = None
                
                # 删除锁文件
                if os.path.exists(self.lock_file):
                    try:
                        os.remove(self.lock_file)
                    except:
                        pass
                
                print(f"🔓 [ModelLock] 已释放锁: {self.lock_name}")
            except Exception as e:
                print(f"⚠️  [ModelLock] 释放锁异常: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        if self.acquire():
            return self
        else:
            raise TimeoutError(f"无法获取模型锁: {self.lock_name}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()


# Windows兼容性（如果没有fcntl）
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    
    # Windows下使用简单的文件锁
    class ModelLock:
        def __init__(self, lock_name: str, timeout: int = 300, wait_interval: float = 1.0):
            self.lock_name = lock_name
            self.timeout = timeout
            self.wait_interval = wait_interval
            lock_dir = os.path.join(tempfile.gettempdir(), "translation_evaluator_locks")
            os.makedirs(lock_dir, exist_ok=True)
            self.lock_file = os.path.join(lock_dir, f"{lock_name}.lock")
        
        def acquire(self, timeout: int = None):
            if timeout is None:
                timeout = self.timeout
            start_time = time.time()
            while True:
                try:
                    if not os.path.exists(self.lock_file):
                        # 创建锁文件
                        with open(self.lock_file, 'w') as f:
                            f.write(f"{os.getpid()}:{time.time()}\n")
                        return True
                    else:
                        # 检查锁是否过期
                        with open(self.lock_file, 'r') as f:
                            content = f.read().strip()
                            if content:
                                parts = content.split(':')
                                if len(parts) >= 2:
                                    lock_pid = int(parts[0])
                                    lock_time = float(parts[1])
                                    if time.time() - lock_time > self.timeout:
                                        os.remove(self.lock_file)
                                        continue
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        return False
                    time.sleep(self.wait_interval)
                except Exception:
                    time.sleep(self.wait_interval)
        
        def release(self):
            if os.path.exists(self.lock_file):
                try:
                    os.remove(self.lock_file)
                except:
                    pass
        
        def __enter__(self):
            if self.acquire():
                return self
            else:
                raise TimeoutError(f"无法获取模型锁: {self.lock_name}")
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.release()
