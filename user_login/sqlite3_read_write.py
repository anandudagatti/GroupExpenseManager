import sqlite3
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
import calendar
import re

def Write_to_DB(dictionary,table_name):
    conn = sqlite3.connect("db.sqlite3")
    data_frame = pd.DataFrame.from_dict(dictionary)
    data_frame.to_sql(table_name, conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

def Get_Income_Category():
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    
    sql_query = """SELECT category FROM income_category GROUP by category ORDER by category;"""  
    cur.execute(sql_query)
    result = cur.fetchall()
    cat_list = []
    for r in result:
        cat_list.append(r[0])
    return cat_list

def Get_Exp_Category():
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    
    sql_query = """SELECT category FROM expense_category GROUP by category ORDER by category;"""  
    cur.execute(sql_query)
    result = cur.fetchall()
    cat_list = []
    for r in result:
        cat_list.append(r[0])
    return cat_list

def Get_SubCategoryTable(category):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    
    select_query = """SELECT subcategory FROM expense_category WHERE category like "%{}%" GROUP by subcategory;""".format(category)  
    cur.execute(select_query)
    result = cur.fetchall()
    prod_list = []
    for r in result:
        prod_list.append(r[0])
    return prod_list

def Get_SessionID(session_data):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    date = session_data['date']
    userid = session_data['user_id']
    loggin_type = session_data['loggin_type']
    select_query = """SELECT session_id FROM session_master WHERE date like "%{}%" AND user_id like "%{}%" AND loggin_type like "%{}%";""".format(date[0],userid[0],loggin_type[0])  
    cur.execute(select_query)
    result = cur.fetchall()
    session_id = []
    for r in result:
        session_id.append(r[0])
    return session_id

def Delete_Issue_Count():
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    
    insert_query = """DELETE FROM Issues_Count_By_Keyword;"""  
    cur.execute(insert_query)
    conn.commit()
    conn.close()

def Get_Payee_List():
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    
    insert_query = """select payee_name FROM payee_list;"""  
    cur.execute(insert_query)
    result = cur.fetchall()
    payee_list = []
    for r in result:
        payee_list.append(r[0])
    conn.commit()
    conn.close()
    return payee_list

def Get_Payment_Method():
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    
    insert_query = """select payment_type FROM payment_methods;"""  
    cur.execute(insert_query)
    result = cur.fetchall()
    payment_methods = []
    for r in result:
        payment_methods.append(r[0])
    conn.commit()
    conn.close()
    return payment_methods

def Get_Payer_List():
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    
    insert_query = """select payer_name FROM payer_list;"""  
    cur.execute(insert_query)
    result = cur.fetchall()
    payer_list = []
    for r in result:
        payer_list.append(r[0])
    conn.commit()
    conn.close()
    return payer_list

def Insert_Payee(payee_list):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    ex_payee_list = Get_Payee_List()
    payee_id = len(ex_payee_list)+1
    for payee_name in payee_list:
        if payee_name not in ex_payee_list:
            insert_query = """INSERT INTO payee_list(payee_id,payee_name) VALUES("{}","{}");""".format(payee_id,payee_name) 
            cur.execute(insert_query)
            payee_id = payee_id +1
    
    conn.commit()
    conn.close()

def Update_Issue_Count_For_Key(key):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    
    insert_query = """SELECT Product, Date, count(Product) FROM Exported_Data WHERE category like "%{}%" GROUP by Date,Product;""".format(key)  
    cur.execute(insert_query)
    result = cur.fetchall()
    issue_dict = {'Product':[],'Date':[],'category':[],'NrOfIssues':[]}
    for r in result:
        issue_dict['Product'].append(r[0])
        issue_dict['Date'].append(r[1])
        issue_dict['category'].append(key)        
        issue_dict['NrOfIssues'].append(r[2])

    data_frame = pd.DataFrame.from_dict(issue_dict)
    data_frame.to_sql('Issues_Count_By_Keyword', conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

def Insert_Transaction(data_dict):
    conn = sqlite3.connect("db.sqlite3")    
    data_frame = pd.DataFrame.from_dict(data_dict)
    data_frame.to_sql('transaction_master', conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

def Get_Transaction_Summary(limit_to,userid):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    trans_dict = {}
    query = '''SELECT trans_date, category, sub_category, group_name, payee, 
    payment_method, tag, amount from transaction_master WHERE user="{}" 
    ORDER BY trans_date DESC LIMIT {};'''.format(userid,limit_to)
    
    cur.execute(query)
    result = cur.fetchall()
    row_count = len(result)
    trans_summary=[]
    for i in range(row_count):
        trans_dict = {'date':'', 'category':'', 'sub_cat':'','group':'', 
                        'payee':'', 'pay_meth':'', 'tag':'', 'expense':''}
        row_tup = result[i]
        trans_dict['date']=str(row_tup[0])
        trans_dict['category']=str(row_tup[1])
        trans_dict['sub_cat']=str(row_tup[2])
        trans_dict['group']=str(row_tup[3])
        trans_dict['payee']=str(row_tup[4])
        trans_dict['pay_meth']=str(row_tup[5])
        trans_dict['tag']=str(row_tup[6])
        trans_dict['expense']=str(row_tup[7])
        trans_summary.append(trans_dict)
    conn.close()
    return trans_summary

def Get_Exp_Summary(trans_type,from_date,to_date,userid):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 
    start_date = datetime.strptime(from_date, "%Y-%m-%d")
    end_date = datetime.strptime(to_date, "%Y-%m-%d")
    sel_days =(end_date-start_date).days + 1
    if(sel_days==1):
        group_tag = 'Total Today'
    elif(sel_days>1 and sel_days<=7):
        group_tag = 'Total This Week'
    else:
        group_tag = 'Total This Month'

    tran_dict = {'total':group_tag, 'income': 0, 'expense':0}
    
    query = '''SELECT trans_type, sum(amount) as Total_Amount FROM transaction_master 
    WHERE group_name="{}" and trans_date BETWEEN "{}" AND "{}" and user="{}" 
    GROUP by trans_type;'''.format(trans_type,from_date,to_date,userid)
    cur.execute(query)
    result = cur.fetchall()
    if result:
        try:
            tran_type_1 = result[0][0].lower()
            tran_type_2 = result[1][0].lower()
        except:
            tran_type_1 = result[0][0].lower()
            tran_type_2 = "Income"

        if(len(result)==1):
            tran_dict[str(tran_type_1)]= result[0][1]
            tran_dict[str(tran_type_2)]= 0
        else:
            tran_dict[str(tran_type_1)]= result[0][1]
            tran_dict[str(tran_type_2)]= result[1][1]

    return tran_dict

def Get_Personal_Exp_Summary(userid):
    cur_day = str(datetime.date(datetime.now()))

    from_date = cur_day
    to_date = cur_day
    total_today = Get_Exp_Summary("Personal Expenses",from_date,to_date,userid)

    dt = datetime.strptime(cur_day, "%Y-%m-%d")
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)
    from_date = start.strftime("%Y-%m-%d")
    to_date = end.strftime("%Y-%m-%d")
    total_thisWeek = Get_Exp_Summary("Personal Expenses",from_date,to_date,userid)

    cur_day = datetime.date(datetime.now())
    start = cur_day.replace(day = 1)
    end = cur_day.replace(day = calendar.monthrange(cur_day.year, cur_day.month)[1])
    from_date = start.strftime("%Y-%m-%d")
    to_date = end.strftime("%Y-%m-%d")
    total_thisMonth = Get_Exp_Summary("Personal Expenses",from_date,to_date,userid)
    grp_total_thisMonth = Get_Total_Group_Expense(from_date,to_date,userid)
    cur_bal = total_thisMonth['income']-(total_thisMonth['expense']+grp_total_thisMonth[0])
    current_balance ={'total_balance':'Current Balance', 'balance':cur_bal} 
    total_group_exp ={'total':'Total Group Expense', 'expense':grp_total_thisMonth[0]} 
    summary_list = [total_today,total_thisWeek, total_thisMonth, total_group_exp, current_balance]
    return summary_list

def Get_User_Exp_Summary(trans_type,from_date,to_date):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 
    start_date = datetime.strptime(from_date, "%Y-%m-%d")
    end_date = datetime.strptime(to_date, "%Y-%m-%d")
    sel_days =(end_date-start_date).days + 1
    if(sel_days==1):
        group_tag = 'Total Today'
    elif(sel_days>1 and sel_days<=7):
        group_tag = 'Total This Week'
    else:
        group_tag = 'Total This Month'

    tran_dict = {'total':group_tag, 'expense':0}
    
    query = '''SELECT trans_type, sum(amount) as Total_Amount FROM transaction_master 
    WHERE group_name="{}" and trans_date BETWEEN "{}" AND "{}" 
    GROUP by trans_type;'''.format(trans_type,from_date,to_date)
    print(query)
    cur.execute(query)
    result = cur.fetchall()
    if result:
        tran_dict['expense']=result[0][1]
    else:
        pass
    return tran_dict

def Get_Total_Group_Expense(from_date, to_date, userid):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    query = """SELECT sum(amount) as Total_Amount FROM transaction_master WHERE trans_type='Expense' 
    and group_name<>"Personal Expenses" and trans_date BETWEEN '{}' AND '{}' and user="{}";""".format(from_date, to_date, userid)
    result = cur.execute(query)
    exp = []
    for r in result:
        exp.append(r[0])
    if(exp==[None]):
        exp=[0]
    
    return exp

def Get_Group_Exp_Summary(group_name):
    cur_day = str(datetime.date(datetime.now()))
    from_date = cur_day
    to_date = cur_day
    total_today = Get_User_Exp_Summary(group_name,from_date,to_date)

    dt = datetime.strptime(cur_day, "%Y-%m-%d")
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)
    from_date = start.strftime("%Y-%m-%d")
    to_date = end.strftime("%Y-%m-%d")
    total_thisWeek = Get_User_Exp_Summary(group_name,from_date,to_date)

    cur_day = datetime.date(datetime.now())
    start = cur_day.replace(day = 1)
    end = cur_day.replace(day = calendar.monthrange(cur_day.year, cur_day.month)[1])
    from_date = start.strftime("%Y-%m-%d")
    to_date = end.strftime("%Y-%m-%d")
    total_thisMonth = Get_User_Exp_Summary(group_name,from_date,to_date)
    summary_list = [total_today, total_thisWeek, total_thisMonth]
    return summary_list

def Get_Group_User_Exp(group_name,from_date,to_date):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    dictionary = {}
    query = """SELECT user, sum(amount) as Total_Amount FROM transaction_master 
            WHERE group_name="{}" and trans_date BETWEEN "{}" AND "{}"
            GROUP by user""".format(group_name,from_date,to_date)
    cur.execute(query)
    result = cur.fetchall()
    
    userlist = []
    exp_list =[]
    for r in result:
        userlist.append(r[0])
        exp_list.append(r[1])
    dictionary = {'user':userlist, 'expenses':exp_list}
    return dictionary

def Get_Group_User_Exp_Summary(group_name, request):
    cur_day = str(datetime.date(datetime.now()))
    from_date = cur_day
    to_date = cur_day
    total_today = Get_Group_User_Exp(group_name,from_date,to_date)

    dt = datetime.strptime(cur_day, "%Y-%m-%d")
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)
    from_date = start.strftime("%Y-%m-%d")
    to_date = end.strftime("%Y-%m-%d")
    total_thisWeek = Get_Group_User_Exp(group_name,from_date,to_date)

    cur_day = datetime.date(datetime.now())
    start = cur_day.replace(day = 1)
    end = cur_day.replace(day = calendar.monthrange(cur_day.year, cur_day.month)[1])
    from_date = start.strftime("%Y-%m-%d")
    to_date = end.strftime("%Y-%m-%d")
    total_thisMonth = Get_Group_User_Exp(group_name,from_date,to_date)

    try:
        req_date = re.split(" ",request.session.get('user-date'))
        from_date = datetime.strptime(req_date[1], '%d/%m/%Y').strftime('%Y-%m-%d')
        to_date = datetime.strptime(req_date[3], '%d/%m/%Y').strftime('%Y-%m-%d')
        total_custom = Get_Group_User_Exp(group_name,from_date,to_date)
        print(total_custom)
    except:
        total_custom ={}
    summary_list = [total_today, total_thisWeek, total_thisMonth, total_custom]
    return summary_list

