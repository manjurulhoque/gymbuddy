from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.db.models.functions import TruncMonth, TruncDate, Extract
from datetime import datetime, timedelta
from decimal import Decimal
import csv
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from users.mixins import StaffOrAboveRequiredMixin
from users.models import User, Attendance, TrainingSession, TrainerTraineeAssignment
from memberships.models import Payment, Subscription


class ReportsDashboardView(StaffOrAboveRequiredMixin, TemplateView):
    """Main reports dashboard"""
    template_name = 'reports/dashboard.html'


class MonthlyRevenueReportView(StaffOrAboveRequiredMixin, TemplateView):
    """Monthly revenue report with export options"""
    template_name = 'reports/monthly_revenue.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get month filter from query params
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        
        if month and year:
            try:
                month_int = int(month)
                year_int = int(year)
                start_date = timezone.make_aware(datetime(year_int, month_int, 1))
                if month_int == 12:
                    end_date = timezone.make_aware(datetime(year_int + 1, 1, 1))
                else:
                    end_date = timezone.make_aware(datetime(year_int, month_int + 1, 1))
            except (ValueError, TypeError):
                month = None
                year = None
        
        if not month or not year:
            # Default to current month
            now = timezone.now()
            month = now.month
            year = now.year
            start_date = timezone.make_aware(datetime(year, month, 1))
            if month == 12:
                end_date = timezone.make_aware(datetime(year + 1, 1, 1))
            else:
                end_date = timezone.make_aware(datetime(year, month + 1, 1))
        
        # Get payments for the month
        payments = Payment.objects.filter(
            status=Payment.PaymentStatus.COMPLETED,
            payment_date__gte=start_date,
            payment_date__lt=end_date
        ).select_related('subscription__user', 'subscription__plan').order_by('payment_date')
        
        # Calculate totals
        total_revenue = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        payment_count = payments.count()
        avg_payment = total_revenue / payment_count if payment_count > 0 else Decimal('0.00')
        
        # Group by payment method
        by_method = payments.values('payment_method').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Daily breakdown
        daily_breakdown = payments.annotate(
            date=TruncDate('payment_date')
        ).values('date').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('date')
        
        # Plan breakdown
        plan_breakdown = payments.values(
            'subscription__plan__display_name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        context.update({
            'month': month,
            'year': year,
            'payments': payments,
            'total_revenue': total_revenue,
            'payment_count': payment_count,
            'avg_payment': avg_payment,
            'by_method': by_method,
            'daily_breakdown': daily_breakdown,
            'plan_breakdown': plan_breakdown,
            'start_date': start_date,
            'end_date': end_date,
        })
        
        return context


class MonthlyRevenueCSVView(StaffOrAboveRequiredMixin, TemplateView):
    """Export monthly revenue report as CSV"""
    
    def get(self, request, *args, **kwargs):
        month = request.GET.get('month')
        year = request.GET.get('year')
        
        if month and year:
            try:
                month_int = int(month)
                year_int = int(year)
                start_date = timezone.make_aware(datetime(year_int, month_int, 1))
                if month_int == 12:
                    end_date = timezone.make_aware(datetime(year_int + 1, 1, 1))
                else:
                    end_date = timezone.make_aware(datetime(year_int, month_int + 1, 1))
            except (ValueError, TypeError):
                now = timezone.now()
                month_int = now.month
                year_int = now.year
                start_date = timezone.make_aware(datetime(year_int, month_int, 1))
                if month_int == 12:
                    end_date = timezone.make_aware(datetime(year_int + 1, 1, 1))
                else:
                    end_date = timezone.make_aware(datetime(year_int, month_int + 1, 1))
        else:
            now = timezone.now()
            month_int = now.month
            year_int = now.year
            start_date = timezone.make_aware(datetime(year_int, month_int, 1))
            if month_int == 12:
                end_date = timezone.make_aware(datetime(year_int + 1, 1, 1))
            else:
                end_date = timezone.make_aware(datetime(year_int, month_int + 1, 1))
        
        payments = Payment.objects.filter(
            status=Payment.PaymentStatus.COMPLETED,
            payment_date__gte=start_date,
            payment_date__lt=end_date
        ).select_related('subscription__user', 'subscription__plan').order_by('payment_date')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="revenue_report_{year_int}_{month_int:02d}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Monthly Revenue Report', f'{year_int}-{month_int:02d}'])
        writer.writerow([])
        writer.writerow(['Date', 'User', 'Plan', 'Amount', 'Payment Method', 'Transaction ID'])
        
        total = Decimal('0.00')
        for payment in payments:
            writer.writerow([
                payment.payment_date.strftime('%Y-%m-%d %H:%M'),
                payment.subscription.user.get_full_name() or payment.subscription.user.username,
                payment.subscription.plan.display_name,
                f'${payment.amount:.2f}',
                payment.get_payment_method_display(),
                payment.transaction_id or ''
            ])
            total += payment.amount
        
        writer.writerow([])
        writer.writerow(['Total Revenue', f'${total:.2f}'])
        writer.writerow(['Total Payments', payments.count()])
        
        return response


