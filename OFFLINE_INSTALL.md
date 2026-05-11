# Windows 离线安装指南

本文档说明如何在 Windows 无网络环境下安装本项目依赖。

## 场景说明

本指南适用于以下场景:
- ✅ 可以通过 pip 下载 Python 包 (可访问 PyPI/镜像)
- ❌ 无法访问 HuggingFace 等模型网站下载模型

---

## 准备工作

### 1. 确定目标机器环境

- **操作系统**: Windows 10/11 (x64)
- **Python 版本**: 3.9 / 3.10 / 3.11 / 3.12
- **架构**: x86_64 (AMD64)

### 2. 准备一台有网络的构建机

在有网络的机器上下载所有依赖，再复制到目标机器。

---

## 第一部分: Python 环境依赖

### 需要下载的包列表

创建 `requirements.txt`:

```
sentence-transformers>=2.7.0
transformers>=4.51.0
torch
pymilvus>=2.4.0
chromadb>=0.4.0
fastapi
uvicorn
pydantic
jieba
```

### 在构建机上下载所有依赖

```powershell
# 创建虚拟环境
python -m venv offline_env
offline_env\Scripts\activate

# 下载所有依赖包 (包括子依赖)
pip download -r requirements.txt -d .\packages

# 同时下载 chromadb 的可选依赖
pip download chromadb -d .\packages
```

**重要**: 下载时需要指定目标平台的 wheel:

```powershell
pip download chromadb --platform win_amd64 --python-version 3.11 --implementation cp -d .\packages
```

---

## 第二部分: 系统依赖 (Windows 必须)

### 1. Microsoft Visual C++ Build Tools

**必须安装**，Chroma 的 `chroma-hnswlib` 需要编译:

1. 下载: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. 选择 "使用 C++ 的桌面开发" 工作负载
3. 安装后需要重启系统

**离线安装方法**:
- 下载 ISO 镜像 (需要 Visual Studio 订阅)
- 或使用 Windows Update 推送

### 2. Microsoft Visual C++ Redistributable

**必须安装**，Chroma 的 Rust 绑定需要运行时:

下载链接:
- VC++ 2015-2022 (x64): https://aka.ms/vs/17/release/vc_redist.x64.exe

**离线安装**:
```powershell
# 下载后复制到目标机器直接安装
vc_redist.x64.exe /install /quiet /norestart
```

---

## 第三部分: 嵌入模型

### 推荐: BGE Small (轻量, 中文优化)

| 模型 | 大小 | 下载链接 |
|------|------|---------|
| `BAAI/bge-small-zh-v1.5` | ~80MB | https://huggingface.co/BAAI/bge-small-zh-v1.5 |

### 下载步骤 (在可访问模型的机器上)

1. 在能访问 HuggingFace 的机器上安装 sentence-transformers:
```bash
pip install sentence-transformers
```

2. 首次运行会自动下载模型到缓存目录:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
```

3. 找到模型缓存路径:
```powershell
# macOS/Linux
ls ~/.cache/huggingface/hub/

