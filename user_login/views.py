from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Permission, User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import Group
from django.db import IntegrityError
import json
import logging
from user_login.sqlite3_read_write import Get_Income_Category, Get_Exp_Category, Get_SubCategoryTable, \
    Write_to_DB, Get_SessionID, Get_Payee_List, Get_Payment_Method, Get_Payer_List,Insert_Transaction, \
    Get_Transaction_Summary, Get_Personal_Exp_Summary,Get_Group_Exp_Summary,Get_Group_User_Exp_Summary, \
    Insert_Payee,Get_Categorywise_Summary,Get_Mini_Tran_Summary,Get_Transaction_By_Id, Edit_Transaction, \
    Get_Category_Sum_For_PieChart,Insert_Payer,Get_User_Exp_For_PieChart, Update_UserDate_to_SessionMaster, \
    Get_FromToDate_From_SessionID,password_check, Delete_Transaction_By_Id
from datetime import datetime
import calendar
from django.views.generic import CreateView
from django.core.mail import send_mail
import os
from django.conf import settings

logging.basicConfig(level=logging.DEBUG)

@csrf_exempt
def home(request):
    logmsg = "home view: Rendering login page template"
    logging.info(logmsg)
    request.session['cur_view']="home"
    return render(request, 'login.html')

@csrf_exempt
def terms(request):
    return render(request, 'terms_of_use.html')

@csrf_exempt
def myprofile(request):
    firstname = request.user.first_name
    lastname = request.user.last_name
    email = request.user.email
    user = request.user.username
    cur_view = request.session.get('cur_view')
    logmsg = "Rendering MyProfile For User"+str(user)
    logging.info(logmsg)

    if request.POST.get('edit_submit'):
        edited_firstname = request.POST.get("firstname")
        edited_lastname = request.POST.get("lastname")
        edited_email = request.POST.get("email")
        cur_user =  User.objects.get(username=user)
        logmsg = "Edited MyProfile For User"+str(cur_user)
        logging.info(logmsg)
        cur_user.first_name = edited_firstname
        cur_user.last_name = edited_lastname
        cur_user.email = edited_email
        cur_user.save()

        firstname = edited_firstname
        lastname = edited_lastname
        email = edited_email
        return render(request, 'myprofile.html', {"firstname":firstname,"lastname":lastname,"email":email, "cur_view":cur_view})
    
    return render(request, 'myprofile.html', {"firstname":firstname,"lastname":lastname,"email":email, "cur_view":cur_view})

@csrf_exempt
def signup(request):       
    if request.POST.get('sign-up'):
        logmsg = "singup view: Rendering singup page"
        logging.info(logmsg)
        logmsg = 'session id'+str(request.session.get('sessionid'))
        logging.info(logmsg)
        logmsg = "sign-up button cliked"
        logging.info(logmsg)
        newuserid = request.POST.get('userid')
        newpassword = request.POST.get('password')
        email = request.POST.get('email')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        data_file = open(os.path.join(settings.BASE_DIR+'/templates', 'welcome-email-template.txt'))
        temp_msg = '''Hi {},\n\nYour User ID: {},\n\n'''.format(firstname,newuserid) + data_file.read()
        password_validation = password_check(newpassword)

        for user in User.objects.all():
            if email == user.email and newuserid == user.username: 
                logmsg = "Error: User already exist! Try forgot password if dont remember password"
                logging.info(logmsg)
                messages.error(request,logmsg)
                return render(request, 'signup.html')
            elif newuserid == user.username:
                logmsg = "Error:Userid already exist! Try with new userid."
                logging.info(logmsg)
                messages.error(request,logmsg)
                return render(request, 'signup.html')
            elif email == user.email:
                logmsg = "Error: Email already exist! Try with new email."
                logging.info(logmsg)
                messages.error(request,logmsg)
                return render(request, 'signup.html')
            elif password_validation!="Success!":
                logmsg = password_validation
                logging.info(logmsg)
                messages.error(request,logmsg)
                return render(request, 'signup.html')
            else:
                pass

        user = User.objects.create_user(username=newuserid, 
                                    password=newpassword,
                                    email=email,
                                    first_name=firstname,
                                    last_name=lastname)

        user.save()
        logmsg = "Successfully signed up!, Login to start adding expenses."
        logging.info(logmsg)
        messages.success(request,logmsg)
        send_mail(
            subject = "Welcome to Group Expense Manger",
            message = temp_msg,
            from_email = "groupexpensemanager@gmail.com",
            recipient_list = [email,],
            fail_silently = False,
        )

    return render(request, 'signup.html')


