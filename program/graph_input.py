# -*- coding: utf-8 -*-
"""
Created on Sun Jun 28 11:06:09 2020

@author: Changmu
"""

# import tushare as ts
import pandas as pd
import re
import pymysql
from sqlalchemy import create_engine
# pro = ts.pro_api('c36133b965c5b2efadfa8f7a97791e8b50c647cdd66913213abffde3')
# company = pro.stock_company()
# managers = pro.stk_managers()

inputpath = 'file:///D:/工作文档/financial_graph/input/'
outputpath = 'D:/工作文档/financial_graph/output/data_graph/'
USER = 'root'
PASSWORD = 'cptbtptp'
HOST = '10.28.100.19'
PORT = 13306
DATABASE = 'graph_input'
engine = create_engine('mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset=utf8' \
                     .format(USER, PASSWORD, HOST, PORT, DATABASE))
all_company_info = pd.read_excel(inputpath + '上市公司基本信息.xlsx')
all_company_info = all_company_info.iloc[0:len(all_company_info)-3]


def truncate_table(DES_TABLE):

    conn=pymysql.connect(
                host = HOST, # 连接名称，默认127.0.0.1
                user = USER, # 用户名,
                passwd= PASSWORD, # 密码,
                port= PORT, # 端口，默认为3306,
                db= DATABASE, # 数据库名称,
                charset='utf8')    # 字符编码
    cur = conn.cursor() # 生成游标对象
    sql="TRUNCATE TABLE {0}".format(DES_TABLE) # SQL语句
    cur.execute(sql) # 执行SQL语句
    print('清空表{0}成功'.format(DES_TABLE))
    cur.close() # 关闭游标
    conn.close() # 关闭连接


def to_date(x):
    x = str(int(x))
    year = x[0:4]
    month = x[4:6]
    day = x[6:8]
    return '-'.join([year, month, day])

    
def company_basic_info():
    init_name = ['证券代码', '股票简称', '股票英文简称', '上市板', '证券存续状态', 
                 '公司中文名称', '公司属性\r\n[交易日期] 最新收盘日', '成立日期', 
                 '注册资本\r\n[单位] 元', '法定代表人', '经营范围', '主营产品名称', 
                 '省份', '城市', '注册地址', '办公地址', '统一社会信用代码', 
                 '所属证监会行业名称\r\n[交易日期] 最新收盘日\r\n[行业级别] 全部明细', 
                 '所属证监会行业代码\r\n[交易日期] 最新收盘日\r\n[行业级别] 全部明细']
    new_name = ['gpdm', 'gpjc', 'gpywjc', 'ssb', 'cxzt', 'gsmc', 'gssx', 'clrq', 
                'zczb', 'fddbr', 'jyfw', 'zycp', 'sf', 'cs', 'zcdz', 'bgdz', 'xydm', 
                'hymc', 'hydm']
    cols = dict(zip(init_name, new_name))
    company_basic_info = all_company_info[init_name].rename(columns=cols)
    company_basic_info['clrq'] = company_basic_info['clrq'].apply(to_date)
    company_basic_info.insert(0, 'id', 0)
    truncate_table('company_basic_info')
    company_basic_info.to_sql('company_basic_info',con=engine,if_exists='append',index=False)
    company_basic_info.to_csv(outputpath + 'company_basic_info.csv', sep='\t', index=False)


