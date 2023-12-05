from django.urls import path
from . import views

urlpatterns = [
    path('', views.base_page, name="base_page"),
    path('home', views.home, name ="home"),
    path('nexar/', views.nexar_part_search, name='nexar_part_search'),
    path('ms/', views.ms_part_search, name='ms_part_search'),
    path('sheet', views.cheat_sheet, name="cheat_sheet"),
    path('base', views.base_page, name='base_page'),
    path('search_mouser/', views.search_mouser, name='search_mouser'),
    path('search_all/', views.search_all, name='search_all'),
    path('sad/', views.searh_and_display, name='sad'),
    path('nxp_mpn',views.search_mpn,name='nxp_mpn'),
    path('nxp_search',views.mpn,name='nxp_search'),
    


]