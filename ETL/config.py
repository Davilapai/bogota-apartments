"""
ETL Configuration Module
Author: Erik Garcia (@erik172)
Version: 3.0.0

This module provides centralized configuration management for the ETL pipeline.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ETLConfig:
    """Configuration class for ETL pipeline"""
    
    # MongoDB Configuration
    mongo_uri: str
    mongo_database: str
    mongo_collection_raw: str
    mongo_collection_processed: str
    
    # Directory Configuration
    data_dir: Path = Path("data")
    raw_data_dir: Path = Path("data/raw")
    external_data_dir: Path = Path("data/external")
    interim_data_dir: Path = Path("data/interim")
    processed_data_dir: Path = Path("data/processed")
    logs_dir: Path = Path("logs")

    # Runtime behavior
    use_raw_files: bool = False
    
    # Processing Configuration
    chunk_size: int = 1000
    max_workers: int = os.cpu_count() or 4
    
    # Geospatial Configuration
    bogota_bounds: dict = None
    
    def __post_init__(self):
        """Initialize derived configurations"""
        if self.bogota_bounds is None:
            # Bogotá coordinate bounds (slightly expanded for safety)
            self.bogota_bounds = {
                'lat_min': 3.8,
                'lat_max': 5.2,
                'lon_min': -74.8,
                'lon_max': -73.2
            }
    
    @classmethod
    def from_env(cls) -> 'ETLConfig':
        """Create configuration from environment variables"""
        use_raw_files_env = os.getenv('ETL_USE_RAW_FILES', 'false').strip().lower()
        use_raw_files = use_raw_files_env in ('1', 'true', 'yes', 'y', 'on')

        return cls(
            mongo_uri=os.getenv('MONGO_URI', ''),
            mongo_database=os.getenv('MONGO_DATABASE', 'bogota_apartments'),
            mongo_collection_raw=os.getenv('MONGO_COLLECTION_RAW', 'scrapy_bogota_apartments'),
            mongo_collection_processed=os.getenv('MONGO_COLLECTION_PROCESSED', 'scrapy_bogota_apartments_processed'),
            use_raw_files=use_raw_files
        )
    
    def setup_directories(self):
        """Create necessary directories"""
        for directory in [
            self.interim_data_dir, 
            self.processed_data_dir,
            self.logs_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate configuration"""
        # If user explicitly wants file-based mode, validate raw files.
        if self.use_raw_files:
            raw_files = list(self.raw_data_dir.glob('*.json')) + list(self.raw_data_dir.glob('*.jsonl'))
            raw_files = [f for f in raw_files if f.name.lower() != 'readme.md']
            if not raw_files:
                raise ValueError(
                    f"ETL_USE_RAW_FILES is enabled but no .json/.jsonl files were found in {self.raw_data_dir}"
                )
            return True

        # Mongo mode if URI is present.
        if self.mongo_uri:
            return True

        # Fallback: if Mongo is not configured but raw files exist, allow file mode automatically.
        raw_files = list(self.raw_data_dir.glob('*.json')) + list(self.raw_data_dir.glob('*.jsonl'))
        raw_files = [f for f in raw_files if f.name.lower() != 'readme.md']
        if not raw_files:
            raise ValueError(
                "MONGO_URI not configured and no raw files found in data/raw. "
                "Provide MONGO_URI or place scraper outputs (.json/.jsonl) in data/raw."
            )
        
        return True


# Global configuration instance
config = ETLConfig.from_env() 