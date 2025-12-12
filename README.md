# 基于LLM的文本智能分析与数据字段自动填写系统

这是一个智能的文本分析系统，能够自动从网页或PDF链接中提取内容，通过大语言模型(LLM)进行三阶段分析，并将结果自动填入Excel表格或Google Sheets的相应字段中。

## 🆕 Google Sheets支持

**全新功能**：现已支持Google Sheets作为数据源！

- ✅ **云端协作**：多人实时查看处理进度
- ✅ **自动同步**：处理结果实时保存到云端
- ✅ **智能切换**：自动检测并选择最佳数据源
- ✅ **零配置回退**：Google Sheets不可用时自动使用本地Excel

## 🌟 主要特性

- **智能内容提取**：支持网页和PDF文件的内容获取
- **三阶段LLM分析**：基本信息提取 → 类型分类 → 中文字段提取
- **多模型支持**：兼容OpenAI API和Ollama本地模型
- **自动数据验证**：内置多层验证机制确保数据质量
- **断点续传**：支持中断后继续处理
- **详细日志记录**：完整的LLM对话记录，包含错误分析
- **PDF缓存管理**：智能缓存，处理完成后自动清理

## 🔍 错误分析和对话记录

### 完整的LLM对话记录

**重要更新**：系统现在能够保存所有LLM对话记录，即使在处理失败的情况下：

- ✅ **成功案例**：保存完整的三阶段分析对话
- ✅ **部分失败**：保存失败前已完成的阶段对话  
- ✅ **完全失败**：保存错误发生前的所有LLM交互
- ✅ **异常情况**：即使程序异常也会尝试保存对话记录

### 对话记录文件格式

每个处理的行都会生成独立的对话记录文件：
```
llm_logs/row_0001_20250709_124317_UTC.txt
```

文件内容包含：
- 🕒 **时间戳**：使用UTC时间统一标准
- 🤖 **模型信息**：使用的具体LLM模型
- 📝 **完整提示词**：发送给LLM的原始提示
- 💬 **模型响应**：LLM的完整回复
- 🏷️ **阶段标识**：stage1/stage2/stage3标记

### 错误分析价值

通过查看对话记录，您可以：
1. **分析失败原因**：查看LLM的具体响应和错误点
2. **优化提示词**：根据实际对话调整提示策略
3. **改进数据质量**：识别常见的数据提取问题
4. **模型对比**：比较不同模型的处理效果
5. **调试系统**：追踪处理流程中的问题

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 依赖包：`pandas`, `openpyxl`, `requests`, `beautifulsoup4`, `PyMuPDF`, `tqdm`
- Google Sheets API库：`google-api-python-client`, `google-auth-oauthlib`
- LLM服务：OpenAI API 或 Ollama 本地模型

### 安装

```bash
# 克隆项目
git clone [项目地址]
cd LLM_Analysis

# 安装依赖
pip install -r requirements.txt

# 检查系统环境
python check_system.py
```

### 配置

#### 1. 选择数据源

**选项A：Google Sheets（推荐）**

Google Sheets模式支持云端协作和实时同步。以下是详细设置步骤：

##### 🔧 前置要求
- Google账户
- Google Cloud Project
- Python环境（已安装项目依赖）

##### 📋 步骤1：创建Google Cloud项目
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 点击"创建项目"或选择现有项目
3. 记录项目ID（稍后需要用到）

##### 🔑 步骤2：启用Google Sheets API
1. 在Google Cloud Console中，导航到"API和服务" > "库"
2. 搜索"Google Sheets API"
3. 点击"启用"

##### 🛡️ 步骤3：创建服务账号凭据

**方法A：服务账号（推荐用于生产环境）**
1. 在Google Cloud Console中，导航到"API和服务" > "凭据"
2. 点击"创建凭据" > "服务账号"
3. 填写服务账号详细信息
4. 创建完成后，点击服务账号，转到"密钥"标签
5. 点击"添加密钥" > "创建新密钥" > JSON格式
6. 下载JSON文件，重命名为`credentials.json`，放到项目根目录

**方法B：OAuth 2.0客户端ID（推荐用于开发环境）**
1. 在Google Cloud Console中，导航到"API和服务" > "凭据"
2. 点击"创建凭据" > "OAuth客户端ID"
3. 选择"桌面应用程序"
4. 下载JSON文件，重命名为`credentials.json`，放到项目根目录

##### 📊 步骤4：准备Google表格
1. 创建或打开您的Google表格
2. 确保表格包含以下列（与原Excel格式相同）：
   - `Notes`：包含链接信息
   - `Source`：备用链接来源
   - `Verifier`：验证人标记
   - `Error`：错误信息
   - 其他分析字段...
