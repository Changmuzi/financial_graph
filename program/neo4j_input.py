# -*- coding: utf-8 -*-
"""
@author: Changmu

启动命令：PYSPARK_PYTHON=/root/anaconda3/bin/python nohup /usr/local/spark-3.0.0/bin/spark-submit --queue root.project.qyxypf --master yarn --conf spark.hadoop.dfs.replication=2 --num-executors 4 --executor-memory 1g --executor-cores 2 --conf spark.yarn.executor.memoryOverhead=30g --driver-memory 10g --driver-cores 4  --conf spark.reducer.maxSizeInFlight=96m --conf "spark.executor.extraJavaOptions= -XX:+UseG1GC" /data8/qyxypf/qyxy_line_code/merge_quant_data/merge_quant_data.py &
"""

import re
import os
import importlib,sys
from pyspark import SparkConf
from pyspark.sql import SparkSession, Row
from pyspark.sql import functions as fun
import json
import pandas as pd

importlib.reload(sys)
# reload(sys)

conf = SparkConf()
conf.set("spark.shuffle.file.buffer", "32k")
conf.set("spark.reducer.maxSizeInFlight", "48m")
conf.set("spark.shuffle.memoryFraction", "0.2")
conf.set("spark.hadoop.dfs.replication", "2")
conf.set("spark.debug.maxToStringFields", "1000")


spark = SparkSession \
	.builder \
	.appName("neo4j") \
	.config(conf=conf) \
	.getOrCreate()
	

def get_dataframe_from_mysql(table_name):
	'''
	:param table_name: 表名
	:return: 表df
	'''
	url = 'jdbc:mysql://127.0.0.1:3306/graph_input?user=root&password=password&characterEncoding=utf8'
	driver = 'com.mysql.cj.jdbc.Driver'
	df = spark.read.format("jdbc").options(url=url, dbtable=table_name, driver=driver).load()
	return df


def save_to_mysql(df, table_name):
	'''
	输入DataFrame，表名
	:param df:
	:param table_name:
	:return:
	'''
	url_output = 'jdbc:mysql://127.0.0.1:3306/neo4j_input?user=root&password=password&characterEncoding=utf8'
	df.write.mode("overwrite").format("jdbc").options(
		url=url_output,
		driver = 'com.mysql.cj.jdbc.Driver',
		dbtable=table_name
	).save()

def char_len(data):
	'''
	返回utf8编码格式的字符串长度
	'''
	return len(data.encode('utf-8'))
# 登记为临时函数
spark.udf.register('char_len', char_len)