def keydirector_info():
    init_name = ['证券代码', '董事长\r\n[交易日期] 最新', '总经理\r\n[交易日期] 最新', 
                 '董事会秘书\r\n[交易日期] 最新', '公司独立董事(现任)', '公司独立董事(历任)', 
                 '公司董事', '公司监事', '公司高管']
    new_name = ['gpdm', 'dsz', 'zjl', 'dshms', 'dldsxr', 'dldslr', 'gsds', 'gsjs', 'gsgg']
    cols = dict(zip(init_name, new_name))
    keydirector_info_init = all_company_info[init_name].rename(columns=cols)
    keydirector_info_init = keydirector_info_init.set_index(['gpdm'])
    keydirector_info = pd.DataFrame()
    for zwdm in new_name[1:]:
        df = keydirector_info_init[zwdm] \
            .str.split(",", expand=True).stack() \
            .reset_index(drop=True, level=-1).reset_index() \
            .rename(columns={0: 'name'})
        df.insert(1, 'zwdm', zwdm)
        keydirector_info = pd.concat([keydirector_info, df], axis=0)
    keydirector_info.insert(0, 'id', 0)
    truncate_table('keydirector_info')
    keydirector_info.to_sql('keydirector_info',con=engine,if_exists='append',index=False) 
    keydirector_info.to_csv(outputpath + 'keydirector_info.csv', sep='\t', index=False)
   

