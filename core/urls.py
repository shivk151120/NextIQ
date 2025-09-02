from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('practice/<int:phrase_id>/', views.practice, name='practice'),
    path('like/<int:phrase_id>/', views.toggle_like, name='toggle_like'),  # AJAX
    path('add_phrase/', views.add_phrase, name='add_phrase'),  # Add Phrase
    path('edit_phrase/<int:phrase_id>/', views.edit_phrase, name='edit_phrase'),  # Edit Phrase
    path('delete_phrase/<int:phrase_id>/', views.delete_phrase, name='delete_phrase'),
    path('practice/<int:phrase_id>/save_attempt/', views.save_attempt, name='save_attempt'),
]
