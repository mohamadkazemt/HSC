from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Q
from .models import Section, Part, UnitGroup, Position, UserProfile
from functools import wraps
from django.core.exceptions import PermissionDenied
import json


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@superuser_required
def organization_chart(request):
    """Display hierarchical organizational chart"""
    section_id = request.GET.get('section')
    show_personnel = request.GET.get('show_personnel', 'false') == 'true'
    
    # Get all sections
    sections = Section.objects.all().order_by('name')
    
    # Filter by section if specified
    sections_qs = sections
    if section_id:
        try:
            sections_qs = sections.filter(id=int(section_id))
        except (ValueError, TypeError):
            pass
    
    # Build hierarchical data structure
    chart_data = []
    
    for section in sections_qs:
        section_personnel_count = UserProfile.objects.filter(section=section).count()
        
        # Create root node for section
        section_node = {
            'id': f'section_{section.id}',
            'name': section.name,
            'title': f'بخش: {section.name}',
            'count': section_personnel_count,
            'type': 'section',
            'parent': None,
            'children': []
        }
        
        # Get parts for this section
        parts = Part.objects.filter(section=section).order_by('name')
        
        for part in parts:
            part_personnel_count = UserProfile.objects.filter(
                section=section,
                part=part
            ).count()
            
            part_node = {
                'id': f'part_{part.id}',
                'name': part.name,
                'title': f'قسمت: {part.name}',
                'count': part_personnel_count,
                'type': 'part',
                'parent': section_node['id'],
                'children': []
            }
            
            # Get unit groups for this part
            unit_groups = UnitGroup.objects.filter(part=part).order_by('name')
            
            for unit_group in unit_groups:
                unit_group_personnel_count = UserProfile.objects.filter(
                    section=section,
                    part=part,
                    unit_group=unit_group
                ).count()
                
                unit_group_node = {
                    'id': f'unit_group_{unit_group.id}',
                    'name': unit_group.name,
                    'title': f'گروه: {unit_group.name}',
                    'count': unit_group_personnel_count,
                    'type': 'unit_group',
                    'parent': part_node['id'],
                    'children': []
                }
                
                # Get positions for this unit group
                positions = Position.objects.filter(unit_group=unit_group).order_by('name')
                
                for position in positions:
                    position_personnel_count = UserProfile.objects.filter(
                        section=section,
                        part=part,
                        unit_group=unit_group,
                        position=position
                    ).count()
                    
                    position_node = {
                        'id': f'position_{position.id}',
                        'name': position.name,
                        'title': f'سمت: {position.name}',
                        'count': position_personnel_count,
                        'type': 'position',
                        'parent': unit_group_node['id'],
                        'children': []
                    }
                    
                    # Get personnel for this position if enabled
                    if show_personnel:
                        personnel = UserProfile.objects.filter(
                            section=section,
                            part=part,
                            unit_group=unit_group,
                            position=position
                        ).select_related('user').order_by('user__last_name', 'user__first_name')
                        
                        for person in personnel:
                            person_node = {
                                'id': f'person_{person.id}',
                                'name': person.user.get_full_name() or person.user.username,
                                'title': f'{person.user.get_full_name() or person.user.username}',
                                'count': 0,
                                'type': 'personnel',
                                'parent': position_node['id'],
                                'personnel_code': person.personnel_code or '',
                                'children': []
                            }
                            position_node['children'].append(person_node)
                    
                    unit_group_node['children'].append(position_node)
                
                part_node['children'].append(unit_group_node)
            
            section_node['children'].append(part_node)
        
        chart_data.append(section_node)
    
    # Convert nested structure to orgchart.js format
    def convert_to_orgchart_format(node):
        # Build title based on node type
        if node['type'] == 'personnel':
            title = node['name']
            if node.get('personnel_code'):
                title += f"\nکد: {node['personnel_code']}"
        else:
            title = f"{node['name']}\n({node['count']} نفر)"
        
        orgchart_node = {
            'id': node['id'],
            'title': title,
            'name': node['name'],
            'count': node['count'],
            'type': node['type']
        }
        
        # Convert children recursively
        if node['children']:
            orgchart_node['children'] = [convert_to_orgchart_format(child) for child in node['children']]
        
        return orgchart_node
    
    # Convert all section nodes
    orgchart_data = [convert_to_orgchart_format(section_node) for section_node in chart_data]
    
    # Debug: Print chart data structure
    if not orgchart_data:
        # If no data, create a placeholder
        orgchart_data = [{
            'id': 'empty',
            'title': 'داده‌ای وجود ندارد\n(0 نفر)',
            'name': 'داده‌ای وجود ندارد',
            'count': 0,
            'type': 'empty'
        }]
    
    context = {
        'chart_data': orgchart_data,  # Pass as Python list, convert to JSON in template
        'chart_data_json': json.dumps(orgchart_data, ensure_ascii=False),  # For template
        'sections': sections,
        'selected_section': int(section_id) if section_id else None,
        'show_personnel': show_personnel,
    }
    
    return render(request, 'accounts/organization_chart.html', context)

