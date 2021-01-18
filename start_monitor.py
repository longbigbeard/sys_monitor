#!/usr/bin/env python3

import configparser, json, os, socket, time
import psutil, requests
import logging
from logging.handlers import RotatingFileHandler


class SystemIndicators():
    def __init__(self, config_info):

        self.url = config_info['post_url']
        self.header = eval(config_info['header'])
        self.net_card = config_info['net_card']
        self.log_size = int(config_info['log_size'])
        self.metric_time = int(time.time() * 1000)
        self.quota_data = []
        self._init_log()
        self.get_base_info()

    def _init_log(self):
        self.log = logging.getLogger()
        fmt = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        header = RotatingFileHandler(r'/opt/sys_monitor/monitor.log', 'a', self.log_size * 1024 * 1024, 2, 'utf-8')
        header.setFormatter(fmt)
        self.log.addHandler(header)
        self.log.setLevel(logging.INFO)

    def get_base_info(self):
        self.system_code = 'deepin_os'
        self.hostname = socket.gethostname()
        self.ipaddr = ''
        self.mac = ''
        net_ip_info = psutil.net_if_addrs().get(self.net_card)
        if net_ip_info:
            self.ipaddr = net_ip_info[0].address
            self.mac = net_ip_info[2].address

    def format_data(self, metric, metric_type, metric_value):
        data = {
            "metric": metric,
            "metricType": metric_type,
            "metricValue": metric_value,
            "metricTime": self.metric_time
        }
        self.quota_data.append(data)

    def get_cpu_info(self):
        cpu_info = psutil.cpu_times_percent(interval=1)
        metric_value = {
            "common": cpu_info.user + cpu_info.nice + cpu_info.system,
            "user": cpu_info.user,
            "nice": cpu_info.nice,
            "system": cpu_info.system,
            "idle": cpu_info.idle,
            "iowait": cpu_info.iowait,
        }

        for metric_type in ['common', 'user', 'nice', 'system', 'iowait', 'idle']:
            self.format_data('CPU', metric_type, metric_value.get(metric_type))

    def get_mem_info(self):
        mem_info = psutil.virtual_memory()
        self.format_data('MEMORY', 'common', mem_info.percent)

    def get_net_and_file_rw_info(self):
        start_net_info = psutil.net_io_counters()
        start_file_rw_info = psutil.disk_io_counters()
        time.sleep(1)
        end_net_info = psutil.net_io_counters()
        end_file_rw_info = psutil.disk_io_counters()

        metric_value = {
            "in": end_net_info.bytes_recv - start_net_info.bytes_recv,
            "out": end_net_info.bytes_sent - start_net_info.bytes_sent,
            "read": end_file_rw_info.read_bytes - start_file_rw_info.read_bytes,
            "write": end_file_rw_info.write_bytes - start_file_rw_info.write_bytes
        }

        for metric_type in ['in', 'out', 'read', 'write']:
            metric = "NETWORK" if metric_type in ['in', 'out'] else 'FILE_RW'
            self.format_data(metric, metric_type, metric_value.get(metric_type))

    def get_disk_info(self):
        disk_info = os.popen("df -m |grep / |awk '{sum +=$3};{sum2 += $4};END {print sum/sum2*100}'").readline()
        self.format_data('DISK', 'common', round(float(disk_info.strip('\n').strip()), 2) if disk_info else 0)

    def do_post(self):
        params = {
            "systemCode": self.system_code,
            "ipAddr": self.ipaddr,
            "macAddr": self.mac,
            "hostname": self.hostname,
            "quotaData": self.quota_data
        }
        self.log.info(params)
        # 尝试三次，成功一次即退出
        for x in range(3):
            try:
                response = requests.post(self.url, data=json.dumps(params), headers=self.header)
                if response.status_code != 200:
                    continue
                response_text = json.loads(response.text)
                if response_text.get('code', 1) == 0:
                    self.log.info(response_text)
                    break
            except Exception as e:
                # print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "data send error: ", e)
                self.log.error(e)

    def run(self):
        self.get_cpu_info()
        self.get_mem_info()
        self.get_net_and_file_rw_info()
        self.get_disk_info()
        self.do_post()
        self.quota_data = []


if __name__ == '__main__':
    config_info = configparser.ConfigParser()
    config_info.read(r'/opt/sys_monitor/sys_monitor.cfg')
    config_info = config_info['DEFAULT']
    timespan = int(config_info['timespan'])

    test = SystemIndicators(config_info)
    while True:
        test.run()
        time.sleep(timespan)
