from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
import boto3
from botocore.config import Config
import base64
import io

class S3UploadBase64(Tool):
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
            's3',
            endpoint_url=self.runtime.credentials["S3_ENDPOINT"],
            aws_access_key_id=self.runtime.credentials["S3_ACCESS_KEY"],
            aws_secret_access_key=self.runtime.credentials["S3_SECRET_KEY"],
            config=Config(signature_version='s3v4', s3={"addressing_style": "path"}, retries={"max_attempts": 3}),
            verify=verify_param
        )
        bucket_name = self.runtime.credentials["BUCKET_NAME"]
        s3_key = tool_parameters.get("s3_key")
        if not s3_key:
            filename_param = tool_parameters.get("filename")
            if filename_param:
                s3_key = filename_param
        if not s3_key:
            yield self.create_text_message("Missing required parameter: s3_key or filename")
            return

        file_base64 = tool_parameters.get("file_base64")
        # 解码base64字符串
        binary_data = base64.b64decode(file_base64)
    
        # 创建文件对象
        file_obj = io.BytesIO(binary_data)
        self.s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            s3_key
        )
        yield self.create_text_message(f"Uploaded object '{s3_key}' to bucket '{bucket_name}'.")

        generate_presigned = bool(
            tool_parameters.get("generate_presigned_url") or tool_parameters.get("generate_presign_url")
        )
        expiration_raw = tool_parameters.get("presigned_expiration") or tool_parameters.get("presign_expiry")
        try:
            expiration = int(expiration_raw) if expiration_raw is not None else 3600
        except Exception:
            expiration = 3600

        if generate_presigned:
            try:
                presigned_url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )
                yield self.create_text_message(f"Presigned URL: {presigned_url}")
            except Exception as e:
                yield self.create_text_message(f"Failed to generate presigned URL: {e}")

    