def clean_supplier_customer():
	'''
	清洗供应商客户表的名称，并写出为csv
	'''
	def clean_name(data):
		'''
		1.如果name没有中文或英文，则删除
		2.如果name以"X"+空格或中文组成，其中X为单个英文字母，则删除该条数据
		3.如果name包含"第X大"或"前X名"，其中X为一到十，则删除该条数据
		4.如果name中含有字符"（原"、"（含"、"（同"、"（购"、"（不"、"（总"、"（关联"、"（注"，"注"则删除这些字符之后的内容（包括该字符）
		5.如果含有":"、"："字符，则删除该字符之前的内容（包括该字符）
		6.将name的以下字符删除："供应商"、"供货商"、"医药商"、"实际控制人"、"同一实际控制人"、"军工"、"军品"、"排名第"、"客户"、"单位"、"收入"、"销售商"、"经销商"、"自然人"、"同一控制"、"所属"、"下属"
		7.将前面处理后的name按以下字符分割成多个字符串："及其下属分子公司"、"及其关联方"、"及其子公司"、"及其关联公司"、"及其下属子公司"、"及其附属公司"、"及子公司"、"及所属单位"、"及其所属企业"、"及其实际控制的公司"、"及同一控制"、"及控股公司"、"及关联方"、"及下属企业"、"及所属企业"、"及其下属研究所"、"下属子公司"、"及下属"、"及其主要关联企业"
		8.将前面处理后的name通过"与"或"、"或"/"进行分割，分割成多个字符串
		'''
		mc = data.mc
		pattern_cn = re.compile(u'[\u4e00-\u9fa5]+')
		pattern_en = re.compile(u'[a-zA-Z]+')
		pattern_xcn = re.compile(u'[a-zA-Z][ |\u4e00-\u9fa5]+')
		pattern = re.compile(u'^第一大|^第二大|^第三大|^第四大|^第五大|^第六大|^第七大|^第八大|^第九大|^第十大'
							 u'|^前一名|^前二名|^前三名|^前四名|^前五名|^前六名|^前七名|^前八名|^前九名|^前十名'
							 u'|^第一名|^第二名|^第三名|^第四名|^第五名|^第六名|^第七名|^第八名|^第九名|^第十名')
		if mc is not None:
			if not (len(re.findall(pattern_cn, mc)) + len(re.findall(pattern_en, mc)) == 0):
				if pd.isnull(re.fullmatch(pattern_xcn, mc)):
					if len(re.findall(pattern, mc)) == 0:
						mc_split = mc.split(u'（原')[0]
						mc_split = mc_split.split(u'（含')[0]
						mc_split = mc_split.split(u'（同')[0]
						mc_split = mc_split.split(u'（购')[0]
						mc_split = mc_split.split(u'（不')[0]
						mc_split = mc_split.split(u'（总')[0]
						mc_split = mc_split.split(u'（关联')[0]
						mc_split = mc_split.split(u'（注')[0]
						mc_split = mc_split.split(u'注')[0]
						mc_split = mc_split.split(u'（合并')[0]
						mc_split = mc_split.split(u'（包')[0]
						if u':' in mc_split:
							mc_split = mc_split.split(u':')[1]
						if u'：' in mc_split:
							mc_split = mc_split.split(u'：')[1]
						mc = mc_split.replace('供应商一', '').replace(u'供应商', u'').replace(u'供货商', u'') \
							.replace(u'医药商', u'').replace(u'实际控制人', u'').replace(u'同一实际控制人', u'') \
							.replace(u'军工', u'').replace(u'军品', u'').replace(u'排名第', u'').replace(u'客户', u'') \
							.replace(u'单位', u'').replace(u'收入', u'').replace(u'销售商', u'').replace(u'经销商', u'') \
							.replace(u'自然人', u'').replace(u'同一控制', u'').replace(u'所属', u'').replace(u'下属', u'') \
							.replace(u'名称', u'').replace(u'合计', u'')
						if (len(re.findall(pattern_cn, mc)) + len(re.findall(pattern_en, mc)) == 0):
							return Row(mc_arr=[], gpdm=data.gpdm, bgnd=data.bgnd,
										order=data.order, bl=data.bl)
						mc_arr = re.split(u'及其分子公司|及其关联方|及其子公司|及其关联公司|及其附属公司|及子公司'
												u'|子公司|及单位|及其企业|及其实际控制的公司|及同一控制|及控股公司|及关联方'
												u'|及企业|及其研究所|及其主要关联企业|与|;|、|/', mc)
						return Row(mc_arr=mc_arr, gpdm=data.gpdm, bgnd=data.bgnd,
								   order=data.order, bl=data.bl)
					return Row(mc_arr=[], gpdm=data.gpdm, bgnd=data.bgnd,
								   order=data.order, bl=data.bl)
				return Row(mc_arr=[], gpdm=data.gpdm, bgnd=data.bgnd,
								   order=data.order, bl=data.bl)
			return Row(mc_arr=[], gpdm=data.gpdm, bgnd=data.bgnd,
								   order=data.order, bl=data.bl)
	# 创建无效名称表
	invalid = ['-8', '-7', '-6', '-5', '-4', '-3', '-2', '-1', 
				'E', 'C', 'B', 'Ec', 'A', 'ABB小计', 'FI美国', '(下同)', '(三)', 
				'(四)', '(五)', '(二)', '(一)', 'BG', 'BJ', 'AI', 'GE', 'AA', 
				'=-E', '-C', 'AR', 'AU', '()', 'D', ',', '1A', 'a1', '1造船厂', 
				'B1', 'A2', 'B2', '2A', '2造船厂', 'A3', '3A', '3M', 'B3', 'b4', 
				'A4', '4A', 'B5', 'a5', '5A', '一', '二', '三', '四', '五',
				'-A', '-B', '-C', '-D', '-E']
	invalid = pd.DataFrame(invalid, columns=['mc'])
	spark.createDataFrame(invalid).createOrReplaceTempView("invalid")
	# customer_info
	get_dataframe_from_mysql('customer_info').createOrReplaceTempView("customer_info")
	customer_rdd = spark.sql(
	'''
	SELECT
		mc,
		gpdm,
		bgnd,
		order,
		bl 
	FROM
		customer_info 
	WHERE
		mc != 'null' 
		AND mc IS NOT NULL
	''').rdd.map(clean_name)
	spark.createDataFrame(customer_rdd).createOrReplaceTempView('customer_rdd')
	spark.sql(
	'''
	SELECT
		mc,
		gpdm,
		bgnd,
		order,
		bl 
	FROM
		( SELECT explode_outer ( mc_arr ) mc, gpdm, bgnd, order, bl FROM customer_rdd )
	WHERE
		mc IS NOT NULL 
		AND mc != '' 
		AND mc != 'null' 
	''').createOrReplaceTempView('customer_info')
	customer_info = spark.sql(
	'''
	SELECT
		l.mc,
		gpdm,
		bgnd,
		order,
		bl 
	FROM
		customer_info l
		LEFT JOIN invalid r ON l.mc = r.mc 
	WHERE 
		r.mc IS NULL
	''')
	customer_info.repartition(1).write.csv(outputdata + 'customer_info', header=True, sep='\t', mode='overwrite')
	# supplier_info
	get_dataframe_from_mysql('supplier_info').createOrReplaceTempView("supplier_info")
	supplier_rdd = spark.sql(
	'''
	SELECT
		mc,
		gpdm,
		bgnd,
		order,
		bl 
	FROM
		supplier_info 
	WHERE
		mc != 'null' 
		AND mc IS NOT NULL
	''').rdd.map(clean_name)
	spark.createDataFrame(supplier_rdd).createOrReplaceTempView('supplier_rdd')
	supplier_info = spark.sql(
	'''
	SELECT
		l.mc,
		gpdm,
		bgnd,
		order,
		bl 
	FROM
		( SELECT explode_outer ( mc_arr ) mc, gpdm, bgnd, order, bl FROM supplier_rdd ) l
		LEFT JOIN invalid r ON l.mc = r.mc 
	WHERE
		l.mc IS NOT NULL 
		AND l.mc != '' 
		AND l.mc != 'null'
		AND r.mc IS NULL
	''')
	supplier_info.write.csv(outputdata + 'supplier_info', header=True, sep='\t',mode='overwrite')


