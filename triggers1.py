import pandas as pd
import numpy as np
import openpyxl
import xlsxwriter
from io import StringIO
from tqdm import tqdm
tqdm.pandas()
import streamlit as st
import os


page=st.sidebar.selectbox("Select any page",["Triggers Data Preparation","Append Files"])


if page=="Triggers Data Preparation":

    st.header("Daily trigges Data Preparation")

# master file with cube column's 
    file=st.file_uploader("***Select file contains cube columns***","csv")
    if file is not None:
        df_cube=pd.read_csv(file)
        # df_cube.columns.T
        # df_cube=df_cube[['CONNO','BPNO','PRODUCT','ASSET_CATEGORY','ASSET_CATEGORY1','ASSET_CATEGORY2',
                                # 'ZONE','STATE','REGION','CUSTOMER_SEGMENT','CUST_SEG','COMPANY_CODE','Allocation_Band']]
        #  for all bpno
        df_cube_bp=df_cube[df_cube['BPNO'].notna()]
        # for no bpno(blank)
        df_cube_nobp=df_cube[df_cube['BPNO'].isna()]

        with st.expander("Data"):
            df_cube.shape
            df_cube




    # Raw Text File
    upload=st.file_uploader("***Upload Daily Text File***",type=["txt"])

    if upload is not None:
        # upload.name
        df=pd.read_csv(upload,sep="|")
        with st.expander("Data"):
            st.write("Shape of the File",df.shape)
            st.write(df)


        def new_cols(x):
            if x['Trigger Type']=='Number of Accounts Delinquent':
                if x['Trigger P4']=='D':
                    return "Paid" , "Collection Opportunity / Recovery" ,"The Customer's number of delinquent account has decreased"
                else:
                    return "Delinquency Increase" , "Early Warning", "The Customer's number of delinquent account has increased"
                
            elif x['Trigger Type']=='Delinquency Change and Threshold':
                if x['Trigger P4']=='D':
                    return "Paid" , "Collection Opportunity / Recovery","The Customer has paid outside"
                else:
                    return "Not Paid" , "Early Warning","The Customer has not paid"
                
            elif x['Trigger Type']=='Change in Utilization-Aggregate of Trades':
                if x['Trigger P4']=='D':
                    return "Paid" , "Collection Opportunity / Recovery","The Customer has paid outside"
                else:
                    return "Not Paid" , "Early Warning","The Customer has not paid"
            
            elif x['Trigger Type'] in ["New Address","New Phone"]:
                if x['Trigger Type']=="New Address":
                    return "For skipped cases" , "Early Warning","The customer has changed Address"
                else:
                    return "For skipped cases" , "Early Warning","The customer has changed phone number"
            
            elif x['Trigger Type']=="New Account":
                loan_type=["GOLD LOAN","PERSONAL LOAN","BUSINESS LOAN - UNSECURED","BUSINESS LOAN - GENERAL","MICROFINANCE - BUSINESS LOAN","BUSINESS LOAN- SECURED","LOAN TO PROFESSIONAL"]
                BL_list=[value for value in df['Acct Info-Account Type'] if str(value).startswith('BLPS')]
                list_loan=loan_type+BL_list
                if x["Acct Info-Account Type"] in list_loan:
                    y=x["Acct Info-Account Type"]
                    return f"Taken {y} from Outside " , "Collection Opportunity / Recovery",f"The customer has taken {y} from Outside "
                else:
                    return "Taken Others Loan from outside" , " ","The customer has taken others loan from outside"
            else:
                return " " , " "," "
            

        df[['Output', 'Action Point', 'Description']] = df.progress_apply(new_cols, axis=1, result_type='expand')

        # Remove _ from account number

        df['CONNO']=df['Account Number'].apply(lambda x:x.replace("_"," "))
        df['CONNO']=df['CONNO'].apply(pd.to_numeric,errors='coerce')
        # Date time

        df['Alert Generation Date Time']=pd.to_datetime(df['Alert Generation Date Time'],errors='coerce')
        df['Date']=df['Alert Generation Date Time'].dt.date

        # Select required columns
        columns=['CONNO', 'Output', 'Action Point','Description', 'Account Type',
        'Ownership Indicator','Date',
        'Acct Info-Account Type', 'Acct Info-Account Ownership',
        'Contact Info-Name1', 'Contact Info-Name2', 'Contact Info-Name3',
        'Contact Info-Name4', 'Contact Info-Name5', 'Contact Info-Gender',
        'Contact Info-DOB', 'Contact Info-Latest Address - Address Line 1',
        'Contact Info-Latest Address - Address Line 2',
        'Contact Info-Latest Address - Address Line 3',
        'Contact Info-Latest Address - Address Line 4',
        'Contact Info-Latest Address - Address Line 5',
        'Contact Info-Latest Address - State Code',
        'Contact Info-Latest Address - Pin Code',
        'Contact Info-Latest Address - Address Category',
        'Contact Info-Latest Address - Residence Code',
        'Contact Info-Second Address - Address Line 1',
        'Contact Info-Second Address - Address Line 2',
        'Contact Info-Second Address - Address Line 3',
        'Contact Info-Second Address - Address Line 4',
        'Contact Info-Second Address - Address Line 5',
        'Contact Info-Second Address - State Code',
        'Contact Info-Second Address - Pin Code',
        'Contact Info-Second Address - Address Category',
        'Contact Info-Second Address - Residence Code',
        'Contact Info-Latest Phone Number',
        'Contact Info-Latest Phone Extension', 'Contact Info-Latest Phone Type',
        'Contact Info-Second Phone Number',
        'Contact Info-Second Phone Extension', 'Contact Info-Second Phone Type',
        'Enquiry Info- Enquiry Type', 'Enquiry Info- Enquiry Amount']

        df1=df[columns]
        

