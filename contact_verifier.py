"""
联系人验证模块
用于通过浏览器搜索验证和补充联系人信息
"""
import logging
import requests
import time
import re
from typing import Optional, Dict, List, Tuple
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup

from config import (REQUEST_TIMEOUT, MAX_RETRIES, CONTACT_VERIFICATION_ENABLED, 
                     CONTACT_SEARCH_TIMEOUT, MAX_SEARCH_RESULTS, MAX_PAGES_TO_ANALYZE)
from utils import normalize_text, is_valid_url

logger = logging.getLogger(__name__)

class ContactVerifier:
    def __init__(self, llm_agent):
        """
        初始化联系人验证器
        
        Args:
            llm_agent: LLM代理实例，用于分析搜索结果
        """
        self.llm_agent = llm_agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self._cleaned = False  # 添加清理标志
        
        # 尝试初始化Playwright浏览器（可选）
        self.browser_searcher = None
        try:
            from browser_search import BrowserSearcher
            self.browser_searcher = BrowserSearcher()
            logger.info("✅ Playwright浏览器搜索器初始化成功")
        except Exception as e:
            logger.warning(f"Playwright浏览器搜索器初始化失败，将使用基础搜索: {e}")
        
        # 优先级搜索引擎列表
        self.search_engines = [
            {
                'name': 'Google',
                'url': 'https://www.google.com/search',
                'query_param': 'q',
                'result_selector': 'div.g',
                'title_selector': 'h3',
                'link_selector': 'a[href]',
                'snippet_selector': '.VwiC3b'
            }
        ]
        
        # 优先网站类型（按优先级排序）
        self.priority_domains = [
            'scholar.google',
            'researchgate.net',
            'linkedin.com',
            'orcid.org',
            'academia.edu',
            '.edu',  # 教育机构
            '.ac.',  # 学术机构
            '.org'   # 组织机构
        ]
    
    def should_verify_contact(self, contact_name: str, contact_email: str, 
                            original_text: str) -> Tuple[bool, str]:
        """
        判断是否需要进行联系人验证
        
        Args:
            contact_name: 联系人姓名（第一阶段LLM提取的结果）
            contact_email: 联系邮箱
            original_text: 原始文档内容
            
        Returns:
            Tuple[bool, str]: (是否需要验证, 验证原因)
        """
        if not contact_name or contact_name.strip() in ['-', '', 'N/A']:
            return False, "缺失联系人，无需验证"
        
        contact_name = contact_name.strip()
        has_email = contact_email and contact_email.strip() not in ['-', '', 'N/A']
        
        # 优先检查：如果第一阶段LLM已经识别出"Dr."前缀且有邮箱，直接跳过验证
        if contact_name.startswith("Dr. ") and has_email:
            return False, "第一阶段已识别博士学位且有邮箱，无需验证"
        
        # 如果第一阶段已有"Dr."前缀但缺少邮箱，需要搜索邮箱
        if contact_name.startswith("Dr. ") and not has_email:
            return True, "第一阶段已识别博士学位但缺少邮箱，需要搜索邮箱"
        
        # 如果第一阶段没有识别出"Dr."，检查原始文本中是否有学位/职称标识
        # 需要移除可能的前缀来匹配原始文本
        clean_name = self._clean_contact_name(contact_name)
        
        title_patterns = [
            r'\bDr\.?\s+' + re.escape(clean_name),
            r'\bProf\.?\s+' + re.escape(clean_name),
            r'\bProfessor\s+' + re.escape(clean_name),
            r'\bAssistant\s+Professor\s+' + re.escape(clean_name),
            r'\bAssociate\s+Professor\s+' + re.escape(clean_name),
            r'\bDoctor\s+' + re.escape(clean_name),
            clean_name + r'\s*,?\s*Ph\.?D',
            clean_name + r'\s*,?\s*PhD',
            clean_name + r'\s*,?\s*Professor',
        ]
        
        has_clear_title = any(re.search(pattern, original_text, re.IGNORECASE) 
                             for pattern in title_patterns)
        
        if has_clear_title and has_email:
            return False, "原始文本中有明确学位标识且有邮箱，无需验证"
        elif has_clear_title and not has_email:
            return True, "原始文本中有学位标识但缺少邮箱，需要搜索邮箱"
        else:
            return True, "联系人学位信息不明确，需要验证学位和邮箱"
    
    def search_contact_info(self, university_en: str, contact_name: str) -> List[Dict]:
        """
        搜索联系人信息
        
        Args:
            university_en: 英文机构名
            contact_name: 联系人姓名
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not contact_name or not university_en:
            logger.warning("搜索参数不完整")
            return []
        
        # 清理联系人姓名（移除可能的称谓前缀）
        clean_name = self._clean_contact_name(contact_name)
        
        # 构建单一搜索查询：University_EN + Contact_Name
        query = f'"{university_en}" "{clean_name}"'
        logger.info(f"搜索联系人信息: {query}")
        
        all_results = []
        
        # 优先使用Playwright搜索（如果可用）
        if self.browser_searcher:
            try:
                playwright_results = self.browser_searcher.search_google(query)
                all_results.extend(playwright_results)
                logger.info(f"Playwright搜索获得 {len(playwright_results)} 个结果")
            except Exception as e:
                logger.warning(f"Playwright搜索失败: {e}")
        
        # 如果Playwright不可用或结果不足，使用基础搜索
        if len(all_results) < 5:
            for search_engine in self.search_engines:
                try:
                    results = self._search_with_engine(query, search_engine)
                    all_results.extend(results)
                    
                    # 如果获得足够结果就停止
                    if len(all_results) >= 15:
                        break
                        
                except Exception as e:
                    logger.warning(f"搜索引擎 {search_engine['name']} 失败: {e}")
                    continue
        
        # 去重并按优先级排序结果
        unique_results = self._remove_duplicate_results(all_results)
        sorted_results = self._sort_results_by_priority(unique_results)
        logger.info(f"获得 {len(sorted_results)} 个唯一搜索结果")
        
        return sorted_results[:10]  # 限制最多10个结果
    
    def _clean_contact_name(self, contact_name: str) -> str:
        """清理联系人姓名，移除称谓前缀和后缀"""
        if not contact_name:
            return ""
        
        name = contact_name.strip()
        
        # 移除常见称谓前缀
        prefixes = ['Dr.', 'Prof.', 'Professor', 'Assistant Professor', 'Associate Professor', 
                   'Mr.', 'Ms.', 'Miss', 'Mrs.', 'Doctor']
        for prefix in prefixes:
            if name.startswith(prefix + ' '):
                name = name[len(prefix):].strip()
                break
        
        # 移除学位后缀
        suffixes = [', Ph.D.', ', PhD', ', Ph.D', ', Professor', ', Prof.', ', Dr.']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        
        # 移除引号中的昵称 (如 KangJae "Jerry" Lee -> KangJae Lee)
        import re
        name = re.sub(r'\s*"[^"]*"\s*', ' ', name)
        
        # 清理多余空格
        name = ' '.join(name.split())
        
        return name
    
    def _validate_and_format_name(self, contact_name: str, title_prefix: str = "") -> str:
        """
        验证并格式化联系人姓名，确保严格符合规范
        
        Args:
            contact_name: 原始联系人姓名
            title_prefix: 验证后的称谓前缀 (Dr./Mr./Ms.)
            
        Returns:
            str: 格式化后的姓名
        """
        if not contact_name:
            return ""
        
        # 先清理姓名
        clean_name = self._clean_contact_name(contact_name)
        
        if not clean_name:
            return ""
        
        # 验证清理后的姓名是否还包含不规范的格式
        import re
        
        # 移除任何剩余的学位标识
        clean_name = re.sub(r'\b(Ph\.?D\.?|PhD|Doctor|Professor|Prof\.?)\b', '', clean_name, flags=re.IGNORECASE)
        
        # 移除任何括号内容
        clean_name = re.sub(r'\([^)]*\)', '', clean_name)
        
        # 移除任何方括号内容
        clean_name = re.sub(r'\[[^\]]*\]', '', clean_name)
        
        # 清理多余的标点符号和空格
        clean_name = re.sub(r'[,;]', '', clean_name)
        clean_name = ' '.join(clean_name.split())
        
        # 确保只包含字母、空格、点号和连字符
        clean_name = re.sub(r'[^a-zA-Z\s\.\-]', '', clean_name)
        clean_name = ' '.join(clean_name.split())
        
        if not clean_name:
            return ""
        
        # 应用称谓前缀
        if title_prefix == "Dr.":
            return f"Dr. {clean_name}"
        elif title_prefix == "Mr.":
            return f"Mr. {clean_name}"
        elif title_prefix == "Ms.":
            return f"Ms. {clean_name}"
        elif title_prefix == "Mr./Ms.":
            # 性别不确定时不加称谓
            return clean_name
        else:
            return clean_name
    
    def _extract_domain(self, university_name: str) -> str:
        """从大学名称提取可能的域名"""
        if not university_name:
            return ""
        
        # 简单的启发式方法提取域名
        name = university_name.lower()
        if 'university' in name:
            # 尝试构建 .edu 域名
            words = name.replace('university', '').replace('of', '').strip().split()
            if words:
                return f"{words[0]}.edu"
        
        return ""
    
    def _remove_duplicate_results(self, results: List[Dict]) -> List[Dict]:
        """移除重复的搜索结果"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def _determine_gender(self, contact_name: str, analyzed_pages: List[Dict]) -> str:
        """
        尝试判断联系人性别
        
        Args:
            contact_name: 联系人姓名
            analyzed_pages: 分析过的页面内容
            
        Returns:
            str: "male", "female", 或 "unknown"
        """
        # 简单的性别判断逻辑
        name_lower = contact_name.lower()
        
        # 常见男性名字
        male_names = {
            'john', 'michael', 'david', 'james', 'robert', 'william', 'richard', 
            'thomas', 'christopher', 'daniel', 'matthew', 'anthony', 'mark', 
            'donald', 'steven', 'paul', 'andrew', 'joshua', 'kenneth', 'kevin',
            'brian', 'george', 'edward', 'ronald', 'timothy', 'jason', 'jeffrey',
            'ryan', 'jacob', 'gary', 'nicholas', 'eric', 'jonathan', 'stephen'
        }
        
        # 常见女性名字
        female_names = {
            'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 
            'susan', 'jessica', 'sarah', 'karen', 'nancy', 'lisa', 'betty', 
            'helen', 'sandra', 'donna', 'carol', 'ruth', 'sharon', 'michelle',
            'laura', 'sarah', 'kimberly', 'deborah', 'dorothy', 'lisa', 'nancy',
            'karen', 'betty', 'helen', 'sandra', 'donna', 'carol', 'ruth', 'sharon'
        }
        
        # 提取名字（通常是第一个单词）
        first_name = name_lower.split()[0] if name_lower.split() else ""
        
        if first_name in male_names:
            return "male"
        elif first_name in female_names:
            return "female"
        
        # 从页面内容中寻找性别线索
        for page in analyzed_pages:
            content = page.get('content', '').lower()
            if 'he ' in content or 'his ' in content or 'him ' in content:
                return "male"
            elif 'she ' in content or 'her ' in content:
                return "female"
        
        return "unknown"
    
    def _search_with_engine(self, query: str, engine_config: Dict) -> List[Dict]:
        """使用指定搜索引擎进行搜索"""
        try:
            # 构建搜索URL
            params = {engine_config['query_param']: query}
            
            response = self.session.get(
                engine_config['url'], 
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # 解析搜索结果
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            for result_element in soup.select(engine_config['result_selector'])[:15]:
                try:
                    # 提取标题
                    title_elem = result_element.select_one(engine_config['title_selector'])
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # 提取链接
                    link_elem = result_element.select_one(engine_config['link_selector'])
                    if not link_elem:
                        continue
                    
                    url = link_elem.get('href', '')
                    if url.startswith('/url?q='):
                        # Google重定向链接处理
                        url = url.split('/url?q=')[1].split('&')[0]
                    elif url.startswith('/'):
                        # 相对链接转绝对链接
                        url = urljoin(engine_config['url'], url)
                    
                    if not is_valid_url(url):
                        continue
                    
                    # 提取摘要
                    snippet_elem = result_element.select_one(engine_config['snippet_selector'])
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': engine_config['name']
                    })
                    
                except Exception as e:
                    logger.debug(f"解析搜索结果项失败: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"搜索请求失败: {e}")
            return []
    
    def _sort_results_by_priority(self, results: List[Dict]) -> List[Dict]:
        """按优先级对搜索结果排序"""
        def get_priority_score(result):
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            score = 0
            
            # 域名优先级评分
            for i, domain in enumerate(self.priority_domains):
                if domain in url:
                    score += (len(self.priority_domains) - i) * 10
                    break
            
            # 关键词加分
            academic_keywords = ['professor', 'dr.', 'phd', 'faculty', 'researcher', 'scholar']
            for keyword in academic_keywords:
                if keyword in title or keyword in snippet:
                    score += 5
            
            # 个人页面指示器
            personal_indicators = ['homepage', 'profile', 'bio', 'cv', 'resume']
            for indicator in personal_indicators:
                if indicator in url or indicator in title:
                    score += 3
            
            return score
        
        return sorted(results, key=get_priority_score, reverse=True)
    
    def analyze_contact_pages(self, search_results: List[Dict], 
                            contact_name: str) -> Tuple[str, str, str]:
        """
        分析联系人相关页面，获取学位信息和邮箱
        
        Args:
            search_results: 搜索结果列表
            contact_name: 联系人姓名
            
        Returns:
            Tuple[str, str, str]: (称谓前缀, 邮箱地址, 分析说明)
        """
        logger.info(f"开始分析联系人页面，共 {len(search_results)} 个结果")
        
        best_pages = []
        
        # 先用LLM选择最相关的页面
        if len(search_results) > 1:
            selected_urls = self._select_relevant_pages(search_results, contact_name)
        else:
            selected_urls = [result['url'] for result in search_results]
        
        # 分析选中的页面
        for url in selected_urls[:3]:  # 最多分析3个页面
            try:
                page_content = self._fetch_page_content(url)
                if page_content:
                    analysis = self._analyze_page_with_llm(page_content, contact_name)
                    if analysis:
                        best_pages.append({
                            'url': url,
                            'analysis': analysis,
                            'content': page_content[:2000]  # 保留部分内容用于调试
                        })
                        
            except Exception as e:
                logger.warning(f"分析页面失败 {url}: {e}")
                continue
        
        # 综合分析结果
        return self._synthesize_contact_info(best_pages, contact_name)
    
    def _select_relevant_pages(self, search_results: List[Dict], 
                             contact_name: str) -> List[str]:
        """使用LLM选择最相关的页面"""
        if len(search_results) <= 3:
            return [result['url'] for result in search_results]
        
        # 构建搜索结果摘要
        results_summary = []
        for i, result in enumerate(search_results[:10]):
            results_summary.append(f"{i+1}. {result['title']}\n   URL: {result['url']}\n   摘要: {result['snippet']}")
        
        prompt = f"""
Please analyze the following search results and select the web pages most likely to contain detailed information about contact person "{contact_name}".

Search Results:
{chr(10).join(results_summary)}

Please rank by relevance and select the most valuable 1-3 web pages for in-depth analysis. Prioritize:
1. University/institution introduction pages
2. Personal homepage
3. Google Scholar, ResearchGate and other academic platform pages

Please return in JSON format:
{{
    "selected_urls": ["url1", "url2", "url3"],
    "reasoning": "Selection reasoning"
}}
"""
        
        try:
            response = self.llm_agent.call_llm(prompt)
            if response:
                import json
                result = json.loads(response)
                selected_urls = result.get('selected_urls', [])
                logger.info(f"LLM选择页面: {result.get('reasoning', '')}")
                return selected_urls
        except Exception as e:
            logger.warning(f"LLM页面选择失败: {e}")
        
        # 回退方案：返回前3个高优先级结果
        return [result['url'] for result in search_results[:3]]
    
    def _fetch_page_content(self, url: str) -> Optional[str]:
        """获取页面内容（智能选择获取方法）"""
        try:
            # 优先使用Playwright（对于需要JavaScript的页面）
            if self.browser_searcher:
                try:
                    content = self.browser_searcher.get_page_content(url)
                    if content and len(content.strip()) > 100:  # 确保获得了有意义的内容
                        return content
                    else:
                        logger.warning("Playwright获取的内容过短，尝试基础请求")
                except Exception as e:
                    logger.warning(f"Playwright页面获取失败: {e}")
            
            # 回退到基础HTTP请求
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取主要文本内容
            text = soup.get_text()
            normalized_text = normalize_text(text)
            
            # 限制内容长度
            if len(normalized_text) > 5000:
                normalized_text = normalized_text[:5000] + "..."
            
            return normalized_text
            
        except Exception as e:
            logger.warning(f"获取页面内容失败 {url}: {e}")
            return None
    
    def _analyze_page_with_llm(self, page_content: str, contact_name: str) -> Optional[Dict]:
        """使用LLM分析页面内容"""
        prompt = f"""
Please analyze the following web page content and extract relevant information about contact person "{contact_name}".

Web Page Content:
{page_content}

Please carefully search for and extract the following information:
1. Degree information: Does this person have a doctorate degree (PhD/Ph.D.) or professor position?
2. Email address: Any email address related to this person
3. Title: Professor, Dr., Mr., Ms., etc.

Please return in JSON format:
{{
    "has_doctorate": true/false,
    "title_prefix": "Dr./Mr./Ms.",
    "email_address": "found email address or null",
    "gender": "male/female/unknown",
    "confidence": "high/medium/low", 
    "evidence": "specific evidence supporting the judgment"
}}

Important notes:
- Set has_doctorate to true when confirmed PhD degree OR professor position (Assistant Professor, Associate Professor, Professor, etc.)
- If uncertain, choose conservative title (Mr./Ms.)
- Try to determine gender from name, pronouns (he/his/him vs she/her), or other context clues
- Email address must be in valid format
"""
        
        try:
            response = self.llm_agent.call_llm(prompt)
            if response:
                import json
                return json.loads(response)
        except Exception as e:
            logger.warning(f"LLM页面分析失败: {e}")
        
        return None
    
    def _synthesize_contact_info(self, analyzed_pages: List[Dict], 
                                contact_name: str) -> Tuple[str, str, str]:
        """综合分析结果，确定最终的联系人信息"""
        if not analyzed_pages:
            return "Mr./Ms.", "", "未找到相关页面信息"
        
        # 收集所有分析结果
        all_analyses = [page['analysis'] for page in analyzed_pages if page['analysis']]
        
        if not all_analyses:
            return "Mr./Ms.", "", "页面分析失败"
        
        # 统计学位信息
        has_doctorate_count = sum(1 for analysis in all_analyses 
                                if analysis.get('has_doctorate', False))
        
        # 收集邮箱地址
        emails = [analysis.get('email_address') for analysis in all_analyses 
                 if analysis.get('email_address')]
        
        # 收集性别信息
        genders = [analysis.get('gender') for analysis in all_analyses 
                  if analysis.get('gender') and analysis.get('gender') != 'unknown']
        
        # 确定称谓前缀
        if has_doctorate_count > len(all_analyses) / 2:  # 多数认为有博士学位
            title_prefix = "Dr."
        else:
            # 如果没有博士学位，判断性别
            if genders:
                # 使用LLM分析结果中的性别信息
                gender_counts = {}
                for gender in genders:
                    gender_counts[gender] = gender_counts.get(gender, 0) + 1
                
                # 选择出现最多的性别
                most_common_gender = max(gender_counts, key=gender_counts.get)
                
                if most_common_gender == "male":
                    title_prefix = "Mr."
                elif most_common_gender == "female":
                    title_prefix = "Ms."
                else:
                    title_prefix = "Mr./Ms."
            else:
                # 回退到基础性别判断
                gender = self._determine_gender(contact_name, analyzed_pages)
                if gender == "male":
                    title_prefix = "Mr."
                elif gender == "female":
                    title_prefix = "Ms."
                else:
                    title_prefix = "Mr./Ms."
        
        # 选择最可信的邮箱
        best_email = ""
        if emails:
            # 选择第一个有效邮箱（已通过LLM验证）
            best_email = emails[0]
        
        # 生成分析说明
        explanation = f"分析了{len(analyzed_pages)}个页面，"
        if has_doctorate_count > 0:
            explanation += f"{has_doctorate_count}个页面确认有博士学位。"
        else:
            explanation += "未找到明确的博士学位证据。"
        
        if best_email:
            explanation += f"找到邮箱地址：{best_email}"
        else:
            explanation += "未找到有效邮箱地址。"
        
        logger.info(f"联系人验证结果: {title_prefix} {contact_name}, {best_email}")
        return title_prefix, best_email, explanation
    
    def verify_and_update_contact(self, university_en: str, contact_name: str, 
                                contact_email: str, original_text: str) -> Dict:
        """
        完整的联系人验证和更新流程
        
        Args:
            university_en: 英文机构名
            contact_name: 联系人姓名
            contact_email: 当前邮箱地址
            original_text: 原始文档内容
            
        Returns:
            Dict: 更新后的联系人信息
        """
        logger.info(f"开始验证联系人: {contact_name} @ {university_en}")
        
        # 检查是否启用联系人验证
        if not CONTACT_VERIFICATION_ENABLED:
            logger.info("联系人验证功能已禁用")
            return {
                'Contact_Name': contact_name,
                'Contact_Email': contact_email,
                'verification_performed': False,
                'verification_reason': "验证功能已禁用",
                'verification_details': ""
            }
        
        # 判断是否需要验证
        should_verify, reason = self.should_verify_contact(
            contact_name, contact_email, original_text
        )
        
        result = {
            'Contact_Name': contact_name,
            'Contact_Email': contact_email,
            'verification_performed': should_verify,
            'verification_reason': reason,
            'verification_details': ""
        }
        
        if not should_verify:
            logger.info(f"无需验证: {reason}")
            return result
        
        try:
            # 执行搜索
            search_results = self.search_contact_info(university_en, contact_name)
            
            if not search_results:
                result['verification_details'] = "搜索未找到相关结果"
                logger.warning("搜索未找到结果")
                return result
            
            # 分析页面
            title_prefix, found_email, explanation = self.analyze_contact_pages(
                search_results, contact_name
            )
            
            # 更新联系人信息
            # 如果第一阶段已经定义了"Dr."前缀，保留不变
            if contact_name.startswith("Dr. "):
                logger.info(f"联系人已有Dr.前缀，保持不变: {contact_name}")
                # 不修改已有的Dr.前缀
            elif title_prefix:
                # 使用新的验证和格式化函数
                formatted_name = self._validate_and_format_name(contact_name, title_prefix)
                
                if formatted_name and formatted_name != contact_name:
                    result['Contact_Name'] = formatted_name
                    logger.info(f"联系人姓名已格式化: {contact_name} -> {formatted_name}")
            
            # 更新邮箱（如果找到了更好的邮箱或原本没有邮箱）
            if found_email:
                if not contact_email or contact_email.strip() in ['-', '', 'N/A']:
                    result['Contact_Email'] = found_email
                # 如果原本有邮箱，保留原邮箱（除非明确要求替换）
            
            result['verification_details'] = explanation
            logger.info(f"验证完成: {result['Contact_Name']}, {result['Contact_Email']}")
            
        except Exception as e:
            error_msg = f"验证过程出错: {str(e)}"
            result['verification_details'] = error_msg
            logger.error(error_msg)
        
        return result
    
    def cleanup(self):
        """清理资源"""
        # 检查是否已经清理，避免重复清理
        if self._cleaned:
            return
        
        if self.browser_searcher:
            try:
                self.browser_searcher.close()
                logger.info("浏览器资源已清理")
            except Exception as e:
                logger.warning(f"清理浏览器资源失败: {e}")
            finally:
                self.browser_searcher = None
        
        self._cleaned = True  # 标记为已清理
    
    def __del__(self):
        """析构函数，确保资源被清理"""
        self.cleanup()