def company():
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	spark.sql(
	'''
	SELECT
		md5( gsmc ) AS uid,
		gsmc AS name,
		'是' AS isipo,
		gpdm AS CODE,
	CASE
		WHEN SUBSTRING( gpdm, - 2, 2 ) = 'SZ' THEN '深交所' 
		WHEN SUBSTRING( gpdm, - 2, 2 ) = 'SH' THEN '上交所' 
		END AS exchange,
		gssx AS type,
		clrq AS opendate,
		jyfw AS scope,
		zczb AS regcapamount,
		'人民币' AS regcapcurrency,
		cxzt AS enterprisestatus,
		sf AS province,
		cs AS city,
		zcdz AS regaddress,
		bgdz AS oaaddress 
	FROM
	company_basic_info
	''').createOrReplaceTempView('part1')
	# customer_info
	spark.read.csv(outputdata + "customer_info", header=True, sep='\t').where(
        "char_len ( mc ) > 12").createOrReplaceTempView("customer_info")
	spark.sql(
	'''
	SELECT
		md5( mc ) AS uid,
		mc AS name,
		'否' AS isipo,
		'' AS code,
		'' AS exchange,
		'' AS type,
		'' AS opendate,
		'' AS scope,
		'' AS regcapamount,
		'' AS regcapcurrency,
		'' AS enterprisestatus,
		'' AS province,
		'' AS city,
		'' AS regaddress,
		'' AS oaaddress 
	FROM
		customer_info 
	''').createOrReplaceTempView('part2')
	# supplier_info
	spark.read.csv(outputdata + "supplier_info", header=True, sep='\t').where(
        "char_len ( mc ) > 12").createOrReplaceTempView("supplier_info")
	spark.sql(
	'''
	SELECT
		md5( mc ) AS uid,
		mc AS name,
		'否' AS isipo,
		'' AS code,
		'' AS exchange,
		'' AS type,
		'' AS opendate,
		'' AS scope,
		'' AS regcapamount,
		'' AS regcapcurrency,
		'' AS enterprisestatus,
		'' AS province,
		'' AS city,
		'' AS regaddress,
		'' AS oaaddress 
	FROM
		supplier_info 
	''').createOrReplaceTempView('part3')
	# shareholder_info
	get_dataframe_from_mysql('shareholder_info').createOrReplaceTempView("shareholder_info")
	spark.sql(
	'''
	( SELECT * FROM shareholder_info WHERE char_len ( name ) > 12 ) UNION ALL
	( SELECT * FROM shareholder_info 
	WHERE
		char_len ( name ) <= 12 
		AND (
		substring( name, - 7 ) = 'limited' 
		OR substring( name, - 2 ) = '公司' 
		OR substring( name, - 1 ) = '.' 
		OR substring( name, - 2 ) = '大学' 
		OR substring( name, - 2 ) = '宾馆' 
		) 
		) UNION ALL
	( SELECT * FROM shareholder_info WHERE char_len ( name ) <= 12 AND name REGEXP 'bank' ) UNION ALL
	( SELECT * FROM shareholder_info WHERE name = 'AU SIU KWOK' )
	''') \
		.dropDuplicates(["name"]) \
		.createOrReplaceTempView('part4_ori')
	spark.sql(
	'''
	SELECT
		md5( name ) AS uid,
		name AS name,
		'否' AS isipo,
		'' AS code,
		'' AS exchange,
		'' AS type,
		'' AS opendate,
		'' AS scope,
		'' AS regcapamount,
		'' AS regcapcurrency,
		'' AS enterprisestatus,
		'' AS province,
		'' AS city,
		'' AS regaddress,
		'' AS oaaddress 
	FROM
		part4_ori
	''').createOrReplaceTempView('part4')
	# union and write
	company = spark.sql(
	'''
	SELECT
		uid,
		name,
		isipo,
		code,
		exchange,
		type,
		opendate,
		scope,
		regcapamount,
		regcapcurrency,
		enterprisestatus,
		province,
		city,
		regaddress,
		oaaddress 
	FROM
		( SELECT * FROM part1 ) UNION ALL
		( SELECT * FROM part2 ) UNION ALL
		( SELECT * FROM part3 ) UNION ALL
		( SELECT * FROM part4 )
	''').dropDuplicates(["uid"]) #\
		#.write.csv(outputdata + 'company.csv', sep='\t', header=True, mode='overwrite')
	# company.write.mode("overwrite").csv(outputdata + 'company.csv')
	company.repartition(1).write.csv(outputdata + 'company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(company, 'company')


def person():
	# keydirector_info
	get_dataframe_from_mysql('keydirector_info').createOrReplaceTempView("keydirector_info")
	spark.sql(
	'''
	SELECT
		md5( concat( gpdm, name ) ) AS uid,
		name,
		'' AS sex,
		'' AS age,
		'' AS resume 
	FROM
		keydirector_info
	''').createOrReplaceTempView('part1')
	# customer_info
	spark.read.csv(outputdata + "customer_info", header=True, sep='\t').where(
        "char_len ( mc ) <= 12").createOrReplaceTempView("customer_info")
	spark.sql(
	'''
	SELECT
		md5( concat( gpdm, mc ) ) AS uid,
		mc AS name,
		'' AS sex,
		'' AS age,
		'' AS resume 
	FROM
		customer_info 
	''').createOrReplaceTempView('part2')
	# supplier_info
	spark.read.csv(outputdata + "supplier_info", header=True, sep='\t').where(
        "char_len ( mc ) <= 12").createOrReplaceTempView("supplier_info")
	spark.sql(
	'''
	SELECT
		md5( concat( gpdm, mc ) ) AS uid,
		mc AS name,
		'' AS sex,
		'' AS age,
		'' AS resume 
	FROM
		supplier_info 
	''').createOrReplaceTempView('part3')
	# shareholder_info
	get_dataframe_from_mysql('shareholder_info').createOrReplaceTempView("shareholder_info")
	spark.sql(
	'''
	SELECT
		md5( concat( gpdm, name ) ) AS uid,
		name AS name,
		'' AS sex,
		'' AS age,
		'' AS resume 
	FROM
		shareholder_info 
	WHERE
		char_len ( name ) <= 12 
		AND (
		substring( name, - 7 ) != 'limited' 
		AND substring( name, - 2 ) != '公司' 
		AND substring( name, - 1 ) != '.' 
		AND substring( name, - 2 ) != '大学' 
		AND substring( name, - 2 ) != '宾馆' 
		) 
		AND name NOT REGEXP 'bank' 
		AND name != 'AU SIU KWOK'
	''') \
		.dropDuplicates(["name"]) \
		.createOrReplaceTempView('part4')
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	spark.sql(
	'''
	SELECT 
		md5( concat( gpdm, fddbr ) ) AS uid, 
		fddbr AS name,
		'' AS sex,
		'' AS age,
		'' AS resume 
	FROM
		company_basic_info
	''').createOrReplaceTempView('part5')
	# union and write
	person = spark.sql(
	'''
	SELECT
		uid,
		name,
		sex,
		age,
		resume 
	FROM
		( SELECT * FROM part1 ) UNION ALL
		( SELECT * FROM part2 ) UNION ALL
		( SELECT * FROM part3 ) UNION ALL
		( SELECT * FROM part4 ) UNION ALL
		( SELECT * FROM part5 ) 
	''').dropDuplicates(["uid"])
	person.repartition(1).write.csv(outputdata + 'person', header=True, sep='\t',mode='overwrite')
	save_to_mysql(person, 'person')


def product():
	# product_info
	get_dataframe_from_mysql('product_info').createOrReplaceTempView("product_info")
	product = spark.sql(
	'''
	SELECT
		md5( zycp ) AS uid,
		zycp AS name,
		'' AS `describe`
	FROM
		product_info
	''').dropDuplicates(["uid"])
	product.repartition(1).write.csv(outputdata + 'product', header=True, sep='\t',mode='overwrite')
	save_to_mysql(product, 'product')

	
def industry():
	# industry_info
	get_dataframe_from_mysql('industry_info').createOrReplaceTempView("industry_info")
	industry = spark.sql(
	'''
	SELECT
		md5( hymc2 ) AS uid,
		hymc2 AS name,
		hydm2 AS code,
		hymc1 AS upper_name,
		hydm1 AS upper_code 
	FROM
		industry_info
	''').dropDuplicates(["uid"])
	industry.repartition(1).write.csv(outputdata + 'industry', header=True, sep='\t',mode='overwrite')
	save_to_mysql(industry, 'industry')

	
def person_shareholderof_company():
	# shareholder_info
	get_dataframe_from_mysql('shareholder_info').createOrReplaceTempView("shareholder_info")
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	spark.sql(
	'''
	SELECT
		gpdm AS gpdm,
		name AS name,
		order AS order,
		gdcg AS amount,
		gdcgbl AS ratio
	FROM
		shareholder_info 
	WHERE
		char_len ( name ) <= 12 
		AND (
		substring( name, - 7 ) != 'limited' 
		AND substring( name, - 2 ) != '公司' 
		AND substring( name, - 1 ) != '.' 
		AND substring( name, - 2 ) != '大学' 
		AND substring( name, - 2 ) != '宾馆' 
		) 
		AND name NOT REGEXP 'bank' 
		AND name != 'AU SIU KWOK'
	''').createOrReplaceTempView('shareholder_info')
	person_shareholderof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( concat( l.gpdm, l.name ) ) AS startnode,
		md5( r.gsmc ) AS endnode,
		'' AS reportdate,
		l.order AS order,
		l.amount AS amount,
		l.ratio AS ratio 
	FROM
		shareholder_info l
		JOIN company_basic_info r ON l.gpdm = r.gpdm
	''').dropDuplicates(['startnode', 'endnode', 'reportdate'])
	person_shareholderof_company.repartition(1).write.csv(outputdata + 'person_shareholderof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(person_shareholderof_company, 'person_shareholderof_company')

	
def person_supplierof_company():
	# supplier_info
	spark.read.csv(outputdata + "supplier_info", header=True, sep='\t').where(
        "char_len ( mc ) <= 12").createOrReplaceTempView("supplier_info")
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	person_supplierof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( concat( l.gpdm, l.mc ) ) AS startnode,
		md5( r.gsmc ) AS endnode,
		l.bgnd AS reportdate,
		l.order AS order,
		l.bl AS ratio 
	FROM
		supplier_info l
		JOIN company_basic_info r ON l.gpdm = r.gpdm
	''').dropDuplicates(['startnode', 'endnode'])
	person_supplierof_company.repartition(1).write.csv(outputdata + 'person_supplierof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(person_supplierof_company, 'person_supplierof_company')
	
	
def person_customerof_company():
	# customer_info
	spark.read.csv(outputdata + "customer_info", header=True, sep='\t').where(
        "char_len ( mc ) <= 12").createOrReplaceTempView("customer_info")
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	person_customerof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( concat( l.gpdm, l.mc ) ) AS startnode,
		md5( r.gsmc ) AS endnode,
		l.bgnd AS reportdate,
		l.order AS order,
		l.bl AS ratio 
	FROM
		customer_info l
		JOIN company_basic_info r ON l.gpdm = r.gpdm
	''').dropDuplicates(['startnode', 'endnode'])
	person_customerof_company.repartition(1).write.csv(outputdata + 'person_customerof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(person_customerof_company, 'person_customerof_company')
	
	
def person_chairmanof_company():
	# keydirector_info
	get_dataframe_from_mysql('keydirector_info').createOrReplaceTempView("keydirector_info")
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	person_chairmanof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( concat( l.gpdm, l.NAME ) ) AS startnode,
		md5( r.gsmc ) AS endnode,
		'' AS startdate,
		'' AS enddate,
	CASE
		WHEN l.zwdm = 'dsz' THEN '董事长' 
		WHEN l.zwdm = 'gsds' THEN '董事' 
		WHEN l.zwdm = 'dldslr' THEN '历任独立董事' 
		WHEN l.zwdm = 'dldsxr' THEN '现任独立董事' 
		END AS title 
	FROM
		keydirector_info l
		JOIN company_basic_info r ON l.gpdm = r.gpdm 
	WHERE
		(l.zwdm = 'dsz' OR l.zwdm = 'gsds' OR l.zwdm = 'dldslr' OR l.zwdm = 'l.dldsxr')
	''').dropDuplicates(['startnode', 'endnode'])
	person_chairmanof_company.repartition(1).write.csv(outputdata + 'person_chairmanof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(person_chairmanof_company, 'person_chairmanof_company')
	
	
def person_executiveof_company():
	# keydirector_info
	get_dataframe_from_mysql('keydirector_info').createOrReplaceTempView("keydirector_info")
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	person_executiveof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( concat( l.gpdm, l.NAME ) ) AS startnode,
		md5( r.gsmc ) AS endnode,
		'' AS startdate,
		'' AS enddate,
		'监事' AS title 
	FROM
		keydirector_info l
		JOIN company_basic_info r ON l.gpdm = r.gpdm 
	WHERE
		l.zwdm = 'gsjs'
	''').dropDuplicates(['startnode', 'endnode'])
	person_executiveof_company.repartition(1).write.csv(outputdata + 'person_executiveof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(person_executiveof_company, 'person_executiveof_company')
	
	
def person_managerof_company():
	# keydirector_info
	get_dataframe_from_mysql('keydirector_info').createOrReplaceTempView("keydirector_info")
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	person_managerof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( concat( l.gpdm, l.NAME ) ) AS startnode,
		md5( r.gsmc ) AS endnode,
		'' AS startdate,
		'' AS enddate,
	CASE
		WHEN l.zwdm = 'zjl' THEN '总经理' 
		WHEN l.zwdm = 'dshms' THEN '董事会秘书' 
		WHEN l.zwdm = 'gsgg' THEN '公司高管' 
		END AS title 
	FROM
		keydirector_info l
		JOIN company_basic_info r ON l.gpdm = r.gpdm 
	WHERE
		(l.zwdm = 'zjl' OR l.zwdm = 'dshms' OR l.zwdm = 'gsgg')
	''').dropDuplicates(['startnode', 'endnode'])
	person_managerof_company.repartition(1).write.csv(outputdata + 'person_managerof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(person_managerof_company, 'person_managerof_company')
	
	
def person_legalof_company():
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	person_legalof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( concat( gpdm, fddbr ) ) AS startnode,
		md5( gsmc ) AS endnode,
		'' AS reportdate
	FROM
		company_basic_info
	''').dropDuplicates(['startnode', 'endnode', 'reportdate'])
	person_legalof_company.repartition(1).write.csv(outputdata + 'person_legalof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(person_legalof_company, 'person_legalof_company')
	
	
def company_shareholderof_company():
	# shareholder_info
	get_dataframe_from_mysql('shareholder_info').createOrReplaceTempView("shareholder_info")
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	spark.sql(
	'''
	( SELECT * FROM shareholder_info WHERE char_len ( name ) > 12 ) UNION ALL
	( SELECT * FROM shareholder_info 
	WHERE
		char_len ( name ) <= 12 
		AND (
		substring( name, - 7 ) = 'limited' 
		OR substring( name, - 2 ) = '公司' 
		OR substring( name, - 1 ) = '.' 
		OR substring( name, - 2 ) = '大学' 
		OR substring( name, - 2 ) = '宾馆' 
		) 
		) UNION ALL
	( SELECT * FROM shareholder_info WHERE char_len ( name ) <= 12 AND name REGEXP 'bank' ) UNION ALL
	( SELECT * FROM shareholder_info WHERE name = 'AU SIU KWOK' )
	''').createOrReplaceTempView('shareholder_info')
	company_shareholderof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( l.name ) AS startnode,
		md5( r.gsmc ) AS endnode,
		'' AS reportdate,
		l.order AS order,
		l.gdcg AS amount,
		l.gdcgbl AS ratio 
	FROM
		shareholder_info l
		JOIN company_basic_info r ON l.gpdm = r.gpdm
	''').dropDuplicates(['startnode', 'endnode', 'reportdate'])
	company_shareholderof_company.repartition(1).write.csv(outputdata + 'company_shareholderof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(company_shareholderof_company, 'company_shareholderof_company')

	
def company_supplierof_company():
	# supplier_info
	spark.read.csv(outputdata + "supplier_info", header=True, sep='\t').where(
        "char_len ( mc ) > 12").createOrReplaceTempView("supplier_info")
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	company_supplierof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( l.mc ) AS startnode,
		md5( r.gsmc ) AS endnode,
		l.bgnd AS reportdate,
		l.order AS order,
		l.bl AS ratio 
	FROM
		supplier_info l
		JOIN company_basic_info r ON l.gpdm = r.gpdm
	''').dropDuplicates(['startnode', 'endnode', 'reportdate'])
	company_supplierof_company.repartition(1).write.csv(outputdata + 'company_supplierof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(company_supplierof_company, 'company_supplierof_company')
	
	
def company_customerof_company():
	# customer_info
	spark.read.csv(outputdata + "customer_info", header=True, sep='\t').where(
        "char_len ( mc ) > 12").createOrReplaceTempView("customer_info")
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	company_customerof_company = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( l.mc ) AS startnode,
		md5( r.gsmc ) AS endnode,
		l.bgnd AS reportdate,
		l.order AS order,
		l.bl AS ratio 
	FROM
		customer_info l
		JOIN company_basic_info r ON l.gpdm = r.gpdm
	''').dropDuplicates(['startnode', 'endnode', 'reportdate'])
	company_customerof_company.repartition(1).write.csv(outputdata + 'company_customerof_company', header=True, sep='\t',mode='overwrite')
	save_to_mysql(company_customerof_company, 'company_customerof_company')
	
	
