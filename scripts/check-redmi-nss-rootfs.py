#!/usr/bin/env python3
"""Smoke-check NSS packaging and service permissions in an extracted rootfs."""
import argparse
from pathlib import Path
import stat
import sys


def check(root):
    failures = []

    def require(condition, description):
        print(f"{'PASS' if condition else 'FAIL'}: {description}")
        if not condition:
            failures.append(description)

    # The ubus daemon runs unprivileged and needs access to shared directories.
    for name in (".", "etc", "sbin", "lib", "usr", "usr/lib", "usr/sbin"):
        path = root / name
        require(path.is_dir() and bool(stat.S_IMODE(path.stat().st_mode) & stat.S_IXOTH),
                f"{name} traversable by the ubus service user")
    daemon = root / "sbin/ubusd"
    require(daemon.exists() and (stat.S_IMODE(daemon.stat().st_mode) & 0o005) == 0o005,
            "ubusd readable and executable by the ubus service user")
    autoload = root / "etc/modules.d/ath11k"
    lines = autoload.read_text().splitlines() if autoload.exists() else []
    require(any(line.split()[0] == "ath11k" and "nss_offload=1" in line.split()[1:]
                for line in lines if line.strip()), "ath11k NSS enabled at initial load")
    versions = [path for path in (root / "lib/modules").glob("*") if path.is_dir()]
    require(len(versions) == 1, "one kernel module directory installed")
    for name in ("ecm.ko", "ath11k.ko", "qca-nss-drv.ko"):
        paths = [path for version in versions for path in version.rglob(name)]
        require(len(paths) == 1 and paths[0].is_file() and paths[0].stat().st_size > 0,
                f"{name} installed")
    firmware = root / "lib/firmware/qca-nss0-retail.bin"
    require(firmware.exists() and firmware.stat().st_size > 0, "NSS core firmware installed")
    for name in ("qca-nss-ecm", "qca-nss-drv"):
        paths = (root / "etc/rc.d").glob(f"S[0-9][0-9]{name}")
        require(any(path.is_symlink() and path.exists() for path in paths), f"{name} enabled")
    require((root / "etc/sysctl.d/11-br-netfilter.conf").exists(),
            "bridge netfilter package configuration installed")
    config = root / "etc/sysctl.d/12-qca-nss-ecm-bridge.conf"
    settings = ["".join(line.split("#", 1)[0].split())
                for line in config.read_text().splitlines()] if config.exists() else []
    require("net.bridge.bridge-nf-call-custom=1" in settings,
            "QSDK custom bridge hook dispatch enabled")
    return not failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rootfs", type=Path)
    args = parser.parse_args()
    sys.exit(0 if check(args.rootfs.resolve()) else 1)
