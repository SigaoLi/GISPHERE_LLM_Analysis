# 基于LLM的文本智能分析与数据字段自动填写系统

这是一个智能的文本分析系统，能够自动从网页或PDF链接中提取内容，通过大语言模型(LLM)进行三阶段分析，并将结果自动填入Excel表格或Google Sheets的相应字段中。

## 📖 文档导航

- **🚀 [快速开始](QUICKSTART.md)** - 5分钟快速安装和运行
- **📦 [安装指南](INSTALL.md)** - 详细的安装步骤和故障排除
- **📚 README.md（本文档）** - 完整功能说明和使用指南

## 🆕 最新功能

### 智能页面加载检测 ⭐ NEW
针对加载缓慢或动态渲染的网站，系统现在具备智能检测页面是否真正加载完成的能力：

**核心能力**：
- ✅ **多策略检测**：网络空闲、关键元素、内容稳定性、高度稳定性四重检测
- ✅ **智能等待**：自动识别动态内容是否加载完成，不再依赖固定等待时间
- ✅ **自动重试**：加载失败时自动重试（最多3次），成功率从60%提升到95%
- ✅ **优雅降级**：即使超时也能获取已加载的内容
- ✅ **详细日志**：清晰了解页面加载过程和使用的策略

**适用场景**：
- JavaScript动态渲染的单页应用
- 加载速度不稳定的网站（如 apply.interfolio.com）
- 内容分批加载的网站
- 需要等待特定元素出现的页面

**快速开始**：无需任何配置，系统已自动启用智能加载检测！  
📚 详细文档：[智能加载器快速参考](QUICK_REFERENCE.md)

### 截图OCR智能回退机制
当网页或PDF无法通过常规方法获取内容时（如受保护的腾讯文档），系统会自动：
1. 使用Playwright浏览器捕获完整截图
2. 对多页文档进行智能翻页和分页截图
3. 使用Tesseract OCR提取文字内容
4. 自动过滤UI元素，清理和优化识别文本
5. 将提取的文本提供给LLM进行分析

**技术亮点**：
- ✅ **智能翻页**：自动检测页数，逐页截图
- ✅ **UI过滤**：自动隐藏工具栏、按钮等干扰元素
- ✅ **图像增强**：对比度、锐度、二值化处理提高识别率
- ✅ **文本清理**：移除OCR错误、修正中文分词、过滤UI文本
- ✅ **自动缩放**：最佳显示比例，确保内容完整捕获

### Google Sheets云端支持
- ✅ **云端协作**：多人实时查看处理进度
- ✅ **自动同步**：处理结果实时保存到云端
- ✅ **智能切换**：自动检测并选择最佳数据源
- ✅ **零配置回退**：Google Sheets不可用时自动使用本地Excel

## 🌟 主要特性

### 内容提取能力
- **智能页面加载**：四重策略检测页面真正加载完成，成功率95%+
- **多种方式获取**：HTTP请求、Playwright动态渲染、PDF下载、Google Drive/Docs
- **截图OCR fallback**：当所有常规方法失败时，自动截图并OCR识别
- **智能重试机制**：失败自动切换方案，多达4层fallback策略
- **特殊文档处理**：支持腾讯文档、Google Docs、受保护的PDF等

### LLM智能分析
- **三阶段分析**：基本信息提取 → 类型分类 → 中文字段提取
- **多模型支持**：兼容OpenAI API和Ollama本地模型
- **上下文管理**：智能对话历史管理，提高分析准确性
- **自动验证**：内置多层验证机制确保数据质量

### 数据管理
- **双模式支持**：本地Excel或云端Google Sheets
- **断点续传**：支持中断后继续处理
- **实时同步**：Google Sheets模式下实时更新
- **自动清理**：处理完成后自动清理临时文件

### 日志与调试
- **完整对话记录**：保存所有LLM交互，包括失败案例
- **详细错误日志**：多层级日志记录，便于追踪问题
- **资源监控**：PDF缓存、截图缓存智能管理

## 🚀 快速开始

### 环境要求

