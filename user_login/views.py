from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Permission, User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import Group
from django.db import IntegrityError
import logging
from user_login.sqlite3_read_write import Get_Income_Category, Get_Exp_Category, Get_SubCategoryTable, \
    Write_to_DB, Get_SessionID, Get_Payee_List, Get_Payment_Method, Get_Payer_List,Insert_Transaction, \
    Get_Transaction_Summary, Get_Personal_Exp_Summary,Get_Group_Exp_Summary,Get_Group_User_Exp_Summary, \
    Insert_Payee
from datetime import datetime
from django.views.generic import CreateView

logging.basicConfig(level=logging.DEBUG)

@csrf_exempt
def home(request):
    logmsg = "home view: Rendering login page template"
    logging.info(logmsg)
    return render(request, 'login.html')

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
        
        try:
            user = User.objects.create_user(username=newuserid, 
                                        password=newpassword,
                                        email=email,
                                        first_name=firstname,
                                        last_name=lastname)

            user.save()
            logmsg = "Successfully Signed Up!, Login to Start Adding Expenses."
            logging.info(logmsg)
            messages.success(request,logmsg)
            return render(request,'signup.html')
        except IntegrityError: 
            logmsg = "Error: User Already Exists!"
            logging.error(logmsg)
            messages.error(request,logmsg)
            return render(request, 'signup.html')
    return render(request, 'signup.html')


@csrf_exempt
def authentication(request):
    authentication = ''
    logmsg = "authentication view: Authentication Veiw Entered"
    logging.info(logmsg)

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

        if (admin=='on' and authentication=='Success' and superuser==True):
            request.session['login_typ'] = 'admin'
            session_data = {'date':[str(login_date)], 'user_id':[str(userid)], 'loggin_type':['admin']}
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
        elif (admin==None and authentication=='Success'):
            request.session['login_typ'] = 'user'
            session_data = {'date':[str(login_date)], 'user_id':[str(userid)], 'loggin_type':['user']}
            Write_to_DB(session_data,'session_master')
            sessionid=Get_SessionID(session_data)
            request.session['sessionid'] = sessionid 
            fullname = request.user.get_full_name()
            logmsg = "User login by: "+str(userid)+": "+str(fullname)
            logging.info(logmsg)
            return redirect('account')
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
def account(request):
    fullname = request.user.get_full_name()
    login_type = request.session.get('login_typ')
    logmsg = "account view: Rendering account page template"
    logging.info(logmsg)
    userid = request.session.get('userid')
    logmsg = 'session id'+str(request.session.get('sessionid'))
    logging.info(logmsg)
    login_type = request.session.get('login_typ')
    limit_to = request.POST.get('limit_to')
    get_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
    grouplist = list(get_groups)
    print(grouplist)
    user_opt = request.POST.get('user_opt')
    request.session['user_opt'] = user_opt
    sess_user_opt = request.session.get('user_opt')
    sel_group = request.POST.get('group_name')
    request.session['group_name']= sel_group
    sess_group = request.session.get('group_name')
    if(sel_group==None and len(grouplist)>0):
        sel_group = grouplist[0]
    else:
        sel_group="Personal Expenses"

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

        per_header = ['Total','Income','Expense']
        per_rows = Get_Personal_Exp_Summary(userid)

        group_header = ['Total','Expense']
        group_user_exp = Get_Group_User_Exp_Summary(sel_group)
        print(group_user_exp)
        group_rows = Get_Group_Exp_Summary(sel_group)
        print(group_rows)
        print(user_opt)
        if user_opt == "Today":
            print("today")
            user_exp_summary=group_user_exp[0]
        elif user_opt == "This Week":
            print("this week")
            user_exp_summary=group_user_exp[1]
        else:
            print("this month")
            user_exp_summary=group_user_exp[2]

        #for usr in group_user_exp[2]['user']:
        #    group_header.append(usr)

        trans_header = ['Date', 'Category', 'Sub Category', 'Group Name', 'Payee', 'Payement Method', 'Tag#', 'Amount']
        if(limit_to==None):
            limit_to=10
            trans_rows = Get_Transaction_Summary(limit_to,userid)
        else:
            trans_rows = Get_Transaction_Summary(limit_to,userid)

    return render(request,'account.html', {"userid":fullname, "logintype":login_type.capitalize(), 
                "per_header":per_header, "per_rows":per_rows, "group_header":group_header,"group_rows":group_rows,
                "trans_header":trans_header,"trans_rows":trans_rows, 'limit_to':limit_to, "grouplist":grouplist, 
                "group_user_exp":user_exp_summary, "sess_user_opt":sess_user_opt, "sess_group":sess_group})

@csrf_exempt
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

    return render(request,'create_group.html')

