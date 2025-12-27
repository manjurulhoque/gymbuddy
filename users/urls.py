from django.urls import path
from .views import (
    LoginView, LogoutView, UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    ProfileView, ProfileUpdateView, ProfilePasswordChangeView,
    AssignmentListView, AssignmentCreateView, AssignmentUpdateView, AssignmentDeleteView,
    TrainerTraineesView, TraineeTrainerView,
    CheckInView, CheckOutView, AttendanceCheckInView, AttendanceHistoryView,
    AttendanceStatisticsView, TrainerMarkAttendanceView, BulkAttendanceMarkView,
    TrainerAvailabilityListView, TrainerAvailabilityCreateView, TrainerAvailabilityUpdateView, TrainerAvailabilityDeleteView,
    TrainingSessionListView, TrainingSessionCreateView, TrainingSessionUpdateView, TrainingSessionDeleteView, TrainingSessionCancelView,
    CalendarView,
    SessionReminderListView, SessionReminderCreateView, SessionReminderDeleteView
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
    # Attendance URLs
    path('attendance/check-in/', AttendanceCheckInView.as_view(), name='attendance_check_in'),
    path('attendance/check-in/action/', CheckInView.as_view(), name='check_in'),
    path('attendance/check-out/action/', CheckOutView.as_view(), name='check_out'),
    path('attendance/history/', AttendanceHistoryView.as_view(), name='attendance_history'),
    path('attendance/statistics/', AttendanceStatisticsView.as_view(), name='attendance_statistics'),
    path('attendance/trainer/mark/', TrainerMarkAttendanceView.as_view(), name='trainer_mark_attendance'),
    path('attendance/bulk-mark/', BulkAttendanceMarkView.as_view(), name='bulk_attendance_mark'),
    # Scheduling URLs
    path('availability/', TrainerAvailabilityListView.as_view(), name='trainer_availability_list'),
    path('availability/create/', TrainerAvailabilityCreateView.as_view(), name='trainer_availability_create'),
    path('availability/<int:pk>/update/', TrainerAvailabilityUpdateView.as_view(), name='trainer_availability_update'),
    path('availability/<int:pk>/delete/', TrainerAvailabilityDeleteView.as_view(), name='trainer_availability_delete'),
    path('sessions/', TrainingSessionListView.as_view(), name='training_session_list'),
    path('sessions/create/', TrainingSessionCreateView.as_view(), name='training_session_create'),
    path('sessions/<int:pk>/update/', TrainingSessionUpdateView.as_view(), name='training_session_update'),
    path('sessions/<int:pk>/delete/', TrainingSessionDeleteView.as_view(), name='training_session_delete'),
    path('sessions/cancel/', TrainingSessionCancelView.as_view(), name='training_session_cancel'),
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('reminders/', SessionReminderListView.as_view(), name='session_reminder_list'),
    path('reminders/create/', SessionReminderCreateView.as_view(), name='session_reminder_create'),
    path('reminders/<int:pk>/delete/', SessionReminderDeleteView.as_view(), name='session_reminder_delete'),
]