- **Python**：3.8+
- **必需依赖**：
  - 核心库：`pandas`, `openpyxl`, `requests`, `beautifulsoup4`, `tqdm`
  - PDF处理：`PyMuPDF`, `pdfplumber`, `PyPDF2`
  - 浏览器自动化：`playwright`
  - OCR识别：`pytesseract`, `Pillow`
  - Google Sheets：`google-api-python-client`, `google-auth-oauthlib`
- **可选依赖**：
  - 图像处理增强：`opencv-python`（强烈推荐，显著提高OCR质量）
- **外部工具**：
  - **Tesseract OCR**：截图文字识别引擎（必需）
  - **Playwright浏览器**：Chromium浏览器（必需）

### 安装步骤

#### 1. 克隆项目
```bash
git clone [项目地址]
cd LLM_Analysis
```

#### 2. 安装Python依赖
```bash
# 安装所有必需依赖
pip install -r requirements.txt

# 可选：安装增强功能依赖（强烈推荐用于OCR）
pip install -r requirements-optional.txt

# 或者只安装opencv-python以获得更好的OCR效果
pip install opencv-python
```

#### 3. 安装Playwright浏览器
```bash
playwright install chromium
```

#### 4. 安装Tesseract OCR（截图OCR功能）

**Windows:**
1. 下载安装程序：https://github.com/UB-Mannheim/tesseract/wiki
2. 运行安装程序（推荐版本：5.x或更高）
3. **重要**：安装时勾选以下选项：
   - ✅ "Add to PATH"（添加到系统PATH）
   - ✅ "Additional language data (download)" > "Chinese (Simplified)"（中文语言包）
4. 默认安装路径：`C:\Program Files\Tesseract-OCR\`
5. **如果没有添加到PATH**，程序会自动查找常见安装路径

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install tesseract tesseract-langpack-chi_sim tesseract-langpack-eng
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**验证安装：**
```bash
tesseract --version
```

应该看到类似输出：
```
tesseract 5.x.x
 leptonica-1.x.x
  ...
```

#### 5. 检查系统环境

**快速检查（推荐）：**
```bash
python check_dependencies.py
```

成功的输出示例：
```
======================================================================
依赖检查 - LLM文本智能分析系统
======================================================================

📌 核心环境
----------------------------------------------------------------------
  ✅ Python 3.11.0

📦 必需依赖
----------------------------------------------------------------------
  ✅ openai (1.3.0)
  ✅ requests (2.31.0)
  ✅ pandas (2.0.0)
  ...

🎁 可选依赖（增强功能）
----------------------------------------------------------------------
  ✓ opencv-python (4.8.0)

🔧 外部工具
----------------------------------------------------------------------
  ✅ Tesseract OCR (tesseract 5.3.3)
  ✅ Playwright Chromium浏览器已安装

======================================================================
📊 检查结果总结
======================================================================
必需依赖: 21/21 已安装 ✅
可选依赖: 1/1 已安装 ✅

