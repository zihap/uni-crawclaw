# -*- coding: utf-8 -*-
"""
辅助函数工具模块
"""

import random
import string
from typing import Dict


def generate_room_id(existing_rooms: Dict[str, dict]) -> str:
    """生成唯一的6位房间号"""
    while True:
        room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if room_id not in existing_rooms:
            return room_id
