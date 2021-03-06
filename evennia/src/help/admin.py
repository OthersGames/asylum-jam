"""
This defines how to edit help entries in Admin.
"""
from django import forms
from django.contrib import admin
from src.help.models import HelpEntry



class HelpEntryForm(forms.ModelForm):
    "Defines how to display the help entry"
    class Meta:
        model = HelpEntry
    db_help_category = forms.CharField(label="Help category", initial='General',
                                       help_text="organizes help entries in lists")
    db_lock_storage = forms.CharField(label="Locks", initial='view:all()',required=False,
                                      widget=forms.TextInput(attrs={'size':'40'}),)

class HelpEntryAdmin(admin.ModelAdmin):
    "Sets up the admin manaager for help entries"

    list_display = ('id', 'db_key', 'db_help_category', 'db_lock_storage')
    list_display_links = ('id', 'db_key')
    search_fields = ['^db_key', 'db_entrytext']
    ordering = ['db_help_category', 'db_key']
    save_as = True
    save_on_top = True
    list_select_related = True

    form = HelpEntryForm
    fieldsets = (
        (None, {'fields':(('db_key', 'db_help_category'), 'db_entrytext', 'db_lock_storage'),
                'description':"Sets a Help entry. Set lock to <i>view:all()</I> unless you want to restrict it."}),)


admin.site.register(HelpEntry, HelpEntryAdmin)
