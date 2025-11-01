import hashlib
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Union
import threading
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class SharedFile:
    """共享文件资源类"""
    id: int
    name: str
    size_gb: float  # 修改为GB单位，便于计算
    uploader: str
    seeds: int
    peers: int
    description: str
    owner_address: str  # 所有者区块链地址
    file_hash: str = ""  # 文件哈希，用于验证文件完整性
    category: str = "general"  # 文件分类
    upload_time: float = None  # 上传时间戳
    is_active: bool = True  # 是否活跃可用
    storage_path: str = ""  # 后端保存的文件路径（可选）
    
    def __post_init__(self):
        if self.upload_time is None:
            self.upload_time = time.time()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'size_gb': self.size_gb,
            'uploader': self.uploader,
            'seeds': self.seeds,
            'peers': self.peers,
            'description': self.description,
            'owner_address': self.owner_address,
            'file_hash': self.file_hash,
            'category': self.category,
            'upload_time': self.upload_time,
            'is_active': self.is_active,
            'storage_path': self.storage_path,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SharedFile':
        """从字典创建对象"""
        return cls(**data)

class ResourceManager:
    """资源管理器"""
    def __init__(self):
        self.files: Dict[int, SharedFile] = {}  # 文件ID到文件的映射
        self.next_file_id = 1
        self.lock = threading.Lock()
        
        # 初始化一些示例文件
        self._initialize_sample_files()
    
    def _initialize_sample_files(self):
        """初始化示例文件"""
        sample_files = [
            SharedFile(
                id=self._get_next_id(),
                name="The Art of Seeding.pdf",
                size_gb=0.0124,  # 12.4 MB 转换为 GB
                uploader="seedMaster",
                seeds=42,
                peers=5,
                description="Illustrated guide to earning wealth rewards efficiently.",
                owner_address="",
                category="document"
            ),
            SharedFile(
                id=self._get_next_id(),
                name="Nexus OST.mp3",
                size_gb=0.0063,  # 6.3 MB 转换为 GB
                uploader="djHyper",
                seeds=18,
                peers=12,
                description="Synthwave soundtrack to keep your node online.",
                owner_address="",
                category="audio"
            ),
            SharedFile(
                id=self._get_next_id(),
                name="ClientSetup.zip",
                size_gb=0.0481,  # 48.1 MB 转换为 GB
                uploader="builderBee",
                seeds=33,
                peers=4,
                description="Automation scripts to bootstrap a new seeding rig.",
                owner_address="",
                category="software"
            )
        ]
        
        for file in sample_files:
            self.files[file.id] = file
    
    def _get_next_id(self) -> int:
        """获取下一个文件ID"""
        id = self.next_file_id
        self.next_file_id += 1
        return id
    
    def add_file(self, file_data: Dict) -> Optional[SharedFile]:
        """添加新文件"""
        with self.lock:
            try:
                file_id = self._get_next_id()
                file = SharedFile(id=file_id, **file_data)
                self.files[file_id] = file
                print(f"文件添加成功: {file.name} (ID: {file_id})")
                return file
            except Exception as e:
                print(f"添加文件失败: {e}")
                return None
    
    def remove_file(self, file_id: int, owner_address: str = None) -> bool:
        """删除文件（只有所有者可以删除）"""
        with self.lock:
            if file_id not in self.files:
                print(f"文件不存在: ID {file_id}")
                return False
            
            file = self.files[file_id]
            
            # 检查所有权
            if owner_address and file.owner_address != owner_address:
                print(f"无权删除文件: 文件属于 {file.owner_address}")
                return False
            
            del self.files[file_id]
            print(f"文件删除成功: {file.name} (ID: {file_id})")
            return True
    
    def update_file(self, file_id: int, update_data: Dict, owner_address: str = None) -> Optional[SharedFile]:
        """更新文件信息"""
        with self.lock:
            if file_id not in self.files:
                print(f"文件不存在: ID {file_id}")
                return None
            
            file = self.files[file_id]
            
            # 检查所有权
            if owner_address and file.owner_address != owner_address:
                print(f"无权更新文件: 文件属于 {file.owner_address}")
                return None
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(file, key) and key not in ['id', 'owner_address']:
                    setattr(file, key, value)
            
            print(f"文件更新成功: {file.name} (ID: {file_id})")
            return file
    
    def get_file(self, file_id: int) -> Optional[SharedFile]:
        """根据ID获取文件"""
        return self.files.get(file_id)
    
    def get_files_by_owner(self, owner_address: str) -> List[SharedFile]:
        """根据所有者获取文件列表"""
        return [file for file in self.files.values() if file.owner_address == owner_address]
    
    def search_files(self, keyword: str = None, category: str = None, 
                    min_size: float = None, max_size: float = None,
                    min_seeds: int = None) -> List[SharedFile]:
        """搜索文件"""
        results = []
        
        for file in self.files.values():
            if not file.is_active:
                continue
            
            # 关键词搜索
            if keyword and keyword.lower() not in file.name.lower() and keyword.lower() not in file.description.lower():
                continue
            
            # 分类筛选
            if category and file.category != category:
                continue
            
            # 大小筛选
            if min_size is not None and file.size_gb < min_size:
                continue
            if max_size is not None and file.size_gb > max_size:
                continue
            
            # 种子数筛选
            if min_seeds is not None and file.seeds < min_seeds:
                continue
            
            results.append(file)
        
        return results
    
    def get_all_files(self) -> List[SharedFile]:
        """获取所有文件"""
        return list(self.files.values())
    
    def get_active_files(self) -> List[SharedFile]:
        """获取所有活跃文件"""
        return [file for file in self.files.values() if file.is_active]
    
    def update_seeds_peers(self, file_id: int, seeds_delta: int = 0, peers_delta: int = 0) -> bool:
        """更新种子数和peer数"""
        with self.lock:
            if file_id not in self.files:
                return False
            
            file = self.files[file_id]
            file.seeds = max(0, file.seeds + seeds_delta)
            file.peers = max(0, file.peers + peers_delta)
            return True
    
    def get_file_count(self) -> int:
        """获取文件总数"""
        return len(self.files)
    
    def get_files_by_category(self) -> Dict[str, List[SharedFile]]:
        """按分类统计文件"""
        categories = {}
        for file in self.files.values():
            if file.category not in categories:
                categories[file.category] = []
            categories[file.category].append(file)
        return categories

