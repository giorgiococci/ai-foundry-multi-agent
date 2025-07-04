"""
Logging configuration for Multi-Agent Orchestrator

This module provides clean logging configuration that suppresses verbose
Azure SDK HTTP request/response logging while keeping useful application logs.
"""

import logging
import sys

def setup_clean_logging(level=logging.INFO):
    """
    Configure clean logging for the multi-agent orchestrator.
    
    Args:
        level: Logging level (default: logging.INFO)
    """
    # Configure main application logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress verbose Azure SDK logging
    azure_loggers = [
        'azure.core.pipeline.policies.http_logging_policy',
        'azure.ai.projects',
        'azure.ai.agents', 
        'azure.identity',
        'azure.core',
        'urllib3',
        'urllib3.connectionpool',
        'requests.packages.urllib3',
        'azure.core.pipeline.policies.authentication',
        'azure.core.pipeline.policies.redirect',
        'azure.core.pipeline.policies.retry'
    ]
    
    for logger_name in azure_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Get the main logger
    logger = logging.getLogger('multi_agent_orchestrator')
    logger.info("Clean logging configuration applied")
    
    return logger

def setup_debug_logging():
    """Enable debug logging for troubleshooting."""
    return setup_clean_logging(level=logging.DEBUG)

def setup_minimal_logging():
    """Enable minimal logging (warnings and errors only)."""
    return setup_clean_logging(level=logging.WARNING)
