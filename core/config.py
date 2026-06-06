"""
配置管理:读写 config.json,带原子写、默认值、损坏自动备份。
"""
import json
import shutil
import uuid
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "version": "1.0",
    "ball": {
        "size": 56,
        "opacity": 0.92,
        "position": {"x": 100, "y": 100},
        "color": "#4A90E2",
        "icon": "📚",
        "auto_start": False,
        "start_expanded": False,
        "click_through": True,
        "radial_radius": 100,
    },
    "buttons": [],
}


class Config:
    """单例式配置管理。"""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.data: dict[str, Any] = {}
        self.load()

    # ---- 加载 ----
    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            self.data = json.loads(json.dumps(DEFAULT_CONFIG))  # 深拷贝
            self.save()
            return self.data
        try:
            text = self.path.read_text(encoding="utf-8")
            self.data = json.loads(text)
        except (json.JSONDecodeError, OSError) as e:
            # 损坏:备份为 .bak 并重置
            try:
                shutil.copy2(self.path, self.path.with_suffix(".bak"))
            except OSError:
                pass
            self.data = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save()
        # 字段补全(向后兼容)
        self._merge_defaults()
        return self.data

    def _merge_defaults(self):
        for k, v in DEFAULT_CONFIG.items():
            if k not in self.data:
                self.data[k] = json.loads(json.dumps(v))
            elif isinstance(v, dict) and isinstance(self.data[k], dict):
                for kk, vv in v.items():
                    if kk not in self.data[k]:
                        self.data[k][kk] = vv

    # ---- 保存(原子写) ----
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)

    # ---- 业务操作 ----
    def add_button(self, btn: dict) -> str:
        if "id" not in btn or not btn["id"]:
            btn["id"] = uuid.uuid4().hex[:8]
        self.data.setdefault("buttons", []).append(btn)
        self.save()
        return btn["id"]

    def update_button(self, btn_id: str, btn: dict) -> bool:
        for i, b in enumerate(self.data.get("buttons", [])):
            if b.get("id") == btn_id:
                btn["id"] = btn_id
                self.data["buttons"][i] = btn
                self.save()
                return True
        return False

    def remove_button(self, btn_id: str) -> bool:
        lst = self.data.get("buttons", [])
        for i, b in enumerate(lst):
            if b.get("id") == btn_id:
                lst.pop(i)
                self.save()
                return True
        return False

    def move_button(self, btn_id: str, delta: int) -> bool:
        lst = self.data.get("buttons", [])
        for i, b in enumerate(lst):
            if b.get("id") == btn_id:
                j = max(0, min(len(lst) - 1, i + delta))
                if i != j:
                    lst.insert(j, lst.pop(i))
                    self.save()
                return True
        return False

    def update_ball(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.data["ball"]:
                self.data["ball"][k] = v
        self.save()