# 修改原有的Transaction类（保持不变，只添加导入）
class Transaction:
    """交易类"""
    def __init__(self, sender: str, receiver: str, amount: float, transaction_type: str, resource_data: Dict = None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.transaction_type = transaction_type
        self.resource_data = resource_data or {}
        self.timestamp = time.time()
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        transaction_string = f"{self.sender}{self.receiver}{self.amount}{self.transaction_type}{self.timestamp}{json.dumps(self.resource_data, sort_keys=True)}"
        return hashlib.sha256(transaction_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'resource_data': self.resource_data,
            'timestamp': self.timestamp,
            'hash': self.hash
        }

# 修改Block类（保持不变）
class Block:
    """区块类"""
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str, difficulty: int = 2):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.difficulty = difficulty
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        transactions_string = "".join([tx.hash for tx in self.transactions])
        block_string = f"{self.index}{self.timestamp}{self.previous_hash}{self.nonce}{transactions_string}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self):
        while self.hash[:self.difficulty] != '0' * self.difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()
    
    def to_dict(self) -> Dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'difficulty': self.difficulty,
            'hash': self.hash
        }

# 修改Blockchain类（保持不变）
class Blockchain:
    """区块链类"""
    def __init__(self):
        self.chain: List[Block] = [self.create_genesis_block()]
        self.pending_transactions: List[Transaction] = []
        self.difficulty = 2
        self.mining_reward = 50.0
        self.reward_halving_interval = 210000
        self.lock = threading.Lock()
        
        print("区块链初始化完成，创世区块已创建")
    
    def create_genesis_block(self) -> Block:
        genesis_transaction = Transaction(
            sender="0",
            receiver="system",
            amount=0,
            transaction_type="genesis"
        )
        block = Block(0, [genesis_transaction], "0")
        block.mine_block()
        return block
    
    def get_latest_block(self) -> Block:
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction) -> bool:
        with self.lock:
            print(f"添加交易: {transaction.sender} -> {transaction.receiver} 金额: {transaction.amount} 类型: {transaction.transaction_type}")
            
            if transaction.sender == "0":
                self.pending_transactions.append(transaction)
                print(f"系统交易添加成功，待处理交易数: {len(self.pending_transactions)}")
                return True
            
            sender_balance = self.get_balance(transaction.sender)
            if sender_balance >= transaction.amount:
                self.pending_transactions.append(transaction)
                print(f"普通交易添加成功，待处理交易数: {len(self.pending_transactions)}")
                return True
            else:
                print(f"交易失败: {transaction.sender} 余额不足。当前余额: {sender_balance}, 需要: {transaction.amount}")
                return False
    
    def mine_pending_transactions(self, mining_reward_address: str) -> Block:
        with self.lock:
            if not self.pending_transactions:
                print("没有待处理的交易")
                return None
            
            print(f"开始处理 {len(self.pending_transactions)} 个待处理交易...")
            
            total_fees = sum(tx.amount * 0.001 for tx in self.pending_transactions if tx.transaction_type in ["resource_download", "transfer"])
            current_reward = self.calculate_current_reward() + total_fees
            
            print(f"区块奖励: {current_reward} (基础奖励: {self.calculate_current_reward()}, 交易费用: {total_fees})")
            
            reward_transaction = Transaction(
                sender="0",
                receiver=mining_reward_address,
                amount=current_reward,
                transaction_type="mining_reward"
            )
            
            transactions_to_mine = self.pending_transactions.copy()
            transactions_to_mine.append(reward_transaction)
            
            block = Block(
                len(self.chain),
                transactions_to_mine,
                self.get_latest_block().hash,
                self.difficulty
            )
            
            print(f"开始挖矿区块 #{block.index}...")
            start_time = time.time()
            block.mine_block()
            end_time = time.time()
            print(f"区块 #{block.index} 挖矿完成! 耗时: {end_time - start_time:.2f}秒, 哈希: {block.hash}")
            
            self.chain.append(block)
            self.pending_transactions = []
            
            print(f"区块 #{block.index} 已添加到区块链，当前链长度: {len(self.chain)}")
            return block
    
    def calculate_current_reward(self) -> float:
        halving_count = len(self.chain) // self.reward_halving_interval
        current_reward = self.mining_reward / (2 ** halving_count)
        return current_reward
    
    def get_balance(self, address: str) -> float:
        balance = 0.0
        
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.receiver == address:
                    balance += transaction.amount
                if transaction.sender == address and transaction.sender != "0":
                    balance -= transaction.amount
        
        return balance
    
    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
            
            if current_block.hash[:current_block.difficulty] != '0' * current_block.difficulty:
                return False
        
        return True

