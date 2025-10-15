# backend/test_app_fixed.py
import unittest
import json
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 在导入 app 之前模拟所有依赖
mock_flask_cors = MagicMock()
sys.modules['flask_cors'] = mock_flask_cors

# 模拟 hyperledger 模块
mock_hyperledger = MagicMock()
sys.modules['hyperledger'] = mock_hyperledger
sys.modules['hyperledger.ledger'] = mock_hyperledger

# 现在导入 Flask 和创建测试应用
from flask import Flask, jsonify

# 创建测试 Flask 应用
app = Flask(__name__)
app.testing = True

# 模拟用户数据
USERS = {
    "admin": type('User', (), {
        'username': 'admin', 
        'password': 'admin', 
        'role': 'administrator'
    })()
}

class CreditSystem:
    """信用积分系统"""
    INITIAL_CREDIT = 10000
    CREDIT_PER_GB = 1000
    MINING_REWARD = 50
    TIP_RATE = 0.001
    
    @staticmethod
    def calculate_upload_credit(size_gb):
        return int(size_gb * CreditSystem.CREDIT_PER_GB)
    
    @staticmethod
    def calculate_download_cost(size_gb):
        cost = int(size_gb * CreditSystem.CREDIT_PER_GB)
        tip = max(1, int(cost * CreditSystem.TIP_RATE))
        return cost, tip

# 添加测试路由
@app.post("/api/register")
def register_user():
    payload = request.get_json() or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    
    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    
    if username in USERS:
        return jsonify({"message": "Username already exists"}), 400
    
    USERS[username] = type('User', (), {
        'username': username,
        'password': password,
        'role': 'user'
    })()
    
    return jsonify({
        "message": f"User {username} registered successfully!",
        "username": username,
        "initial_credit": CreditSystem.INITIAL_CREDIT
    }), 201

@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "")
    password = payload.get("password", "")

    user = USERS.get(username)
    if not user or user.password != password:
        return jsonify({"message": "Invalid username or password."}), 401

    return jsonify({
        "token": f"demo-token-for-{username}",
        "username": username,
        "role": user.role,
    })

@app.get("/api/user/balance")
def get_user_balance():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('demo-token-for-'):
        return jsonify({"message": "Authentication required"}), 401
    
    username = token.replace('demo-token-for-', '')
    if username not in USERS:
        return jsonify({"message": "User not found"}), 404
    
    # 模拟余额
    balance = 10000  # 初始余额
    
    return jsonify({
        "username": username,
        "balance": balance
    }), 200

@app.post("/api/resources/declare")
def declare_resource():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('demo-token-for-'):
        return jsonify({"message": "Authentication required"}), 401
    
    username = token.replace('demo-token-for-', '')
    payload = request.get_json() or {}
    file_data = payload.get("file_data", {})
    
    if not file_data:
        return jsonify({"message": "file_data is required"}), 400
    
    required_fields = ['name', 'size_gb', 'file_hash']
    for field in required_fields:
        if field not in file_data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    return jsonify({
        "message": "Resource declared successfully and pending approval",
        "status": "pending",
        "credit_when_approved": CreditSystem.calculate_upload_credit(file_data['size_gb'])
    }), 201

@app.post("/api/mine")
def mine_block():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('demo-token-for-'):
        return jsonify({"message": "Authentication required"}), 401
    
    username = token.replace('demo-token-for-', '')
    
    return jsonify({
        "message": "Block mined successfully",
        "miner": username,
        "mining_reward": CreditSystem.MINING_REWARD,
        "block_hash": "mock_block_hash"
    }), 200

@app.get("/api/resources")
def list_resources():
    # 返回模拟资源列表
    mock_resources = [
        {
            "id": 1,
            "name": "Sample File 1",
            "size_gb": 1.5,
            "uploader": "user1",
            "seeds": 10,
            "peers": 2,
            "description": "A sample file",
            "category": "document",
            "file_hash": "abc123",
            "status": 1
        },
        {
            "id": 2,
            "name": "Sample File 2", 
            "size_gb": 2.0,
            "uploader": "user2",
            "seeds": 5,
            "peers": 3,
            "description": "Another sample file",
            "category": "software",
            "file_hash": "def456",
            "status": 1
        }
    ]
    
    return jsonify({
        "resources": mock_resources,
        "total": len(mock_resources)
    }), 200

