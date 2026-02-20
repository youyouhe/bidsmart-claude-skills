"""MaterialHub API 客户端

提供与 MaterialHub 后端服务的集成，支持：
- 内部/外部 URL 自动切换
- Session-based 认证和自动 token 刷新
- 材料搜索和图片下载
- 本地图片缓存
"""

import logging
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class MaterialHubClient:
    """MaterialHub API 客户端"""

    def __init__(
        self,
        internal_url: str,
        external_url: str,
        username: str,
        password: str,
        cache_dir: str,
    ):
        """初始化客户端

        Args:
            internal_url: 内部访问地址（优先）
            external_url: 外部访问地址（兜底）
            username: 登录用户名
            password: 登录密码
            cache_dir: 图片缓存目录
        """
        self.internal_url = internal_url.rstrip("/")
        self.external_url = external_url.rstrip("/")
        self.username = username
        self.password = password
        self.cache_dir = Path(cache_dir)
        self.base_url: Optional[str] = None
        self.token: Optional[str] = None
        self.session = requests.Session()

    def connect(self) -> bool:
        """尝试连接 MaterialHub API（内部优先，外部兜底）

        Returns:
            是否成功连接并登录
        """
        # 尝试内部 URL
        if self._test_connection(self.internal_url):
            self.base_url = self.internal_url
            if self._login():
                logger.info(f"Connected to MaterialHub (internal): {self.base_url}")
                return True

        # 兜底到外部 URL
        if self._test_connection(self.external_url):
            self.base_url = self.external_url
            if self._login():
                logger.info(f"Connected to MaterialHub (external): {self.base_url}")
                return True

        # 连接失败
        logger.warning("MaterialHub API unavailable (both internal and external URLs failed)")
        return False

    def _test_connection(self, url: str) -> bool:
        """测试 URL 是否可访问

        Args:
            url: 要测试的 URL

        Returns:
            是否可访问
        """
        try:
            resp = self.session.get(f"{url}/health", timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Connection test failed for {url}: {e}")
            return False

    def _login(self) -> bool:
        """登录获取 token

        Returns:
            是否登录成功
        """
        try:
            resp = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data["token"]
                logger.info(f"Logged in as {self.username}")
                return True
            else:
                logger.error(f"Login failed: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """发送认证请求，自动处理 token 过期

        Args:
            method: HTTP 方法
            endpoint: API 端点路径
            **kwargs: requests 参数

        Returns:
            响应对象，失败时返回 None
        """
        if not self.token:
            logger.warning("No token available, skipping request")
            return None

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"

        try:
            resp = self.session.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                timeout=kwargs.pop("timeout", 30),
                **kwargs,
            )

            # Token 过期，重新登录
            if resp.status_code == 401:
                logger.info("Token expired, re-authenticating")
                if self._login():
                    headers["Authorization"] = f"Bearer {self.token}"
                    resp = self.session.request(
                        method,
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=30,
                        **kwargs,
                    )
                else:
                    logger.error("Re-authentication failed")
                    return None

            return resp

        except Exception as e:
            logger.error(f"Request failed: {method} {endpoint} - {e}")
            return None

    def get_companies(self) -> list[dict]:
        """获取公司列表

        Returns:
            公司列表
        """
        resp = self._request("GET", "/api/companies")
        if resp and resp.status_code == 200:
            data = resp.json()
            return data.get("companies", [])

        logger.warning(f"Get companies failed: {resp.status_code if resp else 'no response'}")
        return []

    def get_company_materials(self, company_id: int) -> list[dict]:
        """获取指定公司的所有材料

        Args:
            company_id: 公司 ID

        Returns:
            材料列表
        """
        resp = self._request("GET", f"/api/companies/{company_id}/materials")
        if resp and resp.status_code == 200:
            data = resp.json()
            return data.get("materials", [])

        logger.warning(f"Get company materials failed: {resp.status_code if resp else 'no response'}")
        return []

    def get_company_details(self, company_id: int) -> Optional[dict]:
        """获取公司详细信息（包含材料）

        Args:
            company_id: 公司 ID

        Returns:
            公司详情，包含关联的材料列表和提取的数据
        """
        resp = self._request("GET", f"/api/companies/{company_id}/materials")
        if resp and resp.status_code == 200:
            return resp.json()

        logger.warning(f"Get company details failed: {resp.status_code if resp else 'no response'}")
        return None

    def get_persons(self, company_id: Optional[int] = None) -> list[dict]:
        """获取人员列表

        Args:
            company_id: 可选，按公司过滤

        Returns:
            人员列表
        """
        params = {}
        if company_id:
            params["company_id"] = company_id

        resp = self._request("GET", "/api/persons", params=params)
        if resp and resp.status_code == 200:
            data = resp.json()
            return data.get("persons", [])

        logger.warning(f"Get persons failed: {resp.status_code if resp else 'no response'}")
        return []

    def get_person_details(self, person_id: int) -> Optional[dict]:
        """获取人员详细信息（包含材料）

        Args:
            person_id: 人员 ID

        Returns:
            人员详情，包含关联的材料列表和提取的数据
        """
        resp = self._request("GET", f"/api/persons/{person_id}/materials")
        if resp and resp.status_code == 200:
            return resp.json()

        logger.warning(f"Get person details failed: {resp.status_code if resp else 'no response'}")
        return None

    def get_material_details(self, material_id: int) -> Optional[dict]:
        """获取材料详细信息（包含extracted_data）

        Args:
            material_id: 材料 ID

        Returns:
            材料详情，包含完整的extracted_data
        """
        resp = self._request("GET", f"/api/materials/{material_id}")
        if resp and resp.status_code == 200:
            return resp.json()

        logger.warning(f"Get material details failed: {resp.status_code if resp else 'no response'}")
        return None

    def search_materials(
        self,
        q: Optional[str] = None,
        document_id: Optional[int] = None,
        status: str = "valid",
        company_id: Optional[int] = None,
    ) -> list[dict]:
        """搜索材料

        Args:
            q: 搜索关键词
            document_id: 文档 ID 过滤
            status: 过期状态过滤 (valid/expired/all)
            company_id: 公司 ID 过滤（如果提供，优先使用公司材料端点）

        Returns:
            材料列表
        """
        # 如果指定了公司 ID，使用公司材料端点
        if company_id:
            materials = self.get_company_materials(company_id)
            # 如果有搜索关键词，客户端过滤
            if q:
                q_lower = q.lower()
                materials = [
                    m for m in materials
                    if q_lower in m.get("title", "").lower()
                    or q_lower in m.get("section", "").lower()
                    or q_lower in (m.get("ocr_text") or "").lower()
                ]
            return materials

        # 否则使用通用搜索端点
        params = {}
        if q:
            params["q"] = q
        if document_id:
            params["document_id"] = document_id
        if status:
            params["status"] = status

        resp = self._request("GET", "/api/materials", params=params)
        if resp and resp.status_code == 200:
            data = resp.json()
            return data.get("results", [])

        logger.warning(f"Search failed: {resp.status_code if resp else 'no response'}")
        return []

    def get_material_image(self, material_id: int) -> bytes:
        """获取材料图片（带缓存）

        Args:
            material_id: 材料 ID

        Returns:
            图片字节数据，失败时返回空
        """
        # 检查缓存
        cache_file = self.cache_dir / f"material_{material_id}.png"
        if cache_file.exists():
            logger.debug(f"Cache hit for material {material_id}")
            return cache_file.read_bytes()

        # 先获取材料信息得到image_url
        logger.debug(f"Getting material {material_id} details for image_url")
        materials = self.search_materials()
        material = next((m for m in materials if m["id"] == material_id), None)

        if not material or "image_url" not in material:
            logger.error(f"Material {material_id} not found or has no image_url")
            return b""

        image_url = material["image_url"]

        # 从 API 下载图片
        logger.debug(f"Downloading image from {image_url}")
        # 注意：/api/files端点不需要Authorization header
        try:
            resp = self.session.get(
                f"{self.base_url}{image_url}",
                timeout=30
            )

            if resp.status_code == 200:
                image_bytes = resp.content

                # 写入缓存
                try:
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    cache_file.write_bytes(image_bytes)
                    logger.debug(f"Cached image for material {material_id}")
                except Exception as e:
                    logger.warning(f"Failed to cache image: {e}")

                return image_bytes
            else:
                logger.error(f"Image download failed: {resp.status_code}")
                return b""
        except Exception as e:
            logger.error(f"Image download exception: {e}")
            return b""
