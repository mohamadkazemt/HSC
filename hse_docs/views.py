# hse_docs/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .models import Document, TopicCategory
from .forms import DocumentForm, DocumentSearchForm
from accounts.models import Section, UnitGroup


def view_section(request, id):
    """Public view: Show topic folders for a specific Section"""
    section = get_object_or_404(Section, pk=id)
    
    # Get all topic categories that have documents in this section
    topics = TopicCategory.objects.filter(
        documents__section=section,
        documents__is_active=True
    ).annotate(
        document_count=Count('documents', filter=Q(documents__section=section, documents__is_active=True))
    ).filter(document_count__gt=0).distinct().order_by('title')
    
    context = {
        'folder_type': 'section',
        'folder_object': section,
        'topics': topics,
    }
    return render(request, 'hse_docs/public_section_group_folders.html', context)


def view_section_topic(request, section_id, topic_slug):
    """Public view: Documents for a specific TopicCategory in a specific Section"""
    section = get_object_or_404(Section, pk=section_id)
    topic = get_object_or_404(TopicCategory, slug=topic_slug)
    
    documents = Document.objects.filter(
        section=section,
        topic_category=topic,
        is_active=True
    ).select_related('topic_category', 'section', 'unit_group').order_by('-uploaded_at')
    
    # Search functionality
    search_form = DocumentSearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data.get('query'):
        query = search_form.cleaned_data['query']
        documents = documents.filter(title__icontains=query)
    
    # Pagination
    paginator = Paginator(documents, 12)
    page = request.GET.get('page', 1)
    try:
        documents_page = paginator.page(page)
    except:
        documents_page = paginator.page(1)
    
    context = {
        'folder_type': 'section_topic',
        'folder_object': section,
        'topic': topic,
        'documents': documents_page,
        'search_form': search_form,
        'view_context': 'section',  # For badge display
    }
    return render(request, 'hse_docs/public_folder_detail.html', context)


def view_group(request, id):
    """Public view: Show topic folders for a specific UnitGroup"""
    unit_group = get_object_or_404(UnitGroup, pk=id)
    
    # Get all topic categories that have documents in this group
    topics = TopicCategory.objects.filter(
        documents__unit_group=unit_group,
        documents__is_active=True
    ).annotate(
        document_count=Count('documents', filter=Q(documents__unit_group=unit_group, documents__is_active=True))
    ).filter(document_count__gt=0).distinct().order_by('title')
    
    context = {
        'folder_type': 'group',
        'folder_object': unit_group,
        'topics': topics,
    }
    return render(request, 'hse_docs/public_section_group_folders.html', context)


def view_group_topic(request, group_id, topic_slug):
    """Public view: Documents for a specific TopicCategory in a specific UnitGroup"""
    unit_group = get_object_or_404(UnitGroup, pk=group_id)
    topic = get_object_or_404(TopicCategory, slug=topic_slug)
    
    documents = Document.objects.filter(
        unit_group=unit_group,
        topic_category=topic,
        is_active=True
    ).select_related('topic_category', 'section', 'unit_group').order_by('-uploaded_at')
    
    # Search functionality
    search_form = DocumentSearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data.get('query'):
        query = search_form.cleaned_data['query']
        documents = documents.filter(title__icontains=query)
    
    # Pagination
    paginator = Paginator(documents, 12)
    page = request.GET.get('page', 1)
    try:
        documents_page = paginator.page(page)
    except:
        documents_page = paginator.page(1)
    
    context = {
        'folder_type': 'group_topic',
        'folder_object': unit_group,
        'topic': topic,
        'documents': documents_page,
        'search_form': search_form,
        'view_context': 'group',  # For badge display
    }
    return render(request, 'hse_docs/public_folder_detail.html', context)


def view_topic(request, slug):
    """Public view: All documents for a specific TopicCategory"""
    topic = get_object_or_404(TopicCategory, slug=slug)
    documents = Document.objects.filter(
        topic_category=topic,
        is_active=True
    ).select_related('topic_category', 'section', 'unit_group').order_by('-uploaded_at')
    
    # Search functionality
    search_form = DocumentSearchForm(request.GET)
    if search_form.is_valid() and search_form.cleaned_data.get('query'):
        query = search_form.cleaned_data['query']
        documents = documents.filter(title__icontains=query)
    
    # Pagination
    paginator = Paginator(documents, 12)
    page = request.GET.get('page', 1)
    try:
        documents_page = paginator.page(page)
    except:
        documents_page = paginator.page(1)
    
    context = {
        'folder_type': 'topic',
        'folder_object': topic,
        'documents': documents_page,
        'search_form': search_form,
        'view_context': 'topic',  # For badge display
    }
    return render(request, 'hse_docs/public_folder_detail.html', context)