# 修改User类，集成ResourceManager
class User:
    """用户类"""
    def __init__(self, username: str, blockchain: Blockchain):
        self.username = username
        self.address = hashlib.sha256(f"{username}{time.time()}".encode()).hexdigest()[:16]
        self.blockchain = blockchain
        self.resource_manager = ResourceManager()  # 每个用户有自己的资源管理器
        self.initial_credit = 10000.0
        
        print(f"创建用户 {username}, 地址: {self.address}")
        
        # 初始信用交易
        initial_transaction = Transaction(
            sender="0",
            receiver=self.address,
            amount=self.initial_credit,
            transaction_type="initial_credit"
        )
        
        success = self.blockchain.add_transaction(initial_transaction)
        if success:
            print(f"用户 {username} 初始信用 {self.initial_credit} 已添加到待处理交易")
        else:
            print(f"用户 {username} 初始信用添加失败")
    
    def declare_resources(self, file_data: Dict) -> bool:
        """声明资源（上传文件）"""
        # 设置文件所有者
        file_data['owner_address'] = self.address
        
        # 添加文件到资源管理器
        file = self.resource_manager.add_file(file_data)
        if not file:
            return False
        
        # 计算获得的信用
        credit_earned = file.size_gb * 1000
        
        print(f"用户 {self.username} 声明资源: {file.name}, 大小: {file.size_gb}GB, 获得信用: {credit_earned}")
        
        # 创建资源声明交易
        resource_transaction = Transaction(
            sender="0",
            receiver=self.address,
            amount=credit_earned,
            transaction_type="resource_declaration",
            resource_data=file.to_dict()
        )
        
        success = self.blockchain.add_transaction(resource_transaction)
        if success:
            print(f"资源声明交易添加成功")
        else:
            print(f"资源声明交易添加失败")
            # 如果交易失败，移除文件
            self.resource_manager.remove_file(file.id, self.address)
        
        return success
    
    def download_resource(self, file_id: int, downloader: 'User') -> bool:
        """下载其他用户的资源"""
        file = self.resource_manager.get_file(file_id)
        if not file or not file.is_active:
            print(f"文件不存在或不可用: ID {file_id}")
            return False
        
        if file.owner_address == downloader.address:
            print("不能下载自己的文件")
            return False
        
        download_cost = file.size_gb * 1000
        miner_fee = download_cost * 0.001
        total_cost = download_cost + miner_fee
        
        print(f"下载成本: {download_cost} (资源费) + {miner_fee} (矿工费) = {total_cost}")
        
        # 检查下载者余额
        downloader_balance = self.blockchain.get_balance(downloader.address)
        print(f"下载者 {downloader.username} 余额: {downloader_balance}, 需要: {total_cost}")
        
        if downloader_balance < total_cost:
            print("余额不足，下载失败")
            return False
        
        # 创建资源下载交易
        download_transaction = Transaction(
            sender=downloader.address,
            receiver=file.owner_address,
            amount=download_cost,
            transaction_type="resource_download",
            resource_data=file.to_dict()
        )
        
        success = self.blockchain.add_transaction(download_transaction)
        if success:
            print("资源下载交易添加成功")
            # 更新种子数（下载者成为新的种子）
            self.resource_manager.update_seeds_peers(file_id, seeds_delta=1)
        else:
            print("资源下载交易添加失败")
        
        return success
    
    # 资源管理接口
    def get_my_files(self) -> List[SharedFile]:
        """获取我的所有文件"""
        return self.resource_manager.get_files_by_owner(self.address)
    
    def remove_my_file(self, file_id: int) -> bool:
        """删除我的文件"""
        return self.resource_manager.remove_file(file_id, self.address)
    
    def update_my_file(self, file_id: int, update_data: Dict) -> Optional[SharedFile]:
        """更新我的文件信息"""
        return self.resource_manager.update_file(file_id, update_data, self.address)
    
    def search_available_files(self, **kwargs) -> List[SharedFile]:
        """搜索可用的文件"""
        return self.resource_manager.search_files(**kwargs)
    
    def get_all_available_files(self) -> List[SharedFile]:
        """获取所有可用的文件"""
        return self.resource_manager.get_active_files()
    
    def mine_block(self) -> Block:
        print(f"用户 {self.username} 开始挖矿...")
        return self.blockchain.mine_pending_transactions(self.address)
    
    def get_balance(self) -> float:
        return self.blockchain.get_balance(self.address)

