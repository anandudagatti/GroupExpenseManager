from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('authentication/', views.authentication, name='authentication'),
    path('account/', views.account, name='account'),
    path('nogroup_account/', views.nogroup_account, name='nogroup_account'),
    path('admin/', views.admin, name='admin'),
    path('groups/', views.groups, name='groups'),
    path('incomes/', views.incomes, name='incomes'),
    path('group_expenses/', views.group_expenses, name='group_expenses'),
    path('personal_expenses/', views.personal_expenses, name='personal_expenses'),
    path('terms_of_use/', views.terms, name='terms')
]
