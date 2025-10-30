from typing import Any
import tempfile

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
import boto3
from botocore.config import Config

class Botos3Provider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            """
            IMPLEMENT YOUR VALIDATION HERE
            """
            required_keys = ["S3_ENDPOINT", "S3_ACCESS_KEY", "S3_SECRET_KEY", "BUCKET_NAME"]
            for key in required_keys:
                if key not in credentials:
                    raise ToolProviderCredentialValidationError(f"Missing required credential: {key}")
            verify_param = False
            ca_bundle_text = credentials.get("S3_CA_BUNDLE")
            if ca_bundle_text:
                try:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
                    tmp.write(ca_bundle_text.encode("utf-8"))
                    tmp.flush()
                    tmp.close()
                    verify_param = tmp.name
                except Exception:
                    verify_param = False

            config = Config(signature_version="s3v4", s3={"addressing_style": "path"}, retries={"max_attempts": 2})
            s3_client = boto3.client(
                's3',
                endpoint_url=credentials["S3_ENDPOINT"],
                aws_access_key_id=credentials["S3_ACCESS_KEY"],
                aws_secret_access_key=credentials["S3_SECRET_KEY"],
                verify=verify_param,
                config=config,
            )
            # Use head_bucket (requires less permission than listing objects)
            s3_client.head_bucket(Bucket=credentials["BUCKET_NAME"])
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