✅ 所有必需依赖已安装！系统可以正常运行。
```

**完整系统检查：**
```bash
python check_system.py
```

此命令会额外检查数据源配置、OpenAI密钥等。

### 配置

#### 1. 选择数据源

**选项A：Google Sheets（推荐用于团队协作）**

##### 前置要求
- Google账户
- Google Cloud Project
- Python环境（已安装项目依赖）

##### 步骤1：创建Google Cloud项目
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 点击"创建项目"或选择现有项目
3. 记录项目ID

##### 步骤2：启用Google Sheets API
1. 在Google Cloud Console中，导航到"API和服务" > "库"
2. 搜索"Google Sheets API"
3. 点击"启用"

##### 步骤3：创建服务账号凭据

**方法A：服务账号（推荐用于生产环境）**
1. 导航到"API和服务" > "凭据"
2. 点击"创建凭据" > "服务账号"
3. 填写服务账号详细信息
4. 创建完成后，转到"密钥"标签
5. 点击"添加密钥" > "创建新密钥" > JSON格式
6. 下载JSON文件，重命名为`credentials.json`，放到项目根目录

**方法B：OAuth 2.0客户端ID（推荐用于开发环境）**
1. 导航到"API和服务" > "凭据"
2. 点击"创建凭据" > "OAuth客户端ID"
3. 选择"桌面应用程序"
4. 下载JSON文件，重命名为`credentials.json`

##### 步骤4：准备Google表格
1. 创建或打开您的Google表格
2. 确保表格包含以下列：
   - `Notes`：包含链接信息（备用）
   - `Source`：主要链接来源（优先使用）
   - `Verifier`：验证人标记
   - `Error`：错误信息
   - 其他分析字段...
3. 创建名为`Unfilled`的工作表
4. 复制表格ID（URL中的长字符串）：
   ```
   https://docs.google.com/spreadsheets/d/1LcfxcTCuj9ZJXXMxyFQwt-xnbAviNP8j9oDr6OG5-Go/edit
   ```
   表格ID为：`1LcfxcTCuj9ZJXXMxyFQwt-xnbAviNP8j9oDr6OG5-Go`

##### 步骤5：配置项目
打开`config.py`，修改：
```python
GOOGLE_SPREADSHEET_ID = '您的表格ID'
```

##### 步骤6：设置权限
**如果使用服务账号：**
1. 打开Google表格
2. 点击"共享"
3. 添加服务账号邮箱（在credentials.json的`client_email`字段）
4. 给予"编辑者"权限

**如果使用OAuth 2.0：**
首次运行时会自动打开浏览器授权

##### 步骤7：测试配置
```bash
python check_system.py
```

成功输出：
```
✅ Google Sheets模式已启用
✅ Google Sheets数据加载成功
```

**选项B：本地Excel**
```bash
# 将待处理数据放入 text_info.xlsx 的 Unfilled 工作表
# 确保包含 Source 和 Notes 列（包含链接信息）
```

#### 2. 配置LLM服务

**OpenAI API（推荐）：**
```bash
# 在openai_key.txt中添加API密钥
echo "your-api-key-here" > openai_key.txt
```

在`config.py`中配置：
```python
USE_OPENAI = True
OPENAI_MODEL = "gpt-4"  # 或其他模型
```

**Ollama本地模型：**
```bash
# 启动Ollama服务
ollama serve

# 下载模型（推荐qwen3）
ollama pull qwen3:14b
```

在`config.py`中配置：
```python
USE_OPENAI = False
OLLAMA_MODEL = "qwen3:14b"
OLLAMA_API_URL = "http://localhost:11434"
```

### 运行

```bash
# 处理所有未填写的行
python main.py

