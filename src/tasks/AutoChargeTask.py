import time
from ok import TriggerTask, TaskDisabledException
from qfluentwidgets import FluentIcon

class AutoChargeTask(TriggerTask):
    """自动聚能触发器：检测到charge图片时按下X键"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "自动聚能"
        self.description = "适合同行状态的挂机，检测到聚能图标时自动按下X键"
        self.icon = FluentIcon.SYNC
        # 防止连续触发的时间间隔（秒）
        self.interval = 0.5
        self.last_charge_time = 0

    def run(self):
        try:
            # 查找图像特征 "charge"，置信度阈值设为 0.7
            charge_box = self.find_one("charge", threshold=0.7)
            if charge_box:
                current_time = time.time()
                if current_time - self.last_charge_time >= self.interval:
                    self.log_info("检测到聚能图标，按下X键")
                    self.send_key_down('x')
                    self.sleep(0.05)   # 短暂按下
                    self.send_key_up('x')
                    self.last_charge_time = current_time
        except TaskDisabledException:
            pass   # 任务被禁用时正常退出
        except Exception as e:
            self.log_error(f"自动聚能执行异常: {e}")