"""
Skill日志记录器 - 记录Skill执行日志到MongoDB和文件
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient


class SkillLogger:
    """Skill日志记录器类"""
    
    def __init__(
        self,
        mongodb: AsyncIOMotorClient,
        log_dir: str = "../logs/skill",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        max_backup_count: int = 5
    ):
        """
        初始化Skill日志记录器
        
        Args:
            mongodb: MongoDB客户端
            log_dir: 日志文件目录
            max_file_size: 单个日志文件最大大小（字节）
            max_backup_count: 保留的备份文件数量
        """
        self._mongodb = mongodb
        self._log_dir = Path(log_dir)
        self._max_file_size = max_file_size
        self._max_backup_count = max_backup_count
        
        # 确保日志目录存在
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据库集合
        self._db = mongodb["ai_gateway"]
        self._collection = self._db["skill_logs"]
        
        # 文件日志配置
        self._system_logger = self._setup_system_logger()
        self._execution_logger = self._setup_execution_logger()
        self._operation_logger = self._setup_operation_logger()
    
    def _setup_system_logger(self) -> logging.Logger:
        """设置系统日志记录器"""
        logger = logging.getLogger("skill_system")
        logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 文件处理器
        log_file = self._log_dir / "system.log"
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self._max_file_size,
            backupCount=self._max_backup_count,
            encoding='utf-8'
        )
        
        # 格式化
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_execution_logger(self) -> logging.Logger:
        """设置执行日志记录器（JSON格式）"""
        logger = logging.getLogger("skill_execution")
        logger.setLevel(logging.INFO)
        
        if logger.handlers:
            return logger
        
        # 每日生成新文件
        today = datetime.now().strftime("%Y%m%d")
        log_file = self._log_dir / f"execution_{today}.log"
        
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        
        return logger
    
    def _setup_operation_logger(self) -> logging.Logger:
        """设置操作日志记录器"""
        logger = logging.getLogger("skill_operation")
        logger.setLevel(logging.INFO)
        
        if logger.handlers:
            return logger
        
        log_file = self._log_dir / "operation.log"
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self._max_file_size,
            backupCount=self._max_backup_count,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def log_execution(
        self,
        category: str,
        skill_name: str,
        skill_version: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        duration_ms: int,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        记录Skill执行日志
        
        Args:
            category: Skill分类
            skill_name: Skill名称
            skill_version: Skill版本
            input_data: 输入数据
            output_data: 输出数据
            duration_ms: 执行耗时（毫秒）
            success: 是否成功
            error_message: 错误信息（失败时）
            metadata: 额外元数据
            
        Returns:
            日志记录ID
        """
        log_id = str(uuid.uuid4())
        
        log_entry = {
            "_id": log_id,
            "category": category,
            "skill_name": skill_name,
            "skill_version": skill_version,
            "input_data": input_data,
            "output_data": output_data if success else None,
            "duration_ms": duration_ms,
            "success": success,
            "error_message": error_message,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }
        
        # 写入MongoDB
        await self._collection.insert_one(log_entry)
        
        # 写入文件日志（JSON格式）
        execution_log = {
            "log_id": log_id,
            "timestamp": datetime.utcnow().isoformat(),
            "category": category,
            "skill_name": skill_name,
            "skill_version": skill_version,
            "duration_ms": duration_ms,
            "success": success,
            "error_message": error_message,
            "metadata": metadata or {}
        }
        
        self._execution_logger.info(json.dumps(execution_log, ensure_ascii=False))
        
        # 系统日志
        if success:
            self._system_logger.info(
                f"Skill执行成功: {category}/{skill_name} v{skill_version} "
                f"耗时{duration_ms}ms"
            )
        else:
            self._system_logger.error(
                f"Skill执行失败: {category}/{skill_name} v{skill_version} "
                f"错误: {error_message}"
            )
        
        return log_id
    
    async def log_skill_load(
        self,
        category: str,
        skill_name: str,
        skill_version: str,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        记录Skill加载日志
        
        Args:
            category: Skill分类
            skill_name: Skill名称
            skill_version: Skill版本
            success: 是否成功加载
            error_message: 错误信息
        """
        if success:
            self._system_logger.info(
                f"Skill加载成功: {category}/{skill_name} v{skill_version}"
            )
        else:
            self._system_logger.error(
                f"Skill加载失败: {category}/{skill_name} v{skill_version} "
                f"错误: {error_message}"
            )
        
        # 操作日志
        self._operation_logger.info(
            f"LOAD: {category}/{skill_name} v{skill_version} "
            f"{'SUCCESS' if success else 'FAILED'}"
        )
    
    async def log_skill_reload(
        self,
        category: Optional[str],
        skill_name: Optional[str],
        success_count: int,
        failed_count: int
    ):
        """
        记录Skill重载日志
        
        Args:
            category: Skill分类（None表示全部）
            skill_name: Skill名称（None表示全部）
            success_count: 成功数量
            failed_count: 失败数量
        """
        if category and skill_name:
            target = f"{category}/{skill_name}"
        elif category:
            target = f"分类: {category}"
        else:
            target = "所有Skill"
        
        self._system_logger.info(
            f"Skill重载完成: {target} "
            f"成功{success_count}个, 失败{failed_count}个"
        )
        
        self._operation_logger.info(
            f"RELOAD: {target} "
            f"成功={success_count}, 失败={failed_count}"
        )
    
    async def get_logs(
        self,
        category: Optional[str] = None,
        skill_name: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        查询Skill执行日志
        
        Args:
            category: Skill分类筛选
            skill_name: Skill名称筛选
            success: 成功状态筛选
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            包含日志列表和总数的字典
        """
        query = {}
        
        if category:
            query["category"] = category
        if skill_name:
            query["skill_name"] = skill_name
        if success is not None:
            query["success"] = success
        
        # 时间范围
        if start_time or end_time:
            query["created_at"] = {}
            if start_time:
                query["created_at"]["$gte"] = start_time
            if end_time:
                query["created_at"]["$lte"] = end_time
        
        cursor = self._collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        logs = []
        
        async for doc in cursor:
            logs.append({
                "id": doc["_id"],
                "category": doc["category"],
                "skill_name": doc["skill_name"],
                "skill_version": doc["skill_version"],
                "duration_ms": doc["duration_ms"],
                "success": doc["success"],
                "error_message": doc.get("error_message"),
                "created_at": doc["created_at"]
            })
        
        total = await self._collection.count_documents(query)
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def get_log_detail(self, log_id: str) -> Optional[Dict[str, Any]]:
        """
        获取日志详情
        
        Args:
            log_id: 日志ID
            
        Returns:
            日志详情字典，不存在则返回None
        """
        doc = await self._collection.find_one({"_id": log_id})
        if not doc:
            return None
        
        return {
            "id": doc["_id"],
            "category": doc["category"],
            "skill_name": doc["skill_name"],
            "skill_version": doc["skill_version"],
            "input_data": doc.get("input_data"),
            "output_data": doc.get("output_data"),
            "duration_ms": doc["duration_ms"],
            "success": doc["success"],
            "error_message": doc.get("error_message"),
            "metadata": doc.get("metadata", {}),
            "created_at": doc["created_at"]
        }
    
    async def get_statistics(
        self,
        category: Optional[str] = None,
        skill_name: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取Skill执行统计
        
        Args:
            category: Skill分类筛选
            skill_name: Skill名称筛选
            days: 统计天数
            
        Returns:
            统计信息字典
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        match_stage = {"created_at": {"$gte": start_date}}
        if category:
            match_stage["category"] = category
        if skill_name:
            match_stage["skill_name"] = skill_name
        
        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": None,
                    "total_executions": {"$sum": 1},
                    "success_count": {
                        "$sum": {"$cond": ["$success", 1, 0]}
                    },
                    "failed_count": {
                        "$sum": {"$cond": [{"$not": "$success"}, 1, 0]}
                    },
                    "avg_duration": {"$avg": "$duration_ms"},
                    "min_duration": {"$min": "$duration_ms"},
                    "max_duration": {"$max": "$duration_ms"}
                }
            }
        ]
        
        result = await self._collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            stats = result[0]
            return {
                "total_executions": stats["total_executions"],
                "success_count": stats["success_count"],
                "failed_count": stats["failed_count"],
                "success_rate": round(stats["success_count"] / stats["total_executions"] * 100, 2),
                "avg_duration_ms": round(stats["avg_duration"], 2),
                "min_duration_ms": stats["min_duration"],
                "max_duration_ms": stats["max_duration"],
                "period_days": days
            }
        
        return {
            "total_executions": 0,
            "success_count": 0,
            "failed_count": 0,
            "success_rate": 0,
            "avg_duration_ms": 0,
            "min_duration_ms": 0,
            "max_duration_ms": 0,
            "period_days": days
        }
    
    async def get_skill_execution_stats(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取各Skill的执行统计
        
        Args:
            days: 统计天数
            limit: 返回数量限制
            
        Returns:
            Skill执行统计列表
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "category": "$category",
                        "skill_name": "$skill_name"
                    },
                    "total_executions": {"$sum": 1},
                    "success_count": {
                        "$sum": {"$cond": ["$success", 1, 0]}
                    },
                    "failed_count": {
                        "$sum": {"$cond": [{"$not": "$success"}, 1, 0]}
                    },
                    "avg_duration": {"$avg": "$duration_ms"}
                }
            },
            {
                "$sort": {"total_executions": -1}
            },
            {
                "$limit": limit
            }
        ]
        
        results = await self._collection.aggregate(pipeline).to_list(length=limit)
        
        stats = []
        for result in results:
            stats.append({
                "category": result["_id"]["category"],
                "skill_name": result["_id"]["skill_name"],
                "total_executions": result["total_executions"],
                "success_count": result["success_count"],
                "failed_count": result["failed_count"],
                "success_rate": round(
                    result["success_count"] / result["total_executions"] * 100, 2
                ),
                "avg_duration_ms": round(result["avg_duration"], 2)
            })
        
        return stats
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """
        清理旧日志
        
        Args:
            days: 保留天数
            
        Returns:
            删除的日志数量
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self._collection.delete_many({
            "created_at": {"$lt": cutoff_date}
        })
        
        deleted_count = result.deleted_count
        
        self._system_logger.info(f"清理旧日志: 删除了{deleted_count}条记录")
        
        return deleted_count
    
    def log_system_event(self, level: str, message: str, **kwargs):
        """
        记录系统事件
        
        Args:
            level: 日志级别 (info/warning/error)
            message: 日志消息
            **kwargs: 额外字段
        """
        log_func = getattr(self._system_logger, level, self._system_logger.info)
        
        if kwargs:
            extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"{message} | {extra_info}"
        
        log_func(message)
    
    def log_operation(self, action: str, target: str, status: str, **kwargs):
        """
        记录操作日志
        
        Args:
            action: 操作类型
            target: 操作目标
            status: 操作状态
            **kwargs: 额外字段
        """
        log_entry = f"{action}: {target} {status}"
        
        if kwargs:
            extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            log_entry = f"{log_entry} | {extra_info}"
        
        self._operation_logger.info(log_entry)
