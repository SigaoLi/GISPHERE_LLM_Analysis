"""
基于LLM的文本智能分析与Excel字段自动填写系统
主入口文件
"""
import os
import socket

# 强制使用IPv4连接（解决macOS等系统上的IPv6连接问题）
_FORCE_IPV4 = os.getenv('FORCE_IPV4', 'true').lower() == 'true'

if _FORCE_IPV4:
    _real_getaddrinfo = socket.getaddrinfo
    def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return _real_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    socket.getaddrinfo = ipv4_only_getaddrinfo

import sys
import logging
from pathlib import Path
from tqdm import tqdm
import time

# 导入项目模块
from config import setup_logging, ensure_directories, GOOGLE_SPREADSHEET_ID, check_google_credentials
from utils import check_dependencies
from excel_handler import ExcelHandler
from fetch_text import ContentFetcher
from analysis_stage import AnalysisStageManager

logger = logging.getLogger(__name__)

class LLMAnalysisSystem:
    def __init__(self):
        self.excel_handler = ExcelHandler()
        self.content_fetcher = ContentFetcher()
        self.analysis_manager = AnalysisStageManager()
        self.processed_count = 0
        self.error_count = 0
        self.success_count = 0
        
    def initialize(self) -> bool:
        """初始化系统"""
        logger.info("=" * 60)
        logger.info("基于LLM的文本智能分析与数据字段自动填写系统")
        logger.info("(支持Google Sheets和本地Excel)")
        logger.info("=" * 60)
        
        # 1. 检查环境和依赖
        logger.info("1. 检查系统环境...")
        if not self._check_environment():
            return False
        
        # 2. 加载Excel数据
        logger.info("2. 加载Excel数据...")
        if not self.excel_handler.load_data():
            logger.error("Excel数据加载失败")
            return False
        
        # 3. 显示模型信息
        model_info = self.analysis_manager.get_model_info()
        logger.info(f"3. LLM模型信息:")
        logger.info(f"   使用OpenAI: {model_info['use_openai']}")
        logger.info(f"   模型: {model_info['model']}")
        if model_info['api_url']:
            logger.info(f"   API地址: {model_info['api_url']}")
        
        # 4. 显示待处理数据统计
        logger.info("4. 数据统计:")
        self.excel_handler.print_statistics()
        
        logger.info("系统初始化完成")
        return True
    
    def _check_environment(self) -> bool:
        """检查环境和依赖"""
        # 确保目录存在
        ensure_directories()
        
        # 检查依赖包
        if not check_dependencies():
            logger.error("依赖包检查失败")
            return False
        
        # 检查数据源
        if check_google_credentials():
            logger.info("🔗 检测到Google凭据，将使用Google Sheets模式")
        else:
            logger.info("📄 将使用本地Excel模式")
            from config import EXCEL_FILE
            if not EXCEL_FILE.exists():
                logger.error(f"Excel文件不存在: {EXCEL_FILE}")
                return False
        
        logger.info("环境检查通过")
        return True
    
    def run(self) -> bool:
        """运行主流程"""
        try:
            # 初始化系统
            if not self.initialize():
                return False
            
            # 获取待处理的行
            unfilled_rows = self.excel_handler.get_unfilled_rows()
            
            if not unfilled_rows:
                logger.info("没有需要处理的行")
                return True
            
            logger.info(f"开始处理 {len(unfilled_rows)} 行数据")
            logger.info("=" * 60)
            
            # 使用进度条处理每一行
            with tqdm(unfilled_rows, desc="处理进度", unit="行") as pbar:
                for row_index in pbar:
                    pbar.set_description(f"处理第 {row_index} 行")
                    
                    success = self._process_single_row(row_index)
                    
                    if success:
                        self.success_count += 1
                        pbar.set_postfix({"成功": self.success_count, "失败": self.error_count})
                    else:
                        self.error_count += 1
                        pbar.set_postfix({"成功": self.success_count, "失败": self.error_count})
                    
                    self.processed_count += 1
                    
                    # 立即保存每行的处理结果
                    self.excel_handler.save_data()
                    logger.info(f"已保存第 {row_index} 行的处理结果")
            
            # 最终保存
            self.excel_handler.save_data()
            
            # 显示最终统计
            self._print_final_statistics()
            
            # 清理资源
            self._cleanup_resources()
            
            logger.info("=" * 60)
            logger.info("处理完成！")
            
            return True
            
        except KeyboardInterrupt:
            logger.warning("用户中断处理")
            self.excel_handler.save_data()
            logger.info("已保存当前进度")
            return False
        except Exception as e:
            logger.error(f"处理过程发生异常: {e}")
            self.excel_handler.save_data()
            self._cleanup_resources()
            return False
    
    def _cleanup_resources(self):
        """清理系统资源"""
        try:
            if hasattr(self, 'analysis_manager') and self.analysis_manager:
                self.analysis_manager.cleanup()
                logger.info("分析管理器资源已清理")
        except Exception as e:
            logger.warning(f"清理资源失败: {e}")
    
    def _process_single_row(self, row_index: int) -> bool:
        """处理单行数据"""
        try:
            logger.info(f"\n开始处理第 {row_index} 行")
            
            # 1. 获取行数据
            row_data = self.excel_handler.get_row_data(row_index)
            if not row_data:
                error_msg = "无法获取行数据"
                logger.error(error_msg)
                self.excel_handler.update_row_error(row_index, error_msg)
                return False
            
            # 2. 提取链接
            url = self.excel_handler.extract_link_from_row(row_data)
            if not url:
                error_msg = "未找到有效链接"
                logger.warning(error_msg)
                self.excel_handler.update_row_error(row_index, error_msg)
                return False
            
            # 3. 获取内容
            logger.info(f"获取内容: {url}")
            content = self.content_fetcher.fetch_content(url)
            if not content:
                error_msg = "内容获取失败"
                logger.error(error_msg)
                self.excel_handler.update_row_error(row_index, error_msg)
                # 如果处理的是PDF文件，删除缓存的PDF文件
                self.content_fetcher.delete_current_pdf()
                return False
            
            logger.info(f"内容获取成功，长度: {len(content)} 字符")
            
            # 4. 分析内容
            logger.info("开始LLM分析...")
            has_results, results, error_msg = self.analysis_manager.analyze_text_complete(content, row_index)
            
            # 处理分析结果
            if has_results:
                # 有结果（完全成功或部分成功）
                logger.info(f"分析获得结果，更新数据...")
                
                # 5. 根据是否有错误决定Verifier字段
                verifier = "LLM" if not error_msg else ""  # 只有完全成功才设置Verifier为LLM
                
                # 同时更新结果和错误信息（如果有）
                update_success = self.excel_handler.update_row_data_with_error(row_index, results, error_msg, verifier)
                if not update_success:
                    final_error_msg = f"结果更新失败{'; ' + error_msg if error_msg else ''}"
                    logger.error("结果更新失败")
                    self.excel_handler.update_row_error(row_index, final_error_msg)
                    # 如果处理的是PDF文件，删除缓存的PDF文件
                    self.content_fetcher.delete_current_pdf()
                    return False
                
                if error_msg:
                    logger.info(f"第 {row_index} 行部分成功（Verifier未设置，Error列记录失败信息）")
                else:
                    logger.info(f"第 {row_index} 行完全成功（Verifier设置为LLM）")
                
            else:
                # 没有任何结果（完全失败）
                logger.error(f"分析完全失败: {error_msg}")
                self.excel_handler.update_row_error(row_index, error_msg)
                # 如果处理的是PDF文件，删除缓存的PDF文件
                self.content_fetcher.delete_current_pdf()
                return False
            
            # 6. 处理成功后，删除缓存的PDF文件
            self.content_fetcher.delete_current_pdf()
            
            return True
            
        except Exception as e:
            error_msg = f"处理异常: {str(e)}"
            logger.error(error_msg)
            self.excel_handler.update_row_error(row_index, error_msg)
            # 如果处理的是PDF文件，删除缓存的PDF文件
            self.content_fetcher.delete_current_pdf()
            # 即使发生异常也尝试保存对话记录（如果有的话）
            try:
                self.analysis_manager.llm_agent.save_conversation_log(row_index)
            except Exception as save_error:
                logger.warning(f"保存对话记录失败: {save_error}")
            return False
    
    def _print_final_statistics(self):
        """打印最终统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("最终处理统计:")
        logger.info(f"总处理行数: {self.processed_count}")
        logger.info(f"成功: {self.success_count}")
        logger.info(f"失败: {self.error_count}")
        
        if self.processed_count > 0:
            success_rate = self.success_count / self.processed_count * 100
            logger.info(f"成功率: {success_rate:.1f}%")
        
        # 显示更新后的数据统计
        logger.info("\n更新后的数据统计:")
        self.excel_handler.print_statistics()
        
        # 显示缓存信息
        cache_info = self.content_fetcher.get_cache_info()
        if cache_info:
            logger.info(f"\nPDF缓存信息:")
            logger.info(f"缓存文件数: {cache_info['file_count']}")
            logger.info(f"缓存大小: {cache_info['total_size_mb']} MB")

def main():
    """主函数"""
    try:
        # 设置日志
        setup_logging()
        
        # 创建系统实例并运行
        system = LLMAnalysisSystem()
        success = system.run()
        
        # 退出码
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        sys.exit(1)

def test_single_row():
    """测试单行处理功能"""
    setup_logging()
    
    try:
        system = LLMAnalysisSystem()
        
        # 初始化
        if not system.initialize():
            logger.error("初始化失败")
            return
        
        # 获取第一个未处理的行进行测试
        unfilled_rows = system.excel_handler.get_unfilled_rows()
        if not unfilled_rows:
            logger.info("没有未处理的行可以测试")
            return
        
        test_row = unfilled_rows[0]
        logger.info(f"测试处理第 {test_row} 行")
        
        success = system._process_single_row(test_row)
        
        if success:
            logger.info("测试成功！")
            system.excel_handler.save_data()
        else:
            logger.error("测试失败")
            
    except Exception as e:
        logger.error(f"测试失败: {e}")

if __name__ == "__main__":
    # 如果传入参数 "test"，则运行测试模式
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_single_row()
    else:
        main() 