@csrf_exempt
def authentication(request):
    authentication = ''
    logmsg = "authentication view: Authentication Veiw Entered"
    logging.info(logmsg)
    request.session.clear_expired()

    if request.POST.get('login'):
        userid = request.POST.get('userid')
        now = datetime.now()
        login_date = now.strftime("%d/%m/%Y %H:%M:%S")
        request.session['userid'] = userid 
        password = request.POST.get('password')
        admin = request.POST.get('admin')
        logging.info("Login Button Clicked")
        
        user = authenticate(request, username=userid, password=password)
        if user is not None:
            login(request, user)
            authentication='Success'
        else:
            authentication='Failed'            

        logging.debug("Authentication : %s",authentication)
    
        if request.user.is_superuser:
            superuser = True
        else:
            superuser = False    

        group_exist = False

        get_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
        grouplist = list(get_groups)
 
        if len(grouplist)>0:
            group_exist = True
        else:
            group_exist = False

        print("groups exist", group_exist)

        if (admin=='on' and authentication=='Success' and superuser==True):
            request.session['login_typ'] = 'admin'
            session_data = {'date':[str(login_date)], 'user_id':[str(userid)], 'loggin_type':['admin'],'dj_session_id':request.session.session_key}
            Write_to_DB(session_data,'session_master')
            sessionid=Get_SessionID(session_data)
            request.session['sessionid'] = sessionid 
            print(request.session.get('sessionid'))
            fullname = request.user.get_full_name()
            logmsg = "Admin login by: "+str(userid)+": "+str(fullname)
            logging.info(logmsg)
            return redirect('admin')
        elif (admin=='on' and authentication=='Success' and superuser==False):
            logmsg = 'Error: User do not have admin rights'
            logging.error(logmsg)
            logging.error('Redirecting to login page')
            messages.error(request,logmsg)
            return redirect('home')
        elif (group_exist==True and admin==None and authentication=='Success'):
            request.session['login_typ'] = 'user'
            session_data = {'date':[str(login_date)], 'user_id':[str(userid)], 'loggin_type':['user'], 'dj_session_id':request.session.session_key}
            Write_to_DB(session_data,'session_master')
            sessionid=Get_SessionID(session_data)
            request.session['sessionid'] = sessionid 
            fullname = request.user.get_full_name()
            logmsg = "User login by: "+str(userid)+": "+str(fullname)
            logging.info(logmsg)
            return redirect('account')
        elif (group_exist==False and admin==None and authentication=='Success'):
            request.session['login_typ'] = 'user'
            session_data = {'date':[str(login_date)], 'user_id':[str(userid)], 'loggin_type':['user'],'dj_session_id':request.session.session_key}
            Write_to_DB(session_data,'session_master')
            sessionid=Get_SessionID(session_data)
            request.session['sessionid'] = sessionid 
            fullname = request.user.get_full_name()
            logmsg = "User login by: "+str(userid)+": "+str(fullname)
            logging.info(logmsg)
            return redirect('nogroup_account')
        else:
            logmsg = 'Error: Invalid UserID or Password'
            logging.error(logmsg)
            messages.error(request,logmsg)
            return redirect('home')
    else:
        try:
            logout(request)
            del request.session['userid']
        except KeyError:
            pass
        logmsg = "user logged out, redirecting to login page"
        logging.info(logmsg)
        info = "User Logged Out Successfully!"
        messages.success(request,info)
        return render(request, 'login.html')

