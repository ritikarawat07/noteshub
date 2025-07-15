from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.landingpage, name='landingpage'),
    path('studentlogin/', views.studentloginview, name='studentlogin'),
    path('teacherlogin/', views.teacheloginview, name='teacherlogin'),
    path('studentlogin/studentdashboard/', views.studentdashboard, name='studentdashboard'),
    path('teacherlogin/teacherdashboard/', views.teacherdashboard, name='teacherdashboard'),
    path('studentlogin/studentupload/', views.studentupload, name='studentupload'),
    path('teacherlogin/teacherupload/', views.teacherupload, name='teacherupload'),
    path('approve/<int:note_id>/', views.approve_note, name='approve_note'),
    path('reject/<int:note_id>/', views.reject_note, name='reject_note'),
    path('pending/<int:note_id>/', views.pending_note, name='pending_note'),
    path('logout/', views.logoutview, name='logout'),
    path('delete/<int:note_id>/', views.delete_note, name='delete_note'),
    path('view/<int:note_id>/', views.view_note, name='view_note'),
    path('download/<int:note_id>/', views.download_note, name='download_note'),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