@csrf_exempt
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
            return render(request, 'income_details.html',{"userid":fullname, "logintype":login_type.capitalize(), 
             "cat_crumb":request.session.get('cat_sel'), "payerlist": payer_list})
        elif request.POST.get('save'):
            info = 'Income Saved!!'
            logmsg = "Save Button Clicked"
            logging.info(logmsg)
            group = "Personal Expenses"
            date = request.POST.get('date')
            amount = request.POST.get('amount')
            payer = request.POST.get('payer')
            category = request.session.get('cat_sel')
            subcategory = 'NA'
            payment = 'NA'
            tag = request.POST.get('tag')
            description = request.POST.get('description')
            recurring = request.POST.get('recurring')
            income_data = {'trans_type':['Income'],'user':[userid],'category':[category], 'sub_category':[subcategory],\
                            'group_name':[group], 'trans_date':[date], 'amount':[amount], 'payee': [payer], 'payment_method': [payment],\
                            'tag':[tag], 'description':[description], 'recurring':[recurring]}
            print(income_data)
            try:
                Insert_Transaction(income_data)
                messages.success(request,'Income Added Succesfully!!')
            except:
                messages.error(request,"Unable to Insert!!")

            fullname = request.user.get_full_name()
            income_cat = Get_Income_Category()
            categories = income_cat
            return render(request, 'incomes.html',{"userid":fullname, "logintype":login_type.capitalize(), "categories":categories})

    income_cat = Get_Income_Category()
    categories = income_cat
    info=""
    return render(request,'incomes.html',{"info":info, "userid":fullname, "logintype":login_type.capitalize(), "categories":categories})

@csrf_exempt
def group_expenses(request):
    logmsg = "group expenses view: Rendering expenses page"
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
        elif request.POST.get('add-payee'):
            fullname = request.user.get_full_name()
            get_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
            grouplist = list(get_groups) 
            payee_list = Get_Payee_List()
            payment_methods = Get_Payment_Method()
            return render(request, 'expense_details_group.html',{"userid":fullname, "logintype":login_type.capitalize(), "cat_crumb":request.session.get('cat_sel'),
             "subcat_crumb":request.session.get('sub_cat_sel'), "grouplist":grouplist, "payeelist": payee_list, "payment_meth":payment_methods})
        elif request.POST.get('save'):
            info = 'Expense Saved!!'
            logmsg = "Save Button Clicked"
            logging.info(logmsg)
            tempvalue = request.POST.getlist('newpayee-list')
            newpayee_list = tempvalue[0].split(",")
            Insert_Payee(newpayee_list) 
            logging.info(newpayee_list)
            group = request.POST.get('group')
            date = request.POST.get('date')
            amount = request.POST.get('amount')
            payee = request.POST.get('payee')
            category = request.session.get('cat_sel')
            subcategory = request.session.get('sub_cat_sel')
            payment = request.POST.get('payment-method')
            tag = request.POST.get('tag')
            description = request.POST.get('description')
            recurring = request.POST.get('recurring')
            expense_data = {'trans_type':['Expense'],'user':[userid],'category':[category], 'sub_category':[subcategory],\
                            'group_name':[group], 'trans_date':[date], 'amount':[amount], 'payee': [payee], 'payment_method': [payment],\
                            'tag':[tag], 'description':[description], 'recurring':[recurring]}
            print(expense_data)
            try:
                Insert_Transaction(expense_data)
                messages.success(request,'Expense Added Succesfully!!')
            except:
                messages.error(request,"Unable to Insert!!")

            fullname = request.user.get_full_name()
            exp_cat = Get_Exp_Category()
            categories = exp_cat
            sub_categories = '' 
            return render(request, 'expenses.html',{"userid":fullname, "logintype":login_type.capitalize(), "categories":categories, "sub_categories":sub_categories})
        elif request.POST.get('category-btn'):
            category_selected=request.POST.get('category-btn')
            request.session['cat_sel'] = category_selected
            print(category_selected)
            fullname = request.user.get_full_name()
            exp_cat = Get_Exp_Category()
            categories = exp_cat
            sub_categories = Get_SubCategoryTable(category_selected)
            return render(request, 'expenses.html',{"userid":fullname, "logintype":login_type.capitalize(), "categories":categories, "sub_categories":sub_categories})
        elif request.POST.get('sub-category-btn'):
            sub_category_selected=request.POST.get('sub-category-btn')
            request.session['sub_cat_sel'] = sub_category_selected
            print(sub_category_selected)
            fullname = request.user.get_full_name()
            get_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
            grouplist = list(get_groups) 
            payee_list = Get_Payee_List()
            payment_methods = Get_Payment_Method()
            return render(request, 'expense_details_group.html',{"userid":fullname, "logintype":login_type.capitalize(), "cat_crumb":request.session.get('cat_sel'),
             "subcat_crumb":request.session.get('sub_cat_sel'), "grouplist":grouplist, "payeelist": payee_list, "payment_meth":payment_methods})
        elif request.POST.get('create-group'):
            group_name = request.POST.get('groupname')
            group_data = {'name':group_name}
            Write_to_DB(group_data,'auth_group')
        else:
            fullname = request.user.get_full_name()
            exp_cat = Get_Exp_Category()
            categories = exp_cat
            sub_categories = '' #Get_SubCategoryTable("Food")
            info=""
            return render(request, 'expenses.html',{"info":info, "userid":fullname, "logintype":login_type.capitalize(), "categories":categories, "sub_categories":sub_categories})
    else:
        return redirect('home')