@csrf_exempt
@login_required(login_url='home')
def account(request):
    # Get Logged in User Details
    fullname = request.user.get_full_name()
    login_type = request.session.get('login_typ')
    userid = request.session.get('userid')
    request.session['edit_trans']=None
    request.session['cur_view']="account"
    
    # Write Log info for session id
    logmsg = "account view: Rendering account page template"
    logging.info(logmsg)
    logmsg = 'session id'+str(request.session.get('sessionid'))
    logging.info(logmsg)

    # Get grouplist for the current logged in user. 
    get_groups = request.user.groups.values_list('name',flat = True) 
    grouplist = list(get_groups)
    logmsg = 'Logged-in User Group List: ' + str(grouplist)
    logging.info(logmsg)
    
    # Redirect to nongroup view if its new user or not part of any group.
    if (grouplist==[]):
        return redirect('nogroup_account')

    #Logout current user on click of logout button.
    if request.POST.get('logout'):
        logmsg = "User logout by: "+str(userid)
        logging.info(logmsg)
        img_name_list = ["GroupExpensesByCategory.svg", "GroupExpensesByUsers.svg", "PersonalExpensesByCategory.svg"]
        sess_id = request.session.get('sessionid')
        for each_img in img_name_list:
            del_img_name = str(sess_id[0]) + each_img
            if os.path.exists('static/charts/'+ del_img_name):
                os.remove('static/charts/'+ del_img_name)
                logmsg = "Static Chart Deleted: " + del_img_name
                logging.info(logmsg)
            else:
                logmsg = "Error In Static Chart Delete: " + del_img_name
                logging.info(logmsg)
        
        try:
            logout(request)
            del request.session[userid]
        except KeyError:
            pass
        info = "User Logged Out Successfully!"
        messages.success(request,info)
        return redirect('home')    

    # Get user selection for group name from Group combobox
    sel_group = request.POST.getlist('group_name')
    request.session['group_name']= sel_group
    logmsg = 'selected group: '+str(sel_group)
    logging.info(logmsg)

    # If user selection for group name not set then set it to first group in the gruop list else redirect to home.
    if(sel_group==[] and len(grouplist)>0):
        sel_group = grouplist[0]
    else:
        try:
            sel_group= sel_group[0]
        except:
            return redirect('home')

    # Check if custom date filter applied by user else set date to current month.
    if request.session.get('user-date'):
        from_to_date = request.session.get('user-date')
    else:
        curdate = datetime.now()
        fromdt = curdate.replace(day = 1).strftime('%d/%m/%Y')
        lastdt = curdate.replace(day = calendar.monthrange(curdate.year, curdate.month)[1]).strftime('%d/%m/%Y')
        from_to_date ='''From {} To {}'''.format(fromdt, lastdt)
        request.session['user-date'] = from_to_date

    # Update date filter value to db in session master table.
    Update_UserDate_to_SessionMaster(request.session.get('sessionid'),from_to_date)

    # Print log msg for filtered date value. 
    logmsg = 'Filtered Date: '+request.session.get('user-date')
    logging.info(logmsg)

    # Delete selected trasaction on clicking of delete button.
    if request.POST.get('delete-btn'):
        tran_id = request.POST.get('del_trans_id')
        logmsg = "Delete button clicked: Trans ID: "+tran_id
        logging.info(logmsg)
        trans = Get_Transaction_By_Id(tran_id)
        if tran_id!=None and len(trans)>0:
            delete_group = trans[0][5]
            tran_user = trans[0][2]

            if delete_group=="Personal Expenses" and tran_user==userid:
                Delete_Transaction_By_Id(tran_id)
            elif delete_group==sel_group and tran_user==userid:
                Delete_Transaction_By_Id(tran_id)
            else:
                info = 'Invalid User! You can not delete other users transaction!'
                messages.error(request,info) 

    # Get data for Personal Expense Summary
    per_header = ['Total','Income','Expense']
    per_rows = Get_Personal_Exp_Summary(userid)

    # Set header for both Group Expense Summary & Group Expense: User Wise Summary
    group_header = ['Total','Expense']

    # Get data for Group Expense Summary
    group_rows = Get_Group_Exp_Summary(sel_group)

    # Get data for Group Expense: User Wise Summary
    group_user_exp = Get_Group_User_Exp_Summary(sel_group, request)
    user_exp_summary=group_user_exp[3]

    # Get user selection for period from Group Expense: User Wise Summary
    user_opt = request.POST.get('user_opt')
    request.session['user_opt'] = user_opt
    if request.POST.get('update_useropt'):
        curdate = datetime.now()
        fromdt = curdate.replace(day = 1).strftime('%d/%m/%Y')
        lastdt = curdate.replace(day = calendar.monthrange(curdate.year, curdate.month)[1]).strftime('%d/%m/%Y')
        from_to_date ='''From {} To {}'''.format(fromdt, lastdt)
        request.session['user-date'] = from_to_date

        if user_opt == "Today":
            logmsg = "Period Selected : Today"
            logging.info(logmsg)
            user_exp_summary=group_user_exp[0]
        elif user_opt == "This Week":
            logmsg = "Period Selected : This Week"
            logging.info(logmsg)
            user_exp_summary=group_user_exp[1]
        else:
            logmsg = "Period Selected : This Month"
            logging.info(logmsg)
            user_exp_summary=group_user_exp[2]

    # Get value for Filter Date from the model dialog box 
    if request.POST.get('save-date'):
        logmsg = 'Custom Date Filter Applied'
        logging.info(logmsg)
        logmsg = "Custom Period Selected: "+from_to_date
        logging.info(logmsg)
        tempfrom_date = datetime.strptime(request.POST.get("from_date"),'%Y-%m-%d').date()
        from_date = tempfrom_date.strftime('%d/%m/%Y')
        tempto_date = datetime.strptime(request.POST.get("to_date"), '%Y-%m-%d').date()
        to_date = tempto_date.strftime('%d/%m/%Y')
        user_sel_date = "From "+from_date+" To "+to_date
        logmsg = 'user date: '+user_sel_date
        logging.info(logmsg)
        request.session['user-date'] = user_sel_date
        from_to_date = request.session.get('user-date')
        group_user_exp = Get_Group_User_Exp_Summary(sel_group, request)
        user_exp_summary=group_user_exp[3]

    # Reset account page to default view.
    if request.POST.get('reset'):
        logmsg = 'Reset Button Clicked '
        logging.info(logmsg)        
        curdate = datetime.now()
        fromdt = curdate.replace(day = 1).strftime('%d/%m/%Y')
        lastdt = curdate.replace(day = calendar.monthrange(curdate.year, curdate.month)[1]).strftime('%d/%m/%Y')
        from_to_date ='''From {} To {}'''.format(fromdt, lastdt)
        request.session['user-date'] = from_to_date
        user_exp_summary=group_user_exp[2]

    # Set header & data for transaction summary desktop version of website.
    trans_header = ['Edit', 'Date', 'User', 'Category', 'Sub Category', 'Group Name', 'Payee', 'Payement Method', 'Tag#', 'Amount']
    trans_rows = Get_Transaction_Summary(request,sel_group,userid)

    # Get data for transaction summary mobile version of website.
    mini_trans_summary = Get_Mini_Tran_Summary(trans_rows)

    # Get data for Group Expense: By Category
    category_summary = Get_Categorywise_Summary(sel_group,request)

    # Chart : Generate Personal Expense Pie Chart
    personal_exp_by_category = Get_Category_Sum_For_PieChart("Personal Expenses",request)

    # Chart : Generate Group Expense Pie Chart
    group_exp_by_category = Get_Category_Sum_For_PieChart(sel_group,request)

    # Chart : Generate Group Expense: User Wise Pie Chart
    group_exp_by_users = Get_User_Exp_For_PieChart(sel_group,request)

    # Redirect to Group or Personal Expense view to edit the selected transaction.
    if request.POST.get('edit-btn'):
        tran_id = request.POST.get('edit-btn')
        logmsg = 'Edit Button Clicked for Transaction ID ' + str(tran_id)
        logging.info(logmsg)        
        request.session['edit_trans']=tran_id
        trans = Get_Transaction_By_Id(tran_id)
        if tran_id!=None and len(trans)>0:
            edit_group = trans[0][5]
            tran_user = trans[0][2]
            if edit_group=="Personal Expenses" and tran_user==userid:
                return redirect('personal_expenses')
            elif edit_group!="Personal Expenses" and tran_user==userid:
                return redirect('group_expenses')
            else:
                info = 'Invalid User to Edit Transaction!'
                messages.error(request,info)

    return render(request,'account.html', {"userid":fullname, "logintype":login_type.capitalize(), 
                "per_header":per_header, "per_rows":per_rows, "group_header":group_header,"group_rows":group_rows,
                "trans_header":trans_header,"trans_rows":trans_rows, "grouplist":grouplist, 
                "group_user_exp":user_exp_summary, "user_opt":user_opt, "sel_group":sel_group,
                "category_summary":category_summary, "mini_trans_summary":mini_trans_summary,
                "from_to_date": from_to_date, 'group_exp_by_category': group_exp_by_category, 
                'personal_exp_by_category': personal_exp_by_category,"group_exp_by_users":group_exp_by_users})

