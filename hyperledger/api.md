## 1. ResourceManager 类接口

### 文件管理接口

```python
# 添加文件
add_file(file_data: Dict) -> Optional[SharedFile]

# 删除文件
remove_file(file_id: int, owner_address: str = None) -> bool

# 更新文件信息
update_file(file_id: int, update_data: Dict, owner_address: str = None) -> Optional[SharedFile]

# 根据ID获取文件
get_file(file_id: int) -> Optional[SharedFile]
```



### 查询搜索接口

```python
# 根据所有者获取文件列表
get_files_by_owner(owner_address: str) -> List[SharedFile]

# 搜索文件（支持多条件）
search_files(keyword: str = None, category: str = None, 
             min_size: float = None, max_size: float = None,
             min_seeds: int = None) -> List[SharedFile]

# 获取所有文件
get_all_files() -> List[SharedFile]

# 获取所有活跃文件
get_active_files() -> List[SharedFile]

# 按分类统计文件
get_files_by_category() -> Dict[str, List[SharedFile]]

# 获取文件总数
get_file_count() -> int
```



### 文件状态接口

```python
# 更新种子数和peer数
update_seeds_peers(file_id: int, seeds_delta: int = 0, peers_delta: int = 0) -> bool
```



## 2. User 类接口

### 资源操作接口

```python
# 声明资源（上传文件）
declare_resources(file_data: Dict) -> bool

# 下载其他用户的资源
download_resource(file_id: int, downloader: 'User') -> bool
```



### 个人文件管理接口

```python
# 获取我的所有文件
get_my_files() -> List[SharedFile]

# 删除我的文件
remove_my_file(file_id: int) -> bool

# 更新我的文件信息
update_my_file(file_id: int, update_data: Dict) -> Optional[SharedFile]

# 搜索可用的文件
search_available_files(**kwargs) -> List[SharedFile]

# 获取所有可用的文件
get_all_available_files() -> List[SharedFile]
```



### 区块链操作接口

```python
# 参与挖矿
mine_block() -> Block

# 获取余额
get_balance() -> float
```



## 3. ResourceSharingSystem 类接口（主系统接口）

### 用户管理接口

```python
# 注册新用户
register_user(username: str) -> User

# 获取用户信息
get_user(username: str) -> Optional[User]
```



### 资源交易接口

```python
# 用户声明资源
declare_user_resources(username: str, file_data: Dict) -> bool

# 下载资源
download_resource(downloader_username: str, file_owner_username: str, file_id: int) -> bool
```



### 区块链操作接口

```python
# 用户挖矿
mine_block(miner_username: str) -> Block

# 获取用户余额
get_user_balance(username: str) -> float

# 获取区块链信息
get_blockchain_info() -> Dict
```



### 全局资源搜索接口

```python
# 全局搜索资源
search_resources(keyword: str = None, category: str = None, 
                min_size: float = None, max_size: float = None,
                min_seeds: int = None) -> List[SharedFile]

# 获取所有可用资源
get_all_resources() -> List[SharedFile]
```



## 4. SharedFile 数据结构

### 文件属性（只读）

```python
id: int                    # 文件唯一ID
name: str                  # 文件名
size_gb: float            # 文件大小（GB）
uploader: str             # 上传者用户名
seeds: int                # 种子数
peers: int                # peer数
description: str          # 文件描述
owner_address: str        # 所有者区块链地址
file_hash: str            # 文件哈希
category: str             # 文件分类
upload_time: float        # 上传时间戳
is_active: bool           # 是否活跃可用
```



### 工具方法

```python
# 转换为字典
to_dict() -> Dict

# 从字典创建对象
@classmethod
from_dict(cls, data: Dict) -> 'SharedFile'
```



## 5. 使用示例

### 文件数据结构示例

```python
file_data = {
    'name': "Python Programming Guide.pdf",
    'size_gb': 0.025,
    'uploader': "Alice",
    'seeds': 10,
    'peers': 2,
    'description': "Comprehensive guide to Python programming",
    'category': "document",
    'file_hash': "a1b2c3d4e5f6"
}
```



### 搜索条件示例

```python
# 按关键词搜索
results = system.search_resources(keyword="python")

# 按分类和大小搜索
results = system.search_resources(category="software", min_size=0.01, max_size=0.1)

# 按种子数搜索热门文件
results = system.search_resources(min_seeds=10)
```



### 更新文件示例

```python
update_data = {
    'description': "Updated description",
    'seeds': 15,
    'category': "updated_category"
}
user.update_my_file(file_id, update_data)
```