# --------------------------------------------------------------------
        #    #experiment 
        # file1=st.file_uploader("**Select main triggers file**","xlsx")
        # if file1 is not None:
        #     df_main=pd.read_excel(file1)
        #     df1=df_main

        #     with st.expander("Data"):
        #         df_main.shape
        #         df_main
# --------------------------------------------------------

        # merge with cube columns

        want=st.checkbox("**Want to add columns**")
        if want:
            
            merge_df0=df1.merge(df_cube[['CONNO','BPNO']],on='CONNO',how='left')

            # reordering columns
            column=list(merge_df0.columns)
            column.remove('BPNO')
            column.insert(1,'BPNO')
            merge_df0=merge_df0[column]


            merge_df1=merge_df0[['CONNO','BPNO','Output','Action Point','Description']]
            merge_df1['Filter']=1

            # base is cube master file

            # with npbp
            merge_df3_nobp=df_cube_nobp.merge(merge_df1,how='left',on='CONNO')

            # with all bpno

            merge_df2=merge_df1.drop('CONNO',axis=1)

            merge_df3_allbp=df_cube_bp.merge(merge_df2,how='left',on='BPNO')


            # Appeend both file

            merge_df3=merge_df3_allbp.append(merge_df3_nobp)
            
            
            merge_df3=merge_df3[merge_df3['Filter'].notna()]

            #columns reordering

            merge_df3=merge_df3[['CONNO','BPNO','Output','Action Point','Description','CONDITION','PRODUCT','ASSET_CATEGORY','ASSET_CATEGORY1','ASSET_CATEGORY2','ZONE','STATE',
                                 'REGION','CUSTOMER_SEGMENT','CUST_SEG','COMPANY_CODE','DEC23_DPD','ODBKT_MONTH_DEC23','Allocation_Band','Sub Group','Vendor Name','FILTER']]

            
            # merge_df1=merge_df1.merge(df_cube,how='left',on='BPNO')


            #create bpno and rest of triggers column dataset
            bpno=merge_df0.iloc[:,1:2]
            rest_cols=merge_df0.iloc[:,5:]
            merge_df00=pd.concat([bpno,rest_cols],axis=1)


            # merge daily triggers column with cube master column

            merge_df3=pd.merge(merge_df3,merge_df00,on='BPNO',how='left')
    
            
            # convert in date
            merge_df3['Date']=pd.to_datetime(merge_df3['Date']).dt.date

            # merge_df3=merge_df3.drop('Date',axis=1)

            

            # Create two columns

            def priority(x):
                if x['Action Point']=='Collection Opportunity / Recovery':
                    return 1
                elif x["Action Point"]=="Early Warning":
                    return 2
                else:
                    pass

            merge_df3['Priority']=merge_df3.apply(priority,axis=1)

            # identify duplicate values
            duplicate=merge_df3.duplicated(subset=['CONNO','BPNO'],keep=False)
            merge_df3['Duplicate']=duplicate.map({True:'Yes',False:'No'})   
            
            # reordering Duplicate and priority columns

            cols=['Priority','Duplicate']
            reorder_columns=list(merge_df3.columns[:5])+['Priority','Duplicate']+[col for col in list(merge_df3.columns) if col not in cols][5:]
            merge_df3=merge_df3[reorder_columns]

            # reordering  date columns
            column=list(merge_df3.columns)
            column.remove('Date')
            column.insert(7,'Date')
            merge_df3=merge_df3[column]

            #drop_duplicates
            merge_df3=merge_df3.drop_duplicates(subset=['CONNO','BPNO','Output','Action Point','Description'])

            #rename
            df1=merge_df3

            #Sort the data

            df1=df1.sort_values(by='CONNO')

            