@csrf_exempt
@login_required(login_url='home')
def nogroup_account(request):
    fullname = request.user.get_full_name()
    login_type = request.session.get('login_typ')
    logmsg = "account view: Rendering account page template"
    logging.info(logmsg)
    userid = request.session.get('userid')
    logmsg = "User ID :" + str(userid)
    logging.info(logmsg)
    logmsg = 'session id'+str(request.session.get('sessionid'))
    logging.info(logmsg)
    login_type = request.session.get('login_typ')
    request.session['cur_view'] = "nogroup_account"
    
    
    if request.POST.get('delete-btn'):
        tran_id = request.POST.get('del_trans_id')
        logmsg = "Delete button clicked: Trans ID: "+tran_id
        logging.info(logmsg)
        trans = Get_Transaction_By_Id(tran_id)
        if tran_id!=None and len(trans)>0:
            Delete_Transaction_By_Id(tran_id)

    if request.POST.get('edit-btn'):
        tran_id = request.POST.get('edit-btn')
        request.session['edit_trans']=tran_id
        trans = Get_Transaction_By_Id(tran_id)
        if tran_id!=None and len(trans)>0:
            return redirect('personal_expenses')

    if userid!=None:
        if request.POST.get('logout'):
            logmsg = "User logout by: "+str(userid)
            logging.info(logmsg)
            img_name_list = ["GroupExpensesByCategory.svg", "GroupExpensesByUsers.svg", "PersonalExpensesByCategory.svg"]
            sess_id = request.session.get('sessionid')
            for each_img in img_name_list:
                del_img_name = str(sess_id[0]) + each_img
                if os.path.exists('static/charts/'+ del_img_name):
                    os.remove('static/charts/'+ del_img_name)
                    logmsg = "Static Chart Deleted: " + del_img_name
                    logging.info(logmsg)
                else:
                    logmsg = "Error In Static Chart Delete: " + del_img_name
                    logging.info(logmsg)
            try:
                logout(request)
                del request.session['userid']
            except KeyError:
                pass
            info = "User Logged Out Successfully!"
            messages.success(request,info)
            return redirect('home')

        if request.session.get('user-date'):
            from_to_date = request.session.get('user-date')
        else:
            curdate = datetime.now()
            fromdt = curdate.replace(day = 1).strftime('%d/%m/%Y')
            lastdt = curdate.replace(day = calendar.monthrange(curdate.year, curdate.month)[1]).strftime('%d/%m/%Y')
            from_to_date ='''From {} To {}'''.format(fromdt, lastdt)
            request.session['user-date'] = from_to_date

        if request.POST.get('save-date'):
            logmsg = 'Custom Date Filter Applied'
            logging.info(logmsg)
            logmsg = "Custom Period Selected: "+from_to_date
            logging.info(logmsg)
            tempfrom_date = datetime.strptime(request.POST.get("from_date"),'%Y-%m-%d').date()
            from_date = tempfrom_date.strftime('%d/%m/%Y')
            tempto_date = datetime.strptime(request.POST.get("to_date"), '%Y-%m-%d').date()
            to_date = tempto_date.strftime('%d/%m/%Y')
            user_sel_date = "From "+from_date+" To "+to_date
            logmsg = 'user date: '+user_sel_date
            logging.info(logmsg)    
            request.session['user-date'] = user_sel_date
            from_to_date = request.session.get('user-date')
            
        if request.POST.get('reset'):
            curdate = datetime.now()
            fromdt = curdate.replace(day = 1).strftime('%d/%m/%Y')
            lastdt = curdate.replace(day = calendar.monthrange(curdate.year, curdate.month)[1]).strftime('%d/%m/%Y')
            from_to_date ='''From {} To {}'''.format(fromdt, lastdt)
            request.session['user-date'] = from_to_date        

        Update_UserDate_to_SessionMaster(request.session.get('sessionid'),from_to_date)

        logmsg = 'user date: '+request.session.get('user-date')
        logging.info(logmsg)

        per_header = ['Total','Income','Expense']
        per_rows = Get_Personal_Exp_Summary(userid)
            
        trans_header = ['Edit', 'Date', 'User', 'Category', 'Sub Category', 'Group Name', 'Payee', 'Payement Method', 'Tag#', 'Amount']
        trans_rows = Get_Transaction_Summary(request,"Non Group",userid)

        mini_trans_summary = Get_Mini_Tran_Summary(trans_rows)
        personal_exp_by_category = Get_Category_Sum_For_PieChart("Personal Expenses",request)

    return render(request,'nogroup_account.html', {"userid":fullname, "logintype":login_type.capitalize(),"from_to_date": from_to_date, 
                "per_header":per_header, "per_rows":per_rows, "trans_header":trans_header,"trans_rows":trans_rows, 
                "mini_trans_summary":mini_trans_summary, 'personal_exp_by_category': personal_exp_by_category})

