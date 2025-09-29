from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    add_phrase,
    edit_phrase,
    delete_phrase,
    leaderboard_page,  # <- THIS MUST BE IMPORTED
)

urlpatterns = [
    # Dashboards
    path('', views.home, name='home'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('parent-dashboard/', views.parent_dashboard, name='parent_dashboard'),
    # Practice
    path('practice/<int:phrase_id>/', views.practice, name='practice'),
    path('save-attempt/<int:phrase_id>/', views.save_attempt, name='save_attempt'),

    # CRUD for phrases
    path('add-phrase/', views.add_phrase, name='add_phrase'),
    path('edit-phrase/<int:phrase_id>/', views.edit_phrase, name='edit_phrase'),
    path('delete-phrase/<int:phrase_id>/', views.delete_phrase, name='delete_phrase'),

    # New Pages (Menu)
    path('about/', views.about_page, name='about_page'),
    path('examples/', views.examples_list, name='examples_list'),
    path('examples/<int:example_id>/', views.example_detail, name='example_detail'),
    path('examples/add/', views.add_example, name='add_example'),
    path('examples/<int:example_id>/edit/', views.edit_example, name='edit_example'),
    path('examples/<int:example_id>/delete/', views.delete_example, name='delete_example'),
    path('contact/', views.contact_page, name='contact_page'),

    # Parent-Student Linking
    path('add-parent-link/', views.add_parent_link, name='add_parent_link'),
    path('delete-parent-link/<int:student_id>/', views.delete_parent_link, name='delete_parent_link'),

    path('link-student-parent/', views.link_student_parent, name='link_student_parent'),
    path('manage-links/', views.manage_links, name='manage_links'),
    path('update-site-settings/', views.update_site_settings, name='update_site_settings'),

    # Leaderboard
    path('leaderboard/', views.leaderboard_data, name='leaderboard'),
    path('leaderboard/data/', views.leaderboard_data, name='leaderboard_data'),
    # Interactive Graphs for Progress
    path('progress-graph/<int:student_id>/', views.progress_graph, name='progress_graph'),
    path('lessons/', views.lessons, name='lessons'),
    path('lessons/add/', views.add_lesson, name='add_lesson'),
    path('lessons/edit/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),
    path('lessons/delete/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('leaderboard/', leaderboard_page, name='leaderboard_page'),
]