# Windows
dir %USERPROFILE%\.cache\huggingface\hub\
```

4. 复制整个模型目录到目标机器的相同位置:
   ```
   源: C:\Users\<用户名>\.cache\huggingface\hub\models--BAAI--bge-small-zh-v1.5\
   目标: C:\Users\<用户名>\.cache\huggingface\hub\models--BAAI--bge-small-zh-v1.5\
   ```

### 手动下载 (通过镜像/代理)

如果无法直接访问 HuggingFace，可以尝试:

1. **HuggingFace 镜像站**:
   - https://hf-mirror.com (国内镜像)
   - 访问 https://hf-mirror.com/BAAI/bge-small-zh-v1.5 下载

2. **ModelScope (阿里)**:
   - https://modelscope.cn/models/AI-ModelScope/bge-small-zh-v1.5
   - 注册后可直接下载

3. **百度飞桨**:
   - 搜索 "bge-small-zh-v1.5"

### 验证模型

```powershell
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('BAAI/bge-small-zh-v1.5'); print(m.get_sentence_embedding_dimension())"
```

### 使用国产镜像源加载模型

如果在目标机器上无法访问 HuggingFace，但需要加载模型，可以:

1. **设置镜像环境变量**:
```powershell
set HF_ENDPOINT=https://hf-mirror.com
python search.py
```

2. **在 config.py 中修改**:
```python
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
```

3. **使用 ModelScope** (如果无法使用 HuggingFace 镜像):
```python
from modelscope import MsDataset
# 下载模型后复制到 HuggingFace 格式目录
```

---

## 第四部分: Chroma 特殊依赖 (如使用 Chroma)

### Chroma Windows 依赖清单

| 依赖 | 用途 | 安装方式 |
|------|------|---------|
| VC++ Build Tools | 编译 chroma-hnswlib | 需安装 |
| VC++ Redistributable | 运行 Rust 绑定 DLL | 需安装 |
| pybind11 | 编译 hnswlib | pip 安装 |
| hnswlib | 向量索引 | pip 安装 |

### Chroma 安装常见问题

**问题 1: 编译失败**
```
error: Microsoft Visual C++ 14.0 or greater is required
```
**解决**: 安装 Visual C++ Build Tools

**问题 2: DLL 加载失败**
```
ImportError: DLL load failed while importing chromadb_rust_bindings
```
**解决**: 安装 Visual C++ Redistributable

**问题 3: 依赖缺失**
```
ModuleNotFoundError: No module named 'pybind11'
```
**解决**:
```powershell
pip install pybind11 --no-build-isolation
pip install hnswlib --no-build-isolation
pip install chromadb
```

### Chroma 离线安装脚本

在目标机器上创建 `install_chroma.ps1`:

```powershell
# 安装 Visual C++ Redistributable (需要提前下载 vc_redist.x64.exe)
.\vc_redist.x64.exe /install /quiet /norestart

# 安装 pybind11 和 hnswlib (需要 Build Tools)
pip install pybind11 --no-build-isolation
pip install hnswlib --no-build-isolation

# 安装 chromadb (使用本地包)
pip install --no-index --find-links=.\packages chromadb
```

---

## 第五部分: 部署到目标机器

### 1. 复制文件

将以下内容复制到目标机器:

```
├── packages/           # Python 包目录
├── vc_redist.x64.exe  # VC++ 运行库
└── models/            # 嵌入模型 (可选)
```

### 2. 安装顺序

```powershell
# 1. 安装系统依赖
.\vc_redist.x64.exe /install /quiet /norestart

# 2. 安装 Python 依赖
pip install --no-index --find-links=.\packages -r requirements.txt

# 3. 安装嵌入模型 (可选，如果模型已预下载)
# 复制到 C:\Users\<用户名>\.cache\huggingface\hub\

# 4. 验证安装
python -c "import chromadb; print('Chroma OK')"
python -c "from sentence_transformers import SentenceTransformer; print('Model OK')"
```

---

## 第六部分: 验证测试

### 1. 基本验证

```powershell
# 测试 Chroma
python -c "import chromadb; client = chromadb.Client(); print('Chroma OK')"

# 测试 sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('BAAI/bge-small-zh-v1.5'); print(m)"

# 测试 Milvus (如使用)
python -c "from pymilvus import connections; connections.connect(host='localhost', port='19530'); print('Milvus OK')"
```

### 2. 运行索引脚本

```powershell
# 索引到 Chroma
python indexer_chroma.py

# 运行搜索服务
python search_chroma.py
```

---

## 常见问题

### Q: pip 安装失败，提示缺少某包

A: 使用 `pip download` 在构建机上下载完整依赖链:
```powershell
pip download chromadb -d .\packages --no-binary :all: --platform win_amd64
```

### Q: 模型加载失败

A: 检查模型路径:
```powershell
# 查看模型缓存位置
python -c "from sentence_transformers import SentenceTransformer; print(SentenceTransformer('BAAI/bge-small-zh-v1.5').tokenizer.name_or_path)"
```

### Q: Chroma 启动失败

A: 检查 VC++ 依赖:
```powershell
# 检查 VC++ Redistributable
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" -ErrorAction SilentlyContinue
```

---

## 快速检查清单

- [ ] Python 3.9+ 已安装
- [ ] Visual C++ Build Tools 已安装 (如需编译)
- [ ] Visual C++ Redistributable 已安装
- [ ] 所有 Python 包已下载并安装
- [ ] 嵌入模型已放置到正确位置
- [ ] 依赖验证通过