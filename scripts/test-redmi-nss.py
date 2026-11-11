#!/usr/bin/env python3
"""Run the Redmi AX3000 NSS regression checks against prepared build sources."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel-source', type=Path)
    parser.add_argument('--ecm-source', type=Path)
    parser.add_argument('--hostapd-source', type=Path, help='Path to driver_nl80211.c')
    parser.add_argument('--rootfs', type=Path, help='Also smoke-check this built or extracted rootfs')
    parser.add_argument('--cc', default='cc')
    parser.add_argument('--runner', help='Run the C fixtures under this emulator with static linking')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]

    def source(option, pattern, marker=None):
        override = getattr(args, option)
        paths = [override.resolve()] if override else sorted((root / 'build_dir').glob(pattern))
        paths = [path for path in paths if (path / marker).is_file()] if marker else [
            path for path in paths if path.is_file()]
        if len(paths) != 1:
            parser.error(f'Expected one prepared source for --{option.replace("_", "-")}; '
                         'build the NSS profile first or pass its path explicitly.')
        return paths[0]

    kernel = source('kernel_source', 'target-*/linux-ipq50xx_*/linux-*',
                    'drivers/thermal/qcom/tsens-ipq5018.c')
    ecm = source('ecm_source',
                 'target-*/linux-ipq50xx_*/qca-nss-ecm-standard/qca-nss-ecm-*',
                 'frontends/nss/ecm_nss_common.h')
    hostapd = source('hostapd_source',
                     'target-*/hostapd-wpad-basic-wolfssl/hostapd-*/src/drivers/driver_nl80211.c')
    compiler = ['--cc', args.cc]
    if args.runner:
        compiler += ['--runner', args.runner]
    checks = [
        ('test-mi-dualboot.py', []),
        ('test-hostapd-vlan.py', [str(hostapd)] + compiler),
        ('test-ecm-stats-work.py', [str(ecm)] + compiler),
        ('test-ipq5018-thermal.py', [str(kernel)] + compiler),
    ]
    if args.rootfs:
        checks.append(('check-redmi-nss-rootfs.py', [str(args.rootfs.resolve())]))
    for script, options in checks:
        print(f'Running {script}', flush=True)
        result = subprocess.run([sys.executable, str(root / 'scripts' / script)] + options,
                                cwd=root)
        if result.returncode:
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
