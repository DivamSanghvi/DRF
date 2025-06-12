from celery import shared_task
from .services import pdf_processor
from .models import Resource, Project
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_pdf_task(resource_id):
    """
    Celery task to process a PDF file and create vector store
    """
    try:
        # Get the resource
        resource = Resource.objects.get(id=resource_id)
        project = resource.project
        # Set status to processing
        resource.status = 'processing'
        resource.save(update_fields=['status'])
        # Process the PDF
        pdf_path = resource.pdf_file.path
        docs = pdf_processor.process_pdf(pdf_path)
        if docs:
            # Create or update vector store
            pdf_processor.save_or_update_vector_store(docs, project.id)
            resource.status = 'complete'
            resource.save(update_fields=['status'])
            logger.info(f"Successfully processed PDF for resource {resource_id}")
            return True
        else:
            resource.status = 'failed'
            resource.save(update_fields=['status'])
            logger.error(f"No documents extracted from PDF for resource {resource_id}")
            return False
    except Resource.DoesNotExist:
        logger.error(f"Resource {resource_id} not found")
        return False
    except Exception as e:
        try:
            resource = Resource.objects.get(id=resource_id)
            resource.status = 'failed'
            resource.save(update_fields=['status'])
        except Exception:
            pass
        logger.error(f"Error processing PDF for resource {resource_id}: {str(e)}")
        return False

@shared_task
def process_multiple_pdfs_task(resource_ids):
    """
    Celery task to process multiple PDF files
    """
    results = []
    for resource_id in resource_ids:
        result = process_pdf_task.delay(resource_id)
        results.append(result)
    return results 