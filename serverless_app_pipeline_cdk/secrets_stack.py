from aws_cdk import (
    core,
    aws_secretsmanager as secretsmanager,
)
import json


class SecretsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        github_oauth = secretsmanager.Secret(
            self,
            "GithubOauth",
            secret_name="GithubOAuthToken",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template="{}", generate_string_key="TOKEN"
            ),
        )

        deploy_env_vars = secretsmanager.Secret(
            self,
            "DeployEnvVars",
            secret_name="DeployEnvVars",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"STATIC_NEXTJS_BUCKET": "","PRECREATED_CLOUDFRONT_ID": ""}',
                generate_string_key="STATIC_NEXTJS_BUCKET",
            ),
        )

        core.CfnOutput(
            self,
            "GithubOauthOutput",
            value=github_oauth.secret_arn,
            export_name=self.stack_name + "-GithubOAuthToken",
        )

        core.CfnOutput(
            self,
            "DeployEnvVarsOutput",
            value=deploy_env_vars.secret_arn,
            export_name=self.stack_name + "-DeployEnvVars",
        )
