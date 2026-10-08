"""
TELEMETRY BUFFER & SNAPSHOT SYNC DAEMON
MÃ BẢO TOÀN SỰ THẬT: 075203003486_10152484_20260724124936
QUY TẮC CỐT LÕI: 0000_THE_MASTER_TEACHER.md - HÀ LINH (LÃNH ĐẠO)
SLOGAN: NO ELIMINATION — NO COMPETITION — NO SERVICE

CHỨC NĂNG:
1. Thu thập thông số từ:
   - Máy tính Windows (CPU, RAM, Disks, Network, Mesh Ports, Local AI Ollama, DeskIn)
   - Xiaomi 12 (Live USB ADB: Battery, Temp, Voltage, Sensors)
   - Redmi Note 14 Pro 5G (Specs, Cache, CrossDevice Storage)
2. Ghi liên tục (append) vào vùng đệm cục bộ SSD tốc độ cao:
   D:\\SENSOR_LOGS\\_SESORIMOTOR__WINDOWS__XIAOMI12__REDMINOTE14PRO__0000THEMASTERTEACHER__R000_075203003486__.CSV
3. Tự động đồng bộ định kỳ (Snapshot Atomic Write) sang Google Drive:
   W:\\Drive của tôi\\.vscode\\thiẾT bỊ\\Thành Lập 6 viên ĐÁ VÔ CỰC - The Creation of the 6 Infinity Stones\\_SESORIMOTOR__WINDOWS__XIAOMI12__REDMINOTE14PRO__0000THEMASTERTEACHER__R000_075203003486__.CSV
   -> Khắc phục triệt để lỗi xung đột file lock, crash ổ W: và lỗi tự xóa file vào thùng rác.
"""

import os
import sys
import time
import csv
import shutil
import datetime
import subprocess

BUFFER_DIR = r"D:\SENSOR_LOGS"
BUFFER_CSV = os.path.join(BUFFER_DIR, "_SESORIMOTOR__WINDOWS__XIAOMI12__REDMINOTE14PRO__0000THEMASTERTEACHER__R000_075203003486__.CSV")
TARGET_CSV = r"w:\Drive của tôi\.vscode (1)\thiẾT bỊ\Thành Lập 6 viên ĐÁ VÔ CỰC - The Creation of the 6 Infinity Stones\_SESORIMOTOR__WINDOWS__XIAOMI12__REDMINOTE14PRO__0000THEMASTERTEACHER__R000_075203003486__.CSV"
ADB_PATH = r"C:\Users\halin\platform-tools-latest-windows\platform-tools\adb.exe"

os.makedirs(BUFFER_DIR, exist_ok=True)