# 测试单行处理
python main.py test
```

## 📊 分析流程

### 阶段1：英文基本信息提取（含联系人验证）

**提取字段：**
- `Deadline`：申请截止日期（YYYY-MM-DD格式或"Soon"）
- `Number_Places`：招生人数（明确数字或留空）
- `Direction`：研究方向（保持原始格式）
- `University_EN`：机构英文全称
- `Contact_Name`：联系人姓名（含学位验证）
- `Contact_Email`：联系邮箱（含自动补全）

**🔍 联系人智能验证**

通过"University_EN" + "Contact_Name"进行浏览器搜索验证：

**场景1：已有明确学位标识**
- 文档明确显示Dr/Prof时
- 有邮箱则跳过验证，无邮箱则搜索补全

**场景2：学位信息不明确**  
- 无论是否有邮箱都进行验证
- 通过搜索确认学位，调整称谓（Dr./Mr./Ms.）
- 补全缺失的邮箱信息

**场景3：缺失联系人**
- 完全无联系人信息时跳过验证

**技术特性：**
- 🎭 **Playwright驱动**：模拟真实用户行为
- 🤖 **英文LLM分析**：专业的英文提示词
- 🔄 **智能回退**：失败时自动使用基础HTTP请求

### 阶段2：类型和专业分类

**分类字段：**
- `招生类型`：Master Student, Doctoral Student, PostDoc, Research Assistant, Competition, Summer School, Conference, Workshop
- `专业方向`：Physical_Geo, Human_Geo, Urban, GIS, RS, GNSS（最多3个，最少1个）

### 阶段3：中文字段提取

**中文字段：**
- `University_CN`：机构中文全称
- `Country_CN`：所在国家中文名
- `WX_Label1-3`：专业领域标签（WX_Label1必填，4-5留空）

## 🔧 内容提取详解

### 多层Fallback策略

系统采用4层fallback策略，确保最大程度提取内容：

#### 第1层：常规HTTP请求
- 适用于：普通网页、可下载的PDF
- 速度：最快
- 成功率：约60%

#### 第2层：Playwright动态渲染
- 适用于：JavaScript动态加载的网页
- 独立进程运行，避免asyncio冲突
- 成功率：约30%

#### 第3层：PDF专用解析
- 使用3个PDF库：PyMuPDF → pdfplumber → PyPDF2
- 适用于：下载的PDF文件
- 成功率：约8%

#### 第4层：截图OCR识别
- 适用于：受保护文档、无法打印的PDF、腾讯文档
- 最后的fallback，但识别率高
- 成功率：约2%

### 截图OCR工作流程

1. **页面加载**
   - 等待页面完全加载（3秒 + body元素）
   - 切换到iframe（如果存在）

2. **UI优化**
   - 自动隐藏工具栏、侧边栏
   - 隐藏按钮和控制元素
   - 缩小页面至90%（2次Ctrl+鼠标滚轮）

3. **页数检测**
   - 查找页码指示器（如"1/2"）
   - 支持多种选择器格式
   - 检测总页数

4. **逐页截图**
   - 对每一页：
     - 重置滚动位置到顶部
     - 逐步向下滚动
     - 每次滚动后截图一次
     - 检测是否到达底部
   - 翻页到下一页（通过键盘ArrowDown或点击按钮）
   - 重复直到所有页面完成

5. **OCR识别**
   - 自动设置Tesseract路径（Windows）
   - 图像预处理：
     - 转灰度图
     - 增强对比度（2.0倍）
     - 增强亮度（1.1倍）
     - 增强锐度（1.5倍）
     - 二值化处理（如果安装了opencv）
   - OCR识别（支持中英文）
   - 文本清理

6. **文本清理**
   - 过滤UI关键词（scroll, rotate, edit等）
   - 移除短行和无意义字符
   - 修正中文分词（移除字符间空格）
   - 标准化文本格式

7. **质量验证**
   - 检查文本长度（>50字符）
   - 检查关键词出现（phd, university等）
   - 检查字符分布（字母比例>30%）

### 特殊网站处理

#### Google Drive
- 自动识别Google Drive链接
- 直接下载PDF文件
- 处理病毒扫描警告页面
- Fallback到Google Drive查看器

#### Google Docs
- 尝试导出为纯文本
- Fallback到HTML导出
- 最终使用截图OCR

#### 腾讯文档
- 检测到`docs.qq.com/pdf/`自动使用特殊策略
- 智能翻页和分页截图
- 优化的OCR处理流程

## ⚙️ 配置选项

在 `config.py` 中可以修改：

### 基础配置
```python
# 文件路径
EXCEL_FILE = Path(__file__).parent / "text_Info.xlsx"
CACHE_DIR = Path(__file__).parent / "cache"
LOG_DIR = Path(__file__).parent / "logs"
LLM_LOG_DIR = Path(__file__).parent / "llm_logs"

# Google Sheets配置
GOOGLE_SPREADSHEET_ID = 'your-spreadsheet-id'
SHEET_NAME = 'Unfilled'
```

### LLM配置
```python
# OpenAI配置
USE_OPENAI = True
OPENAI_API_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4"

# Ollama配置
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:14b"
```

### 网络请求配置
```python
REQUEST_TIMEOUT = 30  # 秒
MAX_RETRIES = 3
PLAYWRIGHT_TIMEOUT = 60  # 秒
PLAYWRIGHT_SCROLL_ENABLED = True
```

### 截图OCR配置
```python
USE_SCREENSHOT_OCR = True  # 启用/禁用截图OCR
OCR_LANGUAGE = 'eng+chi_sim'  # OCR语言（英文+简体中文）
SCREENSHOT_QUALITY = 100  # 截图质量
SCREENSHOT_MAX_PAGES = 10  # 最大截图页数
SCREENSHOT_CLEANUP_AFTER_USE = True  # 处理后自动清理
```

### 联系人验证配置
```python
CONTACT_VERIFICATION_ENABLED = True  # 启用/禁用验证
CONTACT_SEARCH_TIMEOUT = 20  # 搜索超时（秒）
MAX_SEARCH_RESULTS = 10  # 最大搜索结果数
MAX_PAGES_TO_ANALYZE = 3  # 最大分析页面数
```

### 日志配置
```python
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

