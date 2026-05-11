# 离线安装指南

本文档说明如何在无网络环境下安装依赖和模型。

## 需要下载的资源

### 1. Python 依赖包

从以下地址下载 whl 文件:

- **PyPI**: https://pypi.org/simple/
- **第三方镜像**:
  - 阿里云: https://mirrors.aliyun.com/pypi/simple/
  - 清华: https://pypi.tuna.tsinghua.edu.cn/simple/

**必需包列表** (见 `requirements.txt`):
```
sentence-transformers>=2.7.0
transformers>=4.51.0
torch
pymilvus>=2.4.0
chromadb>=0.4.0
fastapi
uvicorn
pydantic
```

### 2. 嵌入模型

#### 推荐: BGE Small (轻量, 中文优化)

| 模型 | 大小 | 下载链接 |
|------|------|---------|
| `BAAI/bge-small-zh-v1.5` | ~80MB | https://huggingface.co/BAAI/bge-small-zh-v1.5 |

**下载方式:**
```bash
# 方法 1: 使用 huggingface-cli (需要网络一次)
huggingface-cli download BAAI/bge-small-zh-v1.5

# 方法 2: 直接下载 (推荐)
# 访问 https://huggingface.co/BAAI/bge-small-zh-v1.5/tree/main
# 下载以下文件到 ~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5/
```

**需要下载的文件:**
```
config.json
config_sentence_transformers.json
model.safetensors
model_config.json
README.md
sentence_bert_config.json
tokenizer.json
tokenizer_config.json
vocab.txt
1_Pooling/config.json
```

#### 可选: BGE Base (中等精度)

| 模型 | 大小 | 下载链接 |
|------|------|---------|
| `BAAI/bge-base-zh-v1.5` | ~170MB | https://huggingface.co/BAAI/bge-base-zh-v1.5 |

#### 可选: Qwen3 Embedding

| 模型 | 大小 | 下载链接 |
|------|------|---------|
| `Qwen/Qwen3-Embedding-0.6B` | ~1.2GB | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B |

## 离线安装步骤

### 步骤 1: 准备 Python 包

在有网络的机器上下载包:
```bash
pip download -r requirements.txt -d ./packages
```

将 `./packages` 目录复制到目标机器:
```bash
pip install --no-index --find-links=./packages -r requirements.txt
```

### 步骤 2: 准备模型文件

**方式 A: 使用模型缓存目录**

1. 在有网络的机器上首次运行脚本 (会自动下载模型):
```bash
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5')"
```

2. 找到模型缓存目录:
```bash
# macOS
ls -la ~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5/

# Linux
ls -la ~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5/
```

3. 复制整个目录到目标机器的相同位置

**方式 B: 直接下载模型文件**

访问以下链接手动下载:

1. BGE Small (推荐):
   - https://huggingface.co/BAAI/bge-small-zh-v1.5/tree/main

2. 解压后放置到:
   ```
   ~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5/
   ```

### 步骤 3: 验证安装

```bash
# 验证 Python 包
python3 -c "import sentence_transformers; print('OK')"

# 验证模型加载 (离线模式)
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
print('Model loaded:', model.get_sentence_embedding_dimension())
"
```

### 步骤 4: 验证向量搜索

```bash
# 测试中文语义搜索
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
vec = model.encode('你好世界')
print('Vector shape:', vec.shape)
print('中文嵌入测试通过!')
"
```

## 模型文件结构示例

```
~/.cache/huggingface/hub/
└── models--BAAI--bge-small-zh-v1.5/
    ├── blobs/
    │   ├── model.safetensors (主模型文件, ~80MB)
    │   └── ...
    ├── refs/
    │   └── main
    ├── snapshots/
    │   └── xxxxxxxxxxxx/
    │       ├── config.json
    │       ├── model.safetensors -> ../../blobs/model.safetensors
    │       ├── tokenizer.json
    │       └── ...
    └── .gitattributes
```

## 常见问题

### Q: 模型下载太慢怎么办?

A: 使用国内镜像或使用 Download Files 功能逐个下载:
```bash
# 使用镜像站
HF_ENDPOINT=https://hf-mirror.com huggingface-cli download BAAI/bge-small-zh-v1.5
```

### Q: 离线后模型仍然无法加载?

A: 检查以下几点:
1. 模型路径是否正确
2. 文件权限是否足够
3. 确认模型版本匹配 (检查 config.json 中的 model_type)

### Q: 如何查看模型缓存位置?

A:
```bash
python3 -c "from sentence_transformers import SentenceTransformer; print(SentenceTransformer('BAAI/bge-small-zh-v1.5').tokenizer.name_or_path)"
```