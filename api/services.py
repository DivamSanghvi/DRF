import os
import fitz
import numpy as np
import cv2
import easyocr
from langdetect import detect
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store_dir = "vector_stores"
        os.makedirs(self.vector_store_dir, exist_ok=True)
        self.vector_stores = {}
        self.allow_dangerous_deserialization = True
        logger.info("PDFProcessor initialized with vector store directory: %s", self.vector_store_dir)

    def extract_text_pymupdf(self, pdf_path, pages=None):
        try:
            document = fitz.open(pdf_path)
            text = ""
            max_pages = pages if pages else len(document)
            for page_num in range(min(max_pages, len(document))):
                page = document.load_page(page_num)
                page_text = page.get_text("text")
                if isinstance(page_text, str):
                    text += page_text + "\n"
                else:
                    logger.warning(f"Page {page_num} returned non-string text: {type(page_text)}")
            document.close()
            return text
        except Exception as e:
            logger.error(f"Error during PyMuPDF extraction: {e}")
            return ""

    def perform_ocr_on_pdf(self, pdf_path):
        try:
            pages = convert_from_path(pdf_path, 300)
            reader = easyocr.Reader(['en', 'hi'])
            extracted_text = ""
            for page in pages:
                open_cv_image = np.array(page)[:, :, ::-1].copy()
                result = reader.readtext(open_cv_image)
                for detection in result:
                    if isinstance(detection[1], str):
                        extracted_text += detection[1] + "\n"
                    else:
                        logger.warning(f"OCR returned non-string text: {type(detection[1])}")
            return extracted_text
        except Exception as e:
            logger.error(f"Error during OCR: {e}")
            return ""

    def detect_language(self, text):
        try:
            return detect(text)
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return None

    def process_pdf(self, pdf_path):
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            # Extract text using PyMuPDF
            text = self.extract_text_pymupdf(pdf_path)
            
            # If text extraction fails or returns empty, try OCR
            if not text.strip():
                logger.info(f"Text extraction failed for {pdf_path}, trying OCR")
                text = self.perform_ocr_on_pdf(pdf_path)
            
            if not text.strip():
                logger.error(f"Failed to extract text from {pdf_path}")
                return []
            
            # Create documents from the text
            documents = self.create_documents(text)
            
            if not documents:
                logger.warning(f"No documents created from {pdf_path}")
                return []
            
            logger.info(f"Successfully processed {pdf_path}, created {len(documents)} documents")
            return documents
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return []

    def chunk_text(self, text):
        try:
            if not isinstance(text, str):
                logger.error(f"Expected string for chunking, got {type(text)}")
                return []
                
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            chunks = text_splitter.split_text(text)
            logger.info(f"Split text into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            return []

    def create_documents(self, text):
        try:
            if not isinstance(text, str):
                logger.error(f"Expected string for document creation, got {type(text)}")
                return []
                
            chunks = self.chunk_text(text)
            documents = []
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            'source': f'chunk_{i}',
                            'chunk_index': i
                        }
                    )
                    documents.append(doc)
            logger.info(f"Created {len(documents)} documents from text chunks")
            return documents
        except Exception as e:
            logger.error(f"Error creating documents: {str(e)}")
            return []

    def get_vector_store_path(self, project_id):
        return os.path.join(self.vector_store_dir, f"project_{project_id}")

    def save_or_update_vector_store(self, documents, project_id):
        try:
            if not documents:
                logger.warning(f"No documents to save for project {project_id}")
                return False

            # Create project directory if it doesn't exist
            project_dir = self.get_vector_store_path(project_id)
            os.makedirs(project_dir, exist_ok=True)
            logger.info(f"Created/verified project directory: {project_dir}")

            # Check if vector store exists
            if project_id in self.vector_stores:
                # Update existing vector store
                self.vector_stores[project_id].add_documents(documents)
                logger.info(f"Updated existing vector store for project {project_id}")
            else:
                # Create new vector store
                self.vector_stores[project_id] = FAISS.from_documents(documents, self.embeddings)
                logger.info(f"Created new vector store for project {project_id}")
            
            # Save to disk
            self.vector_stores[project_id].save_local(project_dir)
            logger.info(f"Successfully saved vector store for project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            return False

    def get_relevant_documents(self, query, project_id):
        try:
            project_dir = self.get_vector_store_path(project_id)
            logger.info(f"Getting relevant documents for project {project_id}")
            
            # Check if vector store exists in memory
            if project_id not in self.vector_stores:
                # Check if vector store exists on disk
                if os.path.exists(os.path.join(project_dir, "index.faiss")):
                    try:
                        # Load from disk
                        self.vector_stores[project_id] = FAISS.load_local(project_dir, self.embeddings)
                        logger.info(f"Loaded vector store for project {project_id} from disk")
                    except Exception as e:
                        logger.error(f"Error loading vector store from disk: {str(e)}")
                        return []
                else:
                    logger.warning(f"No vector store found for project {project_id}")
                    return []

            # Get documents from FAISS
            try:
                faiss_docs = self.vector_stores[project_id].similarity_search(query, k=3)
                logger.info(f"Retrieved {len(faiss_docs)} relevant documents for query")
                return faiss_docs
            except Exception as e:
                logger.error(f"Error during similarity search: {str(e)}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []

    def remove_resource_from_vector_store(self, project_id, resource_id):
        """Remove a resource's documents from the vector store."""
        project_store_path = self.get_vector_store_path(project_id)
        
        try:
            if os.path.exists(project_store_path):
                # Load existing vector store
                vectorstore = FAISS.load_local(project_store_path, self.embeddings)
                
                # Get all documents
                documents = [Document(page_content=doc.page_content, metadata=doc.metadata)
                           for doc in vectorstore.docstore._dict.values()]
                
                # Filter out documents from the deleted resource
                filtered_docs = [doc for doc in documents 
                               if doc.metadata.get('resource_id') != str(resource_id)]
                
                # Create new vector store with filtered documents
                if filtered_docs:
                    new_vectorstore = FAISS.from_documents(filtered_docs, self.embeddings)
                    new_vectorstore.save_local(project_store_path)
                else:
                    # If no documents left, remove the vector store directory
                    import shutil
                    shutil.rmtree(project_store_path)
                
                logger.info(f"Successfully removed resource {resource_id} from vector store")
                return True
        except Exception as e:
            logger.error(f"Error removing resource from vector store: {e}")
            return False

def capture_browser_errors(url):
    """
    Captures browser console errors using Selenium.
    
    Args:
        url (str): The URL to check for console errors
        
    Returns:
        list: List of console errors found
    """
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Enable console logging
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Store console logs
        console_errors = []
        
        try:
            # Navigate to the URL
            driver.get(url)
            
            # Wait for page to load (adjust timeout as needed)
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Get console logs
            logs = driver.get_log('browser')
            
            # Filter for errors and warnings
            for log in logs:
                if log['level'] in ['SEVERE', 'WARNING']:
                    console_errors.append({
                        'level': log['level'],
                        'message': log['message'],
                        'timestamp': log['timestamp']
                    })
                    logger.error(f"Browser Console {log['level']}: {log['message']}")
            
            return console_errors
            
        finally:
            # Always close the driver
            driver.quit()
            
    except Exception as e:
        logger.error(f"Error capturing browser console errors: {str(e)}")
        return [{
            'level': 'ERROR',
            'message': f"Failed to capture browser errors: {str(e)}",
            'timestamp': None
        }]

def check_browser_errors(url):
    """
    Checks for browser console errors and prints them to console.
    
    Args:
        url (str): The URL to check for console errors
    """
    errors = capture_browser_errors(url)
    
    if errors:
        print("\n=== Browser Console Errors ===")
        for error in errors:
            print(f"\nLevel: {error['level']}")
            print(f"Message: {error['message']}")
            if error['timestamp']:
                print(f"Timestamp: {error['timestamp']}")
        print("\n===========================")
    else:
        print("\nNo browser console errors found.")

pdf_processor = PDFProcessor() 