def Get_Categorywise_Summary(group_name, request):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    try:
        req_date = re.split(" ",request.session.get('user-date'))
        from_date = datetime.strptime(req_date[1], '%d/%m/%Y').strftime('%Y-%m-%d')
        to_date = datetime.strptime(req_date[3], '%d/%m/%Y').strftime('%Y-%m-%d')
    except:
        cur_day = datetime.date(datetime.now())
        start = cur_day.replace(day = 1)
        end = cur_day.replace(day = calendar.monthrange(cur_day.year, cur_day.month)[1])
        from_date = start.strftime("%Y-%m-%d")
        to_date = end.strftime("%Y-%m-%d")

    query = '''SELECT category, sub_category, sum(amount) FROM transaction_master
     WHERE group_name="{}" and trans_date BETWEEN "{}" AND "{}" Group By category,
     sub_category;'''.format(group_name,from_date,to_date)

    cur.execute(query)
    result = cur.fetchall()
    category_list = []
    sub_category_list = []
    amount_list = []
    data_dict = {"category_list":"", "sub_category_list":"", "amount_list":""} 
    for row in result:
        category_list.append(row[0])
        sub_category_list.append(row[1])
        amount_list.append(row[2])
    data_dict["category_list"]=category_list
    data_dict["sub_category_list"]=sub_category_list
    data_dict["amount_list"]=amount_list
    return data_dict

