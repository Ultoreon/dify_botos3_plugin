from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
import boto3
from botocore.config import Config
import base64
import logging


class S3DownloadBase64(Tool):
    """Download an object from S3 and return its base64-encoded content, or a pre-signed URL."""

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        verify_param = True
        ca_bundle_text = self.runtime.credentials.get("S3_CA_BUNDLE")
        if ca_bundle_text:
            import tempfile
            try:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
                tmp.write(ca_bundle_text.encode("utf-8"))
                tmp.flush()
                tmp.close()
                verify_param = tmp.name
            except Exception:
                verify_param = True
        s3_client = boto3.client(
            's3',
            endpoint_url=self.runtime.credentials["S3_ENDPOINT"],
            aws_access_key_id=self.runtime.credentials["S3_ACCESS_KEY"],
            aws_secret_access_key=self.runtime.credentials["S3_SECRET_KEY"],
            config=Config(signature_version='s3v4', s3={"addressing_style": "path"}, retries={"max_attempts": 3}),
            verify=verify_param,
        )
        bucket_name = self.runtime.credentials["BUCKET_NAME"]
        s3_key: str | None = tool_parameters.get("s3_key")
        if not s3_key:
            filename_param = tool_parameters.get("filename")
            if filename_param:
                s3_key = filename_param
        if not s3_key:
            yield self.create_text_message("Missing required parameter: s3_key or filename")
            return

        generate_presigned = bool(
            tool_parameters.get("generate_presigned_url") or tool_parameters.get("generate_presign_url")
        )
        expiration_raw = tool_parameters.get("presigned_expiration") or tool_parameters.get("presign_expiry")
        try:
            expiration = int(expiration_raw) if expiration_raw is not None else 3600
        except Exception:
            expiration = 3600

        try:
            obj = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            data = obj["Body"].read()
            size = len(data)
            self.logger.info(f"Downloaded S3 object bucket={bucket_name} key={s3_key} size={size} bytes")
        except Exception as e:
            yield self.create_text_message(f"Failed to download object: {e}")
            return
        yield self.create_text_message(f"Downloaded object '{s3_key}' ({size} bytes). Encoding to base64...")
        # Warning for large objects (arbitrary threshold 5MB)
        if len(data) > 5 * 1024 * 1024:
            yield self.create_text_message("Warning: object larger than 5MB; base64 output may be very long.")
        encoded = base64.b64encode(data).decode('utf-8')
        yield self.create_text_message(encoded)

        if generate_presigned:
            try:
                presigned_url = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )
                yield self.create_text_message(f"Presigned URL: {presigned_url}")
            except Exception as e:
                yield self.create_text_message(f"Failed to generate presigned URL: {e}")
