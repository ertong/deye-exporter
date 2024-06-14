import contextlib
import datetime
import json
import logging
import math
import threading
import time
from collections import defaultdict

import prometheus_client
import requests
import yaml
from prometheus_client.metrics_core import GaugeMetricFamily


class InvPoller:
    def __init__(self, name, ip, serial):
        self.name: str = name
        self.ip: str = ip
        self.serial: str = serial
        self.stat: dict = {}
        self.stat_time: int = 0

        from deye.solarman import Inverter
        self.inv = inv = Inverter("./", int(self.serial), self.ip, 8899, 1, "inverter_definitions/deye_sg04lp3.yaml")

    def run(self):
        while True:
            try:
                self.tick()
                time.sleep(5)
            except Exception as e:
                logging.error(f"[{self.name}]", exc_info=e)
                time.sleep(30)

    def tick(self):
        self.inv.disconnect_from_server()
        self.inv.get_statistics()
        stat = self.inv.get_current_val()
        if "Grid Voltage L1" not in stat:
            return

            # logging.info(f'{stat["Grid Frequency"]}\t{stat["Grid Voltage L1"]}\t{stat["Grid Current L1"]}')
        line = (
                # f'\t{stat["DC Temperature"]:.3f}\t{stat["AC Temperature"]:.3f}\t{res_hex}'
                )

        logging.info(
            f'{self.name}:\t{stat["Grid Voltage L1"]:.3f}\t{stat["Grid Voltage L2"]:.3f}\t{stat["Grid Voltage L3"]:.3f}'
            f'\t{stat["Current L1"]:.3f}\t{stat["Current L2"]:.3f}\t{stat["Current L3"]:.3f}'
            f'\t{stat["Total Grid Power"]:.3f}\t{stat["Total Load Power"]:.3f}'
            f'\t{stat["DC Temperature"]:.3f}\t{stat["AC Temperature"]:.3f}'
        )

        self.stat = stat
        self.stat_time = time.time()


class CustomCollector(object):
    def __init__(self, poolers: list[InvPoller]):
        self.poolers = poolers

    def collect(self):
        now = time.time()
        for pooler in self.poolers:
            if now - pooler.stat_time > 30:
                continue

            stat = pooler.stat

            for key in stat.keys():
                if key in ["Alert", "Control Board Version No.", "Communication Board Version No.", "Inverter ID", "SmartLoad Enable Status"]:
                    continue
                m = GaugeMetricFamily("deye", '', labels=["name", "key"])
                m.add_metric([pooler.name, key], stat[key])
                yield m


def main():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=logging.INFO, format=log_format)

    prometheus_client.start_http_server(9090)

    with open("config.yml", 'r') as f:
        config = yaml.safe_load(f)

    poolers = []

    for inv in config['inverters']:
        pooler = InvPoller(inv['name'], inv['ip'], inv['serial'])
        import threading
        thread = threading.Thread(target=pooler.run, daemon=True, name=f'pooler[{pooler.name}]')
        thread.start()
        poolers.append(pooler)

    collector = CustomCollector(poolers)
    prometheus_client.REGISTRY.register(collector)

    while True:
        time.sleep(5)


if __name__ == '__main__':
    main()
