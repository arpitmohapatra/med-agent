#!/usr/bin/env python3
"""
Data ingestion script for Kaggle Medicine Dataset
"""

import asyncio
import pandas as pd
import json
import logging
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.services.elasticsearch_service import ElasticsearchService
from app.services.embedding_service import EmbeddingService
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicineDataIngester:
    def __init__(self):
        self.es_service = ElasticsearchService()
        self.embedding_service = EmbeddingService()

    async def download_kaggle_dataset(self, dataset_name: str = "shubhendumishra/medicine-recommendation-system"):
        """Download Kaggle dataset (requires kaggle API setup)."""
        try:
            import kaggle
            
            # Create data directory
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            
            # Download dataset
            kaggle.api.dataset_download_files(
                dataset_name,
                path=str(data_dir),
                unzip=True
            )
            
            logger.info(f"Downloaded dataset to {data_dir}")
            return data_dir
            
        except ImportError:
            logger.error("Kaggle package not installed. Run: pip install kaggle")
            return None
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            return None

    async def load_csv_data(self, csv_path: str) -> pd.DataFrame:
        """Load medicine data from CSV file."""
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} records from {csv_path}")
            
            # Display column info
            logger.info(f"Columns: {list(df.columns)}")
            logger.info(f"Sample record:\n{df.iloc[0] if len(df) > 0 else 'No data'}")
            
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return pd.DataFrame()

    def process_medicine_record(self, record: dict) -> dict:
        """Process a single medicine record from the medicine dataset."""
        # Extract basic info
        med_id = str(record.get('id', ''))
        name = str(record.get('name', 'Unknown Medicine')).strip()
        chemical_class = str(record.get('Chemical Class', '')).strip()
        habit_forming = str(record.get('Habit Forming', '')).strip()
        therapeutic_class = str(record.get('Therapeutic Class', '')).strip()
        action_class = str(record.get('Action Class', '')).strip()
        
        # Extract substitutes (substitute0 to substitute4)
        substitutes = []
        for i in range(5):
            sub = str(record.get(f'substitute{i}', '')).strip()
            if sub and sub != 'nan' and sub != '':
                substitutes.append(sub)
        substitutes_text = ', '.join(substitutes) if substitutes else ''
        
        # Extract side effects (sideEffect0 to sideEffect41)
        side_effects = []
        for i in range(42):
            effect = str(record.get(f'sideEffect{i}', '')).strip()
            if effect and effect != 'nan' and effect != '':
                side_effects.append(effect)
        side_effects_text = ', '.join(side_effects) if side_effects else ''
        
        # Extract uses (use0 to use4)
        uses = []
        for i in range(5):
            use = str(record.get(f'use{i}', '')).strip()
            if use and use != 'nan' and use != '':
                uses.append(use)
        uses_text = ', '.join(uses) if uses else ''
        
        # Construct title
        title = name
        if chemical_class and chemical_class != 'NA':
            title += f" ({chemical_class})"
        
        # Construct comprehensive content for embedding
        content_parts = []
        
        content_parts.append(f"Medicine: {name}")
        
        if chemical_class and chemical_class != 'NA':
            content_parts.append(f"Chemical Class: {chemical_class}")
        
        if therapeutic_class and therapeutic_class != 'NA':
            content_parts.append(f"Therapeutic Class: {therapeutic_class}")
        
        if action_class and action_class != 'NA':
            content_parts.append(f"Action Class: {action_class}")
        
        if uses_text:
            content_parts.append(f"Uses: {uses_text}")
        
        if side_effects_text:
            content_parts.append(f"Side Effects: {side_effects_text}")
        
        if substitutes_text:
            content_parts.append(f"Substitutes: {substitutes_text}")
        
        if habit_forming and habit_forming != 'NA':
            content_parts.append(f"Habit Forming: {habit_forming}")
        
        content = "\n\n".join(content_parts)
        
        # Generate document ID
        doc_id = f"med_{med_id}_{hash(name)}"
        
        return {
            "id": doc_id,
            "title": title,
            "content": content,
            "url": f"https://medquery.app/medicine/{doc_id}",
            "metadata": {
                "medicine_id": med_id,
                "name": name,
                "chemical_class": chemical_class,
                "therapeutic_class": therapeutic_class,
                "action_class": action_class,
                "habit_forming": habit_forming,
                "uses": uses_text,
                "side_effects": side_effects_text,
                "substitutes": substitutes_text,
                "uses_list": uses,
                "side_effects_list": side_effects,
                "substitutes_list": substitutes,
                "type": "medicine",
                "source": "medicine_dataset_csv"
            },
            "created_at": datetime.utcnow().isoformat()
        }

    async def create_sample_data(self) -> list:
        """Create sample medicine data for testing."""
        sample_medicines = [
            {
                "name": "Paracetamol",
                "composition": "Acetaminophen 500mg",
                "uses": "Fever, headache, muscle aches, toothache, menstrual cramps, arthritis, or other pain",
                "side_effects": "Nausea, stomach pain, loss of appetite, itching, rash, dark urine, clay-colored stools",
                "substitutes": "Acetaminophen, Tylenol, Crocin, Dolo",
                "manufacturer": "GlaxoSmithKline",
                "dosage": "500mg every 4-6 hours, max 4g/day"
            },
            {
                "name": "Amoxicillin",
                "composition": "Amoxicillin 500mg",
                "uses": "Bacterial infections including bronchitis, pneumonia, ear infections, urinary tract infections",
                "side_effects": "Diarrhea, nausea, vomiting, stomach pain, vaginal itching or discharge",
                "substitutes": "Ampicillin, Augmentin, Penicillin",
                "manufacturer": "Cipla",
                "dosage": "500mg every 8 hours for 7-10 days"
            },
            {
                "name": "Metformin",
                "composition": "Metformin HCl 500mg",
                "uses": "Type 2 diabetes, PCOS, insulin resistance",
                "side_effects": "Diarrhea, nausea, vomiting, gas, stomach upset, metallic taste",
                "substitutes": "Glucophage, Glumetza, Fortamet",
                "manufacturer": "Sun Pharma",
                "dosage": "500mg twice daily with meals"
            },
            {
                "name": "Omeprazole",
                "composition": "Omeprazole 20mg",
                "uses": "Gastroesophageal reflux disease (GERD), stomach ulcers, heartburn",
                "side_effects": "Headache, stomach pain, nausea, diarrhea, vomiting, gas",
                "substitutes": "Prilosec, Losec, Nexium, Pantoprazole",
                "manufacturer": "Dr. Reddy's",
                "dosage": "20mg once daily before breakfast"
            },
            {
                "name": "Lisinopril",
                "composition": "Lisinopril 10mg",
                "uses": "High blood pressure, heart failure, diabetic kidney disease",
                "side_effects": "Dizziness, headache, tired feeling, nausea, diarrhea, dry cough",
                "substitutes": "Enalapril, Captopril, Ramipril, Benazepril",
                "manufacturer": "Lupin",
                "dosage": "10mg once daily, may increase to 40mg daily"
            }
        ]
        
        processed_docs = []
        for med in sample_medicines:
            doc = self.process_medicine_record(med)
            processed_docs.append(doc)
        
        return processed_docs

    async def ingest_data(self, csv_path: str = None, use_sample: bool = False, batch_size: int = 100):
        """Main ingestion process."""
        try:
            # Create index
            logger.info("Creating Elasticsearch index...")
            await self.es_service.create_index()
            
            # Load data
            if use_sample:
                logger.info("Using sample data...")
                documents = await self.create_sample_data()
            elif csv_path:
                logger.info(f"Loading data from {csv_path}...")
                df = await self.load_csv_data(csv_path)
                if df.empty:
                    raise ValueError("No data loaded from CSV")
                
                # Process records
                documents = []
                for _, row in df.iterrows():
                    doc = self.process_medicine_record(row.to_dict())
                    documents.append(doc)
            else:
                # Check for existing medicine dataset in current directory
                current_dir = Path(__file__).parent.parent
                dataset_path = current_dir / "medicine_dataset.csv"
                
                if dataset_path.exists():
                    logger.info(f"Found medicine dataset at {dataset_path}")
                    df = await self.load_csv_data(str(dataset_path))
                    if not df.empty:
                        logger.info(f"Loading {len(df)} records from medicine dataset...")
                        documents = []
                        for _, row in df.iterrows():
                            doc = self.process_medicine_record(row.to_dict())
                            documents.append(doc)
                    else:
                        raise ValueError("Medicine dataset is empty")
                else:
                    # Try to download from Kaggle as fallback
                    logger.info("Medicine dataset not found, attempting to download Kaggle dataset...")
                    data_dir = await self.download_kaggle_dataset()
                    if data_dir:
                        # Look for CSV files in the downloaded data
                        csv_files = list(data_dir.glob("*.csv"))
                        if csv_files:
                            csv_path = csv_files[0]
                            df = await self.load_csv_data(str(csv_path))
                            documents = []
                            for _, row in df.iterrows():
                                doc = self.process_medicine_record(row.to_dict())
                                documents.append(doc)
                        else:
                            logger.warning("No CSV files found, using sample data")
                            documents = await self.create_sample_data()
                    else:
                        logger.warning("Could not download dataset, using sample data")
                        documents = await self.create_sample_data()
            
            if not documents:
                raise ValueError("No documents to process")
            
            logger.info(f"Processing {len(documents)} documents...")
            
            # Process documents in batches
            all_chunks = []
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
                
                for doc in batch:
                    # Embed document
                    embedded_chunks = await self.embedding_service.embed_document(doc)
                    all_chunks.extend(embedded_chunks)
            
            logger.info(f"Generated {len(all_chunks)} embedded chunks")
            
            # Index in Elasticsearch
            logger.info("Indexing documents in Elasticsearch...")
            success = await self.es_service.bulk_index_documents(all_chunks)
            
            if success:
                logger.info("✅ Data ingestion completed successfully!")
                
                # Get stats
                stats = await self.es_service.get_index_stats()
                logger.info(f"Index stats: {stats}")
                
                return True
            else:
                logger.error("❌ Failed to index documents")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
            return False


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest medicine data into MedQuery")
    parser.add_argument("--csv", type=str, help="Path to CSV file")
    parser.add_argument("--sample", action="store_true", help="Use sample data")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    
    args = parser.parse_args()
    
    ingester = MedicineDataIngester()
    
    success = await ingester.ingest_data(
        csv_path=args.csv,
        use_sample=args.sample,
        batch_size=args.batch_size
    )
    
    if success:
        print("🎉 Data ingestion completed successfully!")
    else:
        print("💥 Data ingestion failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