@csrf_exempt
@login_required(login_url='home')
def admin(request):
    auth_type = request.session.get('login_typ')
    logmsg = "admin view: Rendering admin page"
    logging.info(logmsg)
    userid = request.session.get('userid')
    logmsg = 'session id'+str(request.session.get('sessionid'))
    logging.info(logmsg)
    login_type = request.session.get('login_typ')
    get_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
    grouplist = list(get_groups) 
    if (userid!=None and auth_type=='admin'):
        if request.POST.get('logout'):
            logmsg = "Admin logout by: "+str(userid)
            logging.info(logmsg)

            try:
                logout(request)
                del request.session['userid']
            except KeyError:
                pass
            info = "User Logged Out Successfully!"
            messages.success(request,info)
            return redirect('home')
        elif request.POST.get('add-user'):
            sel_group = request.POST.get('group_name')
            new_user = request.POST.get('newuserid')
            fullname = request.user.get_full_name()
            try:
                uid = User.objects.get(username=new_user).id
                my_group = Group.objects.get(name=sel_group) 
                my_group.user_set.add(uid)
                permissions_list = Permission.objects.all()
                my_group.permissions.set(permissions_list)
                logmsg="User added successfully!!"
                errorvalue=""
            except:
                logmsg=""
                errorvalue="User already exist!!"
            return render(request, 'admin.html',{"info":logmsg, "errorvalue":errorvalue, "userid":fullname, "grouplist":grouplist, "logintype":login_type.capitalize()})
        elif request.POST.get('remove-user'):
            sel_group = request.POST.get('group_name')
            sel_user = request.POST.get('newuserid')
            fullname = request.user.get_full_name()
            my_group = Group.objects.get(name=sel_group) 
            uid = User.objects.get(username=sel_user).id
            try:
                if User.objects.filter(pk=uid, groups__name=sel_group).exists():
                    my_group.user_set.remove(uid)
                    logmsg="User removed successfully!!"
                    errorvalue=""
                else:
                    logmsg=""
                    errorvalue="User doesn't exist!!"
            except:
                logmsg=""
                errorvalue="User doesn't exist!!"
            return render(request, 'admin.html',{"info":logmsg, "errorvalue":errorvalue, "userid":fullname, "grouplist":grouplist, "logintype":login_type.capitalize()})
        else:
            logmsg=""
            fullname = request.user.get_full_name()
            return render(request, 'admin.html',{"info":logmsg, "userid":fullname, "grouplist":grouplist, "logintype":login_type.capitalize()})
    else:
        try:
            logout(request)
            del request.session['userid']
        except KeyError:
            pass
        info = "User Logged Out Successfully!"
        messages.success(request,info)
        return redirect('home')

