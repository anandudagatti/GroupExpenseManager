import sqlite3
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
from operator import itemgetter
import calendar
import re
import pygal
from pygal.style import Style
import os

def Write_to_DB(dictionary,table_name):
    conn = sqlite3.connect("db.sqlite3")
    data_frame = pd.DataFrame.from_dict(dictionary)
    data_frame.to_sql(table_name, conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

def password_check(passwd): 
      
    SpecialSym =['$', '@', '#', '%', '!', '&'] 
    val = "Success!"
      
    if len(passwd) < 8: 
        val ='length should be at least 8' 
          
    if len(passwd) > 20: 
        val ='length should be not be greater than 20' 
          
    if not any(char.isdigit() for char in passwd): 
        val ='Password should have at least one numeral' 
          
    if not any(char.isupper() for char in passwd): 
        val ='Password should have at least one uppercase letter' 
          
    if not any(char.islower() for char in passwd): 
        val ='Password should have at least one lowercase letter' 
          
    if not any(char in SpecialSym for char in passwd): 
        val ='Password should have at least one of the symbols $ @ # % ! &' 
 
    return val 

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


def Delete_Expired_Session_Data():
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    select_query = """SELECT session_id, dj_session_id FROM session_master;"""
    cur.execute(select_query)
    session_master = cur.fetchall()

    select_query = """SELECT session_key, expire_date FROM django_session;"""
    cur.execute(select_query)
    django_session = cur.fetchall()

    conn.close()

    delete_sessid = []
    active_sessid = []
    for row in session_master:
        sess_id = row[0]
        sess_key = row[1]
        if (any(sess_key in i for i in django_session)):
            active_sessid.append(sess_id)
        else:
            delete_sessid.append(sess_id)

    img_name_list = ["GroupExpensesByCategory.svg", "GroupExpensesByUsers.svg", "PersonalExpensesByCategory.svg"]
    for sess_id in delete_sessid:
        for each_img in img_name_list:
            del_img_name = str(sess_id) + each_img
            if os.path.exists('static/charts/'+ del_img_name):
                os.remove('static/charts/'+ del_img_name)
            else:
                pass

    return delete_sessid

def Update_UserDate_to_SessionMaster(session_id,from_to_date):
    conn = sqlite3.connect("db.sqlite3")
    sql = ''' UPDATE session_master SET from_to_date = '{}'
            WHERE session_id = {};'''.format(from_to_date,session_id[0])
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    conn.close()

def Get_FromToDate_From_SessionID(session_id):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    dictionary = {}
    query = """SELECT from_to_date FROM session_master 
            WHERE session_id="{}" """.format(session_id)
    cur.execute(query)
    result = cur.fetchall()

    from_to_date = result[0][0]

    return from_to_date

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

def Insert_Payee(payee_name):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    ex_payee_list = Get_Payee_List()
    payee_id = len(ex_payee_list)+1
    if payee_name not in ex_payee_list:
        payee_id = payee_id +1
        insert_query = """INSERT INTO payee_list(payee_id,payee_name) VALUES("{}","{}");""".format(payee_id,payee_name) 
        cur.execute(insert_query)
        conn.commit()
    
    conn.close()

def Insert_Payer(payer_name):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor()
    ex_payer_list = Get_Payer_List()
    payer_id = len(ex_payer_list)+1
    if payer_name not in ex_payer_list:
        payer_id = payer_id +1
        insert_query = """INSERT INTO payer_list(payer_id,payer_name) VALUES("{}","{}");""".format(payer_id,payer_name) 
        cur.execute(insert_query)
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

def Edit_Transaction(transaction_id,edited_data):
    exist_data = Get_Transaction_By_Id(transaction_id)
    for key,value in edited_data.items():
        if str(value[0]) not in exist_data[0]:
            conn = sqlite3.connect("db.sqlite3")
            try:
                sql = ''' UPDATE transaction_master SET {} = '{}'
                        WHERE transaction_id = {};'''.format(key,value[0],transaction_id)
                cur = conn.cursor()
                cur.execute(sql, edited_data)
                conn.commit()
                conn.close()
                status_msg = "Edited Transaction Saved Successfully!"
            except error as e:
                status_msg = "Received error:"+e.data
                conn.close()
    return status_msg

def Get_Transaction_By_Id(transaction_id):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    query = '''SELECT * from transaction_master WHERE transaction_id='{}';'''.format(transaction_id)
    cur.execute(query)
    result = cur.fetchall()
    return result

def Delete_Transaction_By_Id(transaction_id):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    query = '''DELETE FROM transaction_master WHERE transaction_id='{}';'''.format(transaction_id)
    cur.execute(query)
    conn.commit()
    conn.close()

def Get_Transaction_Summary(request,group_name,userid):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    req_date = re.split(" ",request.session.get('user-date'))
    from_date = datetime.strptime(req_date[1], '%d/%m/%Y').strftime('%Y-%m-%d')
    to_date = datetime.strptime(req_date[3], '%d/%m/%Y').strftime('%Y-%m-%d')

    trans_dict = {}
    query = '''SELECT transaction_id, trans_date, user, category, sub_category, group_name, payee, 
    payment_method, tag, description, amount from transaction_master WHERE group_name="{}" and trans_date BETWEEN 
    "{}" AND "{}" ORDER BY trans_date DESC;'''.format(group_name,from_date,to_date)
    
    cur.execute(query)
    result = cur.fetchall()
    query = '''SELECT transaction_id, trans_date, user, category, sub_category, group_name, payee, 
    payment_method, tag, description, amount from transaction_master WHERE group_name="Personal Expenses" 
    and user="{}" and trans_date BETWEEN "{}" AND "{}" ORDER BY trans_date DESC;'''.format(userid,from_date,to_date)
    
    cur.execute(query)
    result_per = cur.fetchall()
    row_count_per = len(result_per)
    
    for a in range(row_count_per):
        result.append(result_per[a])

    result.sort(key=itemgetter(1))
    result.sort(key=lambda L: datetime.strptime(L[1], '%Y-%m-%d'))
    row_count = len(result)
    trans_summary=[]

    for i in range(row_count):
        trans_dict = {'id':'', 'date':'', 'user':'', 'category':'', 'sub_cat':'','group':'', 
                        'payee':'', 'pay_meth':'', 'tag':'', 'description':'', 'expense':''}
        row_tup = result[i]
        trans_dict['id']=str(row_tup[0])
        trans_dict['date']=str( datetime.strptime(row_tup[1], '%Y-%m-%d').strftime('%d %b %Y'))
        trans_dict['user']=str(Get_FirstName_of_User(row_tup[2]))
        trans_dict['category']=str(row_tup[3])
        trans_dict['sub_cat']=str(row_tup[4])
        trans_dict['group']=str(row_tup[5])
        trans_dict['payee']=str(row_tup[6])
        trans_dict['pay_meth']=str(row_tup[7])
        trans_dict['tag']=str(row_tup[8])
        trans_dict['description']=str(row_tup[9])
        trans_dict['expense']=str(row_tup[10])
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
            tran_type_2 = "Balance"

        if(len(result)==1):
            tran_dict[str(tran_type_1)]= result[0][1]
            tran_dict[str(tran_type_2)]= 0
        else:
            tran_dict[str(tran_type_1)]= result[0][1]
            tran_dict[str(tran_type_2)]= result[1][1]
    print(tran_dict)
    return tran_dict

def Get_Total_Cash_Balance(userid,from_date,to_date):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    query = '''SELECT sum(amount) as Total_Amount FROM transaction_master 
    WHERE trans_type="Income" and group_name="Personal Expenses" and user="{}" and trans_date BETWEEN 
    "{}" AND "{}";'''.format(userid,from_date,to_date)
    cur.execute(query)
    result = cur.fetchall()

    if result[0][0]:
        income_result = result[0][0]
    else:
        income_result = 0

    query = '''SELECT sum(amount) as Total_Amount FROM transaction_master 
    WHERE trans_type="Expense" and group_name="Personal Expenses" and user="{}" 
    and payment_method NOT IN ("Credit Card", "Digital Wallet") and trans_date BETWEEN 
    "{}" AND "{}";'''.format(userid,from_date,to_date)

    cur.execute(query)
    result = cur.fetchall()

    if result[0][0]:
        exp_result = result[0][0]
    else:
        exp_result = 0
    
    balance = income_result-exp_result
    if balance<1:
        balance=0

    return balance
    
def Get_Cash_Exp_Summary(from_date,to_date,userid,group):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    if userid=="All":
        query = '''SELECT sum(amount) as Total_Amount FROM transaction_master
        WHERE group_name="{}" and trans_type="Expense" and trans_date BETWEEN 
        "{}" AND "{}" and payment_method NOT IN ("Credit Card", "Digital Wallet");'''.format(group,from_date,to_date)
    else:
        query = '''SELECT sum(amount) as Total_Amount FROM transaction_master
        WHERE group_name="{}" and trans_type="Expense" and trans_date BETWEEN 
        "{}" AND "{}" and user="{}" and payment_method NOT IN ("Credit Card", "Digital Wallet");'''.format(group,from_date,to_date,userid)

    cur.execute(query)
    result = cur.fetchall()
    if result[0][0]==None:
        cashexp = 0
    else:
        cashexp = result[0][0]
    return cashexp

def Get_Credit_Exp_Summary(from_date,to_date,userid,group):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    if userid=="All":
        query = '''SELECT sum(amount) as Total_Amount FROM transaction_master
        WHERE group_name="{}" and trans_type="Expense" and trans_date BETWEEN 
        "{}" AND "{}" and payment_method="Credit Card";'''.format(group,from_date,to_date)
    else:
        query = '''SELECT sum(amount) as Total_Amount FROM transaction_master
        WHERE group_name="{}" and trans_type="Expense" and trans_date BETWEEN 
        "{}" AND "{}" and user="{}" and payment_method="Credit Card";'''.format(group,from_date,to_date,userid)

    cur.execute(query)
    result = cur.fetchall()
    if result[0][0]==None:
        cashexp = 0
    else:
        cashexp = result[0][0]
    return cashexp

def Get_Personal_Exp_Summary(userid,from_to_date):
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

    credit_exp = Get_Credit_Exp_Summary(from_date,to_date,userid,"Personal Expenses") 
    cashexp = Get_Cash_Exp_Summary(from_date,to_date,userid,"Personal Expenses")

    user_group_exp = Get_Total_Group_Expense(from_date, to_date, userid)
    #cur_bal = total_thisMonth['income']-(cashexp+user_group_exp[0])

    #current_balance ={'firstrow':['Cash Expense',cashexp], 'secrow':['Credit Card Expense',credit_exp], 
    #'throw':['Group Expense',user_group_exp[0]], 'fourthrow':['Cash Balance ',cur_bal]}

    total_balance = Get_Total_Cash_Balance(userid,from_date,to_date)

    current_balance ={'firstrow':['Cash Expense',cashexp], 'secrow':['Credit Card Expense',credit_exp], 
    'throw':['Group Expense',user_group_exp[0]], 'fourthrow':['Total Cash Balance ',total_balance]}
    summary_list = [total_today,total_thisWeek, total_thisMonth, current_balance]
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

    userid = "All"
    credit_exp = Get_Credit_Exp_Summary(from_date,to_date,userid,group_name) 
    cashexp = Get_Cash_Exp_Summary(from_date,to_date,userid,group_name)

    current_balance ={'firstrow':['Cash Expense',cashexp], 'secrow':['Credit Card Expense',credit_exp]}
    summary_list = [total_today,total_thisWeek, total_thisMonth, current_balance]

    return summary_list

def Get_FirstName_of_User(username):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 

    dictionary = {}
    query = """SELECT first_name FROM auth_user WHERE username="{}" """.format(username)

    cur.execute(query)
    result = cur.fetchall()
    FirstName = result[0][0]

    return FirstName

def Get_User_list(groups_tuple):
    conn = sqlite3.connect("db.sqlite3")
    with conn:
        cur = conn.cursor() 
    dictionary = {}
    query = """SELECT username, first_name, last_name, 
            ag.name as group_name from auth_user as au
            JOIN auth_user_groups aug on au.id=aug.user_id
            JOIN auth_group ag on aug.group_id=ag.id WHERE group_name in {} """.format(groups_tuple)
    cur.execute(query)
    result = cur.fetchall() 
    return result

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
    exp_list = []
    percent_list = []
    for r in result:
        userlist.append(Get_FirstName_of_User(r[0]))
        exp_list.append(r[1])
    total_exp = sum(exp_list)
    for r in result:
        perc = round((r[1]/total_exp)*100,2)
        percent_list.append(perc)
    try:
        avg_spend = sum(exp_list)/len(exp_list) 
    except:
        avg_spend = 0

    contrib_list = []
    i = 0
    for exp in exp_list:
        contrib = exp-avg_spend
        if contrib<0:
            mask_contrib = '{:,.2f}'.format(abs(contrib))
            contrib_list.append(userlist[i]+" has to contribute ₹"+str(mask_contrib)+" to the common pool")
        else:
            mask_contrib = '{:,.2f}'.format(contrib)
            contrib_list.append(userlist[i]+" has to withdraw ₹"+str(mask_contrib)+" from the common pool")
        i=i+1

    dictionary = {'user':userlist, 'expenses':exp_list, 'percent':percent_list, 'contrib_list':contrib_list}
    
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
    if group_name == "Personal Expenses":
        userid = request.session.get('userid')
        query = '''SELECT category, sub_category, sum(amount) FROM transaction_master
        WHERE group_name="{}" and trans_date BETWEEN "{}" AND "{}" and user="{}" Group By category,
        sub_category;'''.format(group_name,from_date,to_date,userid)
    else:
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

def Get_Category_Sum_For_PieChart(group_name, request):
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

    if group_name == "Personal Expenses":
        userid = request.session.get('userid')
        query = '''SELECT category, sum(amount) FROM transaction_master
        WHERE trans_type="Expense" and group_name="{}" and trans_date BETWEEN "{}" AND "{}" and user="{}"
        Group By category;'''.format(group_name,from_date,to_date,userid)
    else:
        query = '''SELECT category, sum(amount) FROM transaction_master
        WHERE group_name="{}" and trans_date BETWEEN "{}" AND "{}" 
        Group By category;'''.format(group_name,from_date,to_date)

    cur.execute(query)
    result = cur.fetchall()
    category_list = [['Category', 'Expense']]
    total_exp = 0
    for row in result:
        category_list.append([str(row[0]),int(row[1])])
        total_exp = total_exp + int(row[1])

    custom_style = Style(
        title_font_size = 25.0,
        legend_font_size = 25.0,
        value_font_size = 25.0,
        tooltip_font_size = 25.0,
        major_label_font_size = 25.0,
        label_font_sioze = 25.0,
        value_label_font_size = 25.0,
        font_family='googlefont:Raleway')

    tag =""
    if group_name == "Personal Expenses":
        tag = "Personal"
    else:
        tag = "Group"

    pie_chart = pygal.Pie(width=620, legend_at_bottom=True, style=custom_style)
    pie_chart.title = tag +' Expenses By Category'
    percent_formatter = lambda x: '{:.10g}%'.format(x)
    for r in result:
        exp_per = round((int(r[1])/total_exp)*100,2)
        pie_chart.add(str(r[0]),exp_per,formatter = percent_formatter)


    sess_id = request.session.get('sessionid')
    chartname = 'static/charts/'+ str(sess_id[0]) + tag + 'ExpensesByCategory.svg'
    pie_chart.render_to_file(chartname)

    return chartname

def Get_User_Exp_For_PieChart(group_name,request):
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

    query = """SELECT user, sum(amount) as Total_Amount FROM transaction_master 
            WHERE group_name="{}" and trans_date BETWEEN "{}" AND "{}"
            GROUP by user""".format(group_name,from_date,to_date)

    cur.execute(query)
    result = cur.fetchall()
    user_exp_list = [['User', 'Expense']]
    total_exp = 0

    for row in result:
        user_exp_list.append([str(Get_FirstName_of_User(row[0])),int(row[1])])
        total_exp = total_exp + int(row[1])

    custom_style = Style(
        title_font_size = 25.0,
        legend_font_size = 25.0,
        value_font_size = 25.0,
        tooltip_font_size = 25.0,
        major_label_font_size = 25.0,
        label_font_sioze = 25.0,
        value_label_font_size = 25.0,
        font_family='googlefont:Raleway')

    pie_chart = pygal.Pie(width=620, legend_at_bottom=True, style=custom_style)
    pie_chart.title = 'Group Expenses By Users'
    percent_formatter = lambda x: '{:.10g}%'.format(x)
    for r in result:
        exp_per = round((int(r[1])/total_exp)*100,2)
        pie_chart.add(str(Get_FirstName_of_User(r[0])),exp_per,formatter = percent_formatter)
    
    sess_id = request.session.get('sessionid')
    chartname = 'static/charts/'+ str(sess_id[0]) + 'GroupExpensesByUsers.svg'
    pie_chart.render_to_file(chartname)

    return chartname

def Get_Mini_Tran_Summary(trans_summary_dic):
    trans_summary_mini=[]
    for dic in trans_summary_dic:
        shallow_copy = dict(dic)
        del shallow_copy['tag']
        trans_summary_mini.append(shallow_copy)
    return trans_summary_mini

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

