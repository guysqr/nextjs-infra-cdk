from aws_cdk import (
    core,
    aws_secretsmanager as secretsmanager,
)
import json


class GlobalSecretsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        web_infra = secretsmanager.Secret(
            self,
            "WebInfra",
            secret_name="WebInfra",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"DNS_HOSTNAME": "","ACM_ARN": ""}',
                generate_string_key="ACM_ARN",
            ),
        )

        core.CfnOutput(
            self,
            "WebInfraOutput",
            value=web_infra.secret_arn,
            export_name=self.stack_name + "-WebInfra",
        )
