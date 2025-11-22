"""
ماژول تحلیل هوشمند داده‌های HSE
این ماژول داده‌های آنومالی‌ها و حوادث را تحلیل می‌کند و
به صورت خودکار ریسک‌های بالقوه را شناسایی می‌کند
"""
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from anomalis.models import Anomaly, AnomalyDescription, Location, LocationSection
from hse_incidents.models import IncidentReport, InjuryType
from accounts.models import Position
import jdatetime


def get_high_frequency_hazards(days=90, min_count=3):
    """
    شناسایی خطراتی که در X روز گذشته بیش از Y بار گزارش شده‌اند
    
    Returns:
        QuerySet: لیست خطرات پرتکرار با تعداد و درصد
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    frequent_hazards = Anomaly.objects.filter(
        created_at__gte=cutoff_date
    ).values(
        'anomalydescription__id',
        'anomalydescription__description',
        'location__name'
    ).annotate(
        total_count=Count('id'),
        unsafe_count=Count('id', filter=Q(action=False)),
        high_priority_count=Count('id', filter=Q(priority__priority='زیاد'))
    ).filter(
        total_count__gte=min_count
    ).order_by('-total_count')
    
    return frequent_hazards


def get_incident_based_hazards(months=12):
    """
    استخراج خطرات بر اساس حوادث واقعی
    
    Returns:
        dict: اطلاعات حوادث و نوع آسیب‌ها
    """
    cutoff_date = timezone.now() - timedelta(days=months * 30)
    
    incidents = IncidentReport.objects.filter(
        incident_date__gte=cutoff_date
    )
    
    # تحلیل نوع آسیب‌ها
    injury_stats = []
    for injury_type in InjuryType.objects.all():
        count = incidents.filter(injury_type=injury_type).count()
        if count > 0:
            injury_stats.append({
                'injury_type': injury_type,
                'count': count,
                'severity_score': calculate_severity_from_injury(injury_type.name)
            })
    
    # تحلیل مکان‌ها
    location_stats = incidents.values(
        'location__name',
        'section__section'
    ).annotate(
        incident_count=Count('id')
    ).order_by('-incident_count')
    
    return {
        'injury_stats': injury_stats,
        'location_stats': location_stats,
        'total_incidents': incidents.count(),
    }


def calculate_severity_from_injury(injury_name):
    """
    تخمین شدت بر اساس نوع آسیب
    """
    # ماتریس شدت بر اساس نوع آسیب
    severity_matrix = {
        'مرگ': 5,
        'فوت': 5,
        'قطع عضو': 4,
        'شکستگی': 3,
        'سوختگی شدید': 4,
        'سوختگی': 3,
        'جراحت عمیق': 3,
        'کوفتگی': 2,
        'خراش': 1,
        'ضربه': 2,
    }
    
    injury_lower = injury_name.lower()
    for key, value in severity_matrix.items():
        if key in injury_lower:
            return value
    
    return 2  # مقدار پیش‌فرض


def suggest_probability_from_anomalies(hazard_id, location_id=None):
    """
    پیشنهاد احتمال وقوع بر اساس تعداد آنومالی‌ها
    
    Args:
        hazard_id: شناسه خطر
        location_id: شناسه محل (اختیاری)
    
    Returns:
        int: احتمال پیشنهادی (1-5)
    """
    # آنومالی‌های 6 ماه گذشته
    cutoff_date = timezone.now() - timedelta(days=180)
    
    query = Anomaly.objects.filter(
        anomalydescription_id=hazard_id,
        created_at__gte=cutoff_date
    )
    
    if location_id:
        query = query.filter(location_id=location_id)
    
    count = query.count()
    
    # ماتریس تبدیل تعداد به احتمال
    if count >= 10:
        return 5  # خیلی زیاد
    elif count >= 6:
        return 4  # زیاد
    elif count >= 3:
        return 3  # متوسط
    elif count >= 1:
        return 2  # کم
    else:
        return 1  # خیلی کم


def get_position_risk_suggestions(position):
    """
    پیشنهاد ریسک‌های احتمالی برای یک شغل بر اساس داده‌های تاریخی
    
    Args:
        position: شیء Position
    
    Returns:
        list: لیست پیشنهادات ریسک
    """
    suggestions = []
    
    # آنومالی‌های مرتبط با این شغل (از طریق بخش‌های سازمانی)
    related_anomalies = Anomaly.objects.filter(
        followup__position=position
    ).values(
        'anomalydescription__id',
        'anomalydescription__description',
        'location__name'
    ).annotate(
        count=Count('id')
    ).filter(count__gte=2).order_by('-count')[:10]
    
    for anomaly in related_anomalies:
        probability = suggest_probability_from_anomalies(
            anomaly['anomalydescription__id'],
            location_id=None
        )
        
        suggestions.append({
            'hazard_id': anomaly['anomalydescription__id'],
            'hazard_description': anomaly['anomalydescription__description'],
            'location': anomaly['location__name'],
            'frequency': anomaly['count'],
            'suggested_probability': probability,
            'source': 'anomaly_history',
        })
    
    # حوادث مرتبط
    incidents = IncidentReport.objects.filter(
        involved_person__position=position
    ).select_related('location', 'section')
    
    for incident in incidents[:5]:
        for injury in incident.injury_type.all():
            severity = calculate_severity_from_injury(injury.name)
            suggestions.append({
                'consequence': injury.name,
                'suggested_severity': severity,
                'location': incident.location.name if incident.location else 'نامشخص',
                'source': 'incident_history',
            })
    
    return suggestions


def get_anomaly_trend_analysis(hazard_id, months=6):
    """
    تحلیل روند آنومالی‌ها برای یک خطر خاص
    
    Returns:
        dict: داده‌های روند
    """
    cutoff_date = timezone.now() - timedelta(days=months * 30)
    
    anomalies = Anomaly.objects.filter(
        anomalydescription_id=hazard_id,
        created_at__gte=cutoff_date
    ).order_by('created_at')
    
    # گروه‌بندی بر اساس ماه
    monthly_counts = {}
    for anomaly in anomalies:
        jalali_date = jdatetime.datetime.fromgregorian(datetime=anomaly.created_at)
        month_key = f"{jalali_date.year}/{jalali_date.month:02d}"
        
        if month_key not in monthly_counts:
            monthly_counts[month_key] = {'total': 0, 'unsafe': 0}
        
        monthly_counts[month_key]['total'] += 1
        if not anomaly.action:
            monthly_counts[month_key]['unsafe'] += 1
    
    # تشخیص روند (صعودی/نزولی/ثابت)
    counts = [v['total'] for v in monthly_counts.values()]
    if len(counts) >= 3:
        if counts[-1] > counts[-2] > counts[-3]:
            trend = 'increasing'
        elif counts[-1] < counts[-2] < counts[-3]:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        trend = 'insufficient_data'
    
    return {
        'monthly_data': monthly_counts,
        'trend': trend,
        'total_count': sum(v['total'] for v in monthly_counts.values()),
        'unsafe_percentage': (sum(v['unsafe'] for v in monthly_counts.values()) / 
                             sum(v['total'] for v in monthly_counts.values()) * 100) 
                             if sum(v['total'] for v in monthly_counts.values()) > 0 else 0,
    }


def get_critical_locations():
    """
    شناسایی مکان‌های حساس بر اساس تعداد آنومالی و حادثه
    
    Returns:
        QuerySet: لیست مکان‌های پرخطر
    """
    # آنومالی‌های 3 ماه گذشته
    cutoff_date = timezone.now() - timedelta(days=90)
    
    locations = Location.objects.annotate(
        anomaly_count=Count('anomaly', filter=Q(anomaly__created_at__gte=cutoff_date)),
        unsafe_anomaly_count=Count('anomaly', filter=Q(
            anomaly__created_at__gte=cutoff_date,
            anomaly__action=False
        )),
        incident_count=Count('incidentreport', filter=Q(
            incidentreport__incident_date__gte=cutoff_date.date()
        ))
    ).filter(
        Q(anomaly_count__gte=5) | Q(incident_count__gte=1)
    ).order_by('-unsafe_anomaly_count', '-incident_count')
    
    return locations


def get_related_anomalies_for_risk(risk_assessment):
    """
    یافتن آنومالی‌های مرتبط با یک ارزیابی ریسک
    
    Args:
        risk_assessment: شیء RiskAssessment
    
    Returns:
        QuerySet: آنومالی‌های مرتبط
    """
    related_anomalies = Anomaly.objects.filter(
        anomalydescription=risk_assessment.hazard
    ).order_by('-created_at')[:10]
    
    return related_anomalies


def get_related_incidents_for_risk(risk_assessment):
    """
    یافتن حوادث مرتبط با یک ارزیابی ریسک
    
    Args:
        risk_assessment: شیء RiskAssessment
    
    Returns:
        QuerySet: حوادث مرتبط
    """
    related_incidents = IncidentReport.objects.filter(
        injury_type=risk_assessment.consequence
    ).order_by('-incident_date')[:10]
    
    return related_incidents


def generate_risk_insights(risk_assessment):
    """
    تولید بینش‌های هوشمند برای یک ریسک
    
    Args:
        risk_assessment: شیء RiskAssessment
    
    Returns:
        dict: بینش‌ها و پیشنهادات
    """
    insights = {
        'anomaly_trend': get_anomaly_trend_analysis(risk_assessment.hazard.id),
        'related_anomalies': get_related_anomalies_for_risk(risk_assessment),
        'related_incidents': get_related_incidents_for_risk(risk_assessment),
        'suggestions': [],
    }
    
    # پیشنهادات بر اساس روند
    trend = insights['anomaly_trend']['trend']
    if trend == 'increasing':
        insights['suggestions'].append({
            'type': 'warning',
            'message': '⚠️ روند این خطر رو به افزایش است. توصیه می‌شود اقدامات اصلاحی فوری انجام شود.'
        })
    
    # پیشنهاد بر اساس درصد ناایمن
    unsafe_percentage = insights['anomaly_trend']['unsafe_percentage']
    if unsafe_percentage > 50:
        insights['suggestions'].append({
            'type': 'danger',
            'message': f'🔴 {unsafe_percentage:.1f}% آنومالی‌های این خطر ناایمن بوده‌اند. نیاز به بازبینی کنترل‌های موجود'
        })
    
    return insights
