# Nexus BT资源分享平台 - 后端文档

## 项目概述

Nexus是一个基于区块链技术的BT资源分享平台，采用信用积分系统管理资源上传和下载。用户可以通过上传资源、参与记账等方式获取信用积分，通过下载资源消耗信用积分。

## 技术架构

### 技术栈

- **后端框架**: Flask 2.3.3
- **CORS处理**: Flask-CORS 4.0.0
- **区块链**: Hyperledger Fabric (模拟实现)
- **开发语言**: Python 3.8+
- **API格式**: RESTful JSON

### 项目结构

text

```
backend/
├── app.py                 # 主应用文件
├── test_app.py           # 单元测试
├── test_app_fixed.py     # 修复版测试
├── simple_test.py        # 简化测试
└── __init__.py           # 包初始化文件
```



## 核心功能模块

### 1. 用户管理系统

- 用户注册与登录
- 身份认证 (JWT Token)
- 角色管理 (用户/管理员)

### 2. 信用积分系统

python

```
class CreditSystem:
    INITIAL_CREDIT = 10000    # 初始信用
    CREDIT_PER_GB = 1000      # 每GB对应信用
    MINING_REWARD = 50        # 挖矿奖励
    TIP_RATE = 0.001          # 小费比例
```



### 3. 资源管理系统

- 资源声明与上传
- 资源搜索与浏览
- 资源下载与积分扣除
- 资源举报与审核

### 4. 区块链集成

- 交易记录上链
- 信用积分管理
- 挖矿奖励机制

## API接口文档

### 认证相关接口

#### 用户注册

**端点**: `POST /api/register`

**请求体**:

json

```
{
    "username": "string",
    "password": "string"
}
```



**响应**:

json

```
{
    "message": "User {username} registered successfully!",
    "username": "string",
    "initial_credit": 10000
}
```



#### 用户登录

**端点**: `POST /api/login`

**请求体**:

json

```
{
    "username": "string",
    "password": "string"
}
```



**响应**:

json

```
{
    "token": "demo-token-for-{username}",
    "username": "string",
    "role": "user|administrator"
}
```



### 用户相关接口

#### 获取用户余额

**端点**: `GET /api/user/balance`

**请求头**:

text

```
Authorization: Bearer demo-token-for-{username}
```



**响应**:

json

```
{
    "username": "string",
    "balance": 10000
}
```



#### 获取用户文件

**端点**: `GET /api/user/my-files`

**请求头**:

text

```
Authorization: Bearer demo-token-for-{username}
```



**响应**:

json

```
{
    "files": [
        {
            "id": 1,
            "name": "string",
            "size_gb": 1.5,
            "uploader": "string",
            "seeds": 10,
            "peers": 2,
            "description": "string",
            "category": "document",
            "file_hash": "string",
            "status": 1
        }
    ],
    "total": 1
}
```



### 资源管理接口

#### 声明资源

**端点**: `POST /api/resources/declare`

**请求头**:

text

```
Authorization: Bearer demo-token-for-{username}
Content-Type: application/json
```



**请求体**:

json

```
{
    "file_data": {
        "name": "string",
        "size_gb": 1.5,
        "file_hash": "string",
        "description": "string",
        "category": "document|software|video|audio|other"
    }
}
```



**响应**:

json

```
{
    "message": "Resource declared successfully and pending approval",
    "status": "pending",
    "credit_when_approved": 1500
}
```



#### 下载资源

**端点**: `POST /api/resources/download`

**请求头**:

text

```
Authorization: Bearer demo-token-for-{username}
Content-Type: application/json
```



**请求体**:

json

```
{
    "file_id": 1,
    "file_owner": "string"
}
```



**响应**:

json

```
{
    "message": "Download successful",
    "file_id": 1
}
```



#### 获取资源列表

**端点**: `GET /api/resources`

**请求头**:

text

```
Authorization: Bearer demo-token-for-{username}
```



**响应**:

json

```
{
    "resources": [
        {
            "id": 1,
            "name": "string",
            "size_gb": 1.5,
            "uploader": "string",
            "seeds": 10,
            "peers": 2,
            "description": "string",
            "category": "document",
            "file_hash": "string",
            "status": 1
        }
    ],
    "total": 1
}
```



#### 搜索资源

**端点**: `GET /api/resources/search`

**查询参数**:

