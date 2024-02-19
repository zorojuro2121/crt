from django.urls import path
from . import views

urlpatterns = [
    path('', views.base_page, name="base_page"),
    path('nexar/', views.nexar_part_search, name='nexar_part_search'),
    path('sheet', views.cheat_sheet, name="cheat_sheet"),
    path('base', views.base_page, name='base_page'),
    path('search_mouser/', views.search_mouser, name='search_mouser'),
    path('search_all/', views.search_all, name='search_all'),
    path('sad/', views.searh_and_display, name='sad'),
    path('nxp_alt',views.search_nexar_alt,name='nxp_alt'),
    path('store_selected_parts/', views.store_selected_parts, name='store_selected_parts'),
    path('upload_checked_parts/', views.upload_checked_parts, name='upload_checked_parts'),
    path('export-to-excel/', views.export_to_excel, name='export_to_excel'),
    path('search_dynamic/', views.search_dynamic, name='search_dynamic'),
    path('import_data/',views.import_data, name='import_data'),
    path('download-template/', views.download_template, name='download_template'),
    path('irc_result', views.search_irc, name='irc_result'),
    path('login/', views.login, name="login"),
    path('export/',views.export_page, name='export'),
    path('admin_page/', views.admin_page, name='admin_page'),
    path('login_view/', views.login_view, name='login_view'),
    path('getting_started', views.getting_started, name='getting_started'),
    path('filter',views.filter,name="filter"),
    path('download/', views.download_sheet, name='download_sheet'),
    # path('fuzzy_search',views.fuzzy_search,name="fuzzy_search"),
    # path('source',views.source,name="source"),
]
