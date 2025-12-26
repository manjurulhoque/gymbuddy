from django.urls import path
from .views import (
    LoginView, LogoutView, UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    ProfileView, ProfileUpdateView, ProfilePasswordChangeView,
    AssignmentListView, AssignmentCreateView, AssignmentUpdateView, AssignmentDeleteView,
    TrainerTraineesView, TraineeTrainerView
)

app_name = 'users'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/change-password/', ProfilePasswordChangeView.as_view(), name='profile_password_change'),
    path('', UserListView.as_view(), name='user_list'),
    path('create/', UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    path('<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    # Trainer-Trainee Assignment URLs
    path('assignments/', AssignmentListView.as_view(), name='assignment_list'),
    path('assignments/create/', AssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/<int:pk>/update/', AssignmentUpdateView.as_view(), name='assignment_update'),
    path('assignments/<int:pk>/delete/', AssignmentDeleteView.as_view(), name='assignment_delete'),
    # Trainer and Trainee views
    path('trainer/trainees/', TrainerTraineesView.as_view(), name='trainer_trainees'),
    path('trainee/trainer/', TraineeTrainerView.as_view(), name='trainee_trainer'),
]