# -----------------------------------------------------
            # Overall 
            df11=df1

            # OVERALL Collection Opportunity/Recovery

            df12=df11[df11["Action Point"]=="Collection Opportunity / Recovery"]

            # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
            df12=df12.drop('Duplicate',axis=1)
            duplicate=df12.duplicated(subset=['CONNO','BPNO'],keep=False)
            df12['Duplicate']=duplicate.map({True:'Yes',False:'No'})
            # df12=df12.insert(6,'Duplicate',value=df12['Duplicate'])
                # reordering  date columns
            column=list(df12.columns)
            column.remove('Duplicate')
            column.insert(6,'Duplicate')
            df12=df12[column]

# -----------------------------------------------------------------------------------------------------------------

            
                
            
                

            


            # OVERALL Early Warning

            df13=df11[df11["Action Point"]=="Early Warning"]

            # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
            df13=df13.drop('Duplicate',axis=1)
            duplicate=df13.duplicated(subset=['CONNO','BPNO'],keep=False)
            df13['Duplicate']=duplicate.map({True:'Yes',False:'No'})

            # reordering  date columns
            column=list(df13.columns)
            column.remove('Duplicate')
            column.insert(6,'Duplicate')
            df13=df13[column]

# -----------------------------------------------------------------------------------------------------------------



            # SPOCTO/Goalcryst
            df11_goalcryst=df11[df11['FILTER']=="SPOCTO/Goalcryst"]

            

            # SPOCTO/Goalcryst Collection Opportunity/Recovery

            df12_goalcryst=df11_goalcryst[df11_goalcryst["Action Point"]=="Collection Opportunity / Recovery"]

            # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
            df12_goalcryst=df12_goalcryst.drop('Duplicate',axis=1)
            duplicate=df12_goalcryst.duplicated(subset=['CONNO','BPNO'],keep=False)
            df12_goalcryst['Duplicate']=duplicate.map({True:'Yes',False:'No'})
            
            # reordering  date columns
            column=list(df12_goalcryst.columns)
            column.remove('Duplicate')
            column.insert(6,'Duplicate')
            df12_goalcryst=df12_goalcryst[column]

# -----------------------------------------------------------------------------------------------------------------


            # SPOCTO/Goalcryst Early Warning

            df13_goalcryst=df11_goalcryst[df11_goalcryst["Action Point"]=="Early Warning"]

            # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
            df13_goalcryst=df13_goalcryst.drop('Duplicate',axis=1)
            duplicate=df13_goalcryst.duplicated(subset=['CONNO','BPNO'],keep=False)
            df13_goalcryst['Duplicate']=duplicate.map({True:'Yes',False:'No'})
            
            # reordering  date columns
            column=list(df13_goalcryst.columns)
            column.remove('Duplicate')
            column.insert(6,'Duplicate')
            df13_goalcryst=df13_goalcryst[column]

# -----------------------------------------------------------------------------------------------------------------


            # SPOCTO/ARRISE
            df11_arrise=df11[df11['FILTER']=="SPOCTO/ARRISE"]

            # SPOCTO/ARRISE Collection Opportunity/Recovery

            df12_arrise=df11_arrise[df11_arrise["Action Point"]=="Collection Opportunity / Recovery"]

            # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
            df12_arrise=df12_arrise.drop('Duplicate',axis=1)
            duplicate=df12_arrise.duplicated(subset=['CONNO','BPNO'],keep=False)
            df12_arrise['Duplicate']=duplicate.map({True:'Yes',False:'No'})
            
            # reordering  date columns
            column=list(df12_arrise.columns)
            column.remove('Duplicate')
            column.insert(6,'Duplicate')
            df12_arrise=df12_arrise[column]

# -----------------------------------------------------------------------------------------------------------------



            # SPOCTO/ARRISE Early Warning

            df13_arrise=df11_arrise[df11_arrise["Action Point"]=="Early Warning"]

            # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
            df13_arrise=df13_arrise.drop('Duplicate',axis=1)
            duplicate=df13_arrise.duplicated(subset=['CONNO','BPNO'],keep=False)
            df13_arrise['Duplicate']=duplicate.map({True:'Yes',False:'No'})
            
            # reordering  date columns
            column=list(df13_arrise.columns)
            column.remove('Duplicate')
            column.insert(6,'Duplicate')
            df13_arrise=df13_arrise[column]

