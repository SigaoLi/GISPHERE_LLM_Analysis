"""
项目配置文件
"""
import os
import logging
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 文件路径配置
EXCEL_FILE = PROJECT_ROOT / "text_info.xlsx"  # 保留作为备用
SHEET_NAME = "Unfilled"
OPENAI_KEY_FILE = PROJECT_ROOT / "openai_key.txt"

# Google Sheets 配置
GOOGLE_CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
GOOGLE_TOKEN_FILE = PROJECT_ROOT / "token.pickle"
GOOGLE_SPREADSHEET_ID = '1LcfxcTCuj9ZJXXMxyFQwt-xnbAviNP8j9oDr6OG5-Go'
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# 缓存目录
CACHE_DIR = PROJECT_ROOT / "cache"
PDF_CACHE_DIR = CACHE_DIR / "pdf"
SCREENSHOT_CACHE_DIR = CACHE_DIR / "screenshots"

# 日志配置
LOG_DIR = PROJECT_ROOT / "logs"
LLM_LOG_DIR = PROJECT_ROOT / "llm_logs"
RUN_LOG_FILE = LOG_DIR / "run.log"

# 滚动加载配置
SCROLL_STEP = 500  # 每次滚动的像素数
SCROLL_DELAY = 1000  # 每次滚动后的等待时间（毫秒）
MAX_SCROLLS = 50  # 最大滚动次数
NO_NEW_CONTENT_THRESHOLD = 3  # 连续无新内容次数阈值
SCROLL_BUFFER = 1000  # 页面底部缓冲像素数

# Playwright配置
USE_PLAYWRIGHT = True  # 是否使用Playwright（通过独立进程，无异步冲突）
PLAYWRIGHT_TIMEOUT = 60  # Playwright页面加载超时时间（秒）
PLAYWRIGHT_SCROLL_ENABLED = True  # 是否启用滚动加载

# 智能页面加载配置
USE_SMART_PAGE_LOADER = True  # 是否使用智能页面加载检测
SMART_LOAD_INITIAL_WAIT = 15  # 智能检测前的初始等待时间（秒），给页面足够时间加载
SMART_LOAD_MAX_WAIT = 60  # 智能加载最大等待时间（秒）
SMART_LOAD_STABILITY_INTERVAL = 1.0  # 内容稳定性检查间隔（秒）
SMART_LOAD_STABILITY_THRESHOLD = 3  # 内容稳定性阈值（连续N次无变化）
SMART_LOAD_MIN_CONTENT_LENGTH = 500  # 最小内容长度阈值
SMART_LOAD_MAX_RETRIES = 2  # 加载失败时的最大重试次数

# 截图OCR配置
USE_SCREENSHOT_OCR = True  # 是否启用截图OCR作为fallback
OCR_LANGUAGE = 'eng+chi_sim'  # OCR语言设置 (eng=英文, chi_sim=简体中文)
SCREENSHOT_QUALITY = 100  # 截图质量 (1-100, 注意: PNG格式不使用此参数)
SCREENSHOT_MAX_PAGES = 10  # 长页面最大截图页数
SCREENSHOT_CLEANUP_AFTER_USE = True  # 使用后是否自动清理截图

# LLM 配置
OPENAI_MODEL = "gpt-5-chat-latest"
OPENAI_BASE_URL = "https://oneapi.gisphere.info/v1"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:14b"

# Excel 列名配置
EXCEL_COLUMNS = {
    # 输入列
    'Notes': 'Notes',
    'Source': 'Source',
    
    # 英文分析阶段1字段
    'Deadline': 'Deadline',
    'Number_Places': 'Number_Places',
    'Direction': 'Direction',
    'University_EN': 'University_EN',
    'Contact_Name': 'Contact_Name',
    'Contact_Email': 'Contact_Email',
    
    # 英文分析阶段2字段 - 招生类型
    'Master Student': 'Master Student',
    'Doctoral Student': 'Doctoral Student',
    'PostDoc': 'PostDoc',
    'Research Assistant': 'Research Assistant',
    'Competition': 'Competition',
    'Summer School': 'Summer School',
    'Conference': 'Conference',
    'Workshop': 'Workshop',
    
    # 英文分析阶段2字段 - 专业方向
    'Physical_Geo': 'Physical_Geo',
    'Human_Geo': 'Human_Geo',
    'Urban': 'Urban',
    'GIS': 'GIS',
    'RS': 'RS',
    'GNSS': 'GNSS',
    
    # 中文分析阶段字段
    'University_CN': 'University_CN',
    'Country_CN': 'Country_CN',
    'WX_Label1': 'WX_Label1',
    'WX_Label2': 'WX_Label2',
    'WX_Label3': 'WX_Label3',
    'WX_Label4': 'WX_Label4',
    'WX_Label5': 'WX_Label5',
    
    # 状态列
    'Verifier': 'Verifier',
    'Error': 'Error'
}

# 请求配置
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
PDF_DOWNLOAD_TIMEOUT = 60

# 联系人验证配置
CONTACT_VERIFICATION_ENABLED = True
CONTACT_SEARCH_TIMEOUT = 20
MAX_SEARCH_RESULTS = 10
MAX_PAGES_TO_ANALYZE = 3

# 日志配置
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

def setup_logging():
    """设置日志配置"""
    # 确保日志目录存在
    LOG_DIR.mkdir(exist_ok=True)
    LLM_LOG_DIR.mkdir(exist_ok=True)
    
    # 配置根日志
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(RUN_LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def ensure_directories():
    """确保所有必要目录存在"""
    directories = [CACHE_DIR, PDF_CACHE_DIR, SCREENSHOT_CACHE_DIR, LOG_DIR, LLM_LOG_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def check_openai_key():
    """检查OpenAI API Key是否存在"""
    if OPENAI_KEY_FILE.exists():
        try:
            with open(OPENAI_KEY_FILE, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                return key if key else None
        except Exception:
            return None
    return None

def check_google_credentials():
    """检查Google Sheets凭据文件是否存在"""
    return GOOGLE_CREDENTIALS_FILE.exists() 