# User Guide of how to develop a Dify Plugin

Hi there, looks like you have already created a Plugin, now let's get you started with the development!

## Choose a Plugin type you want to develop

Before start, you need some basic knowledge about the Plugin types, Plugin supports to extend the following abilities in Dify:

- **Tool**: Tool Providers like Google Search, Stable Diffusion, etc. it can be used to perform a specific task.
- **Model**: Model Providers like OpenAI, Anthropic, etc. you can use their models to enhance the AI capabilities.
- **Endpoint**: Like Service API in Dify and Ingress in Kubernetes, you can extend a http service as an endpoint and control its logics using your own code.

Based on the ability you want to extend, we have divided the Plugin into three types: **Tool**, **Model**, and **Extension**.

- **Tool**: It's a tool provider, but not only limited to tools, you can implement an endpoint there, for example, you need both `Sending Message` and `Receiving Message` if you are building a Discord Bot, **Tool** and **Endpoint** are both required.
- **Model**: Just a model provider, extending others is not allowed.
- **Extension**: Other times, you may only need a simple http service to extend the functionalities, **Extension** is the right choice for you.

I believe you have chosen the right type for your Plugin while creating it, if not, you can change it later by modifying the `manifest.yaml` file.

### Manifest

Now you can edit the `manifest.yaml` file to describe your Plugin, here is the basic structure of it:

- version(version, required)：Plugin's version
- type(type, required)：Plugin's type, currently only supports `plugin`, future support `bundle`
- author(string, required)：Author, it's the organization name in Marketplace and should also equals to the owner of the repository
- label(label, required)：Multi-language name
- created_at(RFC3339, required)：Creation time, Marketplace requires that the creation time must be less than the current time
- icon(asset, required)：Icon path
- resource (object)：Resources to be applied
  - memory (int64)：Maximum memory usage, mainly related to resource application on SaaS for serverless, unit bytes
  - permission(object)：Permission application
    - tool(object)：Reverse call tool permission
      - enabled (bool)
  - model(object)：Reverse call model permission
    - enabled(bool)
    - llm(bool)
    - text_embedding(bool)
    - rerank(bool)
    - tts(bool)
    - speech2text(bool)
    - moderation(bool)
  - node(object)：Reverse call node permission
    - enabled(bool)
  - endpoint(object)：Allow to register endpoint permission
    - enabled(bool)
  - app(object)：Reverse call app permission
    - enabled(bool)
  - storage(object)：Apply for persistent storage permission
    - enabled(bool)
    - size(int64)：Maximum allowed persistent memory, unit bytes
