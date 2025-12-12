"""
浏览器搜索模块 - 使用Playwright处理动态内容
"""
import logging
import time
import asyncio
from typing import Optional, Dict, List
from urllib.parse import quote

from playwright.async_api import async_playwright, Browser, Page
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from config import CONTACT_SEARCH_TIMEOUT, MAX_SEARCH_RESULTS
from utils import is_valid_url, normalize_text

logger = logging.getLogger(__name__)

class BrowserSearcher:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self._setup_playwright()
    
    def _setup_playwright(self):
        """设置Playwright浏览器"""
        try:
            # 检查是否在异步环境中
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    logger.warning("检测到异步环境，Playwright初始化可能失败")
                    raise Exception("AsyncIO loop detected")
            except RuntimeError:
                # 没有运行中的异步循环，可以安全使用同步API
                pass
            
            self.playwright = sync_playwright().start()
            
            # 启动浏览器（使用Chromium）
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # 创建浏览器上下文，模拟真实用户
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            logger.info("✅ Playwright浏览器初始化成功")
            
        except Exception as e:
            logger.error(f"Playwright初始化失败: {e}")
            logger.info("将使用基础HTTP请求作为备选方案")
            self.playwright = None
            self.browser = None
            self.context = None
    
    def search_google(self, query: str) -> List[Dict]:
        """使用Google搜索"""
        if not self.context:
            logger.error("Playwright浏览器未初始化")
            return []
        
        try:
            # 创建新页面
            page = self.context.new_page()
            
            # 设置额外的反检测措施
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                window.chrome = {
                    runtime: {}
                };
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            # 访问Google搜索
            search_url = f"https://www.google.com/search?q={quote(query)}&hl=en"
            logger.info(f"Google搜索: {query}")
            
            page.goto(search_url, wait_until='networkidle', timeout=CONTACT_SEARCH_TIMEOUT * 1000)
            
            # 等待搜索结果加载
            try:
                page.wait_for_selector('div.g', timeout=CONTACT_SEARCH_TIMEOUT * 1000)
            except Exception:
                logger.warning("搜索结果加载超时")
                page.close()
                return []
            
            # 解析搜索结果
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            results = []
            
            for result_div in soup.select('div.g')[:MAX_SEARCH_RESULTS]:
                try:
                    # 提取标题和链接
                    title_elem = result_div.select_one('h3')
                    link_elem = result_div.select_one('a[href^="http"]')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get('href')
                    
                    # 提取摘要
                    snippet_elem = result_div.select_one('.VwiC3b, .s')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    if url and is_valid_url(url):
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'Google'
                        })
                
                except Exception as e:
                    logger.debug(f"解析搜索结果项失败: {e}")
                    continue
            
            page.close()
            logger.info(f"Google搜索获得 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"Google搜索失败: {e}")
            return []
    
    def get_page_content(self, url: str) -> Optional[str]:
        """获取页面内容（带滚动加载）"""
        if not self.context:
            logger.error("Playwright浏览器未初始化")
            return None
        
        try:
            logger.info(f"获取页面内容: {url}")
            page = self.context.new_page()
            
            # 设置页面反检测
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                delete navigator.__proto__.webdriver;
            """)
            
            # 访问页面
            page.goto(url, wait_until='networkidle', timeout=CONTACT_SEARCH_TIMEOUT * 1000)
            
            # 等待页面完全加载
            page.wait_for_timeout(2000)
            
            # 执行滚动加载策略
            logger.info("开始滚动页面以加载所有动态内容...")
            self._scroll_and_load_content(page)
            
            # 获取页面源码
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # 提取主要文本内容
            text = soup.get_text()
            normalized_text = normalize_text(text)
            
            # 限制内容长度
            if len(normalized_text) > 8000:
                normalized_text = normalized_text[:8000] + "..."
            
            page.close()
            logger.info(f"页面内容获取成功，长度: {len(normalized_text)} 字符")
            return normalized_text
            
        except Exception as e:
            logger.warning(f"获取页面内容失败 {url}: {e}")
            return None
    
    def _scroll_and_load_content(self, page):
        """滚动页面以加载所有动态内容"""
        try:
            # 导入配置参数
            try:
                from config import (SCROLL_STEP, SCROLL_DELAY, MAX_SCROLLS, 
                                  NO_NEW_CONTENT_THRESHOLD, SCROLL_BUFFER)
            except ImportError:
                # 如果无法导入配置，使用默认值
                SCROLL_STEP = 500
                SCROLL_DELAY = 1000
                MAX_SCROLLS = 30
                NO_NEW_CONTENT_THRESHOLD = 3
                SCROLL_BUFFER = 1000
            
            # 获取页面高度
            page_height = page.evaluate("document.body.scrollHeight")
            logger.info(f"页面总高度: {page_height}px")
            logger.info(f"滚动参数: 步长={SCROLL_STEP}px, 延迟={SCROLL_DELAY}ms, 最大次数={MAX_SCROLLS}")
            
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
                    logger.info(f"滚动到 {current_position}px，无新内容 ({no_new_content_count}/{NO_NEW_CONTENT_THRESHOLD})")
                
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
            # 即使滚动失败，也继续获取内容
    
    def close(self):
        """关闭浏览器"""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Playwright浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭Playwright浏览器失败: {e}")
    
    def __del__(self):
        """析构函数，确保浏览器被关闭"""
        self.close()