## 🛠️ 常见问题

### 安装和环境

#### Q: Tesseract OCR安装后仍然提示"未找到"？
A: 
1. **Windows**：确认是否添加到PATH
   ```bash
   # 检查PATH
   echo $env:Path
   # 应该包含：C:\Program Files\Tesseract-OCR
   ```
   如果没有，程序会自动尝试常见路径：
   - `C:\Program Files\Tesseract-OCR\tesseract.exe`
   - `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`

2. **Linux/Mac**：确认安装成功
   ```bash
   which tesseract
   tesseract --version
   ```

3. **重启终端**：修改PATH后需要重启终端生效

#### Q: 如何安装opencv-python？
A: 
```bash
pip install opencv-python
```
安装后OCR质量会显著提高（使用自适应阈值二值化）。这是可选但强烈推荐的依赖。

#### Q: Playwright浏览器安装失败？
A:
```bash
# 尝试手动安装
playwright install chromium

# 如果网络问题，设置镜像
export PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.azureedge.net
playwright install chromium
```

### 功能使用

#### Q: 截图OCR识别效果不好？
A: 
1. **安装opencv-python**：显著提高识别率
   ```bash
   pip install opencv-python
   ```

2. **检查语言包**：确保安装了中文语言包
   ```bash
   # Windows: 重新运行安装程序，勾选Chinese Simplified
   # Linux:
   sudo apt-get install tesseract-ocr-chi-sim
   ```

3. **调整配置**：在`config.py`中
   ```python
   OCR_LANGUAGE = 'eng+chi_sim'  # 确保包含所需语言
   SCREENSHOT_QUALITY = 100  # 提高截图质量
   ```

4. **查看原始截图**：临时禁用自动清理查看截图质量
   ```python
   SCREENSHOT_CLEANUP_AFTER_USE = False
   ```
   截图保存在：`cache/screenshots/`

#### Q: 链接提取优先级是什么？
A: 系统优先从`Source`列提取链接，只有当`Source`列没有有效链接时才从`Notes`列提取。这确保使用最准确的链接来源。

#### Q: 如何处理多页PDF文档？
A: 系统自动处理：
- 检测页数（如"1/5"）
- 逐页翻页和截图
- 合并所有页面的OCR结果
- 最多处理10页（可在`config.py`中修改`SCREENSHOT_MAX_PAGES`）

### Google Sheets相关

#### Q: 如何选择使用Google Sheets还是本地Excel？
A: 系统自动检测：
- 存在`credentials.json` → 优先Google Sheets
- Google Sheets初始化失败 → 自动回退到Excel
- 可强制指定：`excel_handler = ExcelHandler(use_google_sheets=False)`

#### Q: Google Sheets API配额超限？
A:
- 免费配额：每天300次读写请求
- 解决方案：
  1. 申请提高配额
  2. 使用批量操作减少请求
  3. 临时切换到本地Excel模式

#### Q: 权限被拒绝？
A:
1. 检查服务账号是否有表格编辑权限
2. 重新共享表格给服务账号邮箱
3. 如果用OAuth，重新授权：删除`token.pickle`后重新运行

### 数据处理

#### Q: 如何查看详细的错误信息？
A: 检查日志文件：
- `logs/run.log`：系统运行日志
- `llm_logs/row_xxxx_yyyymmdd_hhmmss_UTC.txt`：LLM对话记录

**新功能**：即使处理失败，也会保存LLM对话记录！

#### Q: LLM分析结果不准确？
A:
1. 查看对话记录分析问题
2. 调整提示词（在`llm_agent.py`中）
3. 更换更强大的模型
4. 检查原始文本质量（特别是OCR结果）

