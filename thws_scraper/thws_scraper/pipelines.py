# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import json
from datetime import datetime

from .items import RawPageItem


class RawOutputPipeline:
    """
    Dumps every RawPageItem as one line in data_raw_<TIMESTAMP>.jsonl
    """

    def open_spider(self, spider):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.raw_path = f"result/data_raw_{ts}.jsonl"
        spider.logger.info(f"[RawOutput] opening {self.raw_path}")
        self.raw_file = open(self.raw_path, "w", encoding="utf-8")

    def close_spider(self, spider):
        spider.logger.info(f"[RawOutput] closing {self.raw_path}")
        self.raw_file.close()

    def process_item(self, item, spider):
        if isinstance(item, RawPageItem):
            line = json.dumps(dict(item), ensure_ascii=False)
            self.raw_file.write(line + "\n")
        return item
