#coding:utf-8
#A search engine webapp  based on streamlit 0.79.0
#ref:https://streamlit.io
#dev plan:
#a search box
#a table
#a field to upload xlsx file
#a button to download xlsx file
#streamlit run c:/chemicals/chem2reg/chem2reg_app.py

import streamlit as st
import numpy as np
import sqlite3

class Query:
    def __init__(self,cas_number):
        self.__casno=cas_number

    def CasnumberQuery(self):
        #There are 5 tables (IECSC,TSCAINV,PMNACC,EC and CNOTHERS) have casno field.
        #query in CNOTHERS
        result_list_0=[]
        row=0
        cas_query_0='''SELECT ori_sn,casno,cnname,enname,remark,legid FROM CNOTHERS WHERE casno='CAS_X';'''
        cas_query_1=cas_query_0.replace('CAS_X',str(self.__casno))#1336-21-6为氨的水溶液（7664-41-7为氨气、液氨）
        result_0=chemicals.execute(cas_query_1)
        for chem in result_0:#unpackaged to list
            result_list_0.append(chem[5])
        result_set_0=set(result_list_0)#convert list to set
        if len(result_set_0)==0:#if nothong in the set,it means no any matched result
            return None
        else:
            leg_query='''SELECT leg_cn,leg_en,pub_date FROM CNLAWS WHERE legid='LEG_X';'''
            leg_arr=np.empty((len(result_set_0)+1,3),object)#leg_cn|leg_en|pub_date
            leg_arr[0,:]=(['法规中文名称','English Title','发布日期'])
            for leg_id in result_set_0:
                leg_query_1=leg_query.replace('LEG_X',leg_id)
                leg_result_1=chemicals.execute(leg_query_1).fetchone()
                row+=1
                leg_arr[row,:]=([leg_result_1[0],leg_result_1[1],leg_result_1[2]])
            return leg_arr
st.set_page_config(page_title="A bridge from Chemical to Compliance",layout="wide")#2021-05-16
st.title('化学品关联法规查询')
warehouse=sqlite3.connect(r'cisdatabase.db')
#warehouse=sqlite3.connect(r'.\qehshub\mystock\main\cisdatabase.db') #/app/chem2reg/
st.secrets["password"]
chemicals=warehouse.cursor()
whichcasno=st.text_input('Enter CAS number', value='', max_chars=None, key=None, type='default', help='CAS num looks like 1336-21-6')#how to use the key？
st.text('or')
st.file_uploader('【....Not activated yet】Bulk Query（上传文件格式为xlsx且第一列为CAS no）【building....】')

def findillegalchar(casnum):
    '''
    Detect illegal char in the inputted casnum to prevent attack 
    Return None if not.
    '''
    safetynum=['0','1','2','3','4','5','6','7','8','9','-']
    for char in casnum:
        if char not in safetynum:            
            return char

if whichcasno!='':
    if findillegalchar(whichcasno):
        st.write(whichcasno,'包含非法字符：',findillegalchar(whichcasno))
    else:
        st.write(whichcasno,'的关联法规为：')
        query_test=Query(whichcasno)
        df_result_0=query_test.CasnumberQuery()
        if df_result_0 is not None:
            st.dataframe(data=df_result_0) 
        else:
            st.write('oops!未检索到关联法规数据')   


#显示中文名（要求不重复、非none）
#显示中文别名（要求不重复、非none）
#去EC表调取英文名信息（如果该值为none)
#显示法规中英文名（要求不重复）
#不但要去重还要去none
