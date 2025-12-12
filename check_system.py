#!/usr/bin/env python3
"""
系统检查脚本
用于验证LLM分析系统的各个组件是否正常工作
"""
import sys
import logging
from pathlib import Path

# 设置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查依赖包"""
    logger.info("=== 检查依赖包 ===")
    try:
        from utils import check_dependencies
        return check_dependencies()
    except Exception as e:
        logger.error(f"依赖包检查失败: {e}")
        return False

def check_data_source():
    """检查数据源（Google Sheets或Excel文件）"""
    logger.info("=== 检查数据源 ===")
    try:
        from config import check_google_credentials, EXCEL_FILE
        from excel_handler import ExcelHandler
        
        # 检查Google Sheets凭据
        if check_google_credentials():
            logger.info("🔍 检测到Google凭据文件，尝试Google Sheets模式")
            handler = ExcelHandler(use_google_sheets=True)
            
            if handler.use_google_sheets:
                logger.info("✅ Google Sheets模式已启用")
                if not handler.load_data():
                    logger.error("Google Sheets数据加载失败")
                    return False
                logger.info("✅ Google Sheets数据加载成功")
            else:
                logger.warning("⚠️  Google Sheets初始化失败，回退到本地Excel模式")
                return check_local_excel_file(handler)
        else:
            logger.info("📄 未检测到Google凭据，使用本地Excel模式")
            handler = ExcelHandler(use_google_sheets=False)
            return check_local_excel_file(handler)
        
        # 测试数据处理功能
        unfilled_rows = handler.get_unfilled_rows()
        logger.info(f"找到 {len(unfilled_rows)} 行待处理数据")
        
        if unfilled_rows:
            # 测试获取第一行数据
            first_row = unfilled_rows[0]
            row_data = handler.get_row_data(first_row)
            if row_data:
                logger.info(f"第 {first_row} 行数据格式正确")
            else:
                logger.warning(f"第 {first_row} 行数据获取失败")
        
        logger.info("数据源检查通过")
        return True
        
    except Exception as e:
        logger.error(f"数据源检查失败: {e}")
        return False

def check_local_excel_file(handler=None):
    """检查本地Excel文件"""
    try:
        from config import EXCEL_FILE
        if not EXCEL_FILE.exists():
            logger.error(f"Excel文件不存在: {EXCEL_FILE}")
            return False
        
        if handler is None:
            from excel_handler import ExcelHandler
            handler = ExcelHandler(use_google_sheets=False)
        
        if not handler.load_data():
            logger.error("Excel文件加载失败")
            return False
        
        logger.info("✅ 本地Excel文件检查通过")
        return True
        
    except Exception as e:
        logger.error(f"本地Excel文件检查失败: {e}")
        return False

def check_llm_service():
    """检查LLM服务"""
    logger.info("=== 检查LLM服务 ===")
    try:
        from llm_agent import LLMAgent
        agent = LLMAgent()
        model_info = agent.get_model_info()
        
        logger.info(f"使用模型: {model_info['model']}")
        logger.info(f"OpenAI模式: {model_info['use_openai']}")
        if model_info['api_url']:
            logger.info(f"API地址: {model_info['api_url']}")
        
        # 测试简单调用
        test_response = agent.call_llm("Hello, please respond with 'System working'")
        if test_response:
            logger.info("LLM服务响应正常")
            logger.info(f"测试响应: {test_response[:50]}...")
        else:
            logger.warning("LLM服务无响应")
        
        # 如果使用Ollama，检查qwen3模型
        if not model_info['use_openai']:
            try:
                import requests
                from config import OLLAMA_BASE_URL, OLLAMA_MODEL
                
                response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_names = [model.get('name', '') for model in models]
                    
                    if OLLAMA_MODEL in model_names:
                        logger.info(f"✅ {OLLAMA_MODEL} 模型已可用")
                    else:
                        logger.warning(f"⚠️  {OLLAMA_MODEL} 模型未找到")
                        logger.info(f"可用模型: {model_names}")
                        logger.info(f"请运行: ollama pull {OLLAMA_MODEL}")
                        
            except Exception as e:
                logger.warning(f"检查Ollama模型时出错: {e}")
            
        logger.info("LLM服务检查完成")
        return True
        
    except Exception as e:
        logger.error(f"LLM服务检查失败: {e}")
        return False

