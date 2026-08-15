# -*- coding: utf-8 -*-
"""
P2 数据导出：从 PostgreSQL(mimiciv31) 导出 P1 物化表到本地 parquet
- sepsis_traj_cohort    (24,101 x 44)
- sepsis_traj_daily_wide(24,101 x 76)
只读 SELECT，不改数据库。
"""
import psycopg2
import pandas as pd
import os, sys

OUT = r"C:\Users\12751\WorkBuddy\脓毒症多器官轨迹"
os.makedirs(OUT, exist_ok=True)

conn = psycopg2.connect(
    host="localhost", port=5442, dbname="mimiciv31",
    user="postgres", password="", connect_timeout=30
)
cur = conn.cursor()

def export(sql, path, desc):
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=cols)
    df.to_parquet(path, index=False)
    print(f"{desc}: {df.shape[0]} rows x {df.shape[1]} cols -> {os.path.basename(path)}")
    return df

cohort = export("SELECT * FROM sepsis_traj_cohort ORDER BY stay_id",
                os.path.join(OUT, "P2_cohort.parquet"), "cohort")
wide = export("SELECT * FROM sepsis_traj_daily_wide ORDER BY stay_id",
              os.path.join(OUT, "P2_daily_wide.parquet"), "daily_wide")

# 双向 join 校验
m = cohort.merge(wide, on="stay_id", how="outer", indicator=True)
print("\njoin check:", m["_merge"].value_counts().to_dict())
cur.close(); conn.close()
print("EXPORT_DONE")
