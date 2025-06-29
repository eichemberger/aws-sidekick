import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import logging

import boto3

try:
    import aioboto3
except ImportError:
    aioboto3 = None

from botocore.exceptions import NoCredentialsError, ClientError, BotoCoreError
from core.ports.outbound.aws_client_port import AWSClientPort
from core.domain.value_objects.aws_credentials import AWSCredentials, AWSAccountInfo

logger = logging.getLogger(__name__)


class AWSClientAdapter(AWSClientPort):
    """AWS client adapter with proper async implementation"""

    def __init__(self):
        self._use_aioboto3 = aioboto3 is not None
        self._session_cache: Dict[str, Any] = {}
        self._connection_semaphore = asyncio.Semaphore(10)  # Limit concurrent connections
        
        if not self._use_aioboto3:
            logger.warning(
                "aioboto3 not available, falling back to boto3 with thread pool. "
                "Install aioboto3 for better async performance: pip install aioboto3"
            )

    @asynccontextmanager
    async def _get_client(self, service: str, credentials: AWSCredentials, region: str = None):
        """Get an AWS client with proper async context management"""
        async with self._connection_semaphore:
            if self._use_aioboto3:
                session = self._create_aioboto3_session(credentials)
                async with session.client(
                    service, 
                    region_name=region or credentials.region
                ) as client:
                    yield client
            else:
                # Fallback to boto3 with thread pool (but improved)
                session = self._create_boto3_session(credentials)
                client = session.client(service, region_name=region or credentials.region)
                try:
                    yield client
                finally:
                    # Close client if it has a close method
                    if hasattr(client, 'close'):
                        client.close()

    async def _execute_aws_operation(self, operation_func, *args, **kwargs):
        """Execute AWS operation with proper error handling and retries"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if self._use_aioboto3:
                    # Native async operation
                    return await operation_func(*args, **kwargs)
                else:
                    # Improved thread pool execution with timeout
                    return await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, operation_func, *args, **kwargs
                        ),
                        timeout=30.0  # 30 second timeout
                    )
            except (ClientError, BotoCoreError) as e:
                error_code = getattr(e.response.get('Error', {}), 'Code', None) if hasattr(e, 'response') else None
                
                # Don't retry on auth/permission errors
                if error_code in ['AccessDenied', 'UnauthorizedOperation', 'InvalidUserID.NotFound']:
                    raise
                
                # Retry on throttling or temporary errors
                if attempt < max_retries - 1 and error_code in ['Throttling', 'RequestLimitExceeded', 'ServiceUnavailable']:
                    logger.warning(f"AWS operation failed (attempt {attempt + 1}), retrying in {retry_delay}s: {e}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                
                raise
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    logger.warning(f"AWS operation timed out (attempt {attempt + 1}), retrying...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise RuntimeError("AWS operation timed out after multiple retries")
            except Exception as e:
                logger.error(f"Unexpected error in AWS operation: {e}")
                raise

    async def validate_credentials(self, credentials: AWSCredentials) -> bool:
        """Validate AWS credentials"""
        try:
            async with self._get_client('sts', credentials) as sts:
                if self._use_aioboto3:
                    await sts.get_caller_identity()
                else:
                    await self._execute_aws_operation(sts.get_caller_identity)
            return True
        except (NoCredentialsError, ClientError):
            return False
        except Exception as e:
            logger.error(f"Error validating credentials: {e}")
            return False

    async def get_caller_identity(self, credentials: AWSCredentials) -> AWSAccountInfo:
        """Get AWS caller identity information"""
        async with self._get_client('sts', credentials) as sts:
            if self._use_aioboto3:
                response = await sts.get_caller_identity()
            else:
                response = await self._execute_aws_operation(sts.get_caller_identity)
            
            return AWSAccountInfo(
                account_id=response['Account'],
                user_arn=response['Arn'],
                region=credentials.region
            )

    async def list_ec2_instances(self, credentials: AWSCredentials, region: str = None) -> List[Dict[str, Any]]:
        """List EC2 instances"""
        async with self._get_client('ec2', credentials, region) as ec2:
            if self._use_aioboto3:
                response = await ec2.describe_instances()
            else:
                response = await self._execute_aws_operation(ec2.describe_instances)
            
            instances = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'PublicIpAddress': instance.get('PublicIpAddress'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress'),
                        'Tags': instance.get('Tags', []),
                        'LaunchTime': instance['LaunchTime'].isoformat() if 'LaunchTime' in instance else None
                    })
            
            return instances

    async def list_rds_instances(self, credentials: AWSCredentials, region: str = None) -> List[Dict[str, Any]]:
        """List RDS instances"""
        async with self._get_client('rds', credentials, region) as rds:
            if self._use_aioboto3:
                response = await rds.describe_db_instances()
            else:
                response = await self._execute_aws_operation(rds.describe_db_instances)
            
            instances = []
            for instance in response.get('DBInstances', []):
                instances.append({
                    'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
                    'DBInstanceClass': instance['DBInstanceClass'],
                    'Engine': instance['Engine'],
                    'DBInstanceStatus': instance['DBInstanceStatus'],
                    'AllocatedStorage': instance['AllocatedStorage'],
                    'PubliclyAccessible': instance['PubliclyAccessible'],
                    'MultiAZ': instance['MultiAZ']
                })
            
            return instances

    async def list_s3_buckets(self, credentials: AWSCredentials) -> List[Dict[str, Any]]:
        """List S3 buckets"""
        async with self._get_client('s3', credentials) as s3:
            if self._use_aioboto3:
                response = await s3.list_buckets()
            else:
                response = await self._execute_aws_operation(s3.list_buckets)
            
            buckets = []
            for bucket in response.get('Buckets', []):
                bucket_info = {
                    'Name': bucket['Name'],
                    'CreationDate': bucket['CreationDate'].isoformat(),
                    'Region': 'us-east-1'  # Default
                }
                
                # Get bucket location (with error handling)
                try:
                    if self._use_aioboto3:
                        location_response = await s3.get_bucket_location(Bucket=bucket['Name'])
                    else:
                        location_response = await self._execute_aws_operation(
                            s3.get_bucket_location, Bucket=bucket['Name']
                        )
                    bucket_info['Region'] = location_response.get('LocationConstraint') or 'us-east-1'
                except ClientError as e:
                    logger.warning(f"Could not get location for bucket {bucket['Name']}: {e}")
                    bucket_info['Region'] = 'unknown'
                
                buckets.append(bucket_info)
            
            return buckets

    async def get_cost_and_usage(self, credentials: AWSCredentials, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get cost and usage data"""
        async with self._get_client('ce', credentials, 'us-east-1') as ce:  # Cost Explorer is only in us-east-1
            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Granularity': 'DAILY',
                'Metrics': ['BlendedCost'],
                'GroupBy': [
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            }
            
            if self._use_aioboto3:
                response = await ce.get_cost_and_usage(**params)
            else:
                response = await self._execute_aws_operation(
                    lambda: ce.get_cost_and_usage(**params)
                )
            
            return response

    async def describe_security_groups(self, credentials: AWSCredentials, region: str = None) -> List[Dict[str, Any]]:
        """Describe security groups"""
        async with self._get_client('ec2', credentials, region) as ec2:
            if self._use_aioboto3:
                response = await ec2.describe_security_groups()
            else:
                response = await self._execute_aws_operation(ec2.describe_security_groups)
            
            security_groups = []
            for sg in response.get('SecurityGroups', []):
                security_groups.append({
                    'GroupId': sg['GroupId'],
                    'GroupName': sg['GroupName'],
                    'Description': sg['Description'],
                    'VpcId': sg.get('VpcId'),
                    'IpPermissions': sg['IpPermissions'],
                    'IpPermissionsEgress': sg['IpPermissionsEgress'],
                    'Tags': sg.get('Tags', [])
                })
            
            return security_groups

    def _create_aioboto3_session(self, credentials: AWSCredentials):
        """Create aioboto3 session from credentials"""
        if credentials.uses_profile():
            return aioboto3.Session(
                profile_name=credentials.profile,
                region_name=credentials.region
            )
        else:
            return aioboto3.Session(
                aws_access_key_id=credentials.access_key_id,
                aws_secret_access_key=credentials.secret_access_key,
                aws_session_token=credentials.session_token,
                region_name=credentials.region
            )

    def _create_boto3_session(self, credentials: AWSCredentials) -> boto3.Session:
        """Create boto3 session from credentials (fallback)"""
        if credentials.uses_profile():
            return boto3.Session(
                profile_name=credentials.profile,
                region_name=credentials.region
            )
        else:
            return boto3.Session(
                aws_access_key_id=credentials.access_key_id,
                aws_secret_access_key=credentials.secret_access_key,
                aws_session_token=credentials.session_token,
                region_name=credentials.region
            )

    async def cleanup(self):
        """Cleanup resources"""
        self._session_cache.clear()
        # Additional cleanup can be added here if needed 