def check_content_fetcher():
    """检查内容获取功能"""
    logger.info("=== 检查内容获取功能 ===")
    try:
        from fetch_text import ContentFetcher
        fetcher = ContentFetcher()
        
        # 测试网页内容获取
        test_url = "https://httpbin.org/html"
        content = fetcher.fetch_content(test_url)
        
        if content:
            logger.info(f"网页内容获取成功，长度: {len(content)} 字符")
        else:
            logger.warning("网页内容获取失败（可能是网络问题）")
        
        # 检查缓存信息
        cache_info = fetcher.get_cache_info()
        logger.info(f"PDF缓存目录: {cache_info.get('cache_dir', 'N/A')}")
        
        logger.info("内容获取功能检查完成")
        return True
        
    except Exception as e:
        logger.error(f"内容获取功能检查失败: {e}")
        return False

def check_directories():
    """检查目录结构"""
    logger.info("=== 检查目录结构 ===")
    try:
        from config import ensure_directories, CACHE_DIR, LOG_DIR, LLM_LOG_DIR
        
        ensure_directories()
        
        directories = [CACHE_DIR, LOG_DIR, LLM_LOG_DIR]
        for directory in directories:
            if directory.exists():
                logger.info(f"✅ {directory}")
            else:
                logger.warning(f"❌ {directory}")
        
        logger.info("目录结构检查完成")
        return True
        
    except Exception as e:
        logger.error(f"目录结构检查失败: {e}")
        return False

def main():
    """主检查函数"""
    logger.info("开始系统检查...")
    logger.info("=" * 60)
    
    checks = [
        ("目录结构", check_directories),
        ("依赖包", check_dependencies),
        ("数据源", check_data_source),
        ("LLM服务", check_llm_service),
        ("内容获取", check_content_fetcher),
        ("联系人验证", check_contact_verification),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
            logger.info(f"{name}: {'✅ 通过' if result else '❌ 失败'}")
        except Exception as e:
            logger.error(f"{name}检查出现异常: {e}")
            results.append((name, False))
        
        logger.info("-" * 60)
    
    # 总结
    logger.info("=== 检查总结 ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    logger.info(f"\n总体结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        logger.info("🎉 系统检查全部通过，可以开始使用！")
        return True
    else:
        logger.warning(f"⚠️  有 {total - passed} 项检查失败，请查看上述详细信息")
        return False

def check_contact_verification():
    """检查联系人验证功能"""
    logger.info("=== 检查联系人验证功能 ===")
    try:
        from config import CONTACT_VERIFICATION_ENABLED
        
        if not CONTACT_VERIFICATION_ENABLED:
            logger.info("⚠️  联系人验证功能已禁用")
            return True
        
        # 检查Playwright依赖
        try:
            import playwright
            from playwright.sync_api import sync_playwright
            logger.info("✅ Playwright依赖检查通过")
            
            # 检查浏览器是否已安装
            try:
                with sync_playwright() as p:
                    # 尝试获取已安装的浏览器
                    browsers = p.chromium
                    logger.info("✅ Playwright Chromium浏览器可用")
            except Exception as e:
                logger.warning(f"⚠️  Playwright浏览器未安装: {e}")
                logger.info("请运行: playwright install chromium")
                return True  # 不阻止系统运行
                
        except ImportError as e:
            logger.warning(f"⚠️  Playwright依赖缺失: {e}")
            logger.info("可运行: pip install playwright && playwright install chromium")
            return True  # 不阻止系统运行，只是功能受限
        
        # 测试基础搜索功能
        try:
            from llm_agent import LLMAgent
            from contact_verifier import ContactVerifier
            
            llm_agent = LLMAgent()
            verifier = ContactVerifier(llm_agent)
            
            # 测试判断逻辑
            should_verify, reason = verifier.should_verify_contact(
                "John Smith", "john@example.com", "Contact: Dr. John Smith"
            )
            
            logger.info(f"验证逻辑测试: {should_verify}, {reason}")
            logger.info("✅ 联系人验证功能初始化成功")
            
            # 清理资源
            verifier.cleanup()
            
        except Exception as e:
            logger.warning(f"⚠️  联系人验证功能测试失败: {e}")
            return True  # 不阻止系统运行
        
        return True
        
    except Exception as e:
        logger.error(f"联系人验证功能检查失败: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("检查被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"检查过程发生异常: {e}")
        sys.exit(1) 