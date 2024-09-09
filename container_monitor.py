import os
import docker
import time
import csv
from datetime import datetime

# 获取脚本所在的目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 连接到 Docker
client = docker.from_env()

# 容器 ID 和主机名的映射
container_info = {
    '3f2bbd88136f': 'host10',
    '3b3b4f1079ef': 'host9',
    'e0d30533ac2d': 'host8'
}

# 创建 CSV 文件并写入表头
csv_filename = 'container_stats_multi.csv'
csv_path = os.path.join(script_dir, csv_filename)

with open(csv_path, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Host", "Container ID", "CPU %", "Memory Usage (MB)", "Memory Limit (MB)", "Memory %"])


# 监控时长（秒）
duration = 3600  # 1小时
interval = 5  # 每5秒收集一次数据

start_time = time.time()

def get_container_stats(container):
    stats = container.stats(stream=False)
    
    # CPU 使用率计算
    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
    cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
    
    # 内存使用情况
    mem_usage = stats['memory_stats']['usage'] / (1024 * 1024)  # 转换为 MB
    mem_limit = stats['memory_stats']['limit'] / (1024 * 1024)  # 转换为 MB
    mem_percent = (mem_usage / mem_limit) * 100
    
    return cpu_percent, mem_usage, mem_limit, mem_percent

try:
    while time.time() - start_time < duration:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for container_id, hostname in container_info.items():
            try:
                container = client.containers.get(container_id)
                cpu_percent, mem_usage, mem_limit, mem_percent = get_container_stats(container)
                
                with open(csv_path, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        current_time,
                        hostname,
                        container_id,
                        f"{cpu_percent:.2f}",
                        f"{mem_usage:.2f}",
                        f"{mem_limit:.2f}",
                        f"{mem_percent:.2f}"
                    ])
                
                print(f"{hostname} (Container {container_id}): CPU {cpu_percent:.2f}%, Memory {mem_percent:.2f}%")
            except docker.errors.NotFound:
                print(f"Container {container_id} ({hostname}) not found. Skipping...")
            except Exception as e:
                print(f"Error getting stats for container {container_id} ({hostname}): {str(e)}")
        
        time.sleep(interval)

except KeyboardInterrupt:
    print("\n监控被用户中断")

print(f"监控完成，数据已保存到 {csv_path}")