# -----------------------------------------------------------------------------------------------------------------


    # -----------------------------------------------------------------------
        # See the data

            with st.expander("**Final Data**"):
                choose0=st.selectbox(" ",("Overall","SPOCTO/Goalcryst","SPOCTO/ARRISE"))
                if choose0=="Overall":
                    choose1=st.selectbox("  ",("Main Data","Collection Opportunity/Recovery","Early Warning"))
                    if choose1=="Main Data":
                        st.write("**Shape of Main Data :**",df11.shape)
                        st.write("**Main Data**",df11)

                    if choose1=="Collection Opportunity/Recovery":
                        st.write("**Shape of Collection Opportunity/Recovery Data :**",df12.shape)
                        st.write("**Collection Opportunity/Recovery Data**",df12)

                    if choose1=="Early Warning":
                        st.write("**Shape of Early Warning :**",df13.shape)
                        st.write("**Early Warning**",df13)

                if choose0=="SPOCTO/Goalcryst":
                    choose1=st.selectbox("  ",("Main Data","Collection Opportunity/Recovery","Early Warning"))
                    if choose1=="Main Data":
                        st.write("**Shape of Main Data :**",df11_goalcryst.shape)
                        st.write("**Main Data**",df11_goalcryst)

                    if choose1=="Collection Opportunity/Recovery":
                        st.write("**Shape of Collection Opportunity/Recovery Data :**",df12_goalcryst.shape)
                        st.write("**Collection Opportunity/Recovery Data**",df12_goalcryst)

                    if choose1=="Early Warning":
                        st.write("**Shape of Early Warning :**",df13_goalcryst.shape)
                        st.write("**Early Warning**",df13_goalcryst)

                if choose0=="SPOCTO/ARRISE":
                    choose1=st.selectbox("  ",("Main Data","Collection Opportunity/Recovery","Early Warning"))
                    if choose1=="Main Data":
                        st.write("**Shape of Main Data :**",df11_arrise.shape)
                        st.write("**Main Data**",df11_arrise)

                    if choose1=="Collection Opportunity/Recovery":
                        st.write("**Shape of Collection Opportunity/Recovery Data :**",df12_arrise.shape)
                        st.write("**Collection Opportunity/Recovery Data**",df12_arrise)

                    if choose1=="Early Warning":
                        st.write("**Shape of Early Warning :**",df13_arrise.shape)
                        st.write("**Early Warning**",df13_arrise)



            # Download 

            if st.checkbox("**Want to Download the excel file**"):

                # new folder create

                folder=["main","goalcryst","arrise"]
                for i in folder:
                    os.makedirs(i,exist_ok=True)

                #overall
                name_Overall="main\Collection_Daily_Triggers"
                # name_Overall=os.path.join("main",name_Overall)
                name_goalcryst="goalcryst\Collecetion_Daily_Triggers_SPOCTO_Goalcryst"
                name_arrise="arrise\Collection_Daily_Triggers_SPOCTO_ARRISE"

                # Date
                want=st.text_input("*Enter the Date(Format=ddmmyyyy)*")

                #Excel files name
                want_overall=name_Overall+'_'+want
                want_goalcryst=name_goalcryst+'_'+want
                want_arrise=name_arrise+'_'+want


                if want:
                    # button=st.button("**Download**")
                    # if button:
                    if st.download_button("Download"):

                            # Overall
                            with pd.ExcelWriter(want_overall+".xlsx",engine='xlsxwriter') as want:
                                df11.to_excel(want,sheet_name="Main Data",index=False)
                                df12.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13.to_excel(want,sheet_name="Early Warning",index=False)

                            # SPOCTO/Goalcryst
                            with pd.ExcelWriter(want_goalcryst+".xlsx",engine='xlsxwriter') as want:
                                df11_goalcryst.to_excel(want,sheet_name="Main Data",index=False)
                                df12_goalcryst.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13_goalcryst.to_excel(want,sheet_name="Early Warning",index=False)
                                
                            # SPOCTO/ARRISE
                            with pd.ExcelWriter(want_arrise+".xlsx",engine='xlsxwriter') as want:
                                df11_arrise.to_excel(want,sheet_name="Main Data",index=False)
                                df12_arrise.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13_arrise.to_excel(want,sheet_name="Early Warning",index=False)
        # -------------------------------------------------------------------------------------------------                        