@csrf_exempt
def groups(request):
    if request.POST.get('create-group'):
        userid = request.POST.get('userid')
        password = request.POST.get('password')
        groupname = request.POST.get('groupname')
        
        if(groupname!=""):
            user = authenticate(request, username=userid, password=password)
            if user is not None:
                authentication='Success'
            else:
                authentication='Failed'            

            if(authentication=='Success'):
                try:
                    create_group = Group.objects.create(name=groupname)
                    create_group.user_set.add(user)
                    permissions_list = Permission.objects.all()
                    create_group.permissions.set(permissions_list)
                    cur_user = User.objects.get(username=user)
                    cur_user.is_superuser = True
                    cur_user.save()
                    info="Group Created Successfully!"
                    messages.success(request,info)
                except:
                    error="Group Already Exist!"
                    messages.error(request,error)
            else:
                error="Invalid User Name or Password!"
                messages.error(request,error)
        else:
            error="Group name cannot be blank!"
            messages.error(request,error)
    cur_view = request.session.get('cur_view')
    return render(request,'create_group.html',{"cur_view":cur_view})

@csrf_exempt
@login_required(login_url='home')
def incomes(request):
    fullname = request.user.get_full_name()
    login_type = request.session.get('login_typ')
    logmsg = "incomes view: Rendering incomes page"
    logging.info(logmsg)
    userid = request.session.get('userid')
    logmsg = 'session id'+str(request.session.get('sessionid'))
    logging.info(logmsg)
    login_type = request.session.get('login_typ')
    if userid!=None:
        if request.POST.get('logout'):
            logmsg = "User logout by: "+str(userid)
            logging.info(logmsg)
            
            try:
                logout(request)
                del request.session['userid']
            except KeyError:
                pass
            info = "User Logged Out Successfully!"
            messages.success(request,info)
            return redirect('home')
        elif request.POST.get('category-btn'):
            category_selected=request.POST.get('category-btn')
            request.session['cat_sel'] = category_selected
            print(category_selected)
            fullname = request.user.get_full_name()
            payer_list = Get_Payer_List()
            exp_mode = "Personal"
            return render(request, 'income_details.html',{"userid":fullname, "logintype":login_type.capitalize(), 
             "exp_mode":exp_mode, "cat_crumb":request.session.get('cat_sel'), "payerlist": payer_list})
        elif request.POST.get('save'):
            info = 'Income Saved!!'
            logmsg = "Save Button Clicked"
            logging.info(logmsg)
            group = "Personal Expenses"
            date = request.POST.get('date')
            amount = request.POST.get('amount')
            payer = request.POST.get('payer-name')
            Insert_Payer(payer)
            category = request.session.get('cat_sel')
            subcategory = 'NA'
            payment = 'NA'
            tag = request.POST.get('tag')
            description = request.POST.get('description')
            recurring = request.POST.get('recurring')
            income_data = {'trans_type':['Income'],'user':[userid], 'category':[category], 'sub_category':[subcategory],\
                            'group_name':[group], 'trans_date':[date], 'amount':[amount], 'payee': [payer], 'payment_method': [payment],\
                            'tag':[tag], 'description':[description], 'recurring':[recurring]}
            print(income_data)
            try:
                Insert_Transaction(income_data)
                messages.success(request,'Income Added Succesfully!!')
            except Exception as e:
                messages.error(request, str(e))
                logger.error('Failed to Insert: ' + str(e))

            fullname = request.user.get_full_name()
            income_cat = Get_Income_Category()
            categories = income_cat
            return render(request, 'incomes.html',{"userid":fullname, "logintype":login_type.capitalize(), "categories":categories})

    income_cat = Get_Income_Category()
    categories = income_cat
    exp_mode = "Personal"
    info=""
    return render(request,'incomes.html',{"info":info, "userid":fullname, "logintype":login_type.capitalize(), "exp_mode":exp_mode, "categories":categories})

