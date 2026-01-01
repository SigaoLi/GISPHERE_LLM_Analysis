#!/usr/bin/env python3
"""
依赖检查脚本 - 验证所有必需和可选依赖是否正确安装
"""

import sys
import subprocess
from typing import Dict, Tuple

def check_python_version() -> Tuple[bool, str]:
    """检查Python版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"❌ Python {version.major}.{version.minor}.{version.micro} (需要 3.8+)"

def check_module(module_name: str, import_name: str = None, required: bool = True) -> Tuple[bool, str]:
    """检查模块是否安装"""
    if import_name is None:
        import_name = module_name
    
    try:
        mod = __import__(import_name)
        version = getattr(mod, '__version__', 'unknown')
        status = "✅" if required else "✓"
        return True, f"{status} {module_name} ({version})"
    except ImportError:
        status = "❌" if required else "⚠️"
        req_type = "必需" if required else "可选"
        return False, f"{status} {module_name} 未安装 ({req_type})"

def check_tesseract() -> Tuple[bool, str]:
    """检查Tesseract OCR是否安装"""
    try:
        result = subprocess.run(
            ['tesseract', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return True, f"✅ Tesseract OCR ({version_line})"
        else:
            return False, "❌ Tesseract OCR 未正确安装"
    except FileNotFoundError:
        return False, "❌ Tesseract OCR 未安装或不在PATH中"
    except Exception as e:
        return False, f"❌ Tesseract OCR 检查失败: {e}"

def check_playwright_browsers() -> Tuple[bool, str]:
    """检查Playwright浏览器是否安装"""
    try:
        result = subprocess.run(
            ['playwright', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if 'chromium' in result.stdout.lower():
            return True, "✅ Playwright Chromium浏览器已安装"
        else:
            return False, "❌ Playwright Chromium浏览器未安装"
    except FileNotFoundError:
        return False, "⚠️ Playwright命令行工具未找到（playwright可能未安装）"
    except Exception as e:
        return False, f"⚠️ Playwright浏览器检查失败: {e}"

def main():
    """主检查函数"""
    print("=" * 70)
    print("依赖检查 - LLM文本智能分析系统")
    print("=" * 70)
    print()
    
    # 必需依赖
    required_deps: Dict[str, Tuple[str, str]] = {
        # (package_name, import_name)
        'Python版本': (None, None),  # 特殊处理
        'openai': ('openai', 'openai'),
        'requests': ('requests', 'requests'),
        'pandas': ('pandas', 'pandas'),
        'numpy': ('numpy', 'numpy'),
        'openpyxl': ('openpyxl', 'openpyxl'),
        'beautifulsoup4': ('beautifulsoup4', 'bs4'),
        'lxml': ('lxml', 'lxml'),
        'tqdm': ('tqdm', 'tqdm'),
        'PyMuPDF': ('PyMuPDF', 'fitz'),
        'pdfplumber': ('pdfplumber', 'pdfplumber'),
        'PyPDF2': ('PyPDF2', 'PyPDF2'),
        'pytesseract': ('pytesseract', 'pytesseract'),
        'Pillow': ('Pillow', 'PIL'),
        'playwright': ('playwright', 'playwright'),
        'google-api-python-client': ('google-api-python-client', 'googleapiclient'),
        'google-auth-httplib2': ('google-auth-httplib2', 'google_auth_httplib2'),
        'google-auth-oauthlib': ('google-auth-oauthlib', 'google_auth_oauthlib'),
        'google-auth': ('google-auth', 'google.auth'),
        'inflect': ('inflect', 'inflect'),
    }
    
    # 可选依赖
    optional_deps: Dict[str, Tuple[str, str]] = {
        'opencv-python': ('opencv-python', 'cv2'),
    }
    
    # 外部工具
    external_tools = {
        'Tesseract OCR': check_tesseract,
        'Playwright浏览器': check_playwright_browsers,
    }
    
    # 检查结果统计
    required_passed = 0
    required_failed = 0
    optional_passed = 0
    optional_failed = 0
    
    # 检查Python版本
    print("📌 核心环境")
    print("-" * 70)
    success, message = check_python_version()
    print(f"  {message}")
    if not success:
        required_failed += 1
    else:
        required_passed += 1
    print()
    
    # 检查必需依赖
    print("📦 必需依赖")
    print("-" * 70)
    for name, (pkg, imp) in list(required_deps.items())[1:]:  # 跳过Python版本
        if pkg and imp:
            success, message = check_module(pkg, imp, required=True)
            print(f"  {message}")
            if success:
                required_passed += 1
            else:
                required_failed += 1
    print()
    
    # 检查可选依赖
    print("🎁 可选依赖（增强功能）")
    print("-" * 70)
    for name, (pkg, imp) in optional_deps.items():
        success, message = check_module(pkg, imp, required=False)
        print(f"  {message}")
        if success:
            optional_passed += 1
        else:
            optional_failed += 1
    print()
    
    # 检查外部工具
    print("🔧 外部工具")
    print("-" * 70)
    for name, check_func in external_tools.items():
        success, message = check_func()
        print(f"  {message}")
        if not success and name == 'Tesseract OCR':
            required_failed += 1
        elif success and name == 'Tesseract OCR':
            required_passed += 1
    print()
    
    # 总结
    print("=" * 70)
    print("📊 检查结果总结")
    print("=" * 70)
    
    total_required = required_passed + required_failed
    total_optional = optional_passed + optional_failed
    
    print(f"必需依赖: {required_passed}/{total_required} 已安装", end="")
    if required_failed > 0:
        print(f" ({required_failed} 个缺失)")
    else:
        print(" ✅")
    
    print(f"可选依赖: {optional_passed}/{total_optional} 已安装", end="")
    if optional_failed > 0:
        print(f" ({optional_failed} 个缺失)")
    else:
        print(" ✅")
    
    print()
    
    # 安装建议
    if required_failed > 0:
        print("❌ 系统未就绪！请安装缺失的必需依赖：")
        print()
        print("   pip install -r requirements.txt")
        print("   playwright install chromium")
        print()
        print("   Tesseract OCR安装:")
        print("   - Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   - Linux: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim")
        print("   - macOS: brew install tesseract tesseract-lang")
        print()
        return 1
    else:
        print("✅ 所有必需依赖已安装！系统可以正常运行。")
        print()
        
        if optional_failed > 0:
            print("💡 提示：安装可选依赖可以获得更好的性能：")
            print()
            print("   pip install -r requirements-optional.txt")
            print()
            print("   可选依赖说明：")
            print("   - opencv-python: 显著提高OCR识别质量（强烈推荐）")
            print()
        
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

