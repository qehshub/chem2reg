#coding:utf-8
#2021-09-20
#New in the version 3.1:
#return/export query results in xlsx file
#psycopg2-2.8.6

import streamlit as st
import numpy as np
import psycopg2
import openpyxl
import base64

def findillegalchar(casnum):
    '''
    Detect illegal char in the inputted casnum to prevent attack 
    Return None if not.
    '''
    safetynum=['0','1','2','3','4','5','6','7','8','9','-']
    for char in casnum:
        if char not in safetynum:            
            return char

class Query:
    '''
    :use single cas num to search regulation
    :return a class 'numpy.ndarray'
    '''
    def __init__(self,cas_number):
        self.__casno=cas_number

    def CasnumberQuery(self):
        #There are 5 tables (IECSC,TSCAINV,PMNACC,EC and CNOTHERS) have casno field.
        #query in CNOTHERS
        result_list_0=[]
        row=0
        CAS_X=str(self.__casno)
        cas_query_0='''SELECT ori_sn,casno,cnname,enname,remark,legid FROM CNOTHERS WHERE casno=%s;'''
        #1336-21-6为氨的水溶液（7664-41-7为氨气、液氨）
        chemicals.execute(cas_query_0,(CAS_X,))
        result_0=chemicals.fetchall()
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
                chemicals.execute(leg_query_1)
                leg_result_1=chemicals.fetchone()
                row+=1
                leg_arr[row,:]=([leg_result_1[0],leg_result_1[1],leg_result_1[2]])
            return leg_arr

class BatchQuery:
    '''
    :received an uploaded xlsx file
    :use a list of cas num in xlsx file to search regulations
    :return a xlsx file(to do)
    :return an array to screen(for now)
    :return illegal char if any
    :as numpy array can't be expended or concatenated in place(make sense because arr always occupied a contiguous block of memory). rewrite the code from array to list
    '''
    def __init__(self,xlsx_file):
        self.__xlsx_file=xlsx_file
    
    def b_query(self):
        workbook_0=openpyxl.load_workbook(self.__xlsx_file)#目标文件
        sheet_0=workbook_0.active
        rownum=0
        rowmax=sheet_0.max_row
        chem_i=''
        x=[]
        illgealchar=''        
        arr_titlerow=[['CAS No.','CN Title','EN Title','Publish Date']]
        result_truck_2=[]
        for rownum in range(1,rowmax+1,1):
            result_truck=[]
            result_truck_1=[]
            result_truck_2=[]
            chem_i=sheet_0.cell(row=rownum,column=1).value
            
            if rowmax==1 and chem_i is None:#???为什么xlsx文件时空白的但是max_row检测出来的结果仍然是1
                st.warning('您上传的文件是空白的，请检查！')
                return None
            elif findillegalchar(chem_i):
                arr_titlerow.append([chem_i,'非法字符：'+illgealchar,'illegal character detected!','illegal character detected!'])
            else: 
                query_truck=Query(chem_i)
                result_truck=query_truck.CasnumberQuery()
                if result_truck is None:
                    arr_titlerow.append([chem_i,'No match','No match','No match'])
                else:
                    rownum_truck=result_truck.shape[0]#取得数组的行数值            
                    arr_newcol=np.full(rownum_truck,chem_i,order='F')#构建数组只有1列且每行赋值为chem_i（cas no）
                    result_truck_1=np.column_stack((arr_newcol,result_truck))#将单列数组与2维数组合并（arr_newcol位置在前）
                    result_truck_2=result_truck_1.tolist()#ndarray转换为list
                    for x in result_truck_2[1:]:#解包
                        arr_titlerow.append(x)
                    del result_truck
                    del result_truck_1
                    del result_truck_2
        arr_batch=np.array(arr_titlerow)
        return arr_batch

st.set_page_config(page_title="A bridge to Chemical Compliance",layout="wide")#2021-05-16
st.title('化学品关联法规查询 Chemical in Which Regulation')
warehouse=psycopg2.connect(**st.secrets["postgres"])
chemicals=warehouse.cursor()
st.info('&#x2139 单个查询 Single Query')
whichcasno=st.text_input('输入CAS号码 Enter CAS number', value='', max_chars=None, key=None, type='default', help='CAS num looks like 1336-21-6')#how to use the key？
st.text('or')
st.info('&#x2139 批量查询 Bulk Query')
st.info('The format of your uploaded file should be xlsx and CAS no must be in the first column')
uploaded_xlsx_file=st.file_uploader('上传文件格式为xlsx且第一列为CAS no',type=['xlsx'])

if whichcasno!='':
    if findillegalchar(whichcasno):
        st.write(whichcasno,'包含非法字符：',findillegalchar(whichcasno))
    else:
        st.write(whichcasno,'的关联法规为：')
        query_test=Query(whichcasno)
        df_result_0=query_test.CasnumberQuery()
        if df_result_0 is not None:
            st.dataframe(data=df_result_0) #此处应可调单元格宽度和高度
        else:
            st.warning('&#x1F622未检索到关联法规数据 no any match!')   

if uploaded_xlsx_file is not None:#如果有文件上传
    bquery_test=BatchQuery(uploaded_xlsx_file) 
    bq_result_1=bquery_test.b_query()
    if bq_result_1 is not None:

        #***********************************************************************************
        xlsx_exporter=openpyxl.Workbook()
        sheet=xlsx_exporter.active

        i=0
        rownum_final=bq_result_1.shape[0]
        for i in range(0,rownum_final,1):
                sheet.cell(row=i+1,column=1).value=bq_result_1[i,0]#'CAS No.'
                sheet.cell(row=i+1,column=2).value=bq_result_1[i,1]#'CN Title'
                sheet.cell(row=i+1,column=3).value=bq_result_1[i,2]#'EN Title'
                sheet.cell(row=i+1,column=4).value=bq_result_1[i,3]#'Publish Date'              
        xlsx_exporter.save('results.xlsx')
        data=open('results.xlsx','rb').read()#readonly in binary format
        b64 = base64.b64encode(data).decode('UTF-8')
        href = f'<a href="data:file/data;base64,{b64}" download="results.xlsx">Download xlsx file</a>'
        st.markdown(href, unsafe_allow_html=True)
        xlsx_exporter.close()
        st.dataframe(data=bq_result_1)
        #***********************************************************************************
