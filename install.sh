#!/usr/bin/bash 
set +e
 
# 创建文件
rm -rf /opt/sys_monitor
mkdir -p /opt/sys_monitor
chmod 777 /opt/sys_monitor

# 拷贝配置文件和开机服务
cp -rf start_monitor.py sys_monitor.cfg /opt/sys_monitor/
cp -f sys_monitor.service /lib/systemd/system/
chmod 644 /lib/systemd/system/sys_monitor.service

# 开启服务
systemctl daemon-reload
systemctl enable sys_monitor.service 
systemctl start sys_monitor.service

echo 'success'