class ResourceSharingSystem:
    """资源共享系统主类"""
    def __init__(self):
        self.blockchain = Blockchain()
        self.users: Dict[str, User] = {}
        self.global_resource_manager = ResourceManager()  # 全局资源管理器
        print("资源共享系统初始化完成")
    
    def register_user(self, username: str) -> User:
        if username in self.users:
            raise ValueError(f"用户名 {username} 已存在")
        
        user = User(username, self.blockchain)
        self.users[username] = user
        return user
    
    def get_user(self, username: str) -> Optional[User]:
        return self.users.get(username)
    
    def declare_user_resources(self, username: str, file_data: Dict) -> bool:
        """用户声明资源"""
        user = self.get_user(username)
        if not user:
            print(f"用户 {username} 不存在")
            return False
        return user.declare_resources(file_data)
    
    def download_resource(self, downloader_username: str, file_owner_username: str, file_id: int) -> bool:
        """下载资源"""
        downloader = self.get_user(downloader_username)
        owner = self.get_user(file_owner_username)
        
        if not downloader or not owner:
            print("用户不存在")
            return False
        
        return owner.download_resource(file_id, downloader)
    
    def mine_block(self, miner_username: str) -> Block:
        miner = self.get_user(miner_username)
        if not miner:
            return None
        return miner.mine_block()
    
    def get_user_balance(self, username: str) -> float:
        user = self.get_user(username)
        if not user:
            return 0.0
        return user.get_balance()
    
    def get_blockchain_info(self) -> Dict:
        return {
            'chain_length': len(self.blockchain.chain),
            'pending_transactions': len(self.blockchain.pending_transactions),
            'current_difficulty': self.blockchain.difficulty,
            'current_mining_reward': self.blockchain.calculate_current_reward(),
            'is_valid': self.blockchain.is_chain_valid()
        }
    
    # 全局资源搜索接口
    def search_resources(self, **kwargs) -> List[SharedFile]:
        """全局搜索资源"""
        all_files = []
        for user in self.users.values():
            user_files = user.search_available_files(**kwargs)
            all_files.extend(user_files)
        return all_files
    
    def get_all_resources(self) -> List[SharedFile]:
        """获取所有可用资源"""
        all_files = []
        for user in self.users.values():
            user_files = user.get_all_available_files()
            all_files.extend(user_files)
        return all_files