if page=="Append Files":

    st.header("Final Data")

    files=st.file_uploader("**Upload a folder that contains all excel file that you want to check for using duplicate**",accept_multiple_files=True)

    if files:
        df0=pd.DataFrame()
        for file in files:
            file=pd.read_excel(file)
            df0=df0.append(file)

        # df0.shape

    
    
        # df00=df0[['CONNO','BPNO','Output','Action Point','Description']]

        with st.expander("**Append Data**"):
            st.write("**Shape**",df0.shape)
            st.write("**Data**",df0)

        # Check Duplicate
            
        #Remove duplicate column
        df0=df0.drop('Duplicate',axis=1)    
        
        #drop_duplicates from rows
        df0=df0.drop_duplicates(subset=['CONNO','BPNO','Output','Action Point','Description']) 
        
            
        # identify duplicate values
        df0['Duplicate']=df0.duplicated(subset=['CONNO','BPNO'],keep=False)
        df0['Duplicate']=df0['Duplicate'].map({True:'Yes',False:'No'})
        
        # re-oredreing columns
        column=list(df0.columns)
        column.remove('Duplicate')
        column.insert(6,'Duplicate')

        df0=df0[column]

        #rename dataset

        df11=df0

        #Sort the data

        df11=df11.sort_values(by='CONNO')

# -----------------------------------------------------
        # Overall 
        df11=df11

        # OVERALL Collection Opportunity/Recovery

        df12=df11[df11["Action Point"]=="Collection Opportunity / Recovery"]

        # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
        df12=df12.drop('Duplicate',axis=1)
        duplicate=df12.duplicated(subset=['CONNO','BPNO'],keep=False)
        df12['Duplicate']=duplicate.map({True:'Yes',False:'No'})
        # df12=df12.insert(6,'Duplicate',value=df12['Duplicate'])
            # reordering  date columns
        column=list(df12.columns)
        column.remove('Duplicate')
        column.insert(6,'Duplicate')
        df12=df12[column]

# -----------------------------------------------------------------------------------------------------------------

        
            
        
            

        


        # OVERALL Early Warning

        df13=df11[df11["Action Point"]=="Early Warning"]

        # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
        df13=df13.drop('Duplicate',axis=1)
        duplicate=df13.duplicated(subset=['CONNO','BPNO'],keep=False)
        df13['Duplicate']=duplicate.map({True:'Yes',False:'No'})

        # reordering  date columns
        column=list(df13.columns)
        column.remove('Duplicate')
        column.insert(6,'Duplicate')
        df13=df13[column]

# -----------------------------------------------------------------------------------------------------------------



        # SPOCTO/Goalcryst
        df11_goalcryst=df11[df11['FILTER']=="SPOCTO/Goalcryst"]

        

        # SPOCTO/Goalcryst Collection Opportunity/Recovery

        df12_goalcryst=df11_goalcryst[df11_goalcryst["Action Point"]=="Collection Opportunity / Recovery"]

        # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
        df12_goalcryst=df12_goalcryst.drop('Duplicate',axis=1)
        duplicate=df12_goalcryst.duplicated(subset=['CONNO','BPNO'],keep=False)
        df12_goalcryst['Duplicate']=duplicate.map({True:'Yes',False:'No'})
        
        # reordering  date columns
        column=list(df12_goalcryst.columns)
        column.remove('Duplicate')
        column.insert(6,'Duplicate')
        df12_goalcryst=df12_goalcryst[column]

# -----------------------------------------------------------------------------------------------------------------


        # SPOCTO/Goalcryst Early Warning

        df13_goalcryst=df11_goalcryst[df11_goalcryst["Action Point"]=="Early Warning"]

        # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
        df13_goalcryst=df13_goalcryst.drop('Duplicate',axis=1)
        duplicate=df13_goalcryst.duplicated(subset=['CONNO','BPNO'],keep=False)
        df13_goalcryst['Duplicate']=duplicate.map({True:'Yes',False:'No'})
        
        # reordering  date columns
        column=list(df13_goalcryst.columns)
        column.remove('Duplicate')
        column.insert(6,'Duplicate')
        df13_goalcryst=df13_goalcryst[column]

# -----------------------------------------------------------------------------------------------------------------


        # SPOCTO/ARRISE
        df11_arrise=df11[df11['FILTER']=="SPOCTO/ARRISE"]

        # SPOCTO/ARRISE Collection Opportunity/Recovery

        df12_arrise=df11_arrise[df11_arrise["Action Point"]=="Collection Opportunity / Recovery"]

        # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
        df12_arrise=df12_arrise.drop('Duplicate',axis=1)
        duplicate=df12_arrise.duplicated(subset=['CONNO','BPNO'],keep=False)
        df12_arrise['Duplicate']=duplicate.map({True:'Yes',False:'No'})
        
        # reordering  date columns
        column=list(df12_arrise.columns)
        column.remove('Duplicate')
        column.insert(6,'Duplicate')
        df12_arrise=df12_arrise[column]

# -----------------------------------------------------------------------------------------------------------------



        # SPOCTO/ARRISE Early Warning

        df13_arrise=df11_arrise[df11_arrise["Action Point"]=="Early Warning"]

        # identify duplicate in collection opportunity and early warning
