"""
Raw数据清理任务 - 定时清理过期的原始对话数据
"""

import logging
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class RawDataCleanupTask:
    """定时清理Raw数据任务"""
    
    def __init__(self, db, config_manager):
        """
        初始化清理任务
        
        Args:
            db: MongoDB数据库实例
            config_manager: 配置管理器实例
        """
        self._db = db
        self._config = config_manager
    
    async def cleanup(self):
        """
        执行清理
        
        Returns:
            int: 删除的记录数
        """
        try:
            # 从配置读取保留天数
            retention_days = self._config.get(
                "ai-gateway.log.system.retention.days",
                30
            )
            
            # 计算截止日期
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            logger.info(f"🧹 开始清理Raw数据（保留{retention_days}天，截止日期: {cutoff_date.isoformat()}）")
            
            # 删除过期数据
            result = await self._db["raw_conversation_logs"].delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            
            if deleted_count > 0:
                logger.info(f"🧹 Raw数据清理完成: 删除 {deleted_count} 条记录（保留{retention_days}天）")
            else:
                logger.debug(f"🧹 Raw数据清理完成: 无过期记录需要删除")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Raw数据清理失败: {e}")
            raise
    
    async def get_stats(self):
        """
        获取Raw数据统计
        
        Returns:
            dict: 统计信息
        """
        try:
            total_count = await self._db["raw_conversation_logs"].count_documents({})
            
            retention_days = self._config.get(
                "ai-gateway.log.system.retention.days",
                30
            )
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            expired_count = await self._db["raw_conversation_logs"].count_documents({
                "timestamp": {"$lt": cutoff_date}
            })
            
            # 获取最早的记录时间
            oldest = await self._db["raw_conversation_logs"].find_one(
                sort=[("timestamp", 1)]
            )
            newest = await self._db["raw_conversation_logs"].find_one(
                sort=[("timestamp", -1)]
            )
            
            return {
                "total_records": total_count,
                "expired_records": expired_count,
                "retention_days": retention_days,
                "oldest_record": oldest["timestamp"].isoformat() if oldest else None,
                "newest_record": newest["timestamp"].isoformat() if newest else None
            }
            
        except Exception as e:
            logger.error(f"❌ 获取Raw数据统计失败: {e}")
            raise
