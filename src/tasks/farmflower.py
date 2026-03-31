import time
from ok import Box, TaskDisabledException
from qfluentwidgets import FluentIcon
from src.tasks.MyBaseTask import MyBaseTask


class FarmFlowerTask(MyBaseTask):
    """奇丽花刷花自动化任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "奇丽花刷花"
        self.description = "自动执行奇丽花刷花序列：传送、投掷精灵、背包操作、循环采集"
        self.group_icon = FluentIcon.LEAF
        self.icon = FluentIcon.LEAF

        # 默认配置（UI可调）
        self.default_config.update({
            '收花方式': '上坐骑',
            '背包按键': 'z',  # 打开精灵背包的按键
            '等待时间': 10,          # 步骤5和11中的等待时间（秒）

        })
        self.config_description = {
            '等待时间': '步骤5和11中的等待时间（秒）',
            '背包按键': '打开精灵背包的快捷键',
            '收花方式': '收花时的操作方式',
        }

        # 定义下拉选项（参考 MoKuaiJinBiTask）
        self.config_type = {
            '收花方式': {'type': "drop_down", 'options': ['上坐骑']}
        }

        # 预定义区域坐标（基于1920x1080）
        self.TP_AREA = (740, 310, 1070, 650)   # 地图上tp图标的搜索区域

    def validate_config(self, key, value):
        """验证配置项是否合法"""
        if key == '等待时间':
            if not isinstance(value, (int, float)) or value < 1 or value > 300:
                return "等待时间必须在 1~300 之间"
        elif key == '背包按键':
            if not isinstance(value, str) or len(value) != 1:
                return "背包按键必须是单个字符"
        elif key == '收花方式':
            if value not in ['上坐骑', '投掷精灵']:
                return "收花方式必须是 '上坐骑' 或 '投掷精灵'"
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

    def _open_backpack(self):
        """按配置的按键打开精灵背包"""
        key = self.config.get('背包按键', 'z')
        self.log_info(f"按 '{key}' 打开精灵背包")
        self.send_key(key)
        self.sleep(0.5)

    # ------------------- 步骤方法 -------------------
    def step1_wait_main_page(self):
        """步骤1：无限等待mpg图片出现，判断为主页面"""
        self.log_info("步骤1：等待主页面(mpg)出现...")
        self._wait_infinite('mpg')
        self.log_info("主页面已出现")
        return True

    def step2_open_map_and_teleport(self):
        """步骤2：打开地图，点击tp（带偏移校准），再点击go"""
        self.log_info("步骤2：打开地图并传送")
        self.send_key('m')
        self.sleep(1)

        # 计算tp图片搜索区域
        x1, y1, x2, y2 = self.TP_AREA
        x1_s, y1_s = self._get_scaled_coordinates(x1, y1)
        x2_s, y2_s = self._get_scaled_coordinates(x2, y2)
        tp_box = Box(x1_s, y1_s, width=x2_s - x1_s, height=y2_s - y1_s)

        tp_feature = self.wait_feature('tp', time_out=10, box=tp_box, raise_if_not_found=False)
        if not tp_feature:
            self.log_error("未找到tp图片，传送失败")
            return False

        # 偏移校准（可手动调整）
        OFFSET_X, OFFSET_Y = 0, 0
        center = tp_feature.center()
        click_x = center[0] + OFFSET_X
        click_y = center[1] + OFFSET_Y
        self.log_info(f"点击tp坐标: ({click_x}, {click_y})")
        self.click(click_x, click_y, after_sleep=0.5)

        go_feature = self.wait_feature('go', time_out=10, raise_if_not_found=False)
        if not go_feature:
            self.log_error("未找到go图片")
            return False
        self.click(go_feature, after_sleep=0.5)
        return True

    def step3_wait_mpg_and_move(self):
        """步骤3：等待mpg再次出现（超时30s），然后按住D键2秒，W键2秒"""
        self.log_info("步骤3：等待传送后回到主页面(mpg)，超时30秒")
        mpg_box = self.wait_feature('mpg', time_out=30, raise_if_not_found=False)
        if not mpg_box:
            self.log_error("30秒内未检测到mpg，传送可能失败")
            return False
        self.log_info("主页面已恢复，按住D键2秒")
        self.send_key_down('d')
        self.sleep(2)
        self.send_key_up('d')
        self.log_info("按住W键2秒")
        self.send_key_down('w')
        self.sleep(2)
        self.send_key_up('w')
        self.sleep(0.5)
        return True

    def step4_throw_spirits(self):
        """步骤4：投掷精灵序列：1~6，每个按键后延迟0.7s，左键，再延迟1s"""
        self.log_info("步骤4：开始投掷精灵（1~6）")
        for i in range(1, 7):
            key = str(i)
            self.log_debug(f"投掷精灵 {key}")
            self.send_key(key)
            self.sleep(0.7)          # 按键后延迟0.7秒
            self.click(0.5, 0.5)     # 左键点击屏幕中心
            self.sleep(1)            # 点击后延迟1秒

    def step5_wait_custom(self):
        """步骤5：等待用户配置的时间（秒）"""
        wait_sec = self.config.get('等待时间', 10)
        self.log_info(f"步骤5：等待 {wait_sec} 秒")
        self.sleep(wait_sec)

    def step6_open_backpack_and_click_left(self):
        """步骤6：打开背包，等待left图片并点击，然后ESC返回"""
        self.log_info("步骤6：打开背包，点击左侧按钮(left)")
        self._open_backpack()
        left_box = self.wait_feature('left', time_out=10, raise_if_not_found=False)
        if not left_box:
            self.log_error("未找到left图片")
            return False
        self.click(left_box, after_sleep=0.5)
        self.send_key('esc')
        self.sleep(1.5)
        return True

    def step7_press_keys(self):
        """步骤7：根据收花方式配置执行操作"""
        method = self.config.get('收花方式', '上坐骑')
        if method == '上坐骑':
            self.log_info("步骤7（上坐骑方式）：按1，R，延迟1秒，X")
            self.send_key('1')
            self.sleep(0.05)
            self.send_key('r')
            self.sleep(1)
            self.send_key('x')
            self.sleep(0.5)
        else:  # 投掷精灵
            self.log_info("步骤7（投掷精灵方式）：按1，延迟0.5秒，左键点击")
            self.send_key('1')
            self.sleep(0.5)
            self.click(0.5, 0.5)   # 点击屏幕中心
            self.sleep(0.5)

    def step8_open_backpack_and_click_right(self):
        """步骤8：打开背包，等待right图片并点击，然后ESC返回"""
        self.log_info("步骤8：打开背包，点击右侧按钮(right)")
        self._open_backpack()
        right_box = self.wait_feature('right', time_out=10, raise_if_not_found=False)
        if not right_box:
            self.log_error("未找到right图片")
            return False
        self.click(right_box, after_sleep=0.5)
        self.send_key('esc')
        self.sleep(2)
        return True

    def step9_repeat_step4(self):
        """步骤9：重复第四步（投掷精灵）"""
        self.log_info("步骤9：重复投掷精灵序列")
        self.step4_throw_spirits()

    def step10_tab_and_two(self):
        """步骤10：发送Tab键，延迟0.5，按2，延迟1，ESC返回"""
        self.log_info("步骤10：发送Tab键，然后按2")
        self.send_key('tab')
        self.sleep(0.5)
        self.send_key('2')
        self.sleep(1)
        self.send_key('esc')
        self.sleep(0.5)

    def step11_repeat_step5(self):
        """步骤11：重复第五步（等待自定义时间）"""
        self.log_info("步骤11：重复等待")
        self.step5_wait_custom()

    def step12_repeat_step6(self):
        """步骤12：重复第六步（打开背包点left）"""
        self.log_info("步骤12：重复打开背包点left")
        return self.step6_open_backpack_and_click_left()

    def step13_repeat_step7_and_check(self):
        """
        步骤13：重复第七步（根据收花方式），然后OCR检测向阳花，超时2秒。
        返回 True 表示检测到向阳花（可继续），False 表示未检测到（无法继续产出）
        """
        self.log_info("步骤13：执行收花操作，然后检测向阳花")
        self.step7_press_keys()

        # OCR检测区域（原始坐标）
        x1, y1, x2, y2 = 1685, 275, 1770, 315
        x1_s, y1_s = self._get_scaled_coordinates(x1, y1)
        x2_s, y2_s = self._get_scaled_coordinates(x2, y2)
        ocr_box = Box(x1_s, y1_s, width=x2_s - x1_s, height=y2_s - y1_s)

        result = self.wait_ocr(match="向阳花", box=ocr_box, time_out=2, raise_if_not_found=False)
        if result:
            self.log_info("检测到向阳花，可继续产出")
            return True
        else:
            self.log_info("未检测到向阳花，无法继续产出")
            return False

    def step14_repeat_step8(self):
        """步骤14：重复第八步（打开背包点right）"""
        self.log_info("步骤14：重复打开背包点right")
        return self.step8_open_backpack_and_click_right()

    # ------------------- 主循环 -------------------
    def run(self):
        """任务主入口"""
        try:
            self.log_info("===== 奇丽花刷花任务启动 =====", notify=True)

            outer_loop = 0
            while True:
                outer_loop += 1
                self.log_info(f"========== 第 {outer_loop} 轮完整流程开始 ==========")

                # 执行步骤1~8（前置流程）
                self.step1_wait_main_page()

                if not self.step2_open_map_and_teleport():
                    self.log_error("步骤2失败，重试")
                    self.sleep(5)
                    continue

                if not self.step3_wait_mpg_and_move():
                    self.log_error("步骤3失败，重试")
                    self.sleep(5)
                    continue

                self.step4_throw_spirits()
                self.step5_wait_custom()

                if not self.step6_open_backpack_and_click_left():
                    self.log_error("步骤6失败，重试")
                    self.sleep(5)
                    continue

                self.step7_press_keys()

                if not self.step8_open_backpack_and_click_right():
                    self.log_error("步骤8失败，重试")
                    self.sleep(5)
                    continue

                # 内层循环：步骤9~14，无限循环直到检测不到向阳花
                inner_loop = 0
                while True:
                    inner_loop += 1
                    self.log_info(f"--- 内层循环第 {inner_loop} 次 ---")

                    self.step9_repeat_step4()
                    self.step10_tab_and_two()
                    self.step11_repeat_step5()

                    if not self.step12_repeat_step6():
                        self.log_error("步骤12失败，中断内层循环")
                        break

                    can_continue = self.step13_repeat_step7_and_check()
                    if not self.step14_repeat_step8():
                        self.log_error("步骤14失败，中断内层循环")
                        break

                    if not can_continue:
                        self.log_info("无法继续产出向阳花，跳出内层循环，重新从步骤1开始")
                        break

                # 内层循环结束，继续下一轮外层循环（回到步骤1）
                self.log_info("内层循环结束，准备开始新一轮完整流程")

        except TaskDisabledException:
            self.log_info("奇丽花刷花任务被用户手动停止", notify=True)
        except Exception as e:
            self.log_error(f"奇丽花刷花任务异常: {e}", notify=True)
            self.screenshot("farm_flower_error")
            raise