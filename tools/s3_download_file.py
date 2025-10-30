from collections.abc import Generator
from typing import Any
import base64

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
import boto3
from botocore.config import Config
import io


class S3DownloadFile(Tool):
    """Download an object from S3 and return either the file content or a pre-signed URL."""

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        verify_param = False
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
                verify_param = False
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
            # Fallback to filename parameter
            filename_param = tool_parameters.get("filename")
            if filename_param:
                s3_key = filename_param
        if not s3_key:
            yield self.create_text_message("Missing required parameter: s3_key or filename")
            return

        # Support both naming styles (generate_presigned_url vs generate_presign_url)
        generate_presigned = bool(
            tool_parameters.get("generate_presigned_url") or tool_parameters.get("generate_presign_url")
        )
        # Support both presigned_expiration and presign_expiry
        expiration_raw = tool_parameters.get("presigned_expiration") or tool_parameters.get("presign_expiry")
        try:
            expiration = int(expiration_raw) if expiration_raw is not None else 3600
        except Exception:
            expiration = 3600

        # Download with debug
        try:
            yield self.create_text_message(f"Downloading key='{s3_key}' from bucket='{bucket_name}'...")
            obj = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            data = obj["Body"].read()
            size = len(data)
            content_type = obj.get("ContentType", "application/octet-stream")
            filename = s3_key.split("/")[-1] or "downloaded"
            yield self.create_text_message(f"Downloaded bytes={size} content_type={content_type}")
        except Exception as e:
            yield self.create_text_message(f"Failed to download object: {e}")
            return

        if size == 0:
            yield self.create_text_message("Object is empty (0 bytes). Nothing to return.")
            return

        # Try file message
        try:
            yield self.create_file_message(
                file_name=filename,
                content_type=content_type,
                file_bytes=data,
            )
        except Exception as e:
            # Fallback: emit base64 in text so workflow has output
            b64 = base64.b64encode(data).decode("utf-8")
            yield self.create_text_message(
                f"Downloaded object but failed to create file message: {e}. Base64 (truncated 200 chars): {b64[:200]}"
            )

        # Optional presigned
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

        # Final summary (ensures text field populated)
        yield self.create_text_message(f"Success: key='{s3_key}' size={size} bytes returned.")