@csrf_exempt
def personal_expenses(request):
    logmsg = "personal expenses view: Rendering expenses page"
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
        elif request.POST.get('add-payee'):
            print(request.POST.get('payee-name'))    
            fullname = request.user.get_full_name()
            payee_list = Get_Payee_List()
            payment_methods = Get_Payment_Method()
            return render(request, 'expense_details_personal.html',{"userid":fullname, "logintype":login_type.capitalize(), "cat_crumb":request.session.get('cat_sel'),
             "subcat_crumb":request.session.get('sub_cat_sel'), "payeelist": payee_list, "payment_meth":payment_methods})
        elif request.POST.get('save'):
            info = 'Expense Saved!!'
            logmsg = "Save Button Clicked"
            logging.info(logmsg)
            tempvalue = request.POST.getlist('newpayee-list')
            newpayee_list = tempvalue[0].split(",")
            Insert_Payee(newpayee_list) 
            group = 'Personal Expenses'
            date = request.POST.get('date')
            amount = request.POST.get('amount')
            payee = request.POST.get('payee')
            category = request.session.get('cat_sel')
            subcategory = request.session.get('sub_cat_sel')
            payment = request.POST.get('payment-method')
            tag = request.POST.get('tag')
            description = request.POST.get('description')
            recurring = request.POST.get('recurring')
            expense_data = {'trans_type':['Expense'],'user':[userid],'category':[category], 'sub_category':[subcategory],\
                            'group_name':[group], 'trans_date':[date], 'amount':[amount], 'payee': [payee], 'payment_method': [payment],\
                            'tag':[tag], 'description':[description], 'recurring':[recurring]}
            print(expense_data)
            try:
                Insert_Transaction(expense_data)
                messages.success(request,'Expense Added Succesfully!!')
            except:
                messages.error(request,"Unable to Insert!!")

            fullname = request.user.get_full_name()
            exp_cat = Get_Exp_Category()
            categories = exp_cat
            sub_categories = '' 
            return render(request, 'expenses.html',{"userid":fullname, "logintype":login_type.capitalize(), "categories":categories, "sub_categories":sub_categories})
        elif request.POST.get('category-btn'):
            category_selected=request.POST.get('category-btn')
            request.session['cat_sel'] = category_selected
            print(category_selected)
            fullname = request.user.get_full_name()
            exp_cat = Get_Exp_Category()
            categories = exp_cat
            sub_categories = Get_SubCategoryTable(category_selected)
            return render(request, 'expenses.html',{"userid":fullname, "logintype":login_type.capitalize(), "categories":categories, "sub_categories":sub_categories})
        elif request.POST.get('sub-category-btn'):
            sub_category_selected=request.POST.get('sub-category-btn')
            request.session['sub_cat_sel'] = sub_category_selected
            print(sub_category_selected)
            fullname = request.user.get_full_name()
            get_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
            grouplist = list(get_groups) 
            payee_list = Get_Payee_List()
            payment_methods = Get_Payment_Method()
            return render(request, 'expense_details_personal.html',{"userid":fullname, "logintype":login_type.capitalize(), "cat_crumb":request.session.get('cat_sel'),
             "subcat_crumb":request.session.get('sub_cat_sel'), "grouplist":grouplist, "payeelist": payee_list, "payment_meth":payment_methods})
        elif request.POST.get('create-group'):
            group_name = request.POST.get('groupname')
            group_data = {'name':group_name}
            Write_to_DB(group_data,'auth_group')
        else:
            fullname = request.user.get_full_name()
            exp_cat = Get_Exp_Category()
            categories = exp_cat
            sub_categories = '' #Get_SubCategoryTable("Food")
            info=""
            return render(request, 'expenses.html',{"info":info, "userid":fullname, "logintype":login_type.capitalize(), "categories":categories, "sub_categories":sub_categories})
    else:
        return redirect('home')