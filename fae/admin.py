from django.contrib import admin
from .models import savedata

class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'mpn')

# Register the Manufacturer model with the custom admin class
admin.site.register(savedata, ManufacturerAdmin)