@csrf_exempt
@login_required(login_url='home')
def group_expenses(request):
    logmsg = "group expenses view: Rendering group expenses page"
    logging.info(logmsg)
    userid = request.session.get('userid')
    logmsg = 'session id'+str(request.session.get('sessionid'))
    logging.info(logmsg)
    login_type = request.session.get('login_typ')
    if userid!=None:
        if request.POST.get('logout'):
            logmsg = "User logout by: "+str(userid)
            logging.info(logmsg)
            
            try:
                logout(request)
                del request.session['userid']
            except KeyError:
                pass
            info = "User Logged Out Successfully!"
            messages.success(request,info)
            return redirect('home')
        elif request.POST.get('save'):
            info = 'Expense Saved!!'
            logmsg = "Save Button Clicked"
            logging.info(logmsg)
            group = request.POST.get('group')
            date = request.POST.get('date')
            amount = request.POST.get('amount')
            payee = request.POST.get('payee-name')
            Insert_Payee(payee)
            category = request.session.get('cat_sel')
            subcategory = request.session.get('sub_cat_sel')
            payment = request.POST.get('payment-method')
            tag = request.POST.get('tag')
            description = request.POST.get('description')
            recurring = request.POST.get('recurring')
            expense_data = {'trans_type':['Expense'],'user':[userid], 'category':[category], 'sub_category':[subcategory],\
                            'group_name':[group], 'trans_date':[date], 'amount':[amount], 'payee': [payee], 'payment_method': [payment],\
                            'tag':[tag], 'description':[description], 'recurring':[recurring]}
            print(expense_data)
            tran_id = request.session.get('edit_trans')
            if tran_id==None:
                try:
                    Insert_Transaction(expense_data)
                    messages.success(request,'Expense Added Succesfully!!')
                except:
                    messages.error(request,"Unable to Insert!!")

                fullname = request.user.get_full_name()
                exp_cat = Get_Exp_Category()
                categories = exp_cat
                sub_categories = ''
                exp_mode = "Group"
                return render(request, 'expenses.html',{"userid":fullname, "logintype":login_type.capitalize(), "exp_mode":exp_mode, "categories":categories, "sub_categories":sub_categories})
            else:
                Edit_Transaction(tran_id,expense_data)
                request.session['edit_trans']=None
                return redirect('account')
        elif request.POST.get('category-btn'):
            category_selected=request.POST.get('category-btn')
            request.session['cat_sel'] = category_selected
            print(category_selected)
            fullname = request.user.get_full_name()
            exp_cat = Get_Exp_Category()
            categories = exp_cat
            exp_mode = "Group"
            sub_categories = Get_SubCategoryTable(category_selected)
            return render(request, 'expenses.html',{"userid":fullname, "logintype":login_type.capitalize(), "exp_mode":exp_mode, "categories":categories, "sub_categories":sub_categories})
        elif request.POST.get('sub-category-btn'):
            sub_category_selected=request.POST.get('sub-category-btn')
            request.session['sub_cat_sel'] = sub_category_selected
            print(sub_category_selected)
            fullname = request.user.get_full_name()
            get_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
            grouplist = list(get_groups) 
            payee_list = Get_Payee_List()
            payment_methods = Get_Payment_Method()
            exp_mode = "Group"
            return render(request, 'expense_details_group.html',{"userid":fullname, "logintype":login_type.capitalize(), "exp_mode":exp_mode, "cat_crumb":request.session.get('cat_sel'),
             "subcat_crumb":request.session.get('sub_cat_sel'), "grouplist":grouplist, "payeelist": payee_list, "payment_meth":payment_methods})
        elif request.POST.get('create-group'):
            group_name = request.POST.get('groupname')
            group_data = {'name':group_name}
            Write_to_DB(group_data,'auth_group')
        else:
            fullname = request.user.get_full_name()
            tran_id = request.session.get('edit_trans')
            trans = Get_Transaction_By_Id(tran_id)
            if tran_id!=None and len(trans)>0:
                edit_mode = "True"
                exp_mode = "Group"
                exp_cat = Get_Exp_Category()
                print(trans)
                request.session['cat_sel'] = trans[0][3]
                request.session['sub_cat_sel'] = trans[0][4]
                edit_group = trans[0][5]
                edit_date = trans[0][6]
                edit_amount = trans[0][7]
                edit_payee = trans[0][8]
                edit_pay_type = trans[0][9]
                edit_tag = trans[0][10]
                edit_desc = trans[0][11]

                info=""
                get_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
                grouplist = list(get_groups) 
                payee_list = Get_Payee_List()
                payment_methods = Get_Payment_Method()

                return render(request, 'expense_details_group.html',{"userid":fullname, "logintype":login_type.capitalize(), "exp_mode":exp_mode, "cat_crumb":request.session.get('cat_sel'),
                "subcat_crumb":request.session.get('sub_cat_sel'), "grouplist":grouplist, "payeelist": payee_list, "payment_meth":payment_methods,
                'edit_group':edit_group,'edit_date':edit_date,'edit_amount':edit_amount,'edit_payee':edit_payee,'edit_pay_type':edit_pay_type,
                'edit_tag':edit_tag,'edit_desc':edit_desc, 'edit_mode':edit_mode})
            else:
                edit_mode = "False"
                exp_mode = "Group"
                fullname = request.user.get_full_name()
                exp_cat = Get_Exp_Category()
                categories = exp_cat
                sub_categories = ''
                info=""
            return render(request, 'expenses.html',{"info":info, "userid":fullname, "logintype":login_type.capitalize(),  "exp_mode":exp_mode, "categories":categories, "sub_categories":sub_categories})
    else:
        return redirect('home')