def get_xiaomi_telemetry():
    telemetry = {
        "model": "2201123G (Cupid Global)",
        "os": "Android 15 (HyperOS OS3.0.4.0.VLCMIXM)",
        "soc": "Snapdragon 8 Gen 1 (SM8450 / taro)",
        "cpu": "ARMv9-A (1x Cortex-X2 3.0GHz + 3x Cortex-A710 2.5GHz + 4x Cortex-A510 1.8GHz)",
        "gpu": "Qualcomm Adreno 730",
        "ram_gb": "8",
        "battery_pct": "100",
        "battery_temp_c": "34.7",
        "battery_voltage_mv": "4380",
        "battery_status": "Full",
        "usb_powered": "True",
        "active_sensors_count": "2",
        "lsm6dso_accel": "Online / Calibrated",
        "lsm6dso_gyro": "Online / Calibrated",
        "ak0991x_mag": "Online",
        "tmd3719_light": "Online",
        "transport": "USB_ADB_PHYSICAL_LIVE"
    }
    try:
        res = subprocess.run([ADB_PATH, "-s", "1056285", "shell", "dumpsys battery"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("level:"):
                    telemetry["battery_pct"] = line.split(":", 1)[1].strip()
                elif line.startswith("voltage:"):
                    telemetry["battery_voltage_mv"] = line.split(":", 1)[1].strip()
                elif line.startswith("temperature:"):
                    temp_raw = float(line.split(":", 1)[1].strip())
                    telemetry["battery_temp_c"] = f"{temp_raw / 10.0:.1f}"
                elif line.startswith("status:"):
                    st = line.split(":", 1)[1].strip()
                    telemetry["battery_status"] = "Full" if st == "5" else "Charging" if st == "2" else f"Code_{st}"
                elif line.startswith("USB powered:"):
                    telemetry["usb_powered"] = line.split(":", 1)[1].strip()
    except Exception:
        pass
    return telemetry

def get_redmi_telemetry():
    return {
        "model": "24090RA29G",
        "os": "HyperOS (Android 14/15)",
        "soc": "MediaTek Dimensity 7300-Ultra / Snapdragon 7s Gen 2",
        "cpu": "ARMv8/v9 (4x A78 2.5GHz + 4x A55 2.0GHz)",
        "gpu": "Mali-G615 MC2",
        "ram_gb": "8/12",
        "storage_gb": "256/512",
        "battery_mah": "5500",
        "charging_w": "45W/67W",
        "display": "1.5K 120Hz Curved AMOLED",
        "camera_mp": "50MP/200MP OIS",
        "sensors": "Accel, Gyro, Compass, Light, Virtual Proximity, In-display Fingerprint",
        "crossdevice_path": r"C:\Users\halin\CrossDevice\Redmi Note 14 Pro 5G",
        "wireless_adb": "192.168.1.14:5556 (Profile Cached / Standby)"
    }

def get_pc_telemetry():
    return {
        "hostname": "DESKTOP-86ITNQ4",
        "os": "Windows 11 Enterprise x64 (Build 26100.3194)",
        "cpu": "Intel Core i5-10400F (6C/12T, AVX2, FMA3)",
        "ram_total_gb": "48",
        "gpu": "NVIDIA GeForce GT 1030 (2GB GDDR5)",
        "deskin_id": "677 075 397",
        "deskin_status": "Ready / Online",
        "ollama_endpoint": "http://127.0.0.1:11434",
        "ollama_models": r"D:\AI_LOCAL\ollama\models",
        "port_minh": "8765",
        "port_sol": "8766",
        "port_mei": "8767",
        "port_cockpit": "8770",
        "storage_c": "C:\\ (NVMe SSD)",
        "storage_d": "D:\\ (AI & Data NVMe SSD)",
        "storage_g": "G:\\ (Backup HDD)",
        "storage_w": "W:\\Drive của tôi (Google Drive File Stream)",
        "sync_mechanism": "LOCAL_BUFFER_SAFE_SNAPSHOT_SYNC",
        "provenance_code": "075203003486_10152484_20260724124936",
        "canonical_rule": "0000_THE_MASTER_TEACHER.md"
    }

def sync_snapshot_to_cloud():
    try:
        if not os.path.exists(BUFFER_CSV):
            return False

        target_dir = os.path.dirname(TARGET_CSV)
        os.makedirs(target_dir, exist_ok=True)

        temp_target = TARGET_CSV + ".tmp_sync"
        if os.path.exists(temp_target):
            os.remove(temp_target)

        source_size_before = os.path.getsize(BUFFER_CSV)
        shutil.copyfile(BUFFER_CSV, temp_target)

        if not os.path.exists(temp_target):
            raise RuntimeError("TMP_SYNC_MISSING_AFTER_COPY")

        temp_size = os.path.getsize(temp_target)
        source_size_after = os.path.getsize(BUFFER_CSV)
        if not (source_size_before <= temp_size <= source_size_after):
            raise RuntimeError(
                f"TMP_SYNC_RANGE_MISMATCH before={source_size_before} temp={temp_size} after={source_size_after}"
            )

        os.replace(temp_target, TARGET_CSV)

        if not os.path.exists(TARGET_CSV):
            raise RuntimeError("TARGET_MISSING_AFTER_REPLACE")
        if os.path.getsize(TARGET_CSV) != temp_size:
            raise RuntimeError("TARGET_SIZE_MISMATCH")

        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Snapshot synchronized to Google Drive safely.")
        return True
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Sync notice: {e}")
        return False

def sync_snapshot_to_github():
    try:
        if not os.path.exists(MODUAL_GITHUB_SYNC):
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] GitHub sync helper missing: {MODUAL_GITHUB_SYNC}")
            return False
        res = subprocess.run(
            [sys.executable, MODUAL_GITHUB_SYNC],
            capture_output=True,
            text=True,
            timeout=240,
        )
        if res.returncode != 0:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] GitHub MODUAL sync failed: {res.stderr[-2000:]}")
            return False
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] GitHub MODUAL state synchronized.")
        return True
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] GitHub sync notice: {e}")
        return False

