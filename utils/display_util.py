# Author: RockMan
# CreateTime: 2024/7/18
# FileName: display_util
# Description: simple introduction of the code
import pandas as pd
from utils.db_util import Constants as C


# 将数据处理后显示到web页面上
class DisplayUtil:
    @staticmethod
    def add_total(raw: pd.DataFrame, flag: int = 1) -> pd.DataFrame:
        # flag为1时，合计在最后，为0时，合计在最前

        if raw.empty:
            return raw

        df = raw.copy()
        rate_total = df[C.INST_GROUP].sum() * 365 / df[C.PRODUCT].sum() * 100 if df[C.PRODUCT].sum() != 0 else 0

        total = {
            df.columns[0]: '合计',
            C.AVG_AMT: df[C.AVG_AMT].sum(),
            C.INST_GROUP: df[C.INST_GROUP].sum(),
            C.PRODUCT: df[C.PRODUCT].sum(),
            C.WEIGHT_RATE: rate_total
        }
        if flag == 1:
            return pd.concat([df, pd.DataFrame([total])]).reset_index(drop=True)
        else:
            return pd.concat([pd.DataFrame([total]), df]).reset_index(drop=True)

    @staticmethod
    def merge_lastn(raw: pd.DataFrame, n: int = 10) -> pd.DataFrame:

        if raw.empty:
            return raw

        df = raw.copy()
        # 保留日均余额前n位交易对手，超过n位归入到"其他"
        nums = len(df)

        if nums <= n:
            return df
        else:
            # 保留日均余额前n位交易对手，超过n位归入到"其他"
            tail = df.tail(nums - n)
            data = {
                C.MAIN_ORG: ['其他'],
                C.AVG_AMT: [tail[C.AVG_AMT].sum()],
                C.INST_GROUP: [tail[C.INST_GROUP].sum()],
                C.PRODUCT: [tail[C.PRODUCT].sum()],
                C.WEIGHT_RATE: [tail[C.INST_GROUP].sum() * 365 / tail[C.PRODUCT].sum() * 100]
            }
            lastn = pd.DataFrame(data)

            df.drop(df.tail(nums - n).index, inplace=True)
            df = pd.concat([df, lastn]).reset_index(drop=True)

            return df

    @staticmethod
    def format_output(raw: pd.DataFrame) -> pd.DataFrame:
        raw.index = raw.index + 1
        raw[C.AVG_AMT] = raw[C.AVG_AMT].map('{:,.2f}'.format)
        raw[C.INST_GROUP] = raw[C.INST_GROUP].map('{:,.2f}'.format)
        raw[C.WEIGHT_RATE] = raw[C.WEIGHT_RATE].map('{:.4f}'.format)

        return raw
