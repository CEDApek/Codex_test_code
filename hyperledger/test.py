import ledger
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