def Get_Mini_Tran_Summary(group_name):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    query = '''SELECT trans_date, description, amount FROM transaction_master
     WHERE group_name="{}" ORDER By trans_date;'''.format(group_name)
    cur.execute(query)
    result = cur.fetchall()
    print(result)
    data_dict = []
    for row in result:
        data_dict.append(row)
    return data_dict

def GetData_In_Dict(table_name):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    dictionary = {}
    query = 'SELECT * FROM {}'.format(table_name)
    cur.execute(query)
    result = cur.fetchall()
    for Brand_Name, Link in result:
        dictionary[Brand_Name] = Link
    conn.close()
    return dictionary

def GetData_In_Tuple(table_name):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    data_tuple=()
    mobile_model_year_list = []
    mobile_model_name_list = []
    mobile_model_links_list = []
    

    query = 'SELECT * FROM {}'.format(table_name)
    cur.execute(query)
    result = cur.fetchall()
    for Announced_Year, Model_Name, Model_Link in result:
        mobile_model_name_list.append(Model_Name)
        mobile_model_links_list.append(Model_Link)
        mobile_model_year_list.append(Announced_Year)


    dic_year = defaultdict(list)
    dic_model_name=defaultdict(list)

    i = 0
    for key in mobile_model_year_list:
        dic_year[key].append(mobile_model_name_list[i])
        i += 1

    j = 0
    for mobile_name_key in mobile_model_name_list:
        dic_model_name[mobile_name_key].append(mobile_model_links_list[j])
        j += 1

    conn.close()
    data_tuple = (dic_year,dic_model_name)
    return data_tuple