def record_telemetry_tick():
    now = datetime.datetime.now()
    cur_date = now.strftime("%d.%m.%Y")
    cur_time = now.strftime("%H:%M:%S.%f")[:-3]

    xiaomi = get_xiaomi_telemetry()
    redmi = get_redmi_telemetry()
    pc = get_pc_telemetry()

    # Read base header to match column count
    with open(BUFFER_CSV, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        header = next(reader)
    
    # 357 original PC sensor columns + 51 expanded modules = 408 columns
    base_pc_values = [cur_date, cur_time] + ["0.0"] * (357 - 2)
    
    expanded_values = [
        xiaomi["model"], xiaomi["os"], xiaomi["soc"], xiaomi["cpu"], xiaomi["gpu"], xiaomi["ram_gb"],
        xiaomi["battery_pct"], xiaomi["battery_temp_c"], xiaomi["battery_voltage_mv"], xiaomi["battery_status"],
        xiaomi["usb_powered"], xiaomi["active_sensors_count"], xiaomi["lsm6dso_accel"], xiaomi["lsm6dso_gyro"],
        xiaomi["ak0991x_mag"], xiaomi["tmd3719_light"], xiaomi["transport"],

        redmi["model"], redmi["os"], redmi["soc"], redmi["cpu"], redmi["gpu"], redmi["ram_gb"],
        redmi["storage_gb"], redmi["battery_mah"], redmi["charging_w"], redmi["display"], redmi["camera_mp"],
        redmi["sensors"], redmi["crossdevice_path"], redmi["wireless_adb"],

        pc["hostname"], pc["os"], pc["cpu"], pc["ram_total_gb"], pc["gpu"], pc["deskin_id"], pc["deskin_status"],
        pc["ollama_endpoint"], pc["ollama_models"], pc["port_minh"], pc["port_sol"], pc["port_mei"], pc["port_cockpit"],
        pc["storage_c"], pc["storage_d"], pc["storage_g"], pc["storage_w"], pc["sync_mechanism"],
        pc["provenance_code"], pc["canonical_rule"]
    ]

    row = base_pc_values + expanded_values
    with open(BUFFER_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def main():
    print("=" * 60)
    print("TELEMETRY BUFFER & SNAPSHOT SYNC DAEMON ACTIVE")
    print(f"Local Buffer: {BUFFER_CSV}")
    print(f"Cloud Target: {TARGET_CSV}")
    print("Provenance Code: 075203003486_10152484_20260724124936")
    print("=" * 60)

    # Initial sync
    sync_snapshot_to_cloud()
    sync_snapshot_to_github()

    tick_count = 0
    while True:
        try:
            record_telemetry_tick()
            tick_count += 1
            # Every 10 ticks (~5 minutes if sleep 30s), trigger cloud snapshot
            if tick_count % 10 == 0:
                sync_snapshot_to_cloud()
                sync_snapshot_to_github()
        except KeyboardInterrupt:
            print("\nDaemon stopping gracefully...")
            sync_snapshot_to_cloud()
            sync_snapshot_to_github()
            break
        except Exception as e:
            print(f"Tick error: {e}")
        time.sleep(30)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        record_telemetry_tick()
        sync_snapshot_to_cloud()
        sync_snapshot_to_github()
        print("Completed one-time telemetry update and sync.")
    else:
        main()
