from collections.abc import Generator
from typing import Any
import base64

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
import boto3
from botocore.config import Config


class S3UploadFile(Tool):
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
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.runtime.credentials["S3_ENDPOINT"],
            aws_access_key_id=self.runtime.credentials["S3_ACCESS_KEY"],
            aws_secret_access_key=self.runtime.credentials["S3_SECRET_KEY"],
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 3},
            ),
            verify=verify_param,
        )
        bucket_name = self.runtime.credentials.get(
            "BUCKET_NAME"
        ) or self.runtime.credentials.get("S3_BUCKET")
        if not bucket_name:
            yield self.create_text_message(
                "Missing bucket credential: BUCKET_NAME or S3_BUCKET"
            )
            return
        file = tool_parameters.get("file")
        s3_key = tool_parameters.get("s3_key")
        if not s3_key:
            filename_param = tool_parameters.get("filename")
            if filename_param:
                s3_key = filename_param
        if not s3_key:
            yield self.create_text_message(
                "Missing required parameter: s3_key or filename"
            )
            return

        if not file:
            yield self.create_text_message("Missing required parameter: file")
            return

        # Decode/prepare file content for upload
        if isinstance(file, bytes):
            file_content = file
        elif isinstance(file, str):
            # Try base64 decode; fallback to raw string bytes
            try:
                file_content = base64.b64decode(file)
            except Exception:
                file_content = file.encode("utf-8")
        elif isinstance(file, dict):
            # Expect dict like {"content": "<base64>", "name": "..."}
            content = file.get("content")
            if content:
                try:
                    file_content = base64.b64decode(content)
                except Exception:
                    file_content = content.encode("utf-8")
                else:
                    yield self.create_text_message("File dict missing 'content' field")
                return
        else:
            yield self.create_text_message("Unsupported file type")
            return

        # Upload to S3
        try:
            self.s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=file_content)
            yield self.create_text_message(
                f"File uploaded successfully to s3://{bucket_name}/{s3_key}"
            )
        except Exception as e:
            yield self.create_text_message(f"Upload failed: {str(e)}")
