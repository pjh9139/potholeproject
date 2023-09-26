from django.urls import path
from . import views


urlpatterns = [
    path('pothole/<str:name>', views.pothole, name='pothole'),
    path('graph/<str:name>', views.graph, name='graph'),
    path('folder/<str:name>', views.folder, name='folder'),
]