3. 创建名为`Unfilled`的工作表（或根据需要修改`config.py`中的`SHEET_NAME`）
4. 复制表格URL中的ID，例如：
   ```
   https://docs.google.com/spreadsheets/d/1LcfxcTCuj9ZJXXMxyFQwt-xnbAviNP8j9oDr6OG5-Go/edit
   ```
   表格ID为：`1LcfxcTCuj9ZJXXMxyFQwt-xnbAviNP8j9oDr6OG5-Go`

##### ⚙️ 步骤5：配置项目
1. 打开`config.py`文件
2. 修改`GOOGLE_SPREADSHEET_ID`为您的表格ID：
   ```python
   GOOGLE_SPREADSHEET_ID = '您的表格ID'
   ```

##### 🔐 步骤6：设置权限
**如果使用服务账号：**
1. 打开您的Google表格
2. 点击"共享"按钮
3. 添加服务账号的邮箱地址（可在credentials.json中找到`client_email`字段）
4. 给予"编辑者"权限

**如果使用OAuth 2.0：**
首次运行时会自动打开浏览器进行授权。

##### 🚀 步骤7：测试配置
运行系统检查命令：
```bash
python check_system.py
```

如果看到以下信息，说明配置成功：
```
=== 检查数据源 ===
🔍 检测到Google凭据文件，尝试Google Sheets模式
✅ Google Sheets模式已启用
✅ Google Sheets数据加载成功
```

**选项B：本地Excel**
```bash
# 将待处理数据放入 text_info.xlsx 的 Unfilled 工作表
# 确保包含 Notes 和 Source 列（包含链接信息）
```

#### 2. 配置LLM服务

**OpenAI API**（推荐）：
```bash
# 在openai_key.txt中添加你的API密钥
echo "your-api-key-here" > openai_key.txt
```