def company_hasproductof_product():
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	# product_info
	get_dataframe_from_mysql('product_info').createOrReplaceTempView("product_info")
	company_hasproductof_product = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( l.gsmc ) AS startnode,
		md5( r.zycp ) AS endnode,
		'' AS reportdate 
	FROM
		company_basic_info l
		JOIN product_info r ON l.gpdm = r.gpdm
	''').dropDuplicates(['startnode', 'endnode', 'reportdate'])
	company_hasproductof_product.repartition(1).write.csv(outputdata + 'company_hasproductof_product', header=True, sep='\t',mode='overwrite')
	save_to_mysql(company_hasproductof_product, 'company_hasproductof_product')
	
	
def company_hasindustryof_industry():
	# company_basic_info
	get_dataframe_from_mysql('company_basic_info').createOrReplaceTempView("company_basic_info")
	# industry_info
	get_dataframe_from_mysql('industry_info').createOrReplaceTempView("industry_info")
	company_hasindustryof_industry = spark.sql(
	'''
	SELECT
		regexp_replace ( reflect ( 'java.util.UUID', 'randomUUID' ), '-', '' ) AS uid,
		md5( l.gsmc ) AS startnode,
		md5( r.hymc2 ) AS endnode,
		'' AS reportdate 
	FROM
		company_basic_info l
		JOIN industry_info r ON l.gpdm = r.gpdm
	''').dropDuplicates(['startnode', 'endnode', 'reportdate'])
	company_hasindustryof_industry.repartition(1).write.csv(outputdata + 'company_hasindustryof_industry', header=True, sep='\t',mode='overwrite')
	save_to_mysql(company_hasindustryof_industry, 'company_hasindustryof_industry')
	
	
def product_hasindustryof_industry():
	pass

	
if __name__ == '__main__':
	inputdata = ''
	outputdata = 'file:/root/financial_graph/output/data_neo4j/'
	
	print('processing clean_supplier_customer...')
	clean_supplier_customer()
	
	# print('processing company...')
	# company()
	
	print('processing person...')
	person()
	
	# print('processing product...')
	# product()
	
	# print('processing industry...')
	# industry()
	
	# print('processing person_shareholderof_company...')
	# person_shareholderof_company()
	
	# print('processing person_supplierof_company...')
	# person_supplierof_company()
	
	# print('processing person_customerof_company...')
	# person_customerof_company()
	
	# print('processing person_chairmanof_company...')
	# person_chairmanof_company()
	
	# print('processing person_executiveof_company...')
	# person_executiveof_company()
	
	# print('processing person_managerof_company...')
	# person_managerof_company()
	
	# print('processing person_legalof_company...')
	# person_legalof_company()
	
	# print('processing company_shareholderof_company...')
	# company_shareholderof_company()
	
	# print('processing company_supplierof_company...')
	# company_supplierof_company()
	
	# print('processing company_customerof_company...')
	# company_customerof_company()

	# print('processing company_hasproductof_product...')
	# company_hasproductof_product()
	
	# print('processing company_hasindustryof_industry...')
	# company_hasindustryof_industry()
	
	# print('processing product_hasindustryof_industry...')
	# product_hasindustryof_industry()
