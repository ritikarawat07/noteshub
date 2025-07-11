from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.landingpage, name='landingpage'),
    path('studentlogin/', views.studentloginview, name='studentlogin'),
    path('teacherlogin/', views.teacheloginview, name='teacherlogin'),
    path('studentdashboard/', views.studentdashboard, name='studentdashboard'),
    path('teacherdashboard/', views.teacherdashboard, name='teacherdashboard'),
    path('studentupload/', views.studentupload, name='studentupload'),
    path('teacherupload/', views.teacherupload, name='teacherupload'),
    path('approve/<int:note_id>/', views.approve_note, name='approve_note'),
    path('reject/<int:note_id>/', views.reject_note, name='reject_note'),
    path('logout/', views.logoutview, name='logout'),
    path('delete/<int:note_id>/', views.delete_note, name='delete_note'),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