# ---------------------------------------------------------------------------------------------------------------
        df13_arrise=df13_arrise.drop('Duplicate',axis=1)
        duplicate=df13_arrise.duplicated(subset=['CONNO','BPNO'],keep=False)
        df13_arrise['Duplicate']=duplicate.map({True:'Yes',False:'No'})
        
        # reordering  date columns
        column=list(df13_arrise.columns)
        column.remove('Duplicate')
        column.insert(6,'Duplicate')
        df13_arrise=df13_arrise[column]

# -----------------------------------------------------------------------------------------------------------------


# -----------------------------------------------------------------------
    # See the data

        with st.expander("**Final Data**"):
            choose0=st.selectbox(" ",("Overall","SPOCTO/Goalcryst","SPOCTO/ARRISE"))
            if choose0=="Overall":
                choose1=st.selectbox("  ",("Main Data","Collection Opportunity/Recovery","Early Warning"))
                if choose1=="Main Data":
                    st.write("**Shape of Main Data :**",df11.shape)
                    st.write("**Main Data**",df11)

                if choose1=="Collection Opportunity/Recovery":
                    st.write("**Shape of Collection Opportunity/Recovery Data :**",df12.shape)
                    st.write("**Collection Opportunity/Recovery Data**",df12)

                if choose1=="Early Warning":
                    st.write("**Shape of Early Warning :**",df13.shape)
                    st.write("**Early Warning**",df13)

            if choose0=="SPOCTO/Goalcryst":
                choose1=st.selectbox("  ",("Main Data","Collection Opportunity/Recovery","Early Warning"))
                if choose1=="Main Data":
                    st.write("**Shape of Main Data :**",df11_goalcryst.shape)
                    st.write("**Main Data**",df11_goalcryst)

                if choose1=="Collection Opportunity/Recovery":
                    st.write("**Shape of Collection Opportunity/Recovery Data :**",df12_goalcryst.shape)
                    st.write("**Collection Opportunity/Recovery Data**",df12_goalcryst)

                if choose1=="Early Warning":
                    st.write("**Shape of Early Warning :**",df13_goalcryst.shape)
                    st.write("**Early Warning**",df13_goalcryst)

            if choose0=="SPOCTO/ARRISE":
                choose1=st.selectbox("  ",("Main Data","Collection Opportunity/Recovery","Early Warning"))
                if choose1=="Main Data":
                    st.write("**Shape of Main Data :**",df11_arrise.shape)
                    st.write("**Main Data**",df11_arrise)

                if choose1=="Collection Opportunity/Recovery":
                    st.write("**Shape of Collection Opportunity/Recovery Data :**",df12_arrise.shape)
                    st.write("**Collection Opportunity/Recovery Data**",df12_arrise)

                if choose1=="Early Warning":
                    st.write("**Shape of Early Warning :**",df13_arrise.shape)
                    st.write("**Early Warning**",df13_arrise)



        # Download 

        if st.checkbox("**Want to Download the excel file**"):

            # new folder create

            folder=["main","goalcryst","arrise"]
            for i in folder:
                os.makedirs(i,exist_ok=True)

            #overall
            name_Overall="main\Final_Collection_Daily_Triggers_Until_"
            # name_Overall=os.path.join("main",name_Overall)
            name_goalcryst="goalcryst\Final_Collecetion_Daily_Triggers_SPOCTO_Goalcryst_Until_"
            name_arrise="arrise\Final_Collection_Daily_Triggers_SPOCTO_ARRISE_Until_"

            #  date Filter
            name_goalcryst1="goalcryst\Final_Collecetion_Daily_Triggers_SPOCTO_Goalcryst_from_1st_to_" # <=10 
            name_goalcryst2="goalcryst\Final_Collecetion_Daily_Triggers_SPOCTO_Goalcryst_from_11th_to_" #11-20
            name_goalcryst3="goalcryst\Final_Collecetion_Daily_Triggers_SPOCTO_Goalcryst_from_21st_to_" #21-30/31


            name_arrise1="arrise\Final_Collection_Daily_Triggers_SPOCTO_ARRISE_from_1st_to_" #<=10
            name_arrise2="arrise\Final_Collection_Daily_Triggers_SPOCTO_ARRISE_from_11th_to_" # 11-20
            name_arrise3="arrise\Final_Collection_Daily_Triggers_SPOCTO_ARRISE_from_21st_to_" # 21-30/31

            # Date
            want=st.text_input("*Enter the Date(Format=ddmmyyyy)*")

            #Excel files name
            want_overall=name_Overall+'_'+want
            want_goalcryst=name_goalcryst+'_'+want
            want_arrise=name_arrise+'_'+want

            #  Date filter
            want_goalcryst_date1=name_goalcryst1+'_'+want
            want_goalcryst_date2=name_goalcryst2+'_'+want
            want_goalcryst_date3=name_goalcryst3+'_'+want

            want_arrise_date1=name_arrise1+'_'+want
            want_arrise_date2=name_arrise2+'_'+want
            want_arrise_date3=name_arrise3+'_'+want



            if want:
                # Date format filter
                date_format=want[:2]
                date_format=int(date_format)

                if date_format<=10: # 1-15

                    #goalcryst
                    df11_goalcryst_le10=df11_goalcryst[pd.to_datetime(df11_goalcryst['Date']).dt.day<=date_format] #main data
                    df12_goalcryst_le10=df12_goalcryst[pd.to_datetime(df12_goalcryst['Date']).dt.day<=date_format] #collection opprtunity data
                    df13_goalcryst_le10=df13_goalcryst[pd.to_datetime(df13_goalcryst['Date']).dt.day<=date_format] #Early warning data

                    #arrise
                    df11_arrise_le10=df11_arrise[pd.to_datetime(df11_arrise['Date']).dt.day<=date_format] #main data
                    df12_arrise_le10=df12_arrise[pd.to_datetime(df12_arrise['Date']).dt.day<=date_format] #collection opprtunity data
                    df13_arrise_le10=df13_arrise[pd.to_datetime(df13_arrise['Date']).dt.day<=date_format] #Early warning data

                    # button=st.button("**Download**")
                    # if button:
                    if st.download_button("Download1"):

                            # Overall
                            with pd.ExcelWriter(want_overall+".xlsx",engine='xlsxwriter') as want:
                                df11.to_excel(want,sheet_name="Main Data",index=False)
                                df12.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13.to_excel(want,sheet_name="Early Warning",index=False)

                            # SPOCTO/Goalcryst
                                # Overall
                            # with pd.ExcelWriter(want_goalcryst+".xlsx",engine='xlsxwriter') as want:
                            #     df11_goalcryst.to_excel(want,sheet_name="Main Data",index=False)
                            #     df12_goalcryst.to_excel(want,sheet_name="Collection Opportunity",index=False)
                            #     df13_goalcryst.to_excel(want,sheet_name="Early Warning",index=False)

                                #Date filter
                            with pd.ExcelWriter(want_goalcryst_date1+".xlsx",engine='xlsxwriter') as want:
                                
                                df11_goalcryst_le10.to_excel(want,sheet_name="Main Data",index=False)
                                df12_goalcryst_le10.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13_goalcryst_le10.to_excel(want,sheet_name="Early Warning",index=False)

                                
                            # SPOCTO/ARRISE
                            # with pd.ExcelWriter(want_arrise+".xlsx",engine='xlsxwriter') as want:
                            #     df11_arrise.to_excel(want,sheet_name="Main Data",index=False)
                            #     df12_arrise.to_excel(want,sheet_name="Collection Opportunity",index=False)
                            #     df13_arrise.to_excel(want,sheet_name="Early Warning",index=False)

                                # date filter
                            with pd.ExcelWriter(want_arrise_date1+".xlsx",engine='xlsxwriter') as want:
                                df11_arrise_le10.to_excel(want,sheet_name="Main Data",index=False)
                                df12_arrise_le10.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13_arrise_le10.to_excel(want,sheet_name="Early Warning",index=False)


                elif 11<=date_format<=20: # 11-15: # 11-20 days

                    def inbtwndate(x,strt,end): # in between date filter like 10-20 days of a month
                        x['Date']=pd.to_datetime(x['Date'])
                        filter1=x[x['Date'].dt.day<=end]
                        filter1=filter1[filter1['Date'].dt.day>=strt]
                        return filter1

                    #goalcryst
                    df11_goalcryst_11_20=inbtwndate(df11_goalcryst,11,20) #main data
                    df12_goalcryst_11_20=inbtwndate(df12_goalcryst,11,20) #collection opprtunity data
                    df13_goalcryst_11_20=inbtwndate(df13_goalcryst,11,20) #Early warning data

                    #arrise
                    df11_arrise_11_20=inbtwndate(df11_arrise,11,20) #main data
                    df12_arrise_11_20=inbtwndate(df12_arrise,11,20) #collection opprtunity data
                    df13_arrise_11_20=inbtwndate(df13_arrise,11,20) #Early warning data

                    # button=st.button("**Download**")
                    # if button:
                    if st.download_button("Download2"):

                            # Overall
                            with pd.ExcelWriter(want_overall+".xlsx",engine='xlsxwriter') as want:
                                df11.to_excel(want,sheet_name="Main Data",index=False)
                                df12.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13.to_excel(want,sheet_name="Early Warning",index=False)

                            # SPOCTO/Goalcryst
                                # Overall
                            # with pd.ExcelWriter(want_goalcryst+".xlsx",engine='xlsxwriter') as want:
                            #     df11_goalcryst.to_excel(want,sheet_name="Main Data",index=False)
                            #     df12_goalcryst.to_excel(want,sheet_name="Collection Opportunity",index=False)
                            #     df13_goalcryst.to_excel(want,sheet_name="Early Warning",index=False)

                                #Date filter
                            with pd.ExcelWriter(want_goalcryst_date2+".xlsx",engine='xlsxwriter') as want:
                                
                                df11_goalcryst_11_20.to_excel(want,sheet_name="Main Data",index=False)
                                df12_goalcryst_11_20.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13_goalcryst_11_20.to_excel(want,sheet_name="Early Warning",index=False)

                                
                            # SPOCTO/ARRISE 
                                # OVERALL
                            # with pd.ExcelWriter(want_arrise+".xlsx",engine='xlsxwriter') as want:
                            #     df11_arrise.to_excel(want,sheet_name="Main Data",index=False)
                            #     df12_arrise.to_excel(want,sheet_name="Collection Opportunity",index=False)
                            #     df13_arrise.to_excel(want,sheet_name="Early Warning",index=False)

                                # date filter
                            with pd.ExcelWriter(want_arrise_date2+".xlsx",engine='xlsxwriter') as want:
                                df11_arrise_11_20.to_excel(want,sheet_name="Main Data",index=False)
                                df12_arrise_11_20.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13_arrise_11_20.to_excel(want,sheet_name="Early Warning",index=False)


                else: # 21-31 days

                    #goalcryst
                    df11_goalcryst_gt20=df11_goalcryst[pd.to_datetime(df11_goalcryst['Date']).dt.day>20] #main data
                    df12_goalcryst_gt20=df12_goalcryst[pd.to_datetime(df12_goalcryst['Date']).dt.day>20] #collection opprtunity data
                    df13_goalcryst_gt20=df13_goalcryst[pd.to_datetime(df13_goalcryst['Date']).dt.day>20] #Early warning data

                    #arrise
                    df11_arrise_gt20=df11_arrise[pd.to_datetime(df11_arrise['Date']).dt.day>20] #main data
                    df12_arrise_gt20=df12_arrise[pd.to_datetime(df12_arrise['Date']).dt.day>20] #collection opprtunity data
                    df13_arrise_gt20=df13_arrise[pd.to_datetime(df13_arrise['Date']).dt.day>20] #Early warning data

                    # button=st.button("**Download**")
                    # if button:
                    if st.download_button("Download3"):

                            # Overall
                            with pd.ExcelWriter(want_overall+".xlsx",engine='xlsxwriter') as want:
                                df11.to_excel(want,sheet_name="Main Data",index=False)
                                df12.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13.to_excel(want,sheet_name="Early Warning",index=False)

                            # SPOCTO/Goalcryst
                                # Overall
                            # with pd.ExcelWriter(want_goalcryst+".xlsx",engine='xlsxwriter') as want:
                            #     df11_goalcryst.to_excel(want,sheet_name="Main Data",index=False)
                            #     df12_goalcryst.to_excel(want,sheet_name="Collection Opportunity",index=False)
                            #     df13_goalcryst.to_excel(want,sheet_name="Early Warning",index=False)

                                #Date filter
                            with pd.ExcelWriter(want_goalcryst_date3+".xlsx",engine='xlsxwriter') as want:
                                
                                df11_goalcryst_gt20.to_excel(want,sheet_name="Main Data",index=False)
                                df12_goalcryst_gt20.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13_goalcryst_gt20.to_excel(want,sheet_name="Early Warning",index=False)

                                
                            # SPOCTO/ARRISE 
                                # OVERALL
                            # with pd.ExcelWriter(want_arrise+".xlsx",engine='xlsxwriter') as want:
                            #     df11_arrise.to_excel(want,sheet_name="Main Data",index=False)
                            #     df12_arrise.to_excel(want,sheet_name="Collection Opportunity",index=False)
                            #     df13_arrise.to_excel(want,sheet_name="Early Warning",index=False)

                                # date filter
                            with pd.ExcelWriter(want_arrise_date3+".xlsx",engine='xlsxwriter') as want:
                                df11_arrise_gt20.to_excel(want,sheet_name="Main Data",index=False)
                                df12_arrise_gt20.to_excel(want,sheet_name="Collection Opportunity",index=False)
                                df13_arrise_gt20.to_excel(want,sheet_name="Early Warning",index=False)

        # -------------------------------------------------------------------------------------------------                        
