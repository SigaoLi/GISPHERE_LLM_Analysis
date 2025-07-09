"""
分析阶段封装模块
"""
import logging
from typing import Dict, Optional, Tuple
from llm_agent import LLMAgent
from excel_handler import validate_analysis_result

logger = logging.getLogger(__name__)

class AnalysisStageManager:
    def __init__(self):
        self.llm_agent = LLMAgent()
        self.current_row_index = None
        
    def analyze_text_complete(self, text: str, row_index: int) -> Tuple[bool, Dict, str]:
        """
        完整的三阶段文本分析
        
        Args:
            text: 待分析的文本内容
            row_index: 当前处理的行索引
            
        Returns:
            Tuple[bool, Dict, str]: (是否成功, 结果字典, 错误信息)
        """
        self.current_row_index = row_index
        logger.info(f"开始对行 {row_index} 进行三阶段分析")
        
        # 重置对话保存标志，确保新的行可以保存对话记录
        self.llm_agent.conversation_saved = False
        
        try:
            # 合并所有分析结果
            final_result = {}
            
            # 阶段1：英文基本信息提取
            success, stage1_result, error = self._execute_stage1(text)
            if not success:
                # 即使失败也保存对话记录
                self.llm_agent.save_conversation_log(row_index)
                return False, {}, f"阶段1失败: {error}"
            final_result.update(stage1_result)
            
            # 阶段2：类型和方向分析
            success, stage2_result, error = self._execute_stage2(text)
            if not success:
                # 即使失败也保存对话记录
                self.llm_agent.save_conversation_log(row_index)
                return False, {}, f"阶段2失败: {error}"
            final_result.update(stage2_result)
            
            # 阶段3：中文字段提取
            success, stage3_result, error = self._execute_stage3(text)
            if not success:
                # 即使失败也保存对话记录
                self.llm_agent.save_conversation_log(row_index)
                return False, {}, f"阶段3失败: {error}"
            final_result.update(stage3_result)
            
            # 后处理：数据格式化和验证
            final_result = self._post_process_results(final_result)
            
            logger.info(f"行 {row_index} 三阶段分析完成")
            
            # 保存对话记录
            self.llm_agent.save_conversation_log(row_index)
            
            return True, final_result, ""
            
        except Exception as e:
            error_msg = f"分析过程发生异常: {str(e)}"
            logger.error(error_msg)
            # 即使发生异常也保存对话记录
            try:
                self.llm_agent.save_conversation_log(row_index)
            except Exception as save_error:
                logger.error(f"保存对话记录失败: {save_error}")
            return False, {}, error_msg
    
    def _execute_stage1(self, text: str) -> Tuple[bool, Dict, str]:
        """执行阶段1分析"""
        logger.info("执行英文分析阶段1")
        
        try:
            # 重置上下文
            self.llm_agent.reset_context()
            
            # 调用LLM分析
            result = self.llm_agent.analyze_text_stage1(text)
            
            if not result:
                return False, {}, "LLM返回空结果"
            
            # 验证结果格式
            if not validate_analysis_result(result, 'stage1'):
                return False, {}, "结果格式验证失败"
            
            logger.info("阶段1分析成功")
            return True, result, ""
            
        except Exception as e:
            error_msg = f"阶段1分析异常: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    def _execute_stage2(self, text: str) -> Tuple[bool, Dict, str]:
        """执行阶段2分析"""
        logger.info("执行英文分析阶段2")
        
        try:
            # 重置上下文
            self.llm_agent.reset_context()
            
            # 调用LLM分析
            result = self.llm_agent.analyze_text_stage2(text)
            
            if not result:
                return False, {}, "LLM返回空结果"
            
            # 验证结果格式
            if not validate_analysis_result(result, 'stage2'):
                return False, {}, "结果格式验证失败"
            
            # 验证专业方向字段数量（最多5个，最少1个）
            geo_fields = ['Physical_Geo', 'Human_Geo', 'Urban', 'GIS', 'RS', 'GNSS']
            marked_fields = [field for field in geo_fields if result.get(field) == "1"]
            
            if len(marked_fields) == 0:
                return False, {}, "未标记任何专业方向，至少需要标记1个专业方向"
            elif len(marked_fields) > 5:
                return False, {}, f"标记了{len(marked_fields)}个专业方向，超过最大限制5个"
            
            logger.info("阶段2分析成功")
            return True, result, ""
            
        except Exception as e:
            error_msg = f"阶段2分析异常: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    def _execute_stage3(self, text: str) -> Tuple[bool, Dict, str]:
        """执行阶段3分析"""
        logger.info("执行中文分析阶段")
        
        try:
            # 重置上下文
            self.llm_agent.reset_context()
            
            # 调用LLM分析
            result = self.llm_agent.analyze_text_stage3(text)
            
            if not result:
                return False, {}, "LLM返回空结果"
            
            # 验证结果格式
            if not validate_analysis_result(result, 'stage3'):
                return False, {}, "结果格式验证失败"
            
            # WX_Label1必须有内容
            if not result.get('WX_Label1') or result['WX_Label1'].strip() == "":
                return False, {}, "WX_Label1为空，必须填写至少一个专业标签"
            
            logger.info("阶段3分析成功")
            return True, result, ""
            
        except Exception as e:
            error_msg = f"阶段3分析异常: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    def _post_process_results(self, results: Dict) -> Dict:
        """后处理分析结果"""
        logger.info("开始后处理分析结果")
        
        # 确保所有字段都存在
        all_fields = [
            'Deadline', 'Number_Places', 'Direction', 'University_EN', 'Contact_Name', 'Contact_Email',
            'Master Student', 'Doctoral Student', 'PostDoc', 'Research Assistant', 
            'Competition', 'Summer School', 'Conference', 'Workshop',
            'Physical_Geo', 'Human_Geo', 'Urban', 'GIS', 'RS', 'GNSS',
            'University_CN', 'Country_CN', 'WX_Label1', 'WX_Label2', 'WX_Label3', 'WX_Label4', 'WX_Label5'
        ]
        
        for field in all_fields:
            if field not in results:
                results[field] = ""
        
        # 数据类型转换和清理
        results = self._clean_and_convert_data(results)
        
        # 业务规则验证和修正
        results = self._apply_business_rules(results)
        
        logger.info("结果后处理完成")
        return results
    
    def _clean_and_convert_data(self, results: Dict) -> Dict:
        """清理和转换数据"""
        # 清理字符串字段
        string_fields = ['Deadline', 'Direction', 'University_EN', 'Contact_Name', 'Contact_Email',
                        'University_CN', 'Country_CN', 'WX_Label1', 'WX_Label2', 'WX_Label3']
        
        for field in string_fields:
            if field in results:
                value = str(results[field]).strip()
                results[field] = value if value else ""
        
        # 处理Number_Places字段
        if 'Number_Places' in results:
            try:
                # 尝试提取数字
                import re
                number_str = str(results['Number_Places']).strip()
                if number_str:
                    # 提取第一个数字
                    match = re.search(r'\d+', number_str)
                    if match:
                        results['Number_Places'] = match.group()
                    else:
                        results['Number_Places'] = ""
                else:
                    results['Number_Places'] = ""
            except:
                results['Number_Places'] = ""
        
        # 确保二进制字段只有"1"或空字符串
        binary_fields = ['Master Student', 'Doctoral Student', 'PostDoc', 'Research Assistant',
                        'Competition', 'Summer School', 'Conference', 'Workshop',
                        'Physical_Geo', 'Human_Geo', 'Urban', 'GIS', 'RS', 'GNSS']
        
        for field in binary_fields:
            if field in results:
                value = str(results[field]).strip()
                results[field] = "1" if value == "1" else ""
        
        return results
    
    def _apply_business_rules(self, results: Dict) -> Dict:
        """应用业务规则"""
        # 规则1：事件类型（Competition, Summer School, Conference, Workshop）不填Number_Places
        event_types = ['Competition', 'Summer School', 'Conference', 'Workshop']
        if any(results.get(event_type) == "1" for event_type in event_types):
            results['Number_Places'] = ""
        
        # 规则2：Deadline格式验证
        deadline = results.get('Deadline', '')
        if deadline and deadline != "Soon":
            import re
            # 简单的日期格式验证
            if not re.match(r'\d{4}-\d{2}-\d{2}', deadline):
                raise ValueError(f"Deadline格式不正确: {deadline}，应为YYYY-MM-DD格式或'Soon'")
        
        # 规则3：联系人信息一致性
        if results.get('Contact_Name') == "-":
            results['Contact_Email'] = "-"
        elif results.get('Contact_Email') == "-" and results.get('Contact_Name') != "-":
            logger.warning("有联系人姓名但无邮箱")
        
        return results
    
    def get_model_info(self) -> Dict:
        """获取当前使用的模型信息"""
        return self.llm_agent.get_model_info()

def test_analysis_stage():
    """测试分析阶段管理器"""
    try:
        manager = AnalysisStageManager()
        
        # 测试文本
        test_text = """
        PhD Position in Remote Sensing and Machine Learning
        University of Cambridge, United Kingdom
        
        We are seeking a highly motivated PhD student to work on satellite-based forest monitoring using deep learning techniques. The project involves developing novel algorithms for analyzing time-series satellite imagery to detect deforestation patterns.
        
        Requirements:
        - Master's degree in Computer Science, Geography, or related field
        - Experience with machine learning and remote sensing
        - Programming skills in Python
        
        Application deadline: April 30, 2024
        Duration: 3.5 years
        Positions available: 1
        
        Contact: Prof. Sarah Johnson
        Email: s.johnson@cam.ac.uk
        """
        
        logger.info("测试完整分析流程...")
        
        success, results, error = manager.analyze_text_complete(test_text, 1)
        
        if success:
            logger.info("分析成功！")
            for key, value in results.items():
                logger.info(f"{key}: {value}")
        else:
            logger.error(f"分析失败: {error}")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    test_analysis_stage() 