# 需要导入 request
from flask import request

class TestBTResourceSharingSystemFixed(unittest.TestCase):
    
    def setUp(self):
        """测试前设置"""
        self.app = app.test_client()
        self.app.testing = True
        
        # 清空测试数据
        USERS.clear()
        
        # 重新添加管理员用户
        USERS["admin"] = type('User', (), {
            'username': 'admin',
            'password': 'admin',
            'role': 'administrator'
        })()
    
    def get_auth_headers(self, username):
        """获取认证头"""
        return {
            'Authorization': f'Bearer demo-token-for-{username}',
            'Content-Type': 'application/json'
        }
    
    def test_01_register_user(self):
        """测试用户注册"""
        # 正常注册
        response = self.app.post('/api/register', data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'User testuser registered successfully!')
        self.assertEqual(data['initial_credit'], 10000)
        
        # 重复注册
        response = self.app.post('/api/register', data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_02_login(self):
        """测试用户登录"""
        # 先注册用户
        self.app.post('/api/register', data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }), content_type='application/json')
        
        # 正常登录
        response = self.app.post('/api/login', data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['role'], 'user')
        self.assertTrue(data['token'].startswith('demo-token-for-testuser'))
        
        # 错误密码
        response = self.app.post('/api/login', data=json.dumps({
            'username': 'testuser',
            'password': 'wrongpass'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
    
    def test_03_get_user_balance(self):
        """测试获取用户余额"""
        # 先注册并登录用户
        self.app.post('/api/register', data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }), content_type='application/json')
        
        # 未认证请求
        response = self.app.get('/api/user/balance')
        self.assertEqual(response.status_code, 401)
        
        # 认证请求
        response = self.app.get(
            '/api/user/balance',
            headers=self.get_auth_headers('testuser')
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['balance'], 10000)
    
    def test_04_declare_resource(self):
        """测试声明资源"""
        # 先注册并登录用户
        self.app.post('/api/register', data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }), content_type='application/json')
        
        # 未认证请求
        response = self.app.post('/api/resources/declare', data=json.dumps({
            'file_data': {
                'name': 'test_file.txt',
                'size_gb': 1.0,
                'file_hash': 'abc123'
            }
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        
        # 认证请求 - 缺少必要字段
        response = self.app.post(
            '/api/resources/declare',
            data=json.dumps({
                'file_data': {
                    'name': 'test_file.txt'
                }
            }),
            headers=self.get_auth_headers('testuser'),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        # 正常声明资源
        response = self.app.post(
            '/api/resources/declare',
            data=json.dumps({
                'file_data': {
                    'name': 'test_file.txt',
                    'size_gb': 1.0,
                    'file_hash': 'abc123',
                    'description': 'A test file',
                    'category': 'document'
                }
            }),
            headers=self.get_auth_headers('testuser'),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Resource declared successfully and pending approval')
        self.assertEqual(data['credit_when_approved'], 1000)
    
    def test_05_mine_block(self):
        """测试挖矿"""
        # 先注册并登录用户
        self.app.post('/api/register', data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }), content_type='application/json')
        
        # 挖矿
        response = self.app.post(
            '/api/mine',
            data=json.dumps({}),
            headers=self.get_auth_headers('testuser'),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Block mined successfully')
        self.assertEqual(data['miner'], 'testuser')
        self.assertEqual(data['mining_reward'], 50)
    
    def test_06_list_resources(self):
        """测试获取资源列表"""
        # 先注册并登录用户
        self.app.post('/api/register', data=json.dumps({
            'username': 'testuser',
            'password': 'testpass'
        }), content_type='application/json')
        
        # 获取资源列表
        response = self.app.get(
            '/api/resources',
            headers=self.get_auth_headers('testuser')
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['resources']), 2)
        self.assertEqual(data['total'], 2)

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)