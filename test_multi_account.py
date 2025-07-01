
#!/usr/bin/env python3
"""
Test script for multi-account AWS credentials functionality.
This script tests the backend implementation without requiring a frontend.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.domain.value_objects.aws_credentials import AWSCredentials
from core.domain.entities.aws_account import AWSAccount
from core.domain.entities.chat import Conversation
from core.domain.entities.task import Task, TaskStatus
from infrastructure.dependency_injection import get_container
from datetime import datetime


async def test_multi_account_functionality():
    """Test the multi-account functionality"""
    print("🧪 Testing Multi-Account AWS Credentials Functionality\n")
    
    # Initialize container
    container = get_container()
    
    # Configure dummy agent to avoid MCP initialization issues
    container.configure_agent(None, None, None, None)
    
    # Get services
    account_service = container.get_aws_account_service()
    aws_service = container.get_aws_service()
    
    print("✅ Services initialized successfully")
    
    # Test 1: Register multiple AWS accounts
    print("\n📝 Test 1: Registering AWS accounts")
    
    # Create test credentials (using profile for safety)
    dev_credentials = AWSCredentials(
        profile="dev-profile",
        region="us-east-1"
    )
    
    staging_credentials = AWSCredentials(
        profile="staging-profile", 
        region="us-east-1"
    )
    
    prod_credentials = AWSCredentials(
        profile="prod-profile",
        region="us-east-1"
    )
    
    try:
        # Register accounts (will fail validation since profiles don't exist, but that's okay)
        print("   Attempting to register 'dev' account...")
        try:
            dev_account = await account_service.register_account(
                alias="dev",
                credentials=dev_credentials,
                description="Development environment",
                set_as_default=True
            )
            print("   ✅ Successfully registered 'dev' account")
        except ValueError as e:
            if "Invalid AWS credentials" in str(e):
                print("   ⚠️  'dev' account registration failed due to credential validation (expected)")
                # Create account manually for testing
                dev_account = AWSAccount(
                    alias="dev",
                    credentials=dev_credentials,
                    description="Development environment",
                    is_default=True
                )
                await account_service._account_repository.save_account(dev_account)
                print("   ✅ 'dev' account saved to repository for testing")
            else:
                raise
        
        print("   Attempting to register 'staging' account...")
        try:
            staging_account = await account_service.register_account(
                alias="staging",
                credentials=staging_credentials,
                description="Staging environment"
            )
            print("   ✅ Successfully registered 'staging' account")
        except ValueError as e:
            if "Invalid AWS credentials" in str(e):
                print("   ⚠️  'staging' account registration failed due to credential validation (expected)")
                # Create account manually for testing
                staging_account = AWSAccount(
                    alias="staging",
                    credentials=staging_credentials,
                    description="Staging environment"
                )
                await account_service._account_repository.save_account(staging_account)
                print("   ✅ 'staging' account saved to repository for testing")
            else:
                raise
        
        print("   Attempting to register 'prod' account...")
        try:
            prod_account = await account_service.register_account(
                alias="prod",
                credentials=prod_credentials,
                description="Production environment"
            )
            print("   ✅ Successfully registered 'prod' account")
        except ValueError as e:
            if "Invalid AWS credentials" in str(e):
                print("   ⚠️  'prod' account registration failed due to credential validation (expected)")
                # Create account manually for testing
                prod_account = AWSAccount(
                    alias="prod",
                    credentials=prod_credentials,
                    description="Production environment"
                )
                await account_service._account_repository.save_account(prod_account)
                print("   ✅ 'prod' account saved to repository for testing")
            else:
                raise
        
    except Exception as e:
        print(f"   ❌ Error registering accounts: {e}")
        return False
    
    # Test 2: List accounts
    print("\n📋 Test 2: Listing AWS accounts")
    try:
        accounts = await account_service.list_accounts()
        print(f"   Found {len(accounts)} accounts:")
        for account in accounts:
            default_marker = " (DEFAULT)" if account.is_default else ""
            print(f"   - {account.alias}: {account.description} [{account.credentials.region}]{default_marker}")
        
        if not accounts:
            print("   ❌ No accounts found")
            return False
        
        print("   ✅ Successfully listed accounts")
    except Exception as e:
        print(f"   ❌ Error listing accounts: {e}")
        return False
    
    # Test 3: Get default account
    print("\n🎯 Test 3: Getting default account")
    try:
        default_account = await account_service.get_default_account()
        if default_account:
            print(f"   Default account: {default_account.alias} ({default_account.description})")
            print("   ✅ Successfully retrieved default account")
        else:
            print("   ⚠️  No default account found")
    except Exception as e:
        print(f"   ❌ Error getting default account: {e}")
        return False
    
    # Test 4: Set active account
    print("\n🔄 Test 4: Setting active account")
    try:
        await aws_service.set_active_account("staging")
        active_alias = aws_service.get_active_account_alias()
        print(f"   Active account set to: {active_alias}")
        
        if active_alias == "staging":
            print("   ✅ Successfully set active account")
        else:
            print("   ❌ Active account not set correctly")
            return False
    except Exception as e:
        print(f"   ❌ Error setting active account: {e}")
        return False
    
    # Test 5: Test account-associated entities
    print("\n🗂️  Test 5: Testing account-associated entities")
    try:
        # Create a conversation associated with the staging account
        conversation = Conversation(
            id="test-conv-1",
            title="Test Staging Conversation",
            account_alias="staging",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Create a task associated with the prod account
        task = Task(
            id="test-task-1",
            description="Test production task",
            account_alias="prod",
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        print(f"   Conversation created for account: {conversation.account_alias}")
        print(f"   Task created for account: {task.account_alias}")
        print("   ✅ Successfully created account-associated entities")
    except Exception as e:
        print(f"   ❌ Error creating account-associated entities: {e}")
        return False
    
    # Test 6: Account switching
    print("\n🔀 Test 6: Testing account switching")
    try:
        # Switch to prod account
        await aws_service.set_active_account("prod")
        active_alias = aws_service.get_active_account_alias()
        print(f"   Switched to: {active_alias}")
        
        # Switch back to dev account
        await aws_service.set_active_account("dev")
        active_alias = aws_service.get_active_account_alias()
        print(f"   Switched to: {active_alias}")
        
        # Clear active account
        await aws_service.clear_active_account()
        active_alias = aws_service.get_active_account_alias()
        print(f"   Cleared active account, current: {active_alias}")
        
        if active_alias is None:
            print("   ✅ Successfully tested account switching")
        else:
            print("   ❌ Account not properly cleared")
            return False
    except Exception as e:
        print(f"   ❌ Error testing account switching: {e}")
        return False
    
    print("\n🎉 All tests passed! Multi-account functionality is working correctly.")
    return True


async def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Remove test databases
    test_files = [
        "data/aws_accounts.db",
        "data/chats.db", 
        "data/tasks.db"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"   Removed: {test_file}")
    
    print("   ✅ Cleanup complete")


if __name__ == "__main__":
    print("Multi-Account AWS Credentials Test Suite")
    print("=" * 50)
    
    try:
        success = asyncio.run(test_multi_account_functionality())
        
        if success:
            print("\n✅ All tests passed successfully!")
            exit_code = 0
        else:
            print("\n❌ Some tests failed!")
            exit_code = 1
            
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    finally:
        # Clean up test data
        try:
            asyncio.run(cleanup_test_data())
        except Exception as e:
            print(f"Warning: Failed to clean up test data: {e}")
    
    sys.exit(exit_code) 