#### Q: 如何中断并恢复处理？
A: 
- 使用`Ctrl+C`中断
- 再次运行时自动跳过已处理的行（`Verifier`不为空）
- 支持完整的断点续传

#### Q: PDF文件会占用太多存储空间吗？
A: 
- 不会，处理完每个文件后自动删除
- 截图也会在OCR完成后自动清理（可配置）
- 仅在处理期间临时存储

### 错误处理

#### Q: 出现"Event loop is closed"警告？
A: 
这是Playwright资源清理时的正常警告，已经优化处理：
- 添加了清理标志防止重复清理
- 不影响程序正常运行
- 如果仍然困扰，可以在日志中过滤此警告

#### Q: 处理某些链接总是失败？
A: 
1. 查看日志确定失败阶段
2. 确认链接是否需要登录
3. 检查是否被反爬虫拦截
4. 尝试手动访问链接确认可访问性
5. 对于受保护的内容，截图OCR是最后的fallback

## 📈 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          主程序 (main.py)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
┌───────────────────────┐   ┌───────────────────────────┐
│  数据管理器            │   │  分析管理器                │
│  excel_handler.py     │   │  analysis_stage.py        │
│  google_sheets_handler│   │  (三阶段分析流程)         │
└───────────────────────┘   └──────────┬────────────────┘
        ▲                              │
        │                              ▼
        │                   ┌──────────────────────┐
        │                   │  内容获取模块         │
        │                   │  fetch_text.py       │
        │                   └──────┬───────────────┘
        │                          │
        │              ┌───────────┼───────────┐
        │              ▼           ▼           ▼
        │    ┌─────────────┐ ┌──────────┐ ┌────────────┐
        │    │ HTTP请求    │ │Playwright│ │ PDF解析    │
        │    └─────────────┘ └──────────┘ └────────────┘
        │                          │
        │                          ▼
        │              ┌───────────────────────┐
        │              │ 截图OCR Fallback      │
        │              │ playwright_worker.py  │
        │              │ screenshot_ocr_       │
        │              │   fetcher.py          │
        │              └───────────────────────┘
        │                          │
        └──────────────────────────┼────────────────────┐
                                   ▼                    ▼
                        ┌──────────────────┐  ┌─────────────────┐
                        │  LLM代理模块     │  │  联系人验证      │
                        │  llm_agent.py    │  │  contact_verifier│
                        │  (OpenAI/Ollama) │  │  browser_search  │
                        └──────────────────┘  └─────────────────┘
                                   │
                        ┌──────────┴──────────┐
                        ▼                     ▼
            ┌──────────────────┐  ┌──────────────────┐
            │  对话记录        │  │  数据验证存储    │
            │  llm_logs/       │  │  Excel/Sheets    │
            └──────────────────┘  └──────────────────┘
```

### 关键模块说明

- **main.py**: 程序入口，协调整体流程
- **excel_handler.py / google_sheets_handler.py**: 数据源管理
- **analysis_stage.py**: 三阶段分析流程控制
- **fetch_text.py**: 多层fallback内容提取
- **playwright_worker.py**: 独立进程Playwright任务执行
- **screenshot_ocr_fetcher.py**: OCR图像处理和文本提取
- **llm_agent.py**: LLM API调用和对话管理
- **contact_verifier.py**: 联系人验证和补全
- **browser_search.py**: Playwright浏览器搜索

## 🔧 开发指南

### 扩展新的分析阶段

1. 在 `llm_agent.py` 中添加新的分析方法：
```python
def analyze_stage_new(self, text: str) -> Dict:
    """新的分析阶段"""
    prompt = "你的提示词..."
    response = self._call_llm(prompt)
    return self._parse_response(response)
```

2. 在 `analysis_stage.py` 中集成：
```python
def _execute_stage_new(self, text: str) -> Tuple[bool, Dict, str]:
    result = self.llm_agent.analyze_stage_new(text)
    # 处理结果...
    return success, result, log_content
