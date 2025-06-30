from typing import List, Dict, Any
from datetime import datetime
from core.domain.entities.aws_resource import ResourceType
from core.domain.value_objects.aws_credentials import AWSCredentials, AWSAccountInfo
from core.ports.outbound.aws_client_port import AWSClientPort
from core.ports.outbound.agent_repository_port import AgentRepositoryPort


class AWSAnalysisUseCase:
    """Use case for AWS resource analysis"""

    def __init__(
        self,
        aws_client: AWSClientPort,
        agent_repository: AgentRepositoryPort
    ):
        self._aws_client = aws_client
        self._agent_repository = agent_repository

    async def validate_credentials(self, credentials: AWSCredentials) -> bool:
        """Validate AWS credentials"""
        return await self._aws_client.validate_credentials(credentials)

    async def get_account_info(self, credentials: AWSCredentials) -> AWSAccountInfo:
        """Get AWS account information"""
        if not await self._aws_client.validate_credentials(credentials):
            raise ValueError("Invalid AWS credentials")
        
        return await self._aws_client.get_caller_identity(credentials)

    async def analyze_resources(self, credentials: AWSCredentials, resource_type: ResourceType = None) -> Dict[str, Any]:
        """Analyze AWS resources and provide insights"""
        
        analysis_results = {
            "account_info": await self.get_account_info(credentials),
            "resources": {},
            "recommendations": [],
            "security_findings": [],
            "cost_insights": {}
        }

        if resource_type is None:
            for rt in ResourceType:
                analysis_results["resources"][rt.value] = await self._collect_resource_data(credentials, rt)
        else:
            analysis_results["resources"][resource_type.value] = await self._collect_resource_data(credentials, resource_type)

        context = {
            "account_info": analysis_results["account_info"],
            "resources": analysis_results["resources"]
        }
        
        insights_prompt = self._build_analysis_prompt(analysis_results["resources"])
        insights = await self._agent_repository.execute_prompt(insights_prompt, context)
        
        analysis_results["ai_insights"] = insights

        return analysis_results

    async def analyze_costs(self, credentials: AWSCredentials, days: int = 30) -> Dict[str, Any]:
        """Analyze AWS costs"""
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cost_data = await self._aws_client.get_cost_and_usage(
            credentials,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        cost_analysis_prompt = f"""
        Analyze the following AWS cost data and provide insights:
        
        Cost Data: {cost_data}
        
        Please provide:
        1. Cost trends and patterns
        2. Top cost drivers
        3. Optimization opportunities
        4. Budget recommendations
        """
        
        ai_analysis = await self._agent_repository.execute_prompt(cost_analysis_prompt, {"cost_data": cost_data})
        
        return {
            "raw_data": cost_data,
            "analysis": ai_analysis,
            "period": f"{days} days",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

    async def security_audit(self, credentials: AWSCredentials) -> Dict[str, Any]:
        """Perform security audit of AWS resources"""
        
        security_data = {
            "security_groups": await self._aws_client.describe_security_groups(credentials),
        }

        security_prompt = f"""
        Perform a security audit of the following AWS configuration:
        
        Security Groups: {security_data['security_groups']}
        
        Please identify:
        1. Security vulnerabilities
        2. Overly permissive rules
        3. Best practice violations
        4. Recommended remediation steps
        """

        security_analysis = await self._agent_repository.execute_prompt(security_prompt, security_data)

        return {
            "raw_data": security_data,
            "findings": security_analysis,
            "audit_date": datetime.now().isoformat()
        }

    async def _collect_resource_data(self, credentials: AWSCredentials, resource_type: ResourceType) -> List[Dict[str, Any]]:
        """Collect data for a specific resource type"""
        
        if resource_type == ResourceType.EC2_INSTANCE:
            return await self._aws_client.list_ec2_instances(credentials)
        elif resource_type == ResourceType.RDS_INSTANCE:
            return await self._aws_client.list_rds_instances(credentials)
        elif resource_type == ResourceType.S3_BUCKET:
            return await self._aws_client.list_s3_buckets(credentials)
        else:
            return []

    def _build_analysis_prompt(self, resources: Dict[str, Any]) -> str:
        """Build analysis prompt for AI agent"""
        return f"""
        Analyze the following AWS infrastructure:
        
        Resources: {resources}
        
        Please provide:
        1. Infrastructure overview and architecture assessment
        2. Resource utilization analysis
        3. Performance optimization opportunities
        4. Security considerations
        5. Cost optimization recommendations
        6. Best practices compliance
        """ 