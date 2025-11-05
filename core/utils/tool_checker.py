"""
工具可用性检查器
检查系统中是否已安装所需的安全工具
"""

import shutil
import logging
from functools import lru_cache
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolChecker:
    """工具可用性检查器"""
    
    # 工具安装命令映射
    TOOL_INSTALL_COMMANDS = {
        # Go工具
        'dalfox': 'go install github.com/hahwul/dalfox/v2@latest',
        'subfinder': 'go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest',
        'nuclei': 'go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest',
        'httpx': 'go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest',
        'katana': 'go install github.com/projectdiscovery/katana/cmd/katana@latest',
        'gau': 'go install github.com/lc/gau/v2/cmd/gau@latest',
        'waybackurls': 'go install github.com/tomnomnom/waybackurls@latest',
        'amass': 'go install -v github.com/owasp-amass/amass/v4/...@master',
        'ffuf': 'go install github.com/ffuf/ffuf/v2@latest',
        
        # Python工具
        'arjun': 'pip3 install arjun',
        'sqlmap': 'sudo apt install sqlmap -y',
        'wpscan': 'sudo gem install wpscan',
        
        # APT工具
        'nmap': 'sudo apt install nmap -y',
        'nikto': 'sudo apt install nikto -y',
        'gobuster': 'sudo apt install gobuster -y',
        'masscan': 'sudo apt install masscan -y',
        'hydra': 'sudo apt install hydra -y',
        'john': 'sudo apt install john -y',
        'hashcat': 'sudo apt install hashcat -y',
        'metasploit-framework': 'sudo apt install metasploit-framework -y',
        'feroxbuster': 'sudo apt install feroxbuster -y',
        'dirsearch': 'sudo apt install dirsearch -y',
        'whatweb': 'sudo apt install whatweb -y',
        'testssl': 'sudo apt install testssl.sh -y',
        'sslscan': 'sudo apt install sslscan -y',
    }
    
    # 工具别名映射
    TOOL_ALIASES = {
        'testssl.sh': 'testssl',
    }
    
    @staticmethod
    @lru_cache(maxsize=128)
    def is_tool_available(tool_name: str) -> bool:
        """
        检查工具是否可用
        使用LRU缓存避免重复检查
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 工具是否可用
        """
        # 处理可能的别名
        tool_name = ToolChecker.TOOL_ALIASES.get(tool_name, tool_name)
        
        # 移除可能的路径前缀
        tool_binary = tool_name.split('/')[-1]
        
        # 检查是否在PATH中
        is_available = shutil.which(tool_binary) is not None
        
        if is_available:
            logger.debug(f"✅ Tool '{tool_binary}' is available")
        else:
            logger.debug(f"❌ Tool '{tool_binary}' is NOT available")
        
        return is_available
    
    @classmethod
    def check_tool_or_error(cls, tool_name: str) -> Dict:
        """
        检查工具，如果不可用返回错误信息和安装建议
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Dict: 包含可用性状态和安装建议
        """
        if cls.is_tool_available(tool_name):
            return {
                "available": True,
                "tool": tool_name
            }
        
        install_cmd = cls.TOOL_INSTALL_COMMANDS.get(
            tool_name, 
            f"# Unknown tool. Try: apt search {tool_name}"
        )
        
        return {
            "available": False,
            "error": f"Tool '{tool_name}' is not installed or not in PATH",
            "tool": tool_name,
            "install_command": install_cmd,
            "suggestion": f"Install using: {install_cmd}"
        }
    
    @classmethod
    def get_available_tools(cls, tool_list: List[str]) -> Dict[str, bool]:
        """
        批量检查工具可用性
        
        Args:
            tool_list: 工具名称列表
            
        Returns:
            Dict[str, bool]: 工具名称到可用性的映射
        """
        return {
            tool: cls.is_tool_available(tool)
            for tool in tool_list
        }
    
    @classmethod
    def get_missing_tools(cls, tool_list: List[str]) -> List[str]:
        """
        获取缺失的工具列表
        
        Args:
            tool_list: 工具名称列表
            
        Returns:
            List[str]: 缺失的工具名称列表
        """
        return [
            tool for tool in tool_list
            if not cls.is_tool_available(tool)
        ]
    
    @classmethod
    def get_system_report(cls) -> Dict:
        """
        生成系统工具可用性报告
        
        Returns:
            Dict: 详细的系统报告
        """
        all_tools = list(cls.TOOL_INSTALL_COMMANDS.keys())
        availability = cls.get_available_tools(all_tools)
        
        available_count = sum(1 for v in availability.values() if v)
        total_count = len(all_tools)
        
        missing_tools = [tool for tool, available in availability.items() if not available]
        
        return {
            "total_tools": total_count,
            "available_tools": available_count,
            "missing_tools_count": total_count - available_count,
            "coverage_percentage": round(available_count / total_count * 100, 2),
            "details": availability,
            "missing_tools": missing_tools,
            "install_commands": {
                tool: cls.TOOL_INSTALL_COMMANDS[tool]
                for tool in missing_tools
            }
        }
    
    @classmethod
    def generate_install_script(cls, output_file: str = "install_missing_tools.sh") -> str:
        """
        生成安装脚本用于安装所有缺失的工具
        
        Args:
            output_file: 输出脚本文件路径
            
        Returns:
            str: 脚本文件路径
        """
        report = cls.get_system_report()
        missing = report['missing_tools']
        
        if not missing:
            logger.info("✅ All tools are already installed!")
            return None
        
        script_content = """#!/bin/bash
# HexStrike AI - 自动安装缺失工具脚本
# 生成时间: {timestamp}

set -e  # 遇到错误立即退出

echo "🚀 HexStrike AI - Installing Missing Tools"
echo "=========================================="
echo ""

# 检查是否为root用户（某些命令需要）
if [[ $EUID -ne 0 ]] && [[ "$1" != "--no-sudo" ]]; then
   echo "⚠️  Some tools require sudo privileges."
   echo "   Run with --no-sudo to skip sudo commands"
   echo ""
fi

# 更新包管理器
echo "📦 Updating package manager..."
sudo apt update || true

""".format(timestamp=__import__('datetime').datetime.now())
        
        # 分类工具
        go_tools = []
        pip_tools = []
        apt_tools = []
        gem_tools = []
        
        for tool in missing:
            cmd = cls.TOOL_INSTALL_COMMANDS.get(tool, "")
            if cmd.startswith('go install'):
                go_tools.append((tool, cmd))
            elif cmd.startswith('pip'):
                pip_tools.append((tool, cmd))
            elif cmd.startswith('sudo apt'):
                apt_tools.append((tool, cmd))
            elif cmd.startswith('sudo gem'):
                gem_tools.append((tool, cmd))
        
        # Go工具
        if go_tools:
            script_content += """
# ============ Go Tools ============
echo "🔧 Installing Go tools..."
"""
            for tool, cmd in go_tools:
                script_content += f'echo "  - Installing {tool}..."\n'
                script_content += f'{cmd} 2>/dev/null || echo "    ⚠️  Failed to install {tool}"\n'
        
        # Python工具
        if pip_tools:
            script_content += """
# ============ Python Tools ============
echo "🐍 Installing Python tools..."
"""
            for tool, cmd in pip_tools:
                script_content += f'echo "  - Installing {tool}..."\n'
                script_content += f'{cmd} 2>/dev/null || echo "    ⚠️  Failed to install {tool}"\n'
        
        # APT工具
        if apt_tools:
            script_content += """
# ============ APT Tools ============
echo "📦 Installing APT tools..."
"""
            for tool, cmd in apt_tools:
                script_content += f'echo "  - Installing {tool}..."\n'
                script_content += f'{cmd} 2>/dev/null || echo "    ⚠️  Failed to install {tool}"\n'
        
        # Gem工具
        if gem_tools:
            script_content += """
# ============ Ruby Gem Tools ============
echo "💎 Installing Ruby Gem tools..."
"""
            for tool, cmd in gem_tools:
                script_content += f'echo "  - Installing {tool}..."\n'
                script_content += f'{cmd} 2>/dev/null || echo "    ⚠️  Failed to install {tool}"\n'
        
        script_content += """
echo ""
echo "✅ Installation completed!"
echo "Please verify tool availability with: hexstrike_mcp tool_check"
"""
        
        # 写入文件
        with open(output_file, 'w') as f:
            f.write(script_content)
        
        # 添加执行权限
        import os
        os.chmod(output_file, 0o755)
        
        logger.info(f"✅ Install script generated: {output_file}")
        logger.info(f"   Run with: ./{output_file}")
        
        return output_file


# 全局实例
tool_checker = ToolChecker()