- plugins(object, required)：Plugin extension specific ability yaml file list, absolute path in the plugin package, if you need to extend the model, you need to define a file like openai.yaml, and fill in the path here, and the file on the path must exist, otherwise the packaging will fail.
  - Format
    - tools(list[string]): Extended tool suppliers, as for the detailed format, please refer to [Tool Guide](https://docs.dify.ai/plugins/schema-definition/tool)
    - models(list[string])：Extended model suppliers, as for the detailed format, please refer to [Model Guide](https://docs.dify.ai/plugins/schema-definition/model)
    - endpoints(list[string])：Extended Endpoints suppliers, as for the detailed format, please refer to [Endpoint Guide](https://docs.dify.ai/plugins/schema-definition/endpoint)
  - Restrictions
    - Not allowed to extend both tools and models
    - Not allowed to have no extension
    - Not allowed to extend both models and endpoints
    - Currently only supports up to one supplier of each type of extension
- meta(object)
  - version(version, required)：manifest format version, initial version 0.0.1
  - arch(list[string], required)：Supported architectures, currently only supports amd64 arm64
  - runner(object, required)：Runtime configuration
    - language(string)：Currently only supports python
    - version(string)：Language version, currently only supports 3.12
    - entrypoint(string)：Program entry, in python it should be main

### Install Dependencies

- First of all, you need a Python 3.11+ environment, as our SDK requires that.
- Then, install the dependencies:

  ```bash
  pip install -r requirements.txt
  ```

- If you want to add more dependencies, you can add them to the `requirements.txt` file, once you have set the runner to python in the `manifest.yaml` file, `requirements.txt` will be automatically generated and used for packaging and deployment.

### Implement the Plugin

Now you can start to implement your Plugin, by following these examples, you can quickly understand how to implement your own Plugin:

- [OpenAI](https://github.com/langgenius/dify-plugin-sdks/tree/main/python/examples/openai): best practice for model provider
- [Google Search](https://github.com/langgenius/dify-plugin-sdks/tree/main/python/examples/google): a simple example for tool provider
- [Neko](https://github.com/langgenius/dify-plugin-sdks/tree/main/python/examples/neko): a funny example for endpoint group

### Test and Debug the Plugin

You may already noticed that a `.env.example` file in the root directory of your Plugin, just copy it to `.env` and fill in the corresponding values, there are some environment variables you need to set if you want to debug your Plugin locally.

- `INSTALL_METHOD`: Set this to `remote`, your plugin will connect to a Dify instance through the network.
- `REMOTE_INSTALL_HOST`: The host of your Dify instance, you can use our SaaS instance `https://debug.dify.ai`, or self-hosted Dify instance.
- `REMOTE_INSTALL_PORT`: The port of your Dify instance, default is 5003
- `REMOTE_INSTALL_KEY`: You should get your debugging key from the Dify instance you used, at the right top of the plugin management page, you can see a button with a `debug` icon, click it and you will get the key.

Run the following command to start your Plugin:

```bash
python -m main
```

Refresh the page of your Dify instance, you should be able to see your Plugin in the list now, but it will be marked as `debugging`, you can use it normally, but not recommended for production.

### Package the Plugin

After all, just package your Plugin by running the following command:

```bash
dify-plugin plugin package ./ROOT_DIRECTORY_OF_YOUR_PLUGIN
```

you will get a `plugin.difypkg` file, that's all, you can submit it to the Marketplace now, look forward to your Plugin being listed!


## User Privacy Policy

Please fill in the privacy policy of the plugin if you want to make it published on the Marketplace, refer to [PRIVACY.md](PRIVACY.md) for more details.

## S3 Tools Overview

This plugin provides four S3-related tools:

1. Upload (binary/file) -> `s3_upload_file`
2. Upload (base64) -> `s3_upload_base64`
3. Download (file) -> `s3_download_file`
4. Download (base64) -> `s3_download_base64`

### Common Credentials Required

You must configure the following credentials for the provider (already defined in `provider/botos3.yaml`):

- `DIFY_ENDPOINT`: Base URL of your Dify instance (used to resolve relative file URLs on upload)
- `S3_ENDPOINT`: S3-compatible service endpoint
- `S3_ACCESS_KEY` / `S3_SECRET_KEY`: Credentials
- `BUCKET_NAME`: Target bucket

### Shared Parameters (Download & Upload)

| Parameter | Type | Required | Applies | Description |
|-----------|------|----------|---------|-------------|
| `s3_key` | string | No | All | Explicit object key. If absent, `filename` may be used. |
| `filename` | string | No | All | Fallback key when `s3_key` not provided. Use plain name (optionally with path segments). |
| `generate_presigned_url` / `generate_presign_url` | boolean | No | All | If true, a presigned URL is appended after the normal output. |
| `presigned_expiration` / `presign_expiry` | number | No | All | Expiration seconds for presigned URL (default 3600). |

Upload-specific:

| Parameter | Type | Required | Tool | Description |
|-----------|------|----------|------|-------------|
| `file` | file | Yes | `s3_upload_file` | The binary file from Dify. |
| `file_base64` | string | Yes | `s3_upload_base64` | Base64-encoded content to upload. |

Download-specific:

| Parameter | Type | Required | Tool | Description |
|-----------|------|----------|------|-------------|
| `s3_key` / `filename` | string | One required | Both downloads | Key used to fetch object. |

### Behavior

`s3_upload_file` / `s3_upload_base64`:

1. Determine object key: `s3_key` > `filename` > error.
2. Upload content.
3. Emit confirmation message of successful upload.
4. If presign flag set, emit second message: `Presigned URL: <url>`.

`s3_download_file`:

1. Determine key (same precedence).
2. Return file binary as first message (or fallback public URL if file message fails).
3. If presign flag set, emit second message with presigned URL.

`s3_download_base64`:

1. Determine key.
2. Return base64 content as first message (with size warning if >5MB).
3. If presign flag set, emit second message with presigned URL.

### Notes & Best Practices

- Presigned URL is supplementary now (content always returned first). Use it to share externally or reduce repeated transfers.
- Consider using only presigned URLs for very large objects (set a size threshold in future enhancements).
- `filename` simplifies invocation; prefer `s3_key` for full path control (e.g., `reports/2025/summary.pdf`).
  (Public base URL no longer required; rely on presigned URLs when external sharing is needed.)
- Expiration defaults to 3600 seconds (1 hour); adjust according to security needs.

### TLS & Custom CA Bundle

If your S3-compatible storage uses an internal certificate authority, provide its PEM chain via the credential `S3_CA_BUNDLE` (added in `provider/botos3.yaml`). Each tool will:

1. Write the PEM contents to a temporary `.pem` file.
2. Pass its path to `boto3` as the `verify` parameter.
3. Fall back to system trust store if no bundle is supplied or temp file write fails.

You should NOT disable TLS verification (`verify=False`)—this plugin removed all insecure flags. A CA bundle keeps connections secure while accepting private certs.

Example PEM chain (concatenate root + intermediates):

```pem
-----BEGIN CERTIFICATE-----
<Root CA>
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
<Intermediate CA>
-----END CERTIFICATE-----
```

Troubleshooting:

- CERTIFICATE_VERIFY_FAILED: Missing internal CA -> Add full chain to `S3_CA_BUNDLE`.
- Hostname mismatch: Ensure endpoint URL matches certificate CN/SAN.
- Timeouts: Network/firewall issue; test with `curl` from same environment.

Security Checklist:

- Minimal IAM: `s3:GetObject`, `s3:PutObject`, `s3:HeadBucket` (and multipart if needed).
- Use presigned URLs with short expirations for sensitive objects.
  (No public URL credential—prefer presigned URLs over broad public bucket access.)

### Example Usage (Download File)

Using explicit key:

```yaml
tool: s3_download_file
parameters:
  s3_key: "reports/2025/summary.pdf"
```

Using filename shortcut:

```yaml
tool: s3_download_file
parameters:
  filename: "summary.pdf"
```

Add presigned URL (second message):

```yaml
tool: s3_download_file
parameters:
  s3_key: "reports/2025/summary.pdf"
  generate_presigned_url: true
  presigned_expiration: 900
```

### Example Usage (Download Base64)

```yaml
tool: s3_download_base64
parameters:
  s3_key: "images/logo.png"
```

With presigned URL appended:

```yaml
tool: s3_download_base64
parameters:
  filename: "logo.png"
  generate_presigned_url: true
```

### Example Usage (Upload File)

```yaml
tool: s3_upload_file
parameters:
  filename: "summary.pdf"
  file: <your file reference>
  generate_presigned_url: true
```

### Example Usage (Upload Base64)

```yaml
tool: s3_upload_base64
parameters:
  s3_key: "images/logo.png"
  file_base64: "<base64 data>"
  generate_presigned_url: true
```
