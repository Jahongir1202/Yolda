from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from .views import login_view,logout_view,api_receive_message,message_list

urlpatterns = [
    path('messages/', views.show_last_message, name='show_last_message'),
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('my-messages/', views.my_messages_view, name='my_messages'),
    path('my-list/', views.my_messages_view, name='my_list'),
    path('edit_message/<int:msg_id>/', views.edit_message, name='edit_message'),
    path('delete-message/<int:msg_id>/', views.delete_message, name='delete_message'),
    path('send_to_groups/<int:msg_id>/', views.send_to_groups, name='send_to_groups'),
    path('take_message/<int:id>/', views.take_message, name='take_message'),
    path("api/send/", api_receive_message, name="api_send_message"),
    path("wmessages/", message_list, name="message_list"),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

