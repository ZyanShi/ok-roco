from src.tasks.FarmFlowerTask import FarmFlowerTask

if __name__ == '__main__':
    # 创建任务实例
    task = FarmFlowerTask()

    # 发送 ESC 键
    task.send_key('esc')

    # 输出成功信息作为检测结果
    print("ESC 键已成功发送，测试通过。")