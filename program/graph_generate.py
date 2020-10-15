# -*- coding: utf-8 -*-
"""
@author: Changmu
"""

import os
import pandas as pd
import importlib,sys,time
from neo4j import GraphDatabase

dir = os.path.dirname(os.path.realpath(__file__))
# 将当前路径添加为导报路径列表中
sys.path.append(os.path.dirname(dir))
importlib.reload(sys)


def getpath(filename):
	dirpath = os.path.join(os.path.dirname(dir), 'output/data_neo4j', filename)
	for x in os.listdir(dirpath):
		if x[-4:] == '.csv':
			return os.path.join(dirpath, x)
	
	
def graph_execute(cql, parameters):
	'''
	cql执行函数
	输入cql语句，返回查询结果
	'''
	result = []
	with graph_db.session() as session:
		try:
			for x in session.run(cql, parameters):
				result.append(x)
			print('\n{}\n执行完毕！'.format(cql))
		except Exception as e:
			print('\n{}\n执行失败，请检查语句！'.format(cql))
			print(e)
			#os._exit(0)
	return result
		
		
def create_node(label):
	'''
	输入节点label，返回节点生成cql语句
	'''
	start = time.time()
	LABEL = label
	FILEPATH = getpath(label)
	# 根据csv表头获取所有的属性值
	df = pd.read_csv(FILEPATH, sep='\t')
	col_names = df.columns.values.tolist()
	col_names = ['{0}: line.{1}'.format(x,x) for x in col_names]
	PROPERTY = ', '.join(col_names)
	cql_remove_index = 'DROP INDEX ON:{LABEL}(uid)'.format(LABEL=LABEL)
	cql_create_index = 'CREATE INDEX ON :{LABEL}(uid)'.format(LABEL=LABEL)
	cql = '''
	USING PERIODIC COMMIT 5000
	LOAD CSV WITH HEADERS FROM
	'file://{FILEPATH}' AS line
	FIELDTERMINATOR '{SEP}'
	CREATE (:{LABEL} {{{PROPERTY}}});'''.format(LABEL=LABEL,
												FILEPATH=FILEPATH,
												SEP=r'\t',
												PROPERTY=PROPERTY)
	graph_execute(cql_remove_index,{})
	graph_execute(cql_create_index,{})
	graph_execute(cql,{})
	end = time.time()
	#print('------------------\n节点{0}创建成功,耗时{1}s\n------------------'
	#		.format(LABEL, str(end-start)))


def create_relation(relation):
	'''
	输入节点label，返回节点生成cql语句
	'''
	start = time.time()
	RELATION = relation
	STARTNODE = relation.split('_')[0]
	ENDNODE = relation.split('_')[2]
	TYPE = relation.split('_')[1]
	FILEPATH = getpath(relation)
	# 根据csv表头获取所有的属性值
	df = pd.read_csv(FILEPATH, sep='\t')
	col_names = df.columns.values.tolist()
	col_names = ['r.{0} = line.{1}'.format(x,x) for x in col_names[3::]]
	PROPERTY = ', '.join(col_names)
	cql = '''
	USING PERIODIC COMMIT 5000
	LOAD CSV WITH HEADERS FROM
	'file://{FILEPATH}' AS line
	FIELDTERMINATOR '{SEP}'
	MATCH (node1:{STARTNODE} {{uid: line.startnode}})
	MATCH (node2:{ENDNODE} {{uid: line.endnode}})
	CREATE (node1)-[r:{TYPE}]->(node2)
	SET {PROPERTY};'''.format(FILEPATH=FILEPATH,
							  SEP=r'\t',
							  STARTNODE=STARTNODE,
							  ENDNODE=ENDNODE,
							  TYPE=TYPE,
							  PROPERTY=PROPERTY)
	graph_execute(cql,{})
	end = time.time()
	#print('------------------\n关系{0}创建成功,耗时{1}s\n------------------'
	#		.format(RELATION, str(end-start)))
	

if __name__ == '__main__':
	# HOST = '81.68.175.213'
	HOST = '127.0.0.1'
	PORT = 7687
	USER = 'neo4j'
	#PASSWORD = 'neo4j@changmu'
	PASSWORD = 'neo4jforbigdata'
	graph_db = GraphDatabase.driver('neo4j://%s:%s' % (HOST, PORT), auth = (USER, PASSWORD))
	# 创建节点
	nodes = ['company', 'industry', 'person', 'product']
	#nodes = ['company']
	for label in nodes:
		# 删除图谱所有节点和关系
		graph_execute('match (n:{}) detach delete n'.format(label),{})
		# 创建新的节点
		create_node(label)
	# 创建关系
	relations = ['person_shareholderof_company', 'person_supplierof_company',
				'person_customerof_company', 'person_chairmanof_company',
				'person_executiveof_company', 'person_managerof_company',
				'person_legalof_company', 'company_shareholderof_company',
				'company_supplierof_company', 'company_customerof_company',
				'company_hasproductof_product', 'company_hasindustryof_industry']
	#graph_execute('match ()-[n:legalof]-() delete n',{})
	#relations = ['person_legalof_company']
	for relation in relations:
		create_relation(relation)