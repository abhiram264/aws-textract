"""AWS Textract client module for document text detection"""

import boto3
import os
from typing import Dict, List, Any
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()


class TextractClient:
    """Wrapper for AWS Textract API"""
    
    def __init__(self, region: str = None, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize Textract client
        
        Args:
            region: AWS region (defaults to AWS_REGION env var or us-east-1)
            max_retries: Number of retries for API calls
            retry_delay: Delay in seconds between retries
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Get region from parameter, environment, or default
        if region is None:
            region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Initialize Textract client
        try:
            self.client = boto3.client(
                'textract',
                region_name=region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Textract client: {str(e)}")
    
    def detect_document_text(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect text in document using Textract synchronous API
        
        Args:
            image_bytes: Image file as bytes
            
        Returns:
            Textract response dictionary containing detected text and metadata
            
        Raises:
            Exception: If API call fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.detect_document_text(
                    Document={'Bytes': image_bytes}
                )
                return response
            except self.client.exceptions.ThrottlingException as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Throttled by Textract API. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Textract API throttled after {self.max_retries} attempts: {str(e)}")
            except self.client.exceptions.InvalidParameterException as e:
                raise ValueError(f"Invalid parameter in Textract request: {str(e)}")
            except self.client.exceptions.BadDocumentException as e:
                raise ValueError(f"Invalid or corrupted document: {str(e)}")
            except self.client.exceptions.DocumentTooLargeException as e:
                raise ValueError(f"Document too large: {str(e)}")
            except self.client.exceptions.UnsupportedDocumentException as e:
                raise ValueError(f"Unsupported document format: {str(e)}")
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"Textract API call failed after {self.max_retries} attempts: {str(e)}")
    
    @staticmethod
    def extract_blocks_by_type(response: Dict[str, Any], block_type: str) -> List[Dict[str, Any]]:
        """
        Extract blocks of a specific type from Textract response
        
        Args:
            response: Textract API response
            block_type: Type of block to extract (e.g., 'LINE', 'WORD', 'PAGE')
            
        Returns:
            List of blocks of the specified type
        """
        return [block for block in response.get('Blocks', []) if block.get('BlockType') == block_type]
    
    @staticmethod
    def get_block_text(block: Dict[str, Any]) -> str:
        """
        Get text content from a block
        
        Args:
            block: Textract block dictionary
            
        Returns:
            Text content of the block
        """
        return block.get('Text', '')
    
    @staticmethod
    def get_block_confidence(block: Dict[str, Any]) -> float:
        """
        Get confidence score from a block
        
        Args:
            block: Textract block dictionary
            
        Returns:
            Confidence score as percentage (0-100)
        """
        return block.get('Confidence', 0.0)
    
    @staticmethod
    def get_block_geometry(block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get geometry (bounding box) information from a block
        
        Args:
            block: Textract block dictionary
            
        Returns:
            Geometry dictionary with coordinates
        """
        return block.get('Geometry', {})
    
    @staticmethod
    def format_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Textract response for easier processing
        
        Args:
            response: Raw Textract API response
            
        Returns:
            Formatted response with structured data
        """
        lines = TextractClient.extract_blocks_by_type(response, 'LINE')
        words = TextractClient.extract_blocks_by_type(response, 'WORD')
        
        return {
            'lines': [
                {
                    'text': TextractClient.get_block_text(line),
                    'confidence': TextractClient.get_block_confidence(line),
                    'geometry': TextractClient.get_block_geometry(line)
                }
                for line in lines
            ],
            'words': [
                {
                    'text': TextractClient.get_block_text(word),
                    'confidence': TextractClient.get_block_confidence(word),
                    'geometry': TextractClient.get_block_geometry(word)
                }
                for word in words
            ],
            'raw_response': response
        }


def get_textract_client(region: str = None) -> TextractClient:
    """
    Factory function to get a Textract client instance
    
    Args:
        region: AWS region
        
    Returns:
        TextractClient instance
    """
    return TextractClient(region=region)
