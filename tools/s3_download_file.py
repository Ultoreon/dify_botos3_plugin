from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
import boto3
from botocore.config import Config
import io


class S3DownloadFile(Tool):
    """Download an object from S3 and return either the file content or a pre-signed URL."""

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        s3_client = boto3.client(
            's3',
            endpoint_url=self.runtime.credentials["S3_ENDPOINT"],
            aws_access_key_id=self.runtime.credentials["S3_ACCESS_KEY"],
            aws_secret_access_key=self.runtime.credentials["S3_SECRET_KEY"],
            config=Config(signature_version='s3v4'),
            verify=False,
        )
        bucket_name = self.runtime.credentials["BUCKET_NAME"]
        s3_key: str | None = tool_parameters.get("s3_key")
        if not s3_key:
            yield self.create_text_message("Missing required parameter: s3_key")
            return

        generate_presigned = bool(tool_parameters.get("generate_presigned_url"))
        expiration_raw = tool_parameters.get("presigned_expiration")
        try:
            expiration = int(expiration_raw) if expiration_raw is not None else 3600
        except Exception:
            expiration = 3600

        if generate_presigned:
            try:
                presigned_url = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )
                yield self.create_text_message(presigned_url)
            except Exception as e:
                yield self.create_text_message(f"Failed to generate presigned URL: {e}")
            return

        # Attempt to download the object
        try:
            obj = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            data = obj["Body"].read()
            content_type = obj.get("ContentType", "application/octet-stream")
            filename = s3_key.split("/")[-1] or "downloaded"
        except Exception as e:
            yield self.create_text_message(f"Failed to download object: {e}")
            return

        try:
            yield self.create_file_message(
                file_name=filename,
                content_type=content_type,
                file_bytes=io.BytesIO(data).getvalue(),
            )
        except Exception as e:
            public_base = self.runtime.credentials.get("S3_PUBLIC_URL")
            if public_base:
                yield self.create_text_message(f"{public_base.rstrip('/')}/{s3_key}")
            else:
                yield self.create_text_message(f"Downloaded but failed to create file message: {e}")
