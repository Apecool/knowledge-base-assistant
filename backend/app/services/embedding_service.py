"""
Local Embedding Service using TF-IDF with character n-grams.
No model downloads needed, works completely offline.
Dimension: 128 (balanced for Chinese character n-grams).
"""
from typing import List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD


class LocalEmbeddingService:
    """
    Local embedding using TF-IDF + SVD dimensionality reduction.
    - Zero downloads, completely offline
    - Character n-grams (1-4) for deep Chinese support
    - SVD to 128 dimensions (balanced for small corpus)
    - Normalized to unit vectors for cosine similarity
    """

    _vectorizer = None
    _svd = None
    _vocab_built = False

    @classmethod
    def _ensure_fitted(cls):
        """Fit vectorizer on a diverse Chinese corpus."""
        if cls._vocab_built:
            return

        # Large diverse Chinese corpus for character n-gram extraction
        corpus = [
            # Technical terms
            "微服务 架构 分布式 系统 设计 网关 注册 发现 配置 中心 负载 均衡 熔断 降级 限流",
            "API 接口 RESTful gRPC WebSocket HTTP TCP IP 协议 通信 序列化 反序列化",
            "数据库 MySQL PostgreSQL Oracle Redis MongoDB Elasticsearch 缓存 索引 事务 锁",
            "前端 Vue React Angular HTML CSS JavaScript TypeScript 组件 状态 路由 构建",
            "后端 Python Java Go Rust Node.js 框架 FastAPI Django Spring 异步 并发 线程",
            "DevOps Docker Kubernetes Jenkins Git CI CD 部署 监控 告警 日志 链路追踪",
            "云计算 AWS Azure GCP 阿里云 腾讯云 华为云 容器 函数 计算 存储 网络",
            "安全 认证 授权 JWT OAuth HTTPS SSL 加密 解密 防火墙 漏洞 扫描 渗透",
            "性能 优化 缓存 加速 压缩 CDN 预加载 懒加载 异步 并行 批量 连接池",
            "测试 单元 集成 端到端 自动化 回归 压力 性能 覆盖率 mock pytest jest",
            "设计 模式 单例 工厂 观察者 策略 适配器 代理 装饰 模板 命令 状态 责任链",
            "数据 结构 数组 链表 栈 队列 哈希 表 树 图 堆 排序 查找 递归 迭代",
            "算法 复杂度 时间 空间 动态 规划 贪心 回溯 分支 限界 搜索 BFS DFS",
            "操作系统 进程 线程 内存 文件 系统 调度 同步 死锁 分段 分页 虚拟 内存",
            "网络 协议 TCP IP UDP HTTP HTTPS DNS DHCP ARP ICMP 路由 交换 子网 掩码",
            "软件 工程 需求 分析 设计 编码 测试 部署 维护 文档 版本 管理 敏捷 SCRUM",
            "人工智能 机器学习 深度 学习 神经 网络 CNN RNN LSTM Transformer BERT GPT",
            "自然 语言 处理 分词 词性 标注 命名 实体 识别 文本 分类 情感 分析 机器 翻译",
            "计算机 视觉 图像 识别 目标 检测 语义 分割 人脸 识别 OCR 视频 分析 跟踪",
            "数据 科学 分析 挖掘 统计 概率 回归 分类 聚类 降维 特征 工程 模型 评估",
            # Chinese business / management
            "项目管理 需求 排期 迭代 冲刺 站会 回顾 复盘 风险 进度 质量 交付",
            "产品 设计 用户 体验 交互 原型 线框 流程 导航 信息 架构 可用性 测试",
            "运营 数据 分析 用户 增长 留存 转化 活跃 付费 渠道 活动 内容 社区",
            "商业 模式 市场 竞争 分析 战略 规划 执行 复盘 目标 关键 结果 OKR KPI",
            "团队 管理 沟通 协作 效率 激励 成长 招聘 培训 文化 价值观 使命 愿景",
            # Chinese general text
            "今天 天气 很好 适合 出去 玩 吃饭 看电影 散步 运动 健身 跑步 游泳 打球",
            "教育 学习 考试 复习 课程 老师 学生 学校 大学 专业 知识 技能 培训 证书",
            "健康 医疗 医院 医生 护士 药品 手术 检查 体检 保险 养生 运动 饮食 睡眠",
            "金融 投资 股票 基金 理财 银行 保险 贷款 信用卡 支付 转账 汇率 利率 风险",
            "法律 法规 合同 协议 条款 权利 义务 责任 赔偿 诉讼 仲裁 律师 法院 判决",
            "新闻 资讯 报道 媒体 社交 网络 微博 微信 抖音 快手 直播 短视频 内容 创作",
            "生活 家居 装修 家具 家电 日用 食品 饮料 服装 鞋帽 美妆 护肤 母婴 宠物",
            # Mixed Chinese-English
            "CPU 内存 GPU 显卡 SSD 硬盘 主板 电源 散热 机箱 显示器 键盘 鼠标",
            "iOS Android 手机 平板 电脑 笔记本 充电 电池 屏幕 摄像头 传感器 GPS NFC",
            "微信 支付宝 支付 扫码 小程序 公众号 朋友圈 红包 转账 账单 余额 理财",
            "百度 阿里 腾讯 字节 美团 京东 拼多多 滴滴 快手 B站 小红书 知乎 微博",
            # Programming specific
            "git add commit push pull branch merge rebase clone fetch stash",
            "docker build run compose volume network image container registry",
            "python import def class async await return yield lambda map filter",
            "javascript const let var function arrow promise async await export import",
            "sql select from where join group order insert update delete create table",
            "debug error exception log trace warn info fatal try catch finally throw",
            # English technical
            "authentication authorization encryption decryption hashing salting",
            "microservice monolith serverless event driven CQRS saga pattern",
            "REST API endpoint request response header body status code method",
            "database query index transaction migration seed replica shard cluster",
            "frontend backend fullstack mobile web app desktop cross platform",
            "continuous integration delivery deployment pipeline automation tool",
            "scalability reliability availability maintainability portability",
            "object oriented functional procedural declarative reactive programming",
            "configuration management orchestration provisioning infrastructure",
        ]

        cls._vectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(1, 4),  # 1-4 chars for better Chinese character coverage
            max_features=3000,
            sublinear_tf=True,
        )
        tfidf_matrix = cls._vectorizer.fit_transform(corpus)

        # 128 dimensions — balanced for this corpus size
        cls._svd = TruncatedSVD(n_components=128, random_state=42)
        cls._svd.fit(tfidf_matrix)

        cls._vocab_built = True

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single text string."""
        self._ensure_fitted()
        tfidf = self._vectorizer.transform([text])
        vec = self._svd.transform(tfidf)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec[0].tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of texts."""
        if not texts:
            return []
        self._ensure_fitted()
        tfidf = self._vectorizer.transform(texts)
        vecs = self._svd.transform(tfidf)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vecs = vecs / norms
        return vecs.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Alias for embed_text."""
        return self.embed_text(query)