# 测试运行
if __name__ == "__main__":
    print("=== 资源共享区块链系统测试 ===")
    
    # 创建资源共享系统
    system = ResourceSharingSystem()
    
    # 注册用户
    print("\n--- 注册用户 ---")
    user1 = system.register_user("Alice")
    user2 = system.register_user("Bob")
    
    print(f"\n--- 初始状态 ---")
    print(f"用户 Alice 地址: {user1.address}, 初始余额: {user1.get_balance()}")
    print(f"用户 Bob 地址: {user2.address}, 初始余额: {user2.get_balance()}")
    
    # 用户声明资源
    print(f"\n--- 声明资源 ---")
    # Alice 上传文件
    alice_file = {
        'name': "Python Programming Guide.pdf",
        'size_gb': 0.025,
        'uploader': "Alice",
        'seeds': 10,
        'peers': 2,
        'description': "Comprehensive guide to Python programming",
        'category': "document",
        'file_hash': hashlib.sha256(b"python_guide").hexdigest()[:16]
    }
    user1.declare_resources(alice_file)
    
    # Bob 上传文件
    bob_file = {
        'name': "Data Science Toolkit.zip",
        'size_gb': 0.15,
        'uploader': "Bob",
        'seeds': 5,
        'peers': 1,
        'description': "Essential tools for data science projects",
        'category': "software",
        'file_hash': hashlib.sha256(b"data_science").hexdigest()[:16]
    }
    user2.declare_resources(bob_file)
    
    print(f"\n--- 声明资源后余额 ---")
    print(f"Alice 声明资源后余额: {user1.get_balance()}")
    print(f"Bob 声明资源后余额: {user2.get_balance()}")
    
    # 挖矿确认交易
    print(f"\n--- 第一次挖矿 ---")
    mined_block = user1.mine_block()
    if mined_block:
        print(f"挖矿成功! 区块 #{mined_block.index}")
    
    print(f"\n--- 第一次挖矿后余额 ---")
    print(f"挖矿后 Alice 余额: {user1.get_balance()}")
    print(f"挖矿后 Bob 余额: {user2.get_balance()}")
    
    # 显示用户文件
    print(f"\n--- Alice 的文件 ---")
    for file in user1.get_my_files():
        print(f"  - {file.name} ({file.size_gb}GB, {file.seeds} seeds)")
    
    print(f"\n--- Bob 的文件 ---")
    for file in user2.get_my_files():
        print(f"  - {file.name} ({file.size_gb}GB, {file.seeds} seeds)")
    
    # 搜索文件
    print(f"\n--- 搜索文件 ---")
    available_files = system.search_resources(keyword="data")
    print(f"找到 {len(available_files)} 个相关文件:")
    for file in available_files:
        print(f"  - {file.name} (上传者: {file.uploader})")
    
    # Bob 下载 Alice 的资源
    print(f"\n--- 资源下载 ---")
    alice_files = user1.get_my_files()
    if alice_files:
        success = system.download_resource("Bob", "Alice", alice_files[0].id)
        print(f"资源下载{'成功' if success else '失败'}")
    
    # 再次挖矿确认下载交易
    print(f"\n--- 第二次挖矿 ---")
    user2.mine_block()
    
    print(f"\n--- 最终状态 ---")
    print(f"最终 Alice 余额: {user1.get_balance()}")
    print(f"最终 Bob 余额: {user2.get_balance()}")
    
    # 显示区块链信息
    blockchain_info = system.get_blockchain_info()
    print(f"\n--- 区块链信息 ---")
    print(f"区块链信息: {blockchain_info}")
    
    input("\n按回车键退出...")
