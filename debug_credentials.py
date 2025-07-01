#!/usr/bin/env python3
"""
Debug script to check credential status
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infrastructure.credential_manager import get_credential_manager
from infrastructure.dependency_injection import get_container

async def debug_credentials():
    """Debug credential storage status"""
    try:
        print("🔍 Checking credential storage status...")
        print("=" * 50)
        
        # Get credential manager
        credential_manager = get_credential_manager()
        
        # Check dev mode status
        dev_mode = credential_manager._dev_mode
        print(f"🚀 Development mode: {'✅ ENABLED' if dev_mode else '❌ DISABLED'}")
        if dev_mode:
            storage_path = credential_manager._dev_storage_path
            file_exists = storage_path.exists()
            print(f"📁 Dev storage file: {storage_path}")
            print(f"📄 File exists: {'✅ Yes' if file_exists else '❌ No'}")
        print("")
        
        # Get all accounts with credentials in memory
        accounts_with_creds = await credential_manager.list_accounts_with_credentials()
        
        print(f"📋 Accounts with credentials in memory: {len(accounts_with_creds)}")
        for account in accounts_with_creds:
            print(f"  ✅ {account}")
        
        if not accounts_with_creds:
            print("  ❌ No accounts have credentials in memory")
        
        print("\n" + "=" * 50)
        
        # Get container and AWS service
        container = get_container()
        aws_service = container.get_aws_service()
        
        # Get active account
        active_alias = aws_service.get_active_account_alias()
        
        if active_alias:
            print(f"🎯 Active account: {active_alias}")
            
            # Check if active account has credentials
            has_creds = await credential_manager.has_credentials(active_alias)
            print(f"🔐 Active account has credentials: {'✅ Yes' if has_creds else '❌ No'}")
            
            if not has_creds:
                print("\n⚠️  ISSUE FOUND: Active account has no credentials in memory!")
                print("💡 Solution: Re-enter credentials for this account via the UI")
        else:
            print("🎯 No active account selected")
        
        print("\n" + "=" * 50)
        print("🔧 Next steps:")
        print("1. Go to AWS account management in the UI")
        print("2. Update/re-enter credentials for your account")
        print("3. Select the account again")
        print("4. Run this script again to verify")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_credentials()) 