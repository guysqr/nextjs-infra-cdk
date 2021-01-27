from aws_cdk import (
    core,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_secretsmanager as secretsmanager,
    aws_wafv2 as wafv2,
    aws_certificatemanager as acm,
)
import json
import jsii

# this is needed to fix a bug in CDK
@jsii.implements(wafv2.CfnRuleGroup.IPSetReferenceStatementProperty)
class IPSetReferenceStatement:
    @property
    def arn(self):
        return self._arn

    @arn.setter
    def arn(self, value):
        self._arn = value


class WafCloudfrontStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        web_infra_secret_arn = core.Fn.import_value("global-secrets-stack-WebInfra")
        # This cert needs to be created in us-east-1, and the hostname aliases should be covered by it
        your_cloudfront_certificate_arn = core.SecretValue.secrets_manager(
            web_infra_secret_arn, json_field="ACM_ARN"
        ).to_string()

        your_cloudfront_hostname_aliases = [
            core.SecretValue.secrets_manager(
                web_infra_secret_arn, json_field="DNS_HOSTNAME"
            ).to_string()
        ]

        # AWS WAF, for use with Cloudfront
        # ip_ref_statement_guy = IPSetReferenceStatement()
        # ip_ref_statement_guy.arn = (
        #     "arn:aws:wafv2:us-east-1:123456789:global/ipset/guys-house/a64b4255-25ee-4596-b01d-e886f2f4bb7b"
        # )
        # ip_statement_guy = wafv2.CfnWebACL.StatementOneProperty(ip_set_reference_statement=ip_ref_statement_guy)

        waf = wafv2.CfnWebACL(
            self,
            "CloudFrontWebACL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope="CLOUDFRONT",
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="WAF",
                sampled_requests_enabled=True,
            ),
            rules=[
                # wafv2.CfnWebACL.RuleProperty(
                #     name="guys-ip",
                #     priority=0,
                #     action=wafv2.CfnWebACL.RuleActionProperty(allow={}),
                #     visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                #         sampled_requests_enabled=True,
                #         cloud_watch_metrics_enabled=True,
                #         metric_name="allow-guys-ip",
                #     ),
                #     statement=ip_statement_guy,
                # ),
                wafv2.CfnWebACL.RuleProperty(
                    name="AWS-AWSManagedRulesCommonRuleSet",
                    priority=2,
                    statement=wafv2.CfnWebACL.StatementOneProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS", name="AWSManagedRulesCommonRuleSet"
                        )
                    ),
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWS-AWSManagedRulesCommonRuleSet",
                    ),
                ),
                wafv2.CfnWebACL.RuleProperty(
                    name="AWS-AWSManagedRulesAmazonIpReputationList",
                    priority=3,
                    statement=wafv2.CfnWebACL.StatementOneProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesAmazonIpReputationList",
                        )
                    ),
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWS-AWSManagedRulesAmazonIpReputationList",
                    ),
                ),
                wafv2.CfnWebACL.RuleProperty(
                    name="AWS-AWSManagedRulesKnownBadInputsRuleSet",
                    priority=4,
                    statement=wafv2.CfnWebACL.StatementOneProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesKnownBadInputsRuleSet",
                        )
                    ),
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWS-AWSManagedRulesKnownBadInputsRuleSet",
                    ),
                ),
            ],
        )
        # Static web bucket and CloudFront distribution
        s3_bucket_source = s3.Bucket(
            self,
            "WhtsqrNextBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        oai = cloudfront.OriginAccessIdentity(
            self, "OAI", comment="Connects CF with S3"
        )
        s3_bucket_source.grant_read(oai)

        distribution = cloudfront.CloudFrontWebDistribution(
            self,
            "WhtsqrNextDistribution",
            web_acl_id=waf.attr_arn,
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=s3_bucket_source, origin_access_identity=oai
                    ),
                    behaviors=[cloudfront.Behavior(is_default_behavior=True)],
                )
            ],
            viewer_certificate=cloudfront.ViewerCertificate.from_acm_certificate(
                acm.Certificate.from_certificate_arn(
                    self,
                    "CFCert",
                    certificate_arn=your_cloudfront_certificate_arn,
                ),
                aliases=your_cloudfront_hostname_aliases,
                security_policy=cloudfront.SecurityPolicyProtocol.TLS_V1,
                ssl_method=cloudfront.SSLMethod.SNI,
            ),
        )

        core.CfnOutput(
            self,
            "WhtsqrNextDistributionOutput",
            value=distribution.distribution_id,
            export_name=self.stack_name + ":WhtsqrNextDistributionId",
        )

        core.CfnOutput(
            self,
            "WhtsqrNextBucketOutput",
            value=s3_bucket_source.bucket_name,
            export_name=self.stack_name + ":WhtsqrNextBucket",
        )