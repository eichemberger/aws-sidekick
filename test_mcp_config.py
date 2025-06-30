#!/usr/bin/env python3
"""Test script for YAML MCP configuration"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.config import MCPConfig

def test_mcp_config():
    """Test the YAML MCP configuration loading"""
    
    # Set test environment
    os.environ['GITHUB_PERSONAL_ACCESS_TOKEN'] = 'test_token'
    
    try:
        print('🔧 Testing YAML MCP configuration...')
        
        # Load the configuration
        mcp_config = MCPConfig.from_yaml('config/mcp-config.yaml')
        
        print(f'✅ Successfully loaded {len(mcp_config.servers)} enabled MCP servers:')
        for name, server in mcp_config.servers.items():
            status = '✅ enabled' if server.enabled else '❌ disabled'
            desc = server.description or 'No description'
            print(f'  - {name}: {status} | {desc}')
            print(f'    Command: {server.command} {" ".join(server.args)}')
            if server.env:
                print(f'    Environment: {list(server.env.keys())}')
        
        print('\n📊 Configuration Summary:')
        print(f'  Total servers configured: {len(mcp_config.servers)}')
        print(f'  AWS Documentation: {"✅" if "aws_docs" in mcp_config.servers else "❌"}')
        print(f'  AWS Diagrams: {"✅" if "aws_diagram" in mcp_config.servers else "❌"}')
        print(f'  GitHub: {"✅" if "github" in mcp_config.servers else "❌"}')
        
        return True
        
    except Exception as e:
        print(f'❌ Configuration test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mcp_config()
    sys.exit(0 if success else 1) 