**Ollama本地模型**：
```bash
# 启动Ollama服务
ollama serve

# 下载qwen3模型（推荐）
ollama pull qwen3:14b
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
- **Deadline**：申请截止日期（YYYY-MM-DD格式或"Soon"）
- **Number_Places**：招生人数（明确数字或留空）
- **Direction**：研究方向（保持原始格式）
- **University_EN**：机构英文全称
- **Contact_Name**：联系人姓名（🆕 含学位验证）
- **Contact_Email**：联系邮箱（🆕 含自动补全）

#### 🔍 新功能：联系人智能验证
阶段1现在包含智能联系人验证流程，通过"University_EN" + "Contact_Name"进行浏览器搜索：

**场景1：已有明确学位标识**
- 文档明确显示联系人为Dr/Prof时
- 如有邮箱则跳过验证，如无邮箱则搜索补全

**场景2：学位信息不明确**  
- 无论是否有邮箱都进行验证
- 通过搜索确认学位，调整称谓（Dr./Mr./Ms.）
- 同时补全缺失的邮箱信息

**场景3：缺失联系人**
- 完全无联系人信息时跳过验证

验证流程会智能选择最相关的页面（个人主页、学校介绍页、学术平台等）进行深度分析。

**技术特性**：
- 🎭 **Playwright驱动**：更强的反反爬虫能力，模拟真实用户行为
- 🤖 **英文LLM分析**：专业的英文提示词，提高分析准确性
- 🔄 **智能回退**：Playwright失败时自动使用基础HTTP请求

### 阶段2：类型和专业分类
- **招生类型**：Master Student, Doctoral Student, PostDoc, Research Assistant, Competition, Summer School, Conference, Workshop
- **专业方向**：Physical_Geo, Human_Geo, Urban, GIS, RS, GNSS（最多3个，最少1个）

### 阶段3：中文字段提取
- **University_CN**：机构中文全称
- **Country_CN**：所在国家中文名
- **WX_Label1-3**：专业领域标签（WX_Label1必填，4-5留空）

## ⚙️ 配置选项

在 `config.py` 中可以修改：

- **LLM配置**：模型名称、API地址
- **文件路径**：Excel文件路径、缓存目录
- **请求配置**：超时时间、重试次数
- **联系人验证**：启用/禁用验证功能、搜索参数
- **日志级别**：INFO、DEBUG、WARNING等

## 🛠️ 常见问题

### Q: 如何处理网络连接问题？
A: 系统内置重试机制，会自动重试失败的请求。可在config.py中调整重试次数和超时时间。

### Q: 如何查看详细的错误信息？
A: 检查以下日志文件：
- `logs/run.log`：系统运行日志
- `llm_logs/row_xxxx_yyyymmdd_hhmmss_UTC.txt`：具体行的LLM对话记录（使用英国时间UTC命名）

**🆕 新功能**：现在即使处理失败，也会保存LLM对话记录，方便分析失败原因！

### Q: 如何分析处理失败的原因？
A: 
1. 查看错误行的对话记录文件
2. 检查LLM的提示词和响应
3. 分析是否为数据质量问题还是提示词问题
4. 根据分析结果调整配置或提示词

### Q: 如何选择使用Google Sheets还是本地Excel？
A: 系统会自动检测：
- 如果存在`credentials.json`文件，优先使用Google Sheets
- 如果Google Sheets初始化失败，自动回退到本地Excel
- 可以通过代码强制指定模式

### Q: Google Sheets和本地Excel有什么区别？
A: 
- **Google Sheets**：实时同步、多人协作、云端备份、需要网络
- **本地Excel**：离线处理、速度更快、无需配置、数据本地存储

### Q: Google Sheets使用过程中遇到问题怎么办？

#### 🔄 自动模式切换
- 如果检测到`credentials.json`文件，系统会自动使用Google Sheets模式
- 如果Google Sheets初始化失败，会自动回退到本地Excel模式
- 可以通过修改`excel_handler = ExcelHandler(use_google_sheets=False)`强制使用本地模式

#### 🔄 实时同步特性
- 每次处理完一行数据，都会立即同步到Google表格
- 支持多人协作，实时查看处理进度
- 所有操作都会记录在云端，不用担心数据丢失

#### 🛠️ 常见错误及解决方案

1. **"Google凭据文件不存在"**
   - 确保`credentials.json`文件在项目根目录
   - 检查文件名是否正确

2. **"权限被拒绝"**
   - 检查服务账号是否有表格编辑权限
   - 重新进行OAuth授权

3. **"找不到工作表"**
   - 确保表格中存在`Unfilled`工作表
   - 检查`config.py`中的`SHEET_NAME`设置

4. **"API配额超限"**
   - Google Sheets API有使用限制
   - 可以申请提高配额或减少请求频率

#### 📈 性能优化建议

1. **批量操作**：系统支持批量更新，减少API调用次数
2. **缓存机制**：本地保存DataFrame，只在必要时同步到云端
3. **错误重试**：网络错误时自动重试，确保数据完整性

#### 🔒 安全建议

1. **凭据安全**：
   - 不要将`credentials.json`提交到版本控制
   - 定期轮换API密钥
   - 使用最小权限原则

2. **数据保护**：
   - 定期备份Google表格
   - 设置适当的共享权限
   - 考虑使用私有表格

### Q: 如何中断并恢复处理？
A: 使用Ctrl+C中断程序，再次运行时会自动跳过已处理的行（Verifier不为空）。

### Q: PDF文件会占用太多存储空间吗？
A: 不会。系统在处理完每个PDF文件后会自动删除，仅在处理期间临时存储。

### Q: 为什么LLM对话记录文件名包含UTC时间？
A: 使用英国时间（UTC）统一时间标准，避免时区混乱，文件名格式为：`row_xxxx_yyyymmdd_hhmmss_UTC.txt`

### Q: LLM分析结果不准确怎么办？
A: 可以：
1. 查看对话记录分析具体问题
2. 调整提示词（在llm_agent.py中）
3. 更换更强大的模型
4. 根据对话记录优化数据预处理

## 📈 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   内容获取模块   │───▶│   LLM分析模块   │───▶│   Excel更新模块  │
│  fetch_text.py  │    │  llm_agent.py   │    │ excel_handler.py│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF/网页缓存   │    │   对话记录保存   │    │   数据验证存储   │
│   cache/pdf/    │    │   llm_logs/     │    │  text_info.xlsx │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 开发指南

### 扩展新的分析阶段
1. 在 `llm_agent.py` 中添加新的分析方法
2. 在 `analysis_stage.py` 中集成新阶段
3. 更新 `excel_handler.py` 中的验证逻辑

### 自定义提示词
编辑 `llm_agent.py` 中的提示词模板，可以：
- 调整分析策略
- 添加新的字段
- 修改输出格式要求

### 添加新的内容源
在 `fetch_text.py` 中扩展支持新的文档格式或网站类型。

### 联系人验证功能
#### 安装和配置
```bash
# 安装Playwright依赖
pip install playwright
playwright install chromium
```

#### 功能控制
在 `config.py` 中可以控制验证功能：
```python
CONTACT_VERIFICATION_ENABLED = True  # 启用/禁用验证
CONTACT_SEARCH_TIMEOUT = 20         # 搜索超时时间
MAX_SEARCH_RESULTS = 10             # 最大搜索结果数
MAX_PAGES_TO_ANALYZE = 3            # 最大分析页面数
```

#### 测试验证功能
```bash
# 测试基础验证逻辑
python test_contact_verification.py

# 测试完整验证流程
python example_contact_verification.py
```

## 📄 许可证

[添加许可证信息]

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

---

**🔍 提示**：遇到问题时，首先查看对应行的LLM对话记录，这通常能帮助您快速定位问题所在！ 