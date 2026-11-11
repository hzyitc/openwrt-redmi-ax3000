#!/usr/bin/env python3
"""Ensure merged flash layouts cannot enter the stock dual-slot write path."""
import os
from pathlib import Path
import subprocess


root = Path(__file__).resolve().parents[1]
source = (root / "target/linux/ipq50xx/base-files/lib/upgrade/mi_dualboot.sh").read_text()
source = source.replace(". /lib/functions.sh", "")
stubs = """
v() { :; }
find_mtd_index() {
    case "$1" in
        rootfs) echo 18;;
        rootfs_1) [ "$TEST_LAYOUT" = dual ] && echo 19;;
    esac
}
mkdir() { echo UNEXPECTED_MKDIR >&2; return 99; }
fw_printenv() { echo UNEXPECTED_ENV_ACCESS >&2; return 99; }
identify() { echo UNEXPECTED_IMAGE_CHECK >&2; return 99; }
ubiformat() { echo UNEXPECTED_FLASH >&2; return 99; }
"""


def run(layout, command, expected):
    result = subprocess.run(
        ["bash", "-c", stubs + source + "\n" + command],
        env={**os.environ, "TEST_LAYOUT": layout}, capture_output=True, text=True,
    )
    if result.returncode != expected or result.stderr:
        raise SystemExit(f"FAIL: {layout}: {command}: {result.returncode}: {result.stderr}")


run("single", "mi_dualboot_require_layout", 1)
run("dual", "mi_dualboot_require_layout", 0)
run("single", "mi_dualboot_check_image dummy.ubi", 1)
run("single", "mi_dualboot_do_upgrade dummy.ubi", 1)
print("PASS: dual layout accepted; merged layout rejected before flash or environment access")
