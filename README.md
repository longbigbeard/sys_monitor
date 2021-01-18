## 安装运行依赖
- `apt install python3-requests python3-psutil:5.0.1-1`

## 修改sys_monitor.cfg文件
- 数据发送路径
- 网卡型号（ip -a查看）
- 数据发送时间间隔

## 安装、开机服务(root权限）
- ./install.sh

## 查看程序运行
- `systemctl status sys_monitor.service`
