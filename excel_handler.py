"""
Excel文件处理模块 - 现已集成Google Sheets支持
"""
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

from config import EXCEL_FILE, SHEET_NAME, EXCEL_COLUMNS, check_google_credentials
from google_sheets_handler import GoogleSheetsHandler

logger = logging.getLogger(__name__)

class ExcelHandler:
    def __init__(self, use_google_sheets=True):
        self.use_google_sheets = use_google_sheets and check_google_credentials()
        self.excel_file = EXCEL_FILE
        self.sheet_name = SHEET_NAME
        self.df = None
        self.original_df = None
        
        # 初始化Google Sheets处理器
        if self.use_google_sheets:
            try:
                self.google_handler = GoogleSheetsHandler()
                logger.info("✅ 使用Google Sheets模式")
            except Exception as e:
                logger.warning(f"Google Sheets初始化失败，回退到本地Excel模式: {e}")
                self.use_google_sheets = False
                self.google_handler = None
        else:
            self.google_handler = None
            logger.info("📄 使用本地Excel模式")
        
    def load_data(self) -> bool:
        """加载数据（Google Sheets或本地Excel）"""
        if self.use_google_sheets and self.google_handler:
            return self._load_google_sheets_data()
        else:
            return self._load_local_excel_data()
    
    def _load_google_sheets_data(self) -> bool:
        """加载Google Sheets数据"""
        try:
            success = self.google_handler.load_data()
            if success:
                self.df = self.google_handler.df
                self.original_df = self.google_handler.original_df
                logger.info("✅ Google Sheets数据加载成功")
            return success
        except Exception as e:
            logger.error(f"Google Sheets数据加载失败: {e}")
            return False
    
    def _load_local_excel_data(self) -> bool:
        """加载本地Excel数据"""
        try:
            if not self.excel_file.exists():
                logger.error(f"Excel文件不存在: {self.excel_file}")
                return False
            
            # 读取Excel文件
            self.df = pd.read_excel(self.excel_file, sheet_name=self.sheet_name)
            self.original_df = self.df.copy()
            
            logger.info(f"成功加载Excel文件: {self.excel_file}")
            logger.info(f"数据行数: {len(self.df)}")
            logger.info(f"数据列数: {len(self.df.columns)}")
            
            # 验证必要列是否存在
            required_columns = ['Notes', 'Source', 'Verifier', 'Error']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            
            if missing_columns:
                logger.error(f"缺少必要列: {missing_columns}")
                return False
            
            # 预设可能需要字符串数据的列类型为object，避免类型不兼容警告
            string_columns = [
                'Deadline', 'Direction', 'University_EN', 'Contact_Name', 'Contact_Email',
                'University_CN', 'Country_CN', 'WX_Label1', 'WX_Label2', 'WX_Label3',
                'WX_Label4', 'WX_Label5', 'Verifier', 'Error', 'Number_Places'
            ]
            
            for col in string_columns:
                if col in self.df.columns:
                    self.df[col] = self.df[col].astype('object')
            
            logger.info("已优化数据类型设置")
            return True
            
        except Exception as e:
            logger.error(f"加载Excel文件失败: {e}")
            return False
    
    def get_unfilled_rows(self) -> List[int]:
        """获取需要处理的行索引（Verifier和Error都为空的行）"""
        if self.use_google_sheets and self.google_handler:
            return self.google_handler.get_unfilled_rows()
        
        if self.df is None:
            logger.error("数据未加载")
            return []
        
        # 筛选Verifier和Error都为空的行
        condition = (
            (self.df['Verifier'].isna() | (self.df['Verifier'] == '')) &
            (self.df['Error'].isna() | (self.df['Error'] == ''))
        )
        
        unfilled_indices = self.df[condition].index.tolist()
        logger.info(f"找到 {len(unfilled_indices)} 行需要处理")
        
        return unfilled_indices
    
    def get_row_data(self, row_index: int) -> Optional[Dict]:
        """获取指定行的数据"""
        if self.use_google_sheets and self.google_handler:
            return self.google_handler.get_row_data(row_index)
        
        if self.df is None or row_index not in self.df.index:
            return None
        
        row_data = self.df.loc[row_index].to_dict()
        
        # 清理NaN值
        for key, value in row_data.items():
            if pd.isna(value):
                row_data[key] = ""
        
        return row_data
    
    def extract_link_from_row(self, row_data: Dict) -> Optional[str]:
        """从行数据中提取链接"""
        if self.use_google_sheets and self.google_handler:
            return self.google_handler.extract_link_from_row(row_data)
        
        from utils import extract_url_from_text, is_valid_url
        
        # 首先尝试从Notes中提取链接
        notes = row_data.get('Notes', '')
        if notes:
            url = extract_url_from_text(notes)
            if url:
                logger.info(f"从Notes中提取到链接: {url}")
                return url
        
        # 如果Notes中没有链接，尝试从Source中获取
        source = row_data.get('Source', '')
        if source and is_valid_url(source):
            logger.info(f"从Source中获取到链接: {source}")
            return source
        
        logger.warning("未找到有效链接")
        return None
    
    def update_row_data(self, row_index: int, update_data: Dict, verifier: str = "LLM") -> bool:
        """更新指定行的数据"""
        if self.use_google_sheets and self.google_handler:
            return self.google_handler.update_row_data(row_index, update_data, verifier)
        
        try:
            if self.df is None or row_index not in self.df.index:
                logger.error(f"无效的行索引: {row_index}")
                return False
            
            # 更新数据
            for column, value in update_data.items():
                if column in self.df.columns:
                    # 处理数据类型兼容性
                    if pd.isna(self.df.loc[row_index, column]) or self.df.loc[row_index, column] == '':
                        # 如果原始值是NaN或空字符串，确保列类型允许字符串
                        if self.df[column].dtype in ['float64', 'int64'] and isinstance(value, str):
                            # 将列转换为object类型以支持字符串
                            self.df[column] = self.df[column].astype('object')
                    
                    self.df.loc[row_index, column] = value
                else:
                    logger.warning(f"列不存在: {column}")
            
            # 设置验证人（只有verifier不为空时才设置）
            if 'Verifier' in self.df.columns and verifier:
                if self.df['Verifier'].dtype in ['float64', 'int64']:
                    self.df['Verifier'] = self.df['Verifier'].astype('object')
                self.df.loc[row_index, 'Verifier'] = verifier
            
            logger.info(f"成功更新行 {row_index} 的数据")
            return True
            
        except Exception as e:
            logger.error(f"更新行数据失败: {e}")
            return False
    
    def update_row_error(self, row_index: int, error_message: str) -> bool:
        """更新指定行的错误信息"""
        if self.use_google_sheets and self.google_handler:
            return self.google_handler.update_row_error(row_index, error_message)
        
        try:
            if self.df is None or row_index not in self.df.index:
                logger.error(f"无效的行索引: {row_index}")
                return False
            
            # 确保Error列可以存储字符串
            if 'Error' in self.df.columns:
                if self.df['Error'].dtype in ['float64', 'int64']:
                    self.df['Error'] = self.df['Error'].astype('object')
                self.df.loc[row_index, 'Error'] = error_message
            
            logger.info(f"更新行 {row_index} 错误信息: {error_message}")
            return True
            
        except Exception as e:
            logger.error(f"更新错误信息失败: {e}")
            return False
    
    def update_row_data_with_error(self, row_index: int, update_data: Dict, error_message: str = "", verifier: str = "") -> bool:
        """
        同时更新行数据和错误信息（用于部分成功的情况）
        
        Args:
            row_index: 行索引
            update_data: 要更新的数据字典
            error_message: 错误信息（如果有）
            verifier: 验证人标识，如果为空字符串则不设置Verifier字段
        """
        if self.use_google_sheets and self.google_handler:
            # 对于Google Sheets，分别调用两个更新方法
            result_success = self.google_handler.update_row_data(row_index, update_data, verifier)
            if error_message:
                error_success = self.google_handler.update_row_error(row_index, error_message)
                return result_success and error_success
            return result_success
        
        try:
            # 先更新结果数据（只有verifier不为空时才设置Verifier字段）
            if not self.update_row_data(row_index, update_data, verifier):
                return False
            
            # 然后更新错误信息（如果有）
            if error_message:
                if not self.update_row_error(row_index, error_message):
                    logger.warning(f"结果数据更新成功，但错误信息更新失败：行 {row_index}")
                    # 即使错误信息更新失败，我们仍然认为整体操作成功
                    # 因为结果数据已经保存了
            
            verifier_status = f"Verifier={'LLM' if verifier else '未设置'}"
            logger.info(f"行 {row_index} 数据更新完成（{verifier_status}{'，含错误信息' if error_message else ''}）")
            return True
            
        except Exception as e:
            logger.error(f"更新行数据和错误信息失败: {e}")
            return False
    
    def save_data(self) -> bool:
        """保存数据（Google Sheets或本地Excel）"""
        if self.use_google_sheets and self.google_handler:
            return self.google_handler.save_data()
        
        return self._save_local_excel_data()
    
    def _save_local_excel_data(self) -> bool:
        """保存数据到本地Excel文件"""
        try:
            if self.df is None:
                logger.error("没有数据需要保存")
                return False
            
            # 方法1：尝试读取现有的所有sheet并保持它们
            try:
                # 读取现有Excel文件的所有sheet
                existing_sheets = {}
                if self.excel_file.exists():
                    with pd.ExcelFile(self.excel_file) as xls:
                        for sheet_name in xls.sheet_names:
                            if sheet_name != self.sheet_name:  # 不读取我们要更新的sheet
                                existing_sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)
                
                # 重新写入文件
                with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                    # 写入更新后的数据
                    self.df.to_excel(writer, sheet_name=self.sheet_name, index=False)
                    
                    # 写入其他现有的sheet
                    for sheet_name, sheet_df in existing_sheets.items():
                        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                logger.info(f"数据已保存到: {self.excel_file}")
                return True
                
            except Exception as e1:
                logger.warning(f"保存方法1失败: {e1}，尝试方法2")
                
                # 方法2：简单覆盖保存
                try:
                    with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                        self.df.to_excel(writer, sheet_name=self.sheet_name, index=False)
                    
                    logger.info(f"数据已保存到: {self.excel_file} (仅{self.sheet_name}工作表)")
                    return True
                    
                except Exception as e2:
                    logger.error(f"保存方法2也失败: {e2}")
                    return False
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        if self.use_google_sheets and self.google_handler:
            return self.google_handler.get_statistics()
        
        if self.df is None:
            return {}
        
        total_rows = len(self.df)
        filled_rows = len(self.df[self.df['Verifier'].notna() & (self.df['Verifier'] != '')])
        error_rows = len(self.df[self.df['Error'].notna() & (self.df['Error'] != '')])
        pending_rows = total_rows - filled_rows - error_rows
        
        stats = {
            'total_rows': total_rows,
            'filled_rows': filled_rows,
            'error_rows': error_rows,
            'pending_rows': pending_rows,
            'completion_rate': filled_rows / total_rows * 100 if total_rows > 0 else 0
        }
        
        return stats
    
    def print_statistics(self):
        """打印统计信息"""
        if self.use_google_sheets and self.google_handler:
            return self.google_handler.print_statistics()
        
        stats = self.get_statistics()
        if not stats:
            logger.info("暂无统计信息")
            return
        
        logger.info("=" * 50)
        logger.info("处理统计信息:")
        logger.info(f"总行数: {stats['total_rows']}")
        logger.info(f"已完成: {stats['filled_rows']}")
        logger.info(f"错误: {stats['error_rows']}")
        logger.info(f"待处理: {stats['pending_rows']}")
        logger.info(f"完成率: {stats['completion_rate']:.1f}%")
        logger.info("=" * 50)

def validate_analysis_result(result: Dict, stage: str) -> bool:
    """验证分析结果的格式"""
    if not isinstance(result, dict):
        logger.error(f"{stage} 分析结果不是字典格式")
        return False
    
    # 定义每个阶段应该包含的字段
    stage_fields = {
        'stage1': ['Deadline', 'Number_Places', 'Direction', 'University_EN', 'Contact_Name', 'Contact_Email'],
        'stage2': ['Master Student', 'Doctoral Student', 'PostDoc', 'Research Assistant', 
                  'Competition', 'Summer School', 'Conference', 'Workshop',
                  'Physical_Geo', 'Human_Geo', 'Urban', 'GIS', 'RS', 'GNSS'],
        'stage3': ['University_CN', 'Country_CN', 'WX_Label1', 'WX_Label2', 'WX_Label3', 'WX_Label4', 'WX_Label5']
    }
    
    expected_fields = stage_fields.get(stage, [])
    
    # 检查必要字段是否存在
    missing_fields = [field for field in expected_fields if field not in result]
    if missing_fields:
        logger.error(f"{stage} 分析结果缺少字段: {missing_fields}")
        return False
    
    logger.info(f"{stage} 分析结果格式验证通过")
    return True 