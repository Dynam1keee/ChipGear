from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import *

class ProductInline(admin.TabularInline):
    model = Product
    fields = ['name_link', 'quantity', 'price', 'discount']
    extra = 0
    readonly_fields = fields
    view_on_site = False
    can_delete = False

    def name_link(self, obj):
        for rel in obj._meta.get_fields():
            if isinstance(rel, models.OneToOneRel):
                if hasattr(obj, rel.get_accessor_name()):
                    category = rel.get_accessor_name()
                    url = reverse("admin:%s_%s_change" % (obj._meta.app_label, category), args=[obj.pk])
                    return format_html('<a href="{}">{}</a>', url, obj)
    name_link.short_description = 'Name'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ['name']}
    list_display = ['id', 'name', 'slug']
    inlines = [ProductInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    
    def name_link(self, obj):
        for rel in obj._meta.get_fields():
            if isinstance(rel, models.OneToOneRel):
                if hasattr(obj, rel.get_accessor_name()):
                    category = rel.get_accessor_name()
                    url = reverse("admin:%s_%s_change" % (obj._meta.app_label, category), args=[obj.pk])
                    return format_html('<a href="{}">{}</a>', url, obj)
    name_link.short_description = 'Name'

    list_per_page = 25

    prepopulated_fields = {'slug': ['name',]}
    list_display = ['display_id', 'name_link', 'category', 'quantity', 'price', 'discount']
    list_display_links = ['name_link']
    # sortable_by = ['display_id', 'name_link', 'category', 'quantity', 'price', 'discount']
    list_editable = list_display[3:]
    search_fields = ['name']
    list_filter = ['discount', 'quantity', 'category']


admin.site.register(Case)
admin.site.register(CPU)
admin.site.register(GraphicsCard)
admin.site.register(HardDrive)
admin.site.register(Keyboard)
admin.site.register(Motherboard)
admin.site.register(Mouse)
admin.site.register(PowerSupply)
admin.site.register(RAM)
admin.site.register(SoundCard)
admin.site.register(CoolingSystem)
admin.site.register(Monitor)

@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'viewed_at']

admin.site.register(SearchHistory)
