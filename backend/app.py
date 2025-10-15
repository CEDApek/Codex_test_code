"""Flask backend for Nexus-style BT resource sharing application.

This backend implements a credit-based resource sharing system with blockchain integration.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple
from flask import Flask, jsonify, request
from flask_cors import CORS

# 从hyperledger模块导入
try:
    from hyperledger import ResourceSharingSystem, LedgerClient, InMemoryLedger
except ImportError:
    # 如果直接导入失败，尝试从ledger子模块导入
    from hyperledger.ledger import ResourceSharingSystem, LedgerClient, InMemoryLedger


@dataclass
class User:
    username: str
    password: str
    role: str


@dataclass
class FileData:
    """文件数据结构"""
    name: str
    size_gb: float
    uploader: str
    seeds: int = 0
    peers: int = 0
    description: str = ""
    category: str = "other"
    file_hash: str = ""
    status: int = 0  # 0-挂起, 1-正常, 2-已审核, 3-下架


class CreditSystem:
    """信用积分系统"""
    
    INITIAL_CREDIT = 10000  # 初始信用
    CREDIT_PER_GB = 1000   # 每GB对应的信用
    MINING_REWARD = 50     # 挖矿奖励
    TIP_RATE = 0.001       # 小费比例
    
    @staticmethod
    def calculate_upload_credit(size_gb: float) -> int:
        """计算上传资源应获得的信用"""
        return int(size_gb * CreditSystem.CREDIT_PER_GB)
    
    @staticmethod
    def calculate_download_cost(size_gb: float) -> Tuple[int, int]:
        """计算下载资源消耗的信用和给记账人的小费"""
        cost = int(size_gb * CreditSystem.CREDIT_PER_GB)
        tip = max(1, int(cost * CreditSystem.TIP_RATE))  # 至少1信用
        return cost, tip


app = Flask(__name__)
CORS(app)

# 用户存储（实际项目中应该用数据库）
USERS: Dict[str, User] = {
    "admin": User(username="admin", password="admin", role="administrator"),
}

# 初始化区块链系统
ledger = InMemoryLedger()
system = ResourceSharingSystem()


def get_current_user() -> Optional[User]:
    """从请求中获取当前用户"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('demo-token-for-'):
        return None
    
    username = token.replace('demo-token-for-', '')
    return USERS.get(username)


@app.post("/api/register")
def register_user():
    """注册新用户"""
    payload = request.get_json() or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    
    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    
    if username in USERS:
        return jsonify({"message": "Username already exists"}), 400
    
    try:
        # 注册系统用户
        user = system.register_user(username)
        # 创建本地用户
        USERS[username] = User(username=username, password=password, role="user")
        
        return jsonify({
            "message": f"User {username} registered successfully!",
            "username": username,
            "initial_credit": CreditSystem.INITIAL_CREDIT
        }), 201
        
    except Exception as e:
        return jsonify({"message": f"Registration failed: {str(e)}"}), 400


@app.post("/api/login")
def login():
    """用户登录"""
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    password = payload.get("password", "")

    user: Optional[User] = USERS.get(username)
    if not user or user.password != password:
        return jsonify({"message": "Invalid username or password."}), 401

    return jsonify({
        "token": f"demo-token-for-{username}",
        "username": username,
        "role": user.role,
    })


@app.get("/api/user/balance")
def get_user_balance():
    """获取用户信用余额"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401
    
    try:
        balance = system.get_user_balance(current_user.username)
        return jsonify({
            "username": current_user.username,
            "balance": balance
        }), 200
    except Exception as e:
        return jsonify({"message": f"Failed to get balance: {str(e)}"}), 500


@app.post("/api/resources/declare")
def declare_resource():
    """声明资源（第一阶段）"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401
    
    payload = request.get_json() or {}
    file_data = payload.get("file_data", {})
    
    if not file_data:
        return jsonify({"message": "file_data is required"}), 400
    
    # 验证必要字段
    required_fields = ['name', 'size_gb', 'file_hash']
    for field in required_fields:
        if field not in file_data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    # 设置上传者
    file_data['uploader'] = current_user.username
    
    try:
        success = system.declare_user_resources(current_user.username, file_data)
        if not success:
            return jsonify({"message": "Failed to declare resource"}), 500
            
        return jsonify({
            "message": "Resource declared successfully and pending approval",
            "status": "pending",
            "credit_when_approved": CreditSystem.calculate_upload_credit(file_data['size_gb'])
        }), 201
        
    except Exception as e:
        return jsonify({"message": f"Declaration failed: {str(e)}"}), 500