def public_folder_list(request):
    """Public view: List all topic categories as folders"""
    topics = TopicCategory.objects.all().annotate(
        document_count=Count('documents', filter=Q(documents__is_active=True))
    ).filter(document_count__gt=0).order_by('title')
    
    context = {
        'topics': topics,
    }
    return render(request, 'hse_docs/public_folder_list.html', context)


def document_detail(request, pk):
    """Public view: Individual document detail"""
    document = get_object_or_404(Document, pk=pk, is_active=True)
    
    context = {
        'document': document,
    }
    return render(request, 'hse_docs/document_detail.html', context)


# Admin Views
@staff_member_required
def admin_dashboard(request):
    """Admin dashboard for HSE Documents management"""
    documents = Document.objects.all().select_related(
        'topic_category', 'section', 'unit_group', 'uploaded_by'
    ).order_by('-uploaded_at')
    
    # Statistics
    stats = {
        'total_documents': Document.objects.filter(is_active=True).count(),
        'total_topics': TopicCategory.objects.count(),
        'total_sections': Section.objects.filter(documents__is_active=True).distinct().count(),
        'total_groups': UnitGroup.objects.filter(documents__is_active=True).distinct().count(),
    }
    
    # Recent documents
    recent_documents = documents[:10]
    
    context = {
        'documents': recent_documents,
        'stats': stats,
    }
    return render(request, 'hse_docs/admin/dashboard.html', context)


@staff_member_required
def upload_document(request):
    """Admin view: Upload new document"""
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, f'سند "{document.title}" با موفقیت بارگذاری شد.')
            return redirect('hse_docs:admin_dashboard')
    else:
        form = DocumentForm()
    
    context = {
        'form': form,
    }
    return render(request, 'hse_docs/admin/upload_document.html', context)


@staff_member_required
def edit_document(request, pk):
    """Admin view: Edit existing document"""
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, f'سند "{document.title}" با موفقیت بروزرسانی شد.')
            return redirect('hse_docs:admin_dashboard')
    else:
        form = DocumentForm(instance=document)
    
    context = {
        'form': form,
        'document': document,
    }
    return render(request, 'hse_docs/admin/edit_document.html', context)


@staff_member_required
def qr_center(request):
    """Admin QR Code Generation Center"""
    sections = Section.objects.all()
    unit_groups = UnitGroup.objects.all()
    topic_categories = TopicCategory.objects.all()
    
    context = {
        'sections': sections,
        'unit_groups': unit_groups,
        'topic_categories': topic_categories,
    }
    return render(request, 'hse_docs/admin/qr_center.html', context)


@staff_member_required
def generate_qr_code(request, qr_type, obj_id):
    """Generate QR code image for Section, UnitGroup, TopicCategory, or Main Folder List"""
    from django.http import HttpResponse
    import qrcode
    
    # Build URL based on type
    if qr_type == 'main' or qr_type == 'folder_list':
        url = reverse('hse_docs:public_folder_list')
    elif qr_type == 'section':
        url = reverse('hse_docs:view_section', kwargs={'id': obj_id})
    elif qr_type == 'group':
        url = reverse('hse_docs:view_group', kwargs={'id': obj_id})
    elif qr_type == 'topic':
        url = reverse('hse_docs:view_topic', kwargs={'slug': obj_id})
    else:
        return HttpResponse("Invalid QR type", status=400)
    
    # Build absolute URL
    absolute_url = request.build_absolute_uri(url)
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(absolute_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Return as PNG
    response = HttpResponse(content_type='image/png')
    img.save(response, 'PNG')
    return response


@staff_member_required
def document_list(request):
    """List view for all documents (alias for admin_dashboard)"""
    return admin_dashboard(request)


@staff_member_required
def topic_list(request):
    """List view for topic categories"""
    topics = TopicCategory.objects.all().prefetch_related('documents').order_by('title')
    
    # Add document count to each topic
    for topic in topics:
        topic.doc_count = topic.documents.filter(is_active=True).count()
    
    context = {
        'topics': topics,
    }
    return render(request, 'hse_docs/admin/topic_list.html', context)
