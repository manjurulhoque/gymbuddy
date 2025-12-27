from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsDashboardView.as_view(), name='dashboard'),
    path('revenue/monthly/', views.MonthlyRevenueReportView.as_view(), name='monthly_revenue'),
    path('revenue/monthly/csv/', views.MonthlyRevenueCSVView.as_view(), name='monthly_revenue_csv'),
    path('revenue/monthly/pdf/', views.MonthlyRevenuePDFView.as_view(), name='monthly_revenue_pdf'),
    path('attendance/heatmap/', views.AttendanceHeatmapView.as_view(), name='attendance_heatmap'),
    path('attendance/heatmap/csv/', views.AttendanceHeatmapCSVView.as_view(), name='attendance_heatmap_csv'),
    path('attendance/heatmap/pdf/', views.AttendanceHeatmapPDFView.as_view(), name='attendance_heatmap_pdf'),
    path('trainer/utilization/', views.TrainerUtilizationView.as_view(), name='trainer_utilization'),
    path('trainer/utilization/csv/', views.TrainerUtilizationCSVView.as_view(), name='trainer_utilization_csv'),
    path('trainer/utilization/pdf/', views.TrainerUtilizationPDFView.as_view(), name='trainer_utilization_pdf'),
    path('member/retention/', views.MemberRetentionView.as_view(), name='member_retention'),
    path('member/retention/csv/', views.MemberRetentionCSVView.as_view(), name='member_retention_csv'),
    path('member/retention/pdf/', views.MemberRetentionPDFView.as_view(), name='member_retention_pdf'),
]