@csrf_exempt
@login_required(login_url='home')
def personal_expenses(request):
    logmsg = "personal expenses view: Rendering personal expenses page"
    logging.info(logmsg)
    userid = request.session.get('userid')
    logmsg = 'session id'+str(request.session.get('sessionid'))
    logging.info(logmsg)
    login_type = request.session.get('login_typ')
    if userid!=None:
        if request.POST.get('logout'):
            logmsg = "User logout by: "+str(userid)
            logging.info(logmsg)
            
            try:
                logout(request)
                del request.session['userid']
            except KeyError:
                pass
            info = "User Logged Out Successfully!"
            messages.success(request,info)
            return redirect('home')
        elif request.POST.get('save'):
            info = 'Expense Saved!!'
            logmsg = "Save Button Clicked"
            logging.info(logmsg)
            group = 'Personal Expenses'
            date = request.POST.get('date')
            amount = request.POST.get('amount')
            payee = request.POST.get('payee-name')
            Insert_Payee(payee)
            category = request.session.get('cat_sel')
            subcategory = request.session.get('sub_cat_sel')
            payment = request.POST.get('payment-method')
            tag = request.POST.get('tag')
            description = request.POST.get('description')
            recurring = request.POST.get('recurring')
            expense_data = {'trans_type':['Expense'],'user':[userid],'category':[category], 'sub_category':[subcategory],\
                            'group_name':[group], 'trans_date':[date], 'amount':[amount], 'payee': [payee], 'payment_method': [payment],\
                            'tag':[tag], 'description':[description], 'recurring':[recurring]}

            tran_id = request.session.get('edit_trans')
            if tran_id==None:
                try:
                    Insert_Transaction(expense_data)
                    messages.success(request,'Expense Added Succesfully!!')
                except:
                    messages.error(request,"Unable to Insert!!")

                fullname = request.user.get_full_name()
                exp_cat = Get_Exp_Category()
                categories = exp_cat
                sub_categories = ''
                exp_mode = "Personal"
                return render(request, 'expenses.html',{"userid":fullname, "logintype":login_type.capitalize(), "exp_mode":exp_mode, "categories":categories, "sub_categories":sub_categories})
            else:
                Edit_Transaction(tran_id,expense_data)
                request.session['edit_trans']=None
                fullname = request.user.get_full_name()
                exp_cat = Get_Exp_Category()
                categories = exp_cat
                sub_categories = ''
                exp_mode = "Personal"
                return render(request, 'expenses.html',{"userid":fullname, "exp_mode":exp_mode, "logintype":login_type.capitalize(), "categories":categories, "sub_categories":sub_categories})
        elif request.POST.get('category-btn'):
            category_selected=request.POST.get('category-btn')
            request.session['cat_sel'] = category_selected
            fullname = request.user.get_full_name()
            exp_cat = Get_Exp_Category()
            categories = exp_cat
            sub_categories = Get_SubCategoryTable(category_selected)
            exp_mode = "Personal"
            return render(request, 'expenses.html',{"userid":fullname, "exp_mode":exp_mode, "logintype":login_type.capitalize(), "categories":categories, "sub_categories":sub_categories})
        elif request.POST.get('sub-category-btn'):
            sub_category_selected=request.POST.get('sub-category-btn')
            request.session['sub_cat_sel'] = sub_category_selected
            fullname = request.user.get_full_name()
            get_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
            grouplist = list(get_groups) 
            payee_list = Get_Payee_List()
            payment_methods = Get_Payment_Method()
            exp_mode = "Personal"
            return render(request, 'expense_details_personal.html',{"userid":fullname, "logintype":login_type.capitalize(), "cat_crumb":request.session.get('cat_sel'),
             "exp_mode":exp_mode, "subcat_crumb":request.session.get('sub_cat_sel'), "grouplist":grouplist, "payeelist": payee_list, "payment_meth":payment_methods})
        elif request.POST.get('create-group'):
            group_name = request.POST.get('groupname')
            group_data = {'name':group_name}
            Write_to_DB(group_data,'auth_group')
        else:
            tran_id = request.session.get('edit_trans')
            trans = Get_Transaction_By_Id(tran_id)
            if tran_id!=None and len(trans)>0:
                edit_mode = "True"
                exp_mode = "Personal"
                fullname = request.user.get_full_name()
                exp_cat = Get_Exp_Category()
                request.session['cat_sel'] = trans[0][3]
                request.session['sub_cat_sel'] = trans[0][4]                
                edit_date = trans[0][6]
                edit_amount = trans[0][7]
                edit_payee = trans[0][8]
                edit_pay_type = trans[0][9]
                edit_tag = trans[0][10]
                edit_desc = trans[0][11]

                info=""
                payee_list = Get_Payee_List()
                payment_methods = Get_Payment_Method()
                return render(request, 'expense_details_personal.html',{"userid":fullname, "logintype":login_type.capitalize(), "cat_crumb":request.session.get('cat_sel'),
                "exp_mode":exp_mode, "subcat_crumb":request.session.get('sub_cat_sel'), "payeelist": payee_list, "payment_meth":payment_methods,
                'edit_date':edit_date,'edit_amount':edit_amount,'edit_payee':edit_payee,'edit_pay_type':edit_pay_type,
                'edit_tag':edit_tag,'edit_desc':edit_desc, 'edit_mode':edit_mode})
            else:
                edit_mode = "False"
                exp_mode = "Personal"
                fullname = request.user.get_full_name()
                exp_cat = Get_Exp_Category()
                categories = exp_cat
                sub_categories = '' #Get_SubCategoryTable("Food")
                info=""
                return render(request, 'expenses.html',{"info":info, "userid":fullname, "logintype":login_type.capitalize(), "exp_mode":exp_mode, "categories":categories, "sub_categories":sub_categories})
    else:
        return redirect('home')