- `keyword` (可选): 搜索关键词
- `category` (可选): 资源分类
- `min_size` (可选): 最小文件大小(GB)
- `max_size` (可选): 最大文件大小(GB)
- `min_seeds` (可选): 最小种子数

**响应**: 同资源列表接口

#### 举报资源

**端点**: `POST /api/resources/report`

**请求头**:

text

```
Authorization: Bearer demo-token-for-{username}
Content-Type: application/json
```



**请求体**:

json

```
{
    "file_id": 1,
    "reason": "违规内容"
}
```



**响应**:

json

```
{
    "message": "File 1 has been reported and is under review",
    "action": "reported"
}
```



### 区块链相关接口

#### 挖矿

**端点**: `POST /api/mine`

**请求头**:

text

```
Authorization: Bearer demo-token-for-{username}
Content-Type: application/json
```



**响应**:

json

```
{
    "message": "Block mined successfully",
    "miner": "string",
    "mining_reward": 50,
    "block_hash": "string"
}
```



#### 系统统计

**端点**: `GET /api/system/stats`

**响应**:

json

```
{
    "total_users": 10,
    "blockchain_height": 5,
    "pending_transactions": 2,
    "current_difficulty": 2,
    "is_valid": true,
    "timestamp": 1234567890
}
```



## 数据模型

### 用户模型

python

```
@dataclass
class User:
    username: str
    password: str
    role: str  # "user" 或 "administrator"
```



### 文件模型

python

```
@dataclass
class FileData:
    name: str
    size_gb: float
    uploader: str
    seeds: int = 0
    peers: int = 0
    description: str = ""
    category: str = "other"
    file_hash: str = ""
    status: int = 0  # 0-挂起, 1-正常, 2-已审核, 3-下架
```



## 信用积分规则

### 获取信用

1. **初始信用**: 注册用户获得 10,000 信用
2. **上传奖励**: 每GB资源获得 1,000 信用
3. **挖矿奖励**: 每次成功挖矿获得 50 信用 + 交易小费

### 消耗信用

1. **下载成本**: 每GB资源消耗 1,000 信用
2. **矿工小费**: 下载成本的 0.1% (至少1信用)

### 计算公式

python

```
# 上传奖励
upload_reward = size_gb * 1000

# 下载成本
download_cost = size_gb * 1000
miner_tip = max(1, int(download_cost * 0.001))
total_cost = download_cost + miner_tip
```



## 资源状态流程

text

```
声明资源 (status=0)
    ↓
挖矿确认 → 正式发布 (status=1)
    ↓
用户下载 → 可能被举报 → 挂起审查 (status=1+举报标记)
    ↓
管理员审核 → 通过: 已审核 (status=2) / 不通过: 下架 (status=3)
```



## 错误处理

### 常见HTTP状态码

- `200`: 请求成功
- `201`: 资源创建成功
- `400`: 请求参数错误
- `401`: 未授权访问
- `404`: 资源未找到
- `500`: 服务器内部错误

### 错误响应格式

json

```
{
    "message": "错误描述信息"
}
```



## 部署和运行

### 环境要求

- Python 3.8+
- Flask 2.3.3
- Flask-CORS 4.0.0

### 安装依赖

bash

```
pip install flask flask-cors
```



### 运行应用

bash

```
cd backend
python app.py
```



应用将在 `http://localhost:5000` 启动

### 运行测试

bash

```
cd backend
python test_app_fixed.py
```



## 开发说明

### 代码规范

- 使用类型注解
- 遵循PEP8编码规范
- 使用dataclass定义数据结构
- 完整的错误处理

### 扩展建议

1. **数据库集成**: 使用SQLAlchemy替换内存存储
2. **安全增强**: 实现密码哈希、JWT Token过期机制
3. **文件存储**: 集成实际的文件存储系统
4. **区块链集成**: 替换为真实的Hyperledger Fabric网络
5. **缓存优化**: 添加Redis缓存提升性能

## 注意事项

1. 当前版本使用内存存储，重启后数据会丢失
2. 认证机制为简易实现，生产环境需要加强安全性
3. 文件哈希验证需要在实际文件传输中实现
4. 区块链部分为模拟实现，需要对接真实的Fabric网络

这个后端系统为Nexus BT资源分享平台提供了完整的API支持，包括用户管理、资源管理、信用系统和区块链集成等功能。