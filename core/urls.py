from django.urls import path
from . import views

urlpatterns = [
    # Dashboards
    path('', views.home, name='home'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),

    # Practice
    path('practice/<int:phrase_id>/', views.practice, name='practice'),
    path('save-attempt/<int:phrase_id>/', views.save_attempt, name='save_attempt'),

    # CRUD for phrases
    path('add-phrase/', views.add_phrase, name='add_phrase'),
    path('edit-phrase/<int:phrase_id>/', views.edit_phrase, name='edit_phrase'),
    path('delete-phrase/<int:phrase_id>/', views.delete_phrase, name='delete_phrase'),

    # New Pages (Menu)
    path('about/', views.about_page, name='about'),
    path('examples/', views.examples_page, name='examples'),
    path('examples/<int:example_id>/', views.example_detail, name='example_detail'),
    path('contact/', views.contact_page, name='contact'),

    # Parent-Student Linking
    path('link-student-parent/', views.link_student_parent, name='link_student_parent'),
    path('manage-links/', views.manage_links, name='manage_links'),

    # Leaderboard
    path('leaderboard/', views.leaderboard_data, name='leaderboard'),
    path('leaderboard/data/', views.leaderboard_data, name='leaderboard_data'),
    # Interactive Graphs for Progress
    path('progress-graph/<int:student_id>/', views.progress_graph, name='progress_graph'),
]
