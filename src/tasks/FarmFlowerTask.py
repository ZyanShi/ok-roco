import time
from ok import Box, TaskDisabledException
from qfluentwidgets import FluentIcon
from src.tasks.MyBaseTask import MyBaseTask


class FarmFlowerTask(MyBaseTask):
    """奇丽花刷花自动化任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "奇丽花刷花"
        self.description = "自动执行奇丽花刷花序列：传送、移动、投掷精灵，然后循环鞠躬采集"
        self.group_icon = FluentIcon.LEAF
        self.icon = FluentIcon.LEAF

        # 默认配置
        self.default_config.update({
            '挂机点位': '商店街炼金釜',  # 仅一个选项，预留扩展
            '鞠躬间隔': 15,          # 6→R 后的等待时间（秒）
            '传送时间': 180,         # 内层循环最大持续时间（秒）
        })
        self.config_description = {
            '鞠躬间隔': '鞠躬之间的等待时间（秒）',
            '传送时间': '超时后重新传送（秒）',
            '挂机点位': '请确保在从传送点附近，将地图尺度拉到最小，放大地图',
        }

        self.config_type['挂机点位'] = {
        'type': "drop_down",
        'options': ['商店街炼金釜']

    }

        # 预定义区域坐标（基于1920x1080）
        self.TP_AREA = (740, 310, 1070, 650)   # 地图上tp图标的搜索区域

    def validate_config(self, key, value):
        if key == '鞠躬间隔':
            if not isinstance(value, (int, float)) or value < 1 or value > 300:
                return "鞠躬间隔必须在 1~300 之间"
        elif key == '传送时间':
            if not isinstance(value, (int, float)) or value < 10 or value > 600:
                return "传送时间必须在 10~600 之间"
        return None

    # ------------------- 辅助方法 -------------------
    def _wait_infinite(self, feature_name, box=None):
        """无限等待某个特征出现（无超时）"""
        self.log_info(f"无限等待图片 '{feature_name}' 出现...")
        while True:
            box_found = self.find_one(feature_name, box=box)
            if box_found:
                return box_found
            self.sleep(0.5)

    # ------------------- 步骤方法 -------------------
    def step1_wait_main_page(self):
        """等待主页面(mpg)出现，若超时则按ESC返回"""
        self.log_info("步骤1：等待主页面(mpg)出现...")
        while True:
            mpg_box = self.wait_feature('mpg', time_out=10, raise_if_not_found=False)
            if mpg_box:
                self.log_info("主页面已出现")
                return True
            self.log_info("10秒内未检测到mpg，按ESC尝试返回主页面")
            self.send_key('esc')
            self.sleep(2)

    def step2_open_map_and_teleport(self):
        """打开地图，3秒内寻找mallpot1/2并点击，未找到则点中心，再点go传送"""
        self.log_info("步骤2：打开地图并传送")
        self.send_key('m')
        self.sleep(1)

        # 计算tp图片搜索区域（复用为mallpot图标区域）
        x1, y1, x2, y2 = self.TP_AREA
        x1_s, y1_s = self._get_scaled_coordinates(x1, y1)
        x2_s, y2_s = self._get_scaled_coordinates(x2, y2)
        search_box = Box(x1_s, y1_s, width=x2_s - x1_s, height=y2_s - y1_s)

        # 3秒内轮询查找mallpot1或mallpot2
        start_time = time.time()
        found_icon = None
        while time.time() - start_time < 3:
            # 先尝试mallpot1
            pot = self.find_one('mallpot1', box=search_box)
            if pot:
                found_icon = pot
                break
            # 再尝试mallpot2
            pot = self.find_one('mallpot2', box=search_box)
            if pot:
                found_icon = pot
                break
            self.sleep(0.1)

        if found_icon:
            self.log_info("找到挂机点位图标，点击")
            self.click(found_icon, after_sleep=0.5)
        else:
            self.log_info("3秒内未找到mallpot图标，点击区域中心点（默认点位）")
            center_x = (x1_s + x2_s) // 2
            center_y = (y1_s + y2_s) // 2
            self.click(center_x, center_y, after_sleep=0.5)

        # 点击go完成传送
        go_feature = self.wait_feature('go', time_out=10, raise_if_not_found=False)
        if not go_feature:
            self.log_error("未找到go图片")
            return False
        self.click(go_feature, after_sleep=0.5)
        return True

    def step3_wait_mpg_and_move(self):
        """等待传送后回到主页面，然后按住W键4秒"""
        self.log_info("步骤3：等待传送后回到主页面(mpg)，超时30秒")
        mpg_box = self.wait_feature('mpg', time_out=30, raise_if_not_found=False)
        if not mpg_box:
            self.log_error("30秒内未检测到mpg，传送可能失败")
            return False
        self.log_info("主页面已恢复，按住W键4秒")
        self.send_key_down('w')
        self.sleep(3.5)
        self.send_key_up('w')
        self.sleep(0.5)
        return True

    # ------------------- 主循环 -------------------
    def run(self):
        """任务主入口"""
        try:
            self.log_info("===== 奇丽花刷花任务启动 =====", notify=True)

            while True:  # 外层循环：每次重新传送
                self.step1_wait_main_page()

                if not self.step2_open_map_and_teleport():
                    self.log_error("步骤2失败，5秒后重试")
                    self.sleep(5)
                    continue

                if not self.step3_wait_mpg_and_move():
                    self.log_error("步骤3失败，5秒后重试")
                    self.sleep(5)
                    continue

                # 投掷精灵1~5
                self.log_info("步骤4：投掷精灵1~5")
                for i in range(1, 6):
                    self.send_key(str(i))
                    self.sleep(0.3)
                    self.click(0.5, 0.5)
                    self.sleep(0.8)
                self.sleep(1)

                # 内层循环：鞠躬采集
                loop_start = time.time()
                teleport_time = self.config.get('传送时间', 180)
                bow_wait = self.config.get('鞠躬间隔', 15)

                while True:
                    # Tab -> 2 -> ESC
                    self.log_info("执行操作：Tab -> 2 -> ESC")
                    self.send_key('tab')
                    self.sleep(0.5)
                    self.send_key('2')
                    self.sleep(1)
                    self.send_key('esc')
                    self.sleep(0.5)

                    # 6 -> R -> 等待 -> X
                    self.log_info(f"执行操作：6 -> R -> 等待 {bow_wait} 秒 -> X")
                    self.send_key('6')
                    self.sleep(0.5)
                    self.send_key('r')
                    self.sleep(bow_wait)
                    self.send_key('x')
                    self.sleep(0.5)

                    if time.time() - loop_start >= teleport_time:
                        self.log_info("达到传送时间上限，重新传送")
                        break
                    self.log_info("继续鞠躬循环")

        except TaskDisabledException:
            self.log_info("奇丽花刷花任务被用户手动停止", notify=True)
        except Exception as e:
            self.log_error(f"奇丽花刷花任务异常: {e}", notify=True)
            self.screenshot("farm_flower_error")
            raise