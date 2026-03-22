"""
OSS 云存储备份实现

使用阿里云 OSS 进行记忆数据备份
支持：
- 自动备份
- 增量备份
- 备份恢复
- 版本管理
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.memory import Memory


class OSSBackup:
    """阿里云 OSS 备份服务

    特点:
    - 自动备份到云端
    - 支持增量备份
    - 备份版本管理
    - 自动恢复

    Requires:
        pip install oss2
    """

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        bucket_name: Optional[str] = None,
        endpoint: str = "oss-cn-shanghai.aliyuncs.com",
        backup_dir: str = "memorybridge/backups",
    ):
        """初始化 OSS 备份

        Args:
            access_key_id: 阿里云 AccessKey ID
                (默认从环境变量 OSS_ACCESS_KEY_ID 读取)
            access_key_secret: 阿里云 AccessKey Secret
                (默认从环境变量 OSS_ACCESS_KEY_SECRET 读取)
            bucket_name: OSS Bucket 名称
                (默认从环境变量 OSS_BUCKET_NAME 读取)
            endpoint: OSS Endpoint (默认：oss-cn-shanghai.aliyuncs.com)
            backup_dir: 备份目录前缀 (默认：memorybridge/backups)
        """
        try:
            import oss2
        except ImportError:
            raise ImportError(
                "oss2 not installed. Install with: pip install oss2"
            )

        # 从环境变量或参数获取配置
        self.access_key_id = access_key_id or os.getenv("OSS_ACCESS_KEY_ID")
        self.access_key_secret = access_key_secret or os.getenv("OSS_ACCESS_KEY_SECRET")
        self.bucket_name = bucket_name or os.getenv("OSS_BUCKET_NAME")

        if not all([self.access_key_id, self.access_key_secret, self.bucket_name]):
            raise ValueError(
                "OSS credentials not provided. "
                "Set OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME "
                "environment variables or pass them as parameters."
            )

        self.endpoint = endpoint
        self.backup_dir = backup_dir

        # 初始化 OSS
        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)

    def _get_backup_key(self, timestamp: Optional[datetime] = None, suffix: str = "") -> str:
        """生成备份文件路径

        Args:
            timestamp: 时间戳 (默认当前时间)
            suffix: 文件名后缀

        Returns:
            OSS 对象键路径
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        date_str = timestamp.strftime("%Y/%m/%d")
        time_str = timestamp.strftime("%H%M%S")
        
        filename = f"backup_{time_str}{suffix}.json"
        return f"{self.backup_dir}/{date_str}/{filename}"

    def backup(
        self,
        memories: List[Memory],
        timestamp: Optional[datetime] = None,
        compress: bool = True,
    ) -> str:
        """备份记忆到 OSS

        Args:
            memories: 要备份的记忆列表
            timestamp: 备份时间戳 (默认当前时间)
            compress: 是否压缩 (默认 True)

        Returns:
            OSS 对象键路径
        """
        import oss2
        import gzip

        # 序列化记忆数据
        data = json.dumps(
            [m.to_dict() for m in memories],
            indent=2,
            ensure_ascii=False,
        )

        # 生成备份路径
        suffix = ".gz" if compress else ""
        key = self._get_backup_key(timestamp, suffix)

        # 准备数据
        if compress:
            data_bytes = gzip.compress(data.encode("utf-8"))
        else:
            data_bytes = data.encode("utf-8")

        # 上传到 OSS
        result = self.bucket.put_object(key, data_bytes)

        if result.status != 200:
            raise RuntimeError(f"Failed to upload backup: {result.status}")

        return key

    def restore(self, key: str) -> List[Memory]:
        """从 OSS 恢复备份

        Args:
            key: OSS 对象键路径

        Returns:
            恢复的记忆列表
        """
        import gzip

        # 下载备份
        result = self.bucket.get_object(key)
        data_bytes = result.read()

        # 解压（如果是压缩文件）
        if key.endswith(".gz"):
            data = gzip.decompress(data_bytes).decode("utf-8")
        else:
            data = data_bytes.decode("utf-8")

        # 反序列化
        memories_data = json.loads(data)
        return [Memory.from_dict(m) for m in memories_data]

    def list_backups(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """列出备份文件

        Args:
            start_date: 开始日期 (可选)
            end_date: 结束日期 (可选)

        Returns:
            备份文件信息列表
        """
        backups = []
        
        # 列出所有备份
        for obj in oss2.ObjectIterator(self.bucket, prefix=self.backup_dir):
            # 过滤日期范围
            if start_date or end_date:
                obj_time = datetime.fromtimestamp(obj.last_modified)
                if start_date and obj_time < start_date:
                    continue
                if end_date and obj_time > end_date:
                    continue
            
            backups.append({
                "key": obj.key,
                "size": obj.size,
                "last_modified": datetime.fromtimestamp(obj.last_modified),
                "etag": obj.etag,
            })

        # 按时间排序
        backups.sort(key=lambda x: x["last_modified"], reverse=True)
        return backups

    def get_latest_backup(self) -> Optional[Dict[str, Any]]:
        """获取最新备份

        Returns:
            最新备份信息，无备份返回 None
        """
        backups = self.list_backups()
        return backups[0] if backups else None

    def delete_backup(self, key: str) -> bool:
        """删除备份

        Args:
            key: OSS 对象键路径

        Returns:
            是否删除成功
        """
        result = self.bucket.delete_object(key)
        return result.status == 204

    def download_backup(self, key: str, local_path: str) -> str:
        """下载备份到本地

        Args:
            key: OSS 对象键路径
            local_path: 本地保存路径

        Returns:
            本地文件路径
        """
        import gzip

        # 确保目录存在
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        # 下载
        self.bucket.get_object_to_file(key, local_path)

        # 如果是压缩文件，解压
        if key.endswith(".gz"):
            with gzip.open(local_path, "rt", encoding="utf-8") as f:
                data = f.read()
            
            # 保存解压后的文件
            uncompressed_path = local_path[:-3]  # 移除 .gz
            with open(uncompressed_path, "w", encoding="utf-8") as f:
                f.write(data)
            
            # 删除压缩文件
            os.unlink(local_path)
            return uncompressed_path
        
        return local_path

    def auto_backup(
        self,
        memories: List[Memory],
        keep_days: int = 30,
    ) -> str:
        """自动备份（带清理策略）

        Args:
            memories: 要备份的记忆列表
            keep_days: 保留天数 (默认 30 天)

        Returns:
            备份键路径
        """
        from datetime import timedelta

        # 执行备份
        key = self.backup(memories)

        # 清理旧备份
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        backups = self.list_backups()

        for backup in backups:
            if backup["last_modified"] < cutoff_date:
                self.delete_backup(backup["key"])

        return key

    def __repr__(self) -> str:
        return f"OSSBackup(bucket='{self.bucket_name}', dir='{self.backup_dir}')"