@app.post("/api/resources/download")
def download_resource():
    """下载资源"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401
    
    payload = request.get_json() or {}
    file_id = payload.get("file_id")
    file_owner = payload.get("file_owner")  # 需要指定文件所有者
    
    if not file_id or not file_owner:
        return jsonify({"message": "file_id and file_owner are required"}), 400
    
    try:
        # 执行下载（这会扣除信用）
        success = system.download_resource(current_user.username, file_owner, file_id)
        if not success:
            return jsonify({"message": "Download failed - insufficient credit or other error"}), 400
        
        return jsonify({
            "message": "Download successful",
            "file_id": file_id
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Download failed: {str(e)}"}), 500


@app.post("/api/mine")
def mine_block():
    """挖矿（记账）"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401
    
    try:
        block = system.mine_block(current_user.username)
        if not block:
            return jsonify({"message": "Mining failed - no pending transactions"}), 400
        
        return jsonify({
            "message": "Block mined successfully",
            "miner": current_user.username,
            "mining_reward": CreditSystem.MINING_REWARD,
            "block_hash": getattr(block, 'hash', 'unknown'),
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Mining failed: {str(e)}"}), 500


@app.get("/api/resources")
def list_resources():
    """获取资源列表"""
    try:
        resources = system.get_all_resources()
        
        # 转换为字典格式
        resources_data = []
        for resource in resources:
            if hasattr(resource, 'to_dict'):
                resources_data.append(resource.to_dict())
            else:
                # 如果资源对象没有to_dict方法，手动创建字典
                resources_data.append({
                    'id': getattr(resource, 'id', 0),
                    'name': getattr(resource, 'name', ''),
                    'size_gb': getattr(resource, 'size_gb', 0),
                    'uploader': getattr(resource, 'uploader', ''),
                    'seeds': getattr(resource, 'seeds', 0),
                    'peers': getattr(resource, 'peers', 0),
                    'description': getattr(resource, 'description', ''),
                    'category': getattr(resource, 'category', 'other'),
                    'file_hash': getattr(resource, 'file_hash', ''),
                    'status': getattr(resource, 'status', 0),
                    'owner_address': getattr(resource, 'owner_address', '')
                })
        
        return jsonify({
            "resources": resources_data,
            "total": len(resources_data)
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Failed to get resources: {str(e)}"}), 500


@app.get("/api/resources/search")
def search_resources():
    """搜索资源"""
    keyword = request.args.get("keyword", "").strip()
    category = request.args.get("category", "").strip()
    min_size = request.args.get("min_size", type=float)
    max_size = request.args.get("max_size", type=float)
    min_seeds = request.args.get("min_seeds", type=int)
    
    try:
        results = system.search_resources(
            keyword=keyword if keyword else None,
            category=category if category else None,
            min_size=min_size,
            max_size=max_size,
            min_seeds=min_seeds
        )
        
        # 转换为字典格式
        results_data = []
        for resource in results:
            if hasattr(resource, 'to_dict'):
                results_data.append(resource.to_dict())
            else:
                results_data.append({
                    'id': getattr(resource, 'id', 0),
                    'name': getattr(resource, 'name', ''),
                    'size_gb': getattr(resource, 'size_gb', 0),
                    'uploader': getattr(resource, 'uploader', ''),
                    'seeds': getattr(resource, 'seeds', 0),
                    'peers': getattr(resource, 'peers', 0),
                    'description': getattr(resource, 'description', ''),
                    'category': getattr(resource, 'category', 'other'),
                    'file_hash': getattr(resource, 'file_hash', ''),
                    'status': getattr(resource, 'status', 0),
                    'owner_address': getattr(resource, 'owner_address', '')
                })
        
        return jsonify({
            "results": results_data,
            "count": len(results_data)
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Search failed: {str(e)}"}), 500


@app.get("/api/user/my-files")
def get_my_files():
    """获取用户自己的文件"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401
    
    try:
        user_obj = system.get_user(current_user.username)
        if not user_obj:
            return jsonify({"message": "User not found"}), 404
        
        my_files = user_obj.get_my_files()
        files_data = []
        for file in my_files:
            if hasattr(file, 'to_dict'):
                files_data.append(file.to_dict())
            else:
                files_data.append({
                    'id': getattr(file, 'id', 0),
                    'name': getattr(file, 'name', ''),
                    'size_gb': getattr(file, 'size_gb', 0),
                    'uploader': getattr(file, 'uploader', ''),
                    'seeds': getattr(file, 'seeds', 0),
                    'peers': getattr(file, 'peers', 0),
                    'description': getattr(file, 'description', ''),
                    'category': getattr(file, 'category', 'other'),
                    'file_hash': getattr(file, 'file_hash', ''),
                    'status': getattr(file, 'status', 0),
                    'owner_address': getattr(file, 'owner_address', '')
                })
        
        return jsonify({
            "files": files_data,
            "total": len(files_data)
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Failed to get user files: {str(e)}"}), 500


@app.post("/api/resources/report")
def report_resource():
    """举报资源"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"message": "Authentication required"}), 401
    
    payload = request.get_json() or {}
    file_id = payload.get("file_id")
    reason = payload.get("reason", "")
    
    if not file_id:
        return jsonify({"message": "file_id is required"}), 400
    
    try:
        # 这里需要实现举报逻辑
        # 暂时返回成功消息
        return jsonify({
            "message": f"File {file_id} has been reported and is under review",
            "action": "reported"
        }), 200
            
    except Exception as e:
        return jsonify({"message": f"Report failed: {str(e)}"}), 500


@app.get("/api/system/stats")
def get_system_stats():
    """获取系统统计信息"""
    try:
        blockchain_info = system.get_blockchain_info()
        
        return jsonify({
            "total_users": len(USERS),
            "blockchain_height": blockchain_info.get('chain_length', 0),
            "pending_transactions": blockchain_info.get('pending_transactions', 0),
            "current_difficulty": blockchain_info.get('current_difficulty', 0),
            "is_valid": blockchain_info.get('is_valid', False),
            "timestamp": int(time.time())
        }), 200
        
    except Exception as e:
        return jsonify({"message": f"Failed to get system stats: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)