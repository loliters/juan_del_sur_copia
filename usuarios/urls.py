from django.urls import path
from . import views
#app_name = 'usuarios'
urlpatterns = [
    #  LOGIN
    path('login/', views.login_view, name='login'),

    #  LOGOUT
    path('logout/', views.logout_view, name='logout'),

    # REGISTER
    path('register/', views.register, name='register'),

    # DASHBOARDS
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/cajero/', views.dashboard_cajero, name='dashboard_cajero'),

    # MODIFICAR USUARIO
    path('modificar/<int:id>/', views.modify, name='modify'),
    
    # ELIMINAR
    path('eliminar/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),
    
    # INACTIVOS
    path('usuarios/inactivos/', views.ver_inactivos, name='ver_inactivos'),
    
    # GENERAR EMAIL
    path('generar-email-preview/', views.generar_email_preview, name='generar_email_preview'),
    
  
    
    
]