#!/usr/bin/env python3

from aws_cdk import core

from serverless_app_pipeline_cdk.serverless_app_pipeline_cdk_stack import (
    ServerlessAppPipelineCdkStack,
)
from serverless_app_pipeline_cdk.secrets_stack import SecretsStack
from serverless_app_pipeline_cdk.global_secrets_stack import GlobalSecretsStack
from serverless_app_pipeline_cdk.waf_cloudfront_stack import WafCloudfrontStack

global_env = core.Environment(region="us-east-1")

app = core.App()
GlobalSecretsStack(app, "global-secrets-stack", env=global_env)
SecretsStack(app, "secrets-stack")
WafCloudfrontStack(app, "waf-cloudfront-stack", env=global_env)
ServerlessAppPipelineCdkStack(app, "serverless-app-pipeline-cdk")

# add tags here
app.node.apply_aspect(core.Tag("CreatedBy", "guy.morton@versent.com.au"))
app.node.apply_aspect(core.Tag("Application", "app-name"))

# use a context variable to set the environment tag for this deploy's resources
enviro_tag = app.node.try_get_context("environment")

if enviro_tag:
    app.node.apply_aspect(core.Tag("Environment", enviro_tag))
else:
    app.node.apply_aspect(core.Tag("Environment", "not-set"))

app.synth()