def shareholder_info():
    init_name = ['证券代码', '大股东名称\r\n[日期] 最新\r\n[大股东排名] 前10名', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第1名\r\n[单位] 股', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第2名\r\n[单位] 股', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第3名\r\n[单位] 股', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第4名\r\n[单位] 股', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第5名\r\n[单位] 股', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第6名\r\n[单位] 股', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第7名\r\n[单位] 股', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第8名\r\n[单位] 股', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第9名\r\n[单位] 股', 
                 '大股东持股数量\r\n[日期] 最新\r\n[大股东排名] 第10名\r\n[单位] 股', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第1名\r\n[单位] %', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第2名\r\n[单位] %', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第3名\r\n[单位] %', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第4名\r\n[单位] %', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第5名\r\n[单位] %', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第6名\r\n[单位] %', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第7名\r\n[单位] %', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第8名\r\n[单位] %', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第9名\r\n[单位] %', 
                 '大股东持股比例\r\n[日期] 最新\r\n[大股东排名] 第10名\r\n[单位] %']
    new_name = ['gpdm', 'gdmc', 'gdcg1', 'gdcg2', 'gdcg3', 'gdcg4', 'gdcg5', 'gdcg6', 
                'gdcg7', 'gdcg8', 'gdcg9', 'gdcg10', 'gdcgbl1', 'gdcgbl2', 'gdcgbl3', 
                'gdcgbl4', 'gdcgbl5', 'gdcgbl6', 'gdcgbl7', 'gdcgbl8', 'gdcgbl9', 'gdcgbl10']
    cols = dict(zip(init_name, new_name))
    shareholder_info_init = all_company_info[init_name].rename(columns=cols)
    shareholder_info_init = shareholder_info_init.set_index(['gpdm'])
    shareholder_info = pd.DataFrame()
    df_name = shareholder_info_init['gdmc'] \
            .str.split(";", expand=True).stack() \
            .reset_index(drop=False, level=-1).reset_index() \
            .rename(columns={'level_1': 'order', 0: 'name'})
    result = []
    shareholder_info_init = shareholder_info_init.reset_index()
    for gpdm, df in df_name.groupby(['gpdm']):
        append_info = shareholder_info_init[shareholder_info_init['gpdm'] == gpdm] \
                    .unstack().reset_index(drop=True, level=-1).dropna()[2:]
        gdcg = append_info.iloc[0:len(append_info) // 2].rename(columns={0: 'gdcg'})
        gdcgbl = append_info.iloc[len(append_info) // 2:].rename(columns={0: 'gdcgbl'})
        df.insert(3, 'gdcg', gdcg.values.tolist())
        df.insert(4, 'gdcgbl', gdcgbl.values.tolist())
        result.append(df)
    shareholder_info = pd.concat(result)
    shareholder_info.insert(0, 'id', 0)
    truncate_table('shareholder_info')
    shareholder_info.to_sql('shareholder_info',con=engine,if_exists='append',index=False)
    shareholder_info.to_csv(outputpath + 'shareholder_info.csv', sep='\t', index=False)


def customer_info():
    init_name = ['证券代码', '大客户名称\r\n[报告期] 2017年报\r\n[大股东排名] 第1名', 
                 '大客户名称\r\n[报告期] 2018年报\r\n[大股东排名] 第1名', 
                 '大客户名称\r\n[报告期] 2019年报\r\n[大股东排名] 第1名', 
                 '大客户名称\r\n[报告期] 2017年报\r\n[大股东排名] 第2名', 
                 '大客户名称\r\n[报告期] 2018年报\r\n[大股东排名] 第2名', 
                 '大客户名称\r\n[报告期] 2019年报\r\n[大股东排名] 第2名', 
                 '大客户名称\r\n[报告期] 2017年报\r\n[大股东排名] 第3名', 
                 '大客户名称\r\n[报告期] 2018年报\r\n[大股东排名] 第3名', 
                 '大客户名称\r\n[报告期] 2019年报\r\n[大股东排名] 第3名', 
                 '大客户名称\r\n[报告期] 2017年报\r\n[大股东排名] 第4名', 
                 '大客户名称\r\n[报告期] 2018年报\r\n[大股东排名] 第4名', 
                 '大客户名称\r\n[报告期] 2019年报\r\n[大股东排名] 第4名', 
                 '大客户名称\r\n[报告期] 2017年报\r\n[大股东排名] 第5名', 
                 '大客户名称\r\n[报告期] 2018年报\r\n[大股东排名] 第5名', 
                 '大客户名称\r\n[报告期] 2019年报\r\n[大股东排名] 第5名', 
                 '大客户销售收入占比\r\n[报告期] 2017年报\r\n[大股东排名] 第1名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2018年报\r\n[大股东排名] 第1名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2019年报\r\n[大股东排名] 第1名\r\n[单位] %↓', 
                 '大客户销售收入占比\r\n[报告期] 2017年报\r\n[大股东排名] 第2名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2018年报\r\n[大股东排名] 第2名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2019年报\r\n[大股东排名] 第2名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2017年报\r\n[大股东排名] 第3名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2018年报\r\n[大股东排名] 第3名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2019年报\r\n[大股东排名] 第3名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2017年报\r\n[大股东排名] 第4名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2018年报\r\n[大股东排名] 第4名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2019年报\r\n[大股东排名] 第4名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2017年报\r\n[大股东排名] 第5名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2018年报\r\n[大股东排名] 第5名\r\n[单位] %', 
                 '大客户销售收入占比\r\n[报告期] 2019年报\r\n[大股东排名] 第5名\r\n[单位] %']
    new_name = ['gpdm', '2017kh1', '2018kh1', '2019kh1', '2017kh2', '2018kh2', '2019kh2', 
                '2017kh3', '2018kh3', '2019kh3', '2017kh4', '2018kh4', '2019kh4', 
                '2017kh5', '2018kh5', '2019kh5', '2017khbl1', '2018khbl1', '2019khbl1', 
                '2017khbl2', '2018khbl2', '2019khbl2', '2017khbl3', '2018khbl3', 
                '2019khbl3', '2017khbl4', '2018khbl4', '2019khbl4', '2017khbl5', 
                '2018khbl5', '2019khbl5']
    cols = dict(zip(init_name, new_name))
    customer_info_init = all_company_info[init_name].rename(columns=cols)
    customer_info_init = customer_info_init.set_index(['gpdm'])
    customer_info = pd.DataFrame()
    kh_info = customer_info_init.stack().reset_index() \
                .rename(columns={'level_1': 'info', 0: 'kh'})
    kh_info['bgnd'] = kh_info['info'].apply(lambda x: x[0:4])
    kh_info['type'] = kh_info['info'].apply(lambda x: re.sub(r'\d', '', x))
    kh_info['order'] = kh_info['info'].apply(lambda x: x[-1])
    kh_info.drop('info', axis=1, inplace=True)
    khbl_info = kh_info[kh_info['type'] == 'khbl'] \
                .drop('type', axis=1) \
                .rename(columns={'kh': 'bl'}) 
    kh_info = kh_info[kh_info['type'] == 'kh'] \
                .drop('type', axis=1) \
                .rename(columns={'kh': 'mc'})
    customer_info = pd.merge(kh_info, khbl_info, how='left', on=['gpdm', 'bgnd', 'order'])
    customer_info.insert(0, 'id', 0)
    truncate_table('customer_info')
    customer_info.to_sql('customer_info',con=engine,if_exists='append',index=False)
    customer_info.to_csv(outputpath + 'customer_info.csv', sep='\t', index=False)


def supplier_info():
    init_name = ['证券代码', '大供应商名称\r\n[报告期] 2017年报\r\n[大股东排名] 第1名', 
                 '大供应商名称\r\n[报告期] 2018年报\r\n[大股东排名] 第1名', 
                 '大供应商名称\r\n[报告期] 2019年报\r\n[大股东排名] 第1名', 
                 '大供应商名称\r\n[报告期] 2017年报\r\n[大股东排名] 第2名', 
                 '大供应商名称\r\n[报告期] 2018年报\r\n[大股东排名] 第2名', 
                 '大供应商名称\r\n[报告期] 2019年报\r\n[大股东排名] 第2名', 
                 '大供应商名称\r\n[报告期] 2017年报\r\n[大股东排名] 第3名', 
                 '大供应商名称\r\n[报告期] 2018年报\r\n[大股东排名] 第3名', 
                 '大供应商名称\r\n[报告期] 2019年报\r\n[大股东排名] 第3名', 
                 '大供应商名称\r\n[报告期] 2017年报\r\n[大股东排名] 第4名', 
                 '大供应商名称\r\n[报告期] 2018年报\r\n[大股东排名] 第4名', 
                 '大供应商名称\r\n[报告期] 2019年报\r\n[大股东排名] 第4名', 
                 '大供应商名称\r\n[报告期] 2017年报\r\n[大股东排名] 第5名', 
                 '大供应商名称\r\n[报告期] 2018年报\r\n[大股东排名] 第5名', 
                 '大供应商名称\r\n[报告期] 2019年报\r\n[大股东排名] 第5名', 
                 '大供应商采购金额占比\r\n[报告期] 2017年报\r\n[大股东排名] 第1名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2018年报\r\n[大股东排名] 第1名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2019年报\r\n[大股东排名] 第1名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2017年报\r\n[大股东排名] 第2名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2018年报\r\n[大股东排名] 第2名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2019年报\r\n[大股东排名] 第2名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2017年报\r\n[大股东排名] 第3名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2018年报\r\n[大股东排名] 第3名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2019年报\r\n[大股东排名] 第3名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2017年报\r\n[大股东排名] 第4名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2018年报\r\n[大股东排名] 第4名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2019年报\r\n[大股东排名] 第4名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2017年报\r\n[大股东排名] 第5名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2018年报\r\n[大股东排名] 第5名\r\n[单位] %', 
                 '大供应商采购金额占比\r\n[报告期] 2019年报\r\n[大股东排名] 第5名\r\n[单位] %']
    new_name = ['gpdm', '2017gys1', '2018gys1', '2019gys1', '2017gys2', '2018gys2', 
                '2019gys2', '2017gys3', '2018gys3', '2019gys3', '2017gys4', 
                '2018gys4', '2019gys4', '2017gys5', '2018gys5', '2019gys5', 
                '2017gysbl1', '2018gysbl1', '2019gysbl1', '2017gysbl2', 
                '2018gysbl2', '2019gysbl2', '2017gysbl3', '2018gysbl3', 
                '2019gysbl3', '2017gysbl4', '2018gysbl4', '2019gysbl4', 
                '2017gysbl5', '2018gysbl5', '2019gysbl5']
    cols = dict(zip(init_name, new_name))
    supplier_info_init = all_company_info[init_name].rename(columns=cols)
    supplier_info_init = supplier_info_init.set_index(['gpdm'])
    supplier_info = pd.DataFrame()
    gys_info = supplier_info_init.stack().reset_index() \
                .rename(columns={'level_1': 'info', 0: 'gys'})
    gys_info['bgnd'] = gys_info['info'].apply(lambda x: x[0:4])
    gys_info['type'] = gys_info['info'].apply(lambda x: re.sub(r'\d', '', x))
    gys_info['order'] = gys_info['info'].apply(lambda x: x[-1])
    gys_info.drop('info', axis=1, inplace=True)
    gysbl_info = gys_info[gys_info['type'] == 'gysbl'] \
                .drop('type', axis=1) \
                .rename(columns={'gys': 'bl'}) 
    gys_info = gys_info[gys_info['type'] == 'gys'] \
                .drop('type', axis=1) \
                .rename(columns={'gys': 'mc'})
    supplier_info = pd.merge(gys_info, gysbl_info, how='left', on=['gpdm', 'bgnd', 'order'])
    supplier_info.insert(0, 'id', 0)
    truncate_table('supplier_info')
    supplier_info.to_sql('supplier_info',con=engine,if_exists='append',index=False)
    supplier_info.to_csv(outputpath + 'supplier_info.csv', sep='\t', index=False)


def industry_info():
    init_name = ['证券代码', 
                 '所属证监会行业名称\r\n[交易日期] 最新收盘日\r\n[行业级别] 全部明细',
                 '所属证监会行业代码\r\n[交易日期] 最新收盘日\r\n[行业级别] 全部明细']
    new_name = ['gpdm', 'hymc', 'hydm']
    cols = dict(zip(init_name, new_name))
    industry_info_init = all_company_info[init_name].rename(columns=cols)
    industry_info_init['hymc1'], industry_info_init['hymc2'] = \
                        industry_info_init['hymc'].str.split('-', 1).str
    industry_info_init['hydm1'], industry_info_init['hydm2'] = \
                        industry_info_init['hydm'].str.replace('--', '').str.split('-', 1).str
    industry_info = industry_info_init[['gpdm', 'hymc1', 'hydm1', 'hymc2', 'hydm2']]
    industry_info.insert(0, 'id', 0)
    truncate_table('industry_info')
    industry_info.to_sql('industry_info',con=engine,if_exists='append',index=False)
    industry_info.to_csv(outputpath + 'industry_info.csv', sep='\t', index=False)
    
    
def product_info():
    init_name = ['证券代码', '主营产品名称']
    new_name = ['gpdm', 'zycp']
    cols = dict(zip(init_name, new_name))
    product_info_init = all_company_info[init_name].rename(columns=cols)
    product_info_init.dropna(subset=['zycp'], inplace=True)
    df = product_info_init
    product_info = pd.DataFrame()
    for index in range(len(product_info_init)):
        df = product_info_init.iloc[index]
        result = pd.DataFrame(df['zycp'].split('、'), columns=['zycp'])
        result.insert(0, 'gpdm', df['gpdm'])
        product_info = pd.concat([product_info, result], axis=0)
    product_info.insert(0, 'id', 0)
    truncate_table('product_info')    
    product_info.to_sql('product_info',con=engine,if_exists='append',index=False)
    product_info.to_csv(outputpath + 'product_info.csv', sep='\t', index=False)


company_basic_info()
print('company_basic_info complete!')
#keydirector_info()
#print('keydirector_info complete!')
#shareholder_info()
#print('shareholder_info complete!')
#customer_info()
#print('customer_info complete!')
#supplier_info()
#print('supplier_info complete!')
#industry_info()
#print('industry_info complete!')
#product_info()
#print('product_info complete!')