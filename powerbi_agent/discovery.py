"""Dò các phiên bản Power BI Desktop đang chạy trên máy (port msmdsrv)."""

import glob
import os
import sys


def find_active_pbi_ports():
    """
    Quét tìm cổng kết nối của các phiên bản Power BI Desktop đang chạy.
    Ưu tiên tìm thông qua cổng TCP đang lắng nghe của tiến trình msmdsrv.exe.
    Nếu thất bại, sẽ fallback về quét file msmdsrv.port.txt trên đĩa.
    """
    active_instances = []
    ports_found = set()

    # Cách 1: Truy vấn cổng TCP qua PowerShell (Dành cho Windows)
    if sys.platform == 'win32':
        try:
            import subprocess
            # Lệnh PowerShell lấy các cổng TCP đang lắng nghe của tiến trình msmdsrv
            command = (
                'Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | '
                'Where-Object { $_.OwningProcess -in '
                '(Get-Process -Name msmdsrv -ErrorAction SilentlyContinue).Id } | '
                'Select-Object -ExpandProperty LocalPort'
            )
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    port_str = line.strip()
                    if port_str.isdigit():
                        port = int(port_str)
                        if port not in ports_found:
                            ports_found.add(port)
                            active_instances.append({
                                "port": port_str,
                                "workspace_id": f"tcp_{port_str}"
                            })
        except Exception:
            pass  # Nếu lỗi, tiếp tục thử các cách sau

    if active_instances:
        return active_instances

    # Cách 2: Quét file msmdsrv.port.txt truyền thống ở AppData\Local (MSI)
    local_app_data = os.environ.get('LOCALAPPDATA')
    if local_app_data:
        workspace_dir = os.path.join(local_app_data, 'Microsoft', 'Power BI Desktop', 'AnalysisServicesWorkspaces')
        if os.path.exists(workspace_dir):
            port_files = glob.glob(os.path.join(workspace_dir, '*', 'Data', 'msmdsrv.port.txt'))
            for port_file in port_files:
                try:
                    with open(port_file, 'r', encoding='utf-16') as f:
                        port = f.read().strip()
                    parent_dir = os.path.dirname(os.path.dirname(port_file))
                    dir_name = os.path.basename(parent_dir)
                    if port.isdigit() and int(port) not in ports_found:
                        ports_found.add(int(port))
                        active_instances.append({
                            "port": port,
                            "workspace_id": dir_name
                        })
                except Exception:
                    continue

    # Cách 3: Thử quét trong thư mục LocalCache của Store App nếu cách 2 không có
    if local_app_data and not active_instances:
        store_workspaces = glob.glob(os.path.join(
            local_app_data, 'Packages', 'Microsoft.MicrosoftPowerBIDesktop*',
            'LocalCache', 'Local', 'Microsoft', 'Power BI Desktop', 'AnalysisServicesWorkspaces'
        ))
        for workspace_dir in store_workspaces:
            if os.path.exists(workspace_dir):
                port_files = glob.glob(os.path.join(workspace_dir, '*', 'Data', 'msmdsrv.port.txt'))
                for port_file in port_files:
                    try:
                        with open(port_file, 'r', encoding='utf-16') as f:
                            port = f.read().strip()
                        parent_dir = os.path.dirname(os.path.dirname(port_file))
                        dir_name = os.path.basename(parent_dir)
                        if port.isdigit() and int(port) not in ports_found:
                            ports_found.add(int(port))
                            active_instances.append({
                                "port": port,
                                "workspace_id": dir_name
                            })
                    except Exception:
                        continue

    return active_instances