class MonthlyRevenuePDFView(StaffOrAboveRequiredMixin, TemplateView):
    """Export monthly revenue report as PDF"""
    
    def get(self, request, *args, **kwargs):
        month = request.GET.get('month')
        year = request.GET.get('year')
        
        if month and year:
            try:
                month_int = int(month)
                year_int = int(year)
                start_date = timezone.make_aware(datetime(year_int, month_int, 1))
                if month_int == 12:
                    end_date = timezone.make_aware(datetime(year_int + 1, 1, 1))
                else:
                    end_date = timezone.make_aware(datetime(year_int, month_int + 1, 1))
            except (ValueError, TypeError):
                now = timezone.now()
                month_int = now.month
                year_int = now.year
                start_date = timezone.make_aware(datetime(year_int, month_int, 1))
                if month_int == 12:
                    end_date = timezone.make_aware(datetime(year_int + 1, 1, 1))
                else:
                    end_date = timezone.make_aware(datetime(year_int, month_int + 1, 1))
        else:
            now = timezone.now()
            month_int = now.month
            year_int = now.year
            start_date = timezone.make_aware(datetime(year_int, month_int, 1))
            if month_int == 12:
                end_date = timezone.make_aware(datetime(year_int + 1, 1, 1))
            else:
                end_date = timezone.make_aware(datetime(year_int, month_int + 1, 1))
        
        payments = Payment.objects.filter(
            status=Payment.PaymentStatus.COMPLETED,
            payment_date__gte=start_date,
            payment_date__lt=end_date
        ).select_related('subscription__user', 'subscription__plan').order_by('payment_date')
        
        total_revenue = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
        )
        
        # Title
        elements.append(Paragraph('Monthly Revenue Report', title_style))
        elements.append(Paragraph(f'Period: {year_int}-{month_int:02d}', styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary
        summary_data = [
            ['Total Revenue', f'${total_revenue:.2f}'],
            ['Total Payments', str(payments.count())],
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Payment details
        if payments.exists():
            table_data = [['Date', 'User', 'Plan', 'Amount', 'Method']]
            for payment in payments[:50]:  # Limit to 50 rows per page
                table_data.append([
                    payment.payment_date.strftime('%Y-%m-%d'),
                    payment.subscription.user.get_full_name() or payment.subscription.user.username,
                    payment.subscription.plan.display_name,
                    f'${payment.amount:.2f}',
                    payment.get_payment_method_display(),
                ])
            
            table = Table(table_data, colWidths=[1.2*inch, 2*inch, 1.5*inch, 1*inch, 1.3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            elements.append(table)
        
        doc.build(elements)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="revenue_report_{year_int}_{month_int:02d}.pdf"'
        response.write(buffer.getvalue())
        buffer.close()
        return response


class AttendanceHeatmapView(StaffOrAboveRequiredMixin, TemplateView):
    """Attendance heatmap report"""
    template_name = 'reports/attendance_heatmap.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from query params
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Get attendances in range
        attendances = Attendance.objects.filter(
            check_in__date__gte=start_date,
            check_in__date__lte=end_date
        )
        
        # Build heatmap data - day of week vs hour of day
        heatmap_data = {}
        for attendance in attendances:
            date = attendance.check_in.date()
            hour = attendance.check_in.hour
            day_of_week = date.weekday()  # 0=Monday, 6=Sunday
            
            key = (day_of_week, hour)
            heatmap_data[key] = heatmap_data.get(key, 0) + 1
        
        # Create matrix for display
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hours = list(range(24))
        
        matrix = []
        for day_idx, day_name in enumerate(days):
            row = {'day': day_name, 'hours': []}
            for hour in hours:
                count = heatmap_data.get((day_idx, hour), 0)
                row['hours'].append({
                    'hour': hour,
                    'count': count,
                    'intensity': min(count / max(heatmap_data.values()) if heatmap_data.values() else 0, 1.0)
                })
            matrix.append(row)
        
        # Daily totals
        daily_totals = attendances.annotate(
            date=TruncDate('check_in')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Hourly totals
        hourly_totals = {}
        for hour in hours:
            hourly_totals[hour] = attendances.filter(
                check_in__hour=hour
            ).count()
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'heatmap_matrix': matrix,
            'daily_totals': daily_totals,
            'hourly_totals': hourly_totals,
            'total_attendances': attendances.count(),
            'max_count': max(heatmap_data.values()) if heatmap_data else 0,
            'hours': list(range(24)),
        })
        
        return context


class AttendanceHeatmapCSVView(StaffOrAboveRequiredMixin, TemplateView):
    """Export attendance heatmap as CSV"""
    
    def get(self, request, *args, **kwargs):
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        attendances = Attendance.objects.filter(
            check_in__date__gte=start_date,
            check_in__date__lte=end_date
        ).select_related('trainee').order_by('check_in')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_heatmap_{start_date}_{end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Attendance Heatmap Report', f'{start_date} to {end_date}'])
        writer.writerow([])
        writer.writerow(['Date', 'Day of Week', 'Hour', 'Trainee', 'Check-in Time', 'Check-out Time', 'Duration (minutes)'])
        
        for attendance in attendances:
            writer.writerow([
                attendance.check_in.date(),
                attendance.check_in.strftime('%A'),
                attendance.check_in.hour,
                attendance.trainee.get_full_name() or attendance.trainee.username,
                attendance.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_out else 'N/A',
                attendance.duration if attendance.duration else 'N/A'
            ])
        
        writer.writerow([])
        writer.writerow(['Total Attendances', attendances.count()])
        
        return response


class AttendanceHeatmapPDFView(StaffOrAboveRequiredMixin, TemplateView):
    """Export attendance heatmap as PDF"""
    
    def get(self, request, *args, **kwargs):
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        attendances = Attendance.objects.filter(
            check_in__date__gte=start_date,
            check_in__date__lte=end_date
        ).select_related('trainee').order_by('check_in')
        
        # Build heatmap data
        heatmap_data = {}
        for attendance in attendances:
            date = attendance.check_in.date()
            hour = attendance.check_in.hour
            day_of_week = date.weekday()
            key = (day_of_week, hour)
            heatmap_data[key] = heatmap_data.get(key, 0) + 1
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
        )
        
        # Title
        elements.append(Paragraph('Attendance Heatmap Report', title_style))
        elements.append(Paragraph(f'Period: {start_date} to {end_date}', styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary
        elements.append(Paragraph(f'Total Attendances: {attendances.count()}', styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Daily breakdown
        daily_breakdown = attendances.annotate(
            date=TruncDate('check_in')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        if daily_breakdown.exists():
            table_data = [['Date', 'Day of Week', 'Attendance Count']]
            for day in daily_breakdown:
                date_obj = day['date']
                table_data.append([
                    date_obj.strftime('%Y-%m-%d'),
                    date_obj.strftime('%A'),
                    str(day['count'])
                ])
            
            table = Table(table_data, colWidths=[2*inch, 2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            elements.append(table)
        
        doc.build(elements)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="attendance_heatmap_{start_date}_{end_date}.pdf"'
        response.write(buffer.getvalue())
        buffer.close()
        return response


class TrainerUtilizationView(StaffOrAboveRequiredMixin, TemplateView):
    """Trainer utilization report"""
    template_name = 'reports/trainer_utilization.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from query params
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Get all trainers
        trainers = User.objects.filter(role=User.Role.TRAINER)
        
        trainer_stats = []
        for trainer in trainers:
            # Active assignments
            active_assignments = TrainerTraineeAssignment.objects.filter(
                trainer=trainer,
                is_active=True
            ).count()
            
            # Training sessions in period
            sessions = TrainingSession.objects.filter(
                trainer=trainer,
                session_date__gte=start_date,
                session_date__lte=end_date
            )
            
            total_sessions = sessions.count()
            completed_sessions = sessions.filter(status=TrainingSession.Status.COMPLETED).count()
            cancelled_sessions = sessions.filter(status=TrainingSession.Status.CANCELLED).count()
            
            # Calculate total hours
            total_hours = 0
            for session in sessions.filter(status=TrainingSession.Status.COMPLETED):
                total_hours += session.duration_minutes / 60
            
            # Availability hours (simplified - count available slots)
            availability_slots = trainer.availabilities.filter(is_available=True).count()
            
            # Utilization rate (sessions / available slots, capped at 100%)
            utilization_rate = 0
            if availability_slots > 0:
                utilization_rate = min((total_sessions / (availability_slots * 4)) * 100, 100)  # Rough estimate
            
            trainer_stats.append({
                'trainer': trainer,
                'active_assignments': active_assignments,
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'cancelled_sessions': cancelled_sessions,
                'total_hours': round(total_hours, 2),
                'availability_slots': availability_slots,
                'utilization_rate': round(utilization_rate, 2),
            })
        
        # Sort by utilization rate
        trainer_stats.sort(key=lambda x: x['utilization_rate'], reverse=True)
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'trainer_stats': trainer_stats,
            'total_trainers': trainers.count(),
        })
        
        return context


class TrainerUtilizationCSVView(StaffOrAboveRequiredMixin, TemplateView):
    """Export trainer utilization as CSV"""
    
    def get(self, request, *args, **kwargs):
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        trainers = User.objects.filter(role=User.Role.TRAINER)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="trainer_utilization_{start_date}_{end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Trainer Utilization Report', f'{start_date} to {end_date}'])
        writer.writerow([])
        writer.writerow(['Trainer', 'Active Assignments', 'Total Sessions', 'Completed Sessions', 'Cancelled Sessions', 'Total Hours', 'Utilization Rate %'])
        
        for trainer in trainers:
            active_assignments = TrainerTraineeAssignment.objects.filter(
                trainer=trainer,
                is_active=True
            ).count()
            
            sessions = TrainingSession.objects.filter(
                trainer=trainer,
                session_date__gte=start_date,
                session_date__lte=end_date
            )
            
            total_sessions = sessions.count()
            completed_sessions = sessions.filter(status=TrainingSession.Status.COMPLETED).count()
            cancelled_sessions = sessions.filter(status=TrainingSession.Status.CANCELLED).count()
            
            total_hours = 0
            for session in sessions.filter(status=TrainingSession.Status.COMPLETED):
                total_hours += session.duration_minutes / 60
            
            availability_slots = trainer.availabilities.filter(is_available=True).count()
            utilization_rate = 0
            if availability_slots > 0:
                utilization_rate = min((total_sessions / (availability_slots * 4)) * 100, 100)
            
            writer.writerow([
                trainer.get_full_name() or trainer.username,
                active_assignments,
                total_sessions,
                completed_sessions,
                cancelled_sessions,
                f'{total_hours:.2f}',
                f'{utilization_rate:.2f}'
            ])
        
        return response


class TrainerUtilizationPDFView(StaffOrAboveRequiredMixin, TemplateView):
    """Export trainer utilization as PDF"""
    
    def get(self, request, *args, **kwargs):
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
        else:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        trainers = User.objects.filter(role=User.Role.TRAINER)
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
        )
        
        # Title
        elements.append(Paragraph('Trainer Utilization Report', title_style))
        elements.append(Paragraph(f'Period: {start_date} to {end_date}', styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Trainer stats table
        table_data = [['Trainer', 'Active Assignments', 'Total Sessions', 'Completed', 'Cancelled', 'Total Hours', 'Utilization %']]
        
        for trainer in trainers:
            active_assignments = TrainerTraineeAssignment.objects.filter(
                trainer=trainer,
                is_active=True
            ).count()
            
            sessions = TrainingSession.objects.filter(
                trainer=trainer,
                session_date__gte=start_date,
                session_date__lte=end_date
            )
            
            total_sessions = sessions.count()
            completed_sessions = sessions.filter(status=TrainingSession.Status.COMPLETED).count()
            cancelled_sessions = sessions.filter(status=TrainingSession.Status.CANCELLED).count()
            
            total_hours = 0
            for session in sessions.filter(status=TrainingSession.Status.COMPLETED):
                total_hours += session.duration_minutes / 60
            
            availability_slots = trainer.availabilities.filter(is_available=True).count()
            utilization_rate = 0
            if availability_slots > 0:
                utilization_rate = min((total_sessions / (availability_slots * 4)) * 100, 100)
            
            table_data.append([
                trainer.get_full_name() or trainer.username,
                str(active_assignments),
                str(total_sessions),
                str(completed_sessions),
                str(cancelled_sessions),
                f'{total_hours:.2f}',
                f'{utilization_rate:.2f}%'
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(table)
        
        doc.build(elements)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="trainer_utilization_{start_date}_{end_date}.pdf"'
        response.write(buffer.getvalue())
        buffer.close()
        return response


class MemberRetentionView(StaffOrAboveRequiredMixin, TemplateView):
    """Member retention rate report"""
    template_name = 'reports/member_retention.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all subscriptions
        all_subscriptions = Subscription.objects.all().order_by('created_at')
        
        # Calculate retention metrics
        total_members = User.objects.filter(role=User.Role.TRAINEE).count()
        active_subscriptions = Subscription.objects.filter(status=Subscription.Status.ACTIVE).count()
        expired_subscriptions = Subscription.objects.filter(status=Subscription.Status.EXPIRED).count()
        cancelled_subscriptions = Subscription.objects.filter(status=Subscription.Status.CANCELLED).count()
        
        # Calculate retention rate (active / total ever subscribed)
        total_ever_subscribed = all_subscriptions.values('user').distinct().count()
        retention_rate = 0
        if total_ever_subscribed > 0:
            retention_rate = (active_subscriptions / total_ever_subscribed) * 100
        
        # Monthly retention trend
        monthly_data = []
        current_date = timezone.now().date()
        for i in range(12, -1, -1):  # Last 12 months
            month_start = (current_date.replace(day=1) - timedelta(days=30*i)).replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)
            
            # Active at start of month
            active_at_start = Subscription.objects.filter(
                status=Subscription.Status.ACTIVE,
                start_date__lt=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                end_date__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time()))
            ).count()
            
            # New subscriptions in month
            new_in_month = Subscription.objects.filter(
                created_at__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                created_at__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            # Expired in month
            expired_in_month = Subscription.objects.filter(
                status=Subscription.Status.EXPIRED,
                end_date__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                end_date__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            # Cancelled in month
            cancelled_in_month = Subscription.objects.filter(
                status=Subscription.Status.CANCELLED,
                updated_at__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                updated_at__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            # Active at end of month
            active_at_end = Subscription.objects.filter(
                status=Subscription.Status.ACTIVE,
                start_date__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time())),
                end_date__gte=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            monthly_retention = 0
            if active_at_start > 0:
                monthly_retention = ((active_at_start - expired_in_month - cancelled_in_month + new_in_month) / active_at_start) * 100
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%B %Y'),
                'active_at_start': active_at_start,
                'new_subscriptions': new_in_month,
                'expired': expired_in_month,
                'cancelled': cancelled_in_month,
                'active_at_end': active_at_end,
                'retention_rate': round(monthly_retention, 2),
            })
        
        # Churn rate
        total_churned = expired_subscriptions + cancelled_subscriptions
        churn_rate = 0
        if total_ever_subscribed > 0:
            churn_rate = (total_churned / total_ever_subscribed) * 100
        
        context.update({
            'total_members': total_members,
            'total_ever_subscribed': total_ever_subscribed,
            'active_subscriptions': active_subscriptions,
            'expired_subscriptions': expired_subscriptions,
            'cancelled_subscriptions': cancelled_subscriptions,
            'retention_rate': round(retention_rate, 2),
            'churn_rate': round(churn_rate, 2),
            'monthly_data': monthly_data,
        })
        
        return context


class MemberRetentionCSVView(StaffOrAboveRequiredMixin, TemplateView):
    """Export member retention as CSV"""
    
    def get(self, request, *args, **kwargs):
        all_subscriptions = Subscription.objects.all().order_by('created_at')
        total_members = User.objects.filter(role=User.Role.TRAINEE).count()
        active_subscriptions = Subscription.objects.filter(status=Subscription.Status.ACTIVE).count()
        expired_subscriptions = Subscription.objects.filter(status=Subscription.Status.EXPIRED).count()
        cancelled_subscriptions = Subscription.objects.filter(status=Subscription.Status.CANCELLED).count()
        total_ever_subscribed = all_subscriptions.values('user').distinct().count()
        
        retention_rate = 0
        if total_ever_subscribed > 0:
            retention_rate = (active_subscriptions / total_ever_subscribed) * 100
        
        total_churned = expired_subscriptions + cancelled_subscriptions
        churn_rate = 0
        if total_ever_subscribed > 0:
            churn_rate = (total_churned / total_ever_subscribed) * 100
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="member_retention_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Member Retention Report'])
        writer.writerow([])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Members', total_members])
        writer.writerow(['Total Ever Subscribed', total_ever_subscribed])
        writer.writerow(['Active Subscriptions', active_subscriptions])
        writer.writerow(['Expired Subscriptions', expired_subscriptions])
        writer.writerow(['Cancelled Subscriptions', cancelled_subscriptions])
        writer.writerow(['Retention Rate %', f'{retention_rate:.2f}'])
        writer.writerow(['Churn Rate %', f'{churn_rate:.2f}'])
        writer.writerow([])
        writer.writerow(['Monthly Retention Data'])
        writer.writerow(['Month', 'Active at Start', 'New Subscriptions', 'Expired', 'Cancelled', 'Active at End', 'Retention Rate %'])
        
        current_date = timezone.now().date()
        for i in range(12, -1, -1):
            month_start = (current_date.replace(day=1) - timedelta(days=30*i)).replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)
            
            active_at_start = Subscription.objects.filter(
                status=Subscription.Status.ACTIVE,
                start_date__lt=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                end_date__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time()))
            ).count()
            
            new_in_month = Subscription.objects.filter(
                created_at__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                created_at__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            expired_in_month = Subscription.objects.filter(
                status=Subscription.Status.EXPIRED,
                end_date__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                end_date__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            cancelled_in_month = Subscription.objects.filter(
                status=Subscription.Status.CANCELLED,
                updated_at__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                updated_at__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            active_at_end = Subscription.objects.filter(
                status=Subscription.Status.ACTIVE,
                start_date__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time())),
                end_date__gte=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            monthly_retention = 0
            if active_at_start > 0:
                monthly_retention = ((active_at_start - expired_in_month - cancelled_in_month + new_in_month) / active_at_start) * 100
            
            writer.writerow([
                month_start.strftime('%Y-%m'),
                active_at_start,
                new_in_month,
                expired_in_month,
                cancelled_in_month,
                active_at_end,
                f'{monthly_retention:.2f}'
            ])
        
        return response


class MemberRetentionPDFView(StaffOrAboveRequiredMixin, TemplateView):
    """Export member retention as PDF"""
    
    def get(self, request, *args, **kwargs):
        all_subscriptions = Subscription.objects.all().order_by('created_at')
        total_members = User.objects.filter(role=User.Role.TRAINEE).count()
        active_subscriptions = Subscription.objects.filter(status=Subscription.Status.ACTIVE).count()
        expired_subscriptions = Subscription.objects.filter(status=Subscription.Status.EXPIRED).count()
        cancelled_subscriptions = Subscription.objects.filter(status=Subscription.Status.CANCELLED).count()
        total_ever_subscribed = all_subscriptions.values('user').distinct().count()
        
        retention_rate = 0
        if total_ever_subscribed > 0:
            retention_rate = (active_subscriptions / total_ever_subscribed) * 100
        
        total_churned = expired_subscriptions + cancelled_subscriptions
        churn_rate = 0
        if total_ever_subscribed > 0:
            churn_rate = (total_churned / total_ever_subscribed) * 100
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
        )
        
        # Title
        elements.append(Paragraph('Member Retention Report', title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary
        summary_data = [
            ['Total Members', str(total_members)],
            ['Total Ever Subscribed', str(total_ever_subscribed)],
            ['Active Subscriptions', str(active_subscriptions)],
            ['Expired Subscriptions', str(expired_subscriptions)],
            ['Cancelled Subscriptions', str(cancelled_subscriptions)],
            ['Retention Rate', f'{retention_rate:.2f}%'],
            ['Churn Rate', f'{churn_rate:.2f}%'],
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Monthly data
        elements.append(Paragraph('Monthly Retention Data', styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        table_data = [['Month', 'Active Start', 'New', 'Expired', 'Cancelled', 'Active End', 'Retention %']]
        
        current_date = timezone.now().date()
        for i in range(12, -1, -1):
            month_start = (current_date.replace(day=1) - timedelta(days=30*i)).replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)
            
            active_at_start = Subscription.objects.filter(
                status=Subscription.Status.ACTIVE,
                start_date__lt=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                end_date__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time()))
            ).count()
            
            new_in_month = Subscription.objects.filter(
                created_at__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                created_at__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            expired_in_month = Subscription.objects.filter(
                status=Subscription.Status.EXPIRED,
                end_date__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                end_date__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            cancelled_in_month = Subscription.objects.filter(
                status=Subscription.Status.CANCELLED,
                updated_at__gte=timezone.make_aware(datetime.combine(month_start, datetime.min.time())),
                updated_at__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            active_at_end = Subscription.objects.filter(
                status=Subscription.Status.ACTIVE,
                start_date__lt=timezone.make_aware(datetime.combine(month_end, datetime.min.time())),
                end_date__gte=timezone.make_aware(datetime.combine(month_end, datetime.min.time()))
            ).count()
            
            monthly_retention = 0
            if active_at_start > 0:
                monthly_retention = ((active_at_start - expired_in_month - cancelled_in_month + new_in_month) / active_at_start) * 100
            
            table_data.append([
                month_start.strftime('%Y-%m'),
                str(active_at_start),
                str(new_in_month),
                str(expired_in_month),
                str(cancelled_in_month),
                str(active_at_end),
                f'{monthly_retention:.2f}%'
            ])
        
        table = Table(table_data, colWidths=[1*inch, 0.8*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(table)
        
        doc.build(elements)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="member_retention_report.pdf"'
        response.write(buffer.getvalue())
        buffer.close()
        return response

