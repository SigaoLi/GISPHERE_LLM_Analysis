#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright独立进程工作器 - 完全避免异步冲突
通过独立进程运行Playwright，与主进程完全隔离
"""
import sys
import json
import logging
from typing import Optional
import io

# 强制 stdout 使用 UTF-8 编码，避免 Windows 上的 GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置日志 - 降低日志级别，避免在 Windows 上出现编码问题
# 只在严重错误时输出到 stderr，普通日志不输出（避免干扰 stdout 的 JSON 输出）
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_playwright_task(url: str, scroll_enabled: bool = True) -> dict:
    """
    在独立进程中运行Playwright任务
    
    Args:
        url: 要访问的URL
        scroll_enabled: 是否启用滚动加载
        
    Returns:
        dict: {'success': bool, 'content': str, 'error': str}
    """
    try:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        
        logger.info(f"Playwright Worker: 开始处理 {url}")
        
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            # 创建浏览器上下文
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                java_script_enabled=True
            )
            
            # 创建新页面
            page = context.new_page()
            
            # 设置页面反检测
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                delete navigator.__proto__.webdriver;
                
                // 覆盖plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // 覆盖languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            # 访问页面
            logger.info(f"正在访问页面: {url}")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 等待页面完全加载
            page.wait_for_timeout(3000)
            
            # 执行滚动加载
            if scroll_enabled:
                logger.info("开始滚动加载...")
                scroll_and_load(page)
            
            # 获取页面源码
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # 提取主要文本内容
            text = soup.get_text()
            
            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # 关闭浏览器
            browser.close()
            
            logger.info(f"内容获取成功，长度: {len(text)} 字符")
            
            return {
                'success': True,
                'content': text,
                'error': None,
                'length': len(text)
            }
            
    except Exception as e:
        error_msg = f"Playwright处理失败: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'content': None,
            'error': error_msg,
            'length': 0
        }

def scroll_and_load(page):
    """滚动页面以加载所有动态内容"""
    try:
        # 滚动参数
        SCROLL_STEP = 500
        SCROLL_DELAY = 1000
        MAX_SCROLLS = 50
        NO_NEW_CONTENT_THRESHOLD = 3
        SCROLL_BUFFER = 1000
        
        # 获取页面高度
        page_height = page.evaluate("document.body.scrollHeight")
        logger.info(f"页面总高度: {page_height}px")
        
        current_position = 0
        scroll_count = 0
        no_new_content_count = 0
        last_height = page_height
        
        while scroll_count < MAX_SCROLLS:
            # 滚动到下一个位置
            current_position += SCROLL_STEP
            page.evaluate(f"window.scrollTo(0, {current_position})")
            
            # 等待内容加载
            page.wait_for_timeout(SCROLL_DELAY)
            
            # 检查是否有新内容加载
            new_height = page.evaluate("document.body.scrollHeight")
            
            if new_height > last_height:
                logger.info(f"滚动到 {current_position}px，发现新内容 (高度: {last_height} -> {new_height})")
                last_height = new_height
                no_new_content_count = 0
            else:
                no_new_content_count += 1
            
            # 如果连续几次没有新内容，停止滚动
            if no_new_content_count >= NO_NEW_CONTENT_THRESHOLD:
                logger.info("连续多次无新内容，停止滚动")
                break
            
            # 如果已经滚动到页面底部
            if current_position >= new_height - SCROLL_BUFFER:
                logger.info("已滚动到页面底部")
                break
            
            scroll_count += 1
        
        # 滚动回顶部
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
        
        logger.info(f"滚动完成，共滚动 {scroll_count} 次，最终页面高度: {last_height}px")
        
    except Exception as e:
        logger.warning(f"滚动加载过程中出错: {e}")

if __name__ == "__main__":
    # 从命令行参数获取URL
    if len(sys.argv) < 2:
        result = {
            'success': False,
            'content': None,
            'error': 'No URL provided',
            'length': 0
        }
    else:
        url = sys.argv[1]
        scroll_enabled = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else True
        result = run_playwright_task(url, scroll_enabled)
    
    # 输出JSON结果
    print(json.dumps(result, ensure_ascii=False))