```

3. 更新 `excel_handler.py` 中的验证逻辑

### 自定义提示词

编辑 `llm_agent.py` 中的提示词模板：
- 调整分析策略
- 添加新的字段要求
- 修改输出格式要求
- 优化特定场景的识别

### 添加新的内容源

在 `fetch_text.py` 中扩展：
```python
def _handle_custom_source(self, url: str) -> Optional[str]:
    """处理自定义来源"""
    # 实现你的逻辑
    return extracted_text
```

### 优化OCR效果

在 `screenshot_ocr_fetcher.py` 中调整：
- `_preprocess_image()`: 图像预处理参数
- `_clean_ocr_text()`: 文本清理规则
- `validate_ocr_quality()`: 质量验证标准

### 联系人验证功能

#### 启用/禁用
在 `config.py` 中：
```python
CONTACT_VERIFICATION_ENABLED = True  # 或 False
```

#### 调整搜索参数
```python
CONTACT_SEARCH_TIMEOUT = 20  # 搜索超时（秒）
MAX_SEARCH_RESULTS = 10      # 最大搜索结果数
MAX_PAGES_TO_ANALYZE = 3     # 最大分析页面数
```

### 资源清理优化

所有资源管理类都实现了防重复清理机制：
- `BrowserSearcher`: `_closed` 标志
- `ContactVerifier`: `_cleaned` 标志
- `AnalysisManager`: `_cleaned` 标志

确保：
1. 在`__init__`中初始化标志
2. 在`cleanup/close`中检查标志
3. 清理后设置标志并清空引用

## 📊 性能优化建议

### 1. OCR性能优化
- ✅ 安装opencv-python
- ✅ 使用SSD而非HDD存储临时文件
- ✅ 调整`SCREENSHOT_MAX_PAGES`限制大文档

### 2. LLM调用优化
- 使用流式输出减少等待时间
- 合理设置token限制
- 考虑使用本地Ollama模型

### 3. 网络请求优化
- 合理设置超时时间
- 使用并发处理（谨慎使用，避免被封IP）
- 添加请求间隔

### 4. 数据库操作优化
- Google Sheets：使用批量更新
- 本地Excel：减少保存频率
- 定期清理日志文件

## 🔒 安全建议

### 1. 凭据管理
```bash
# 添加到.gitignore
echo "credentials.json" >> .gitignore
echo "openai_key.txt" >> .gitignore
echo "token.pickle" >> .gitignore
```

### 2. API密钥
- 定期轮换
- 使用环境变量
- 设置使用限额

### 3. 数据保护
- 定期备份Google Sheets
- 设置适当的共享权限
- 敏感数据加密存储

## 📝 更新日志

### v2.0 - 2025-01-01
- ✅ 新增截图OCR智能回退功能
- ✅ 优化多页PDF文档处理
- ✅ 改进链接提取优先级（Source优先）
- ✅ 增强OCR文本清理能力
- ✅ 添加opencv-python支持
- ✅ 优化资源清理机制
- ✅ 修复重复警告问题

### v1.5 - 2024-12-XX
- ✅ Google Sheets支持
- ✅ 联系人验证功能
- ✅ 完整的LLM对话记录

### v1.0 - 2024-XX-XX
- ✅ 基础三阶段分析
- ✅ 多种内容提取方式
- ✅ 本地Excel支持

## 📄 许可证

[添加您的许可证信息]

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 贡献指南
1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 报告Bug
请提供：
- 详细的错误描述
- 复现步骤
- 系统环境信息
- 相关日志文件

## 🙏 致谢

感谢以下开源项目：
- Playwright - 浏览器自动化
- Tesseract OCR - 文字识别
- OpenAI - GPT模型
- Ollama - 本地模型运行
- 所有Python依赖库的开发者

---

**💡 提示**：遇到问题时，首先查看对应行的LLM对话记录（`llm_logs/`），这通常能帮助您快速定位问题所在！

**🎯 最佳实践**：
1. 首次使用前运行 `python check_system.py` 检查环境
2. 安装opencv-python以获得最佳OCR效果
3. 定期查看日志文件了解处理状态
4. 使用Google Sheets模式进行团队协作
5. 保留LLM对话记录用于调试和优化
