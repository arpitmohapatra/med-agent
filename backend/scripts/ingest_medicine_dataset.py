#!/usr/bin/env python3
"""
Specialized ingestion script for the medicine_dataset.csv
Optimized for the 248k medicine records with full metadata
"""

import asyncio
import pandas as pd
import logging
from pathlib import Path
import sys
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.services.elasticsearch_service import ElasticsearchService
from app.services.embedding_service import EmbeddingService
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicineDatasetIngester:
    def __init__(self):
        self.es_service = ElasticsearchService()
        self.embedding_service = EmbeddingService()

    async def process_medicine_batch(self, batch_df: pd.DataFrame) -> list:
        """Process a batch of medicine records efficiently."""
        logger.info(f"Processing batch of {len(batch_df)} medicines...")
        
        documents = []
        for _, row in batch_df.iterrows():
            doc = self.process_single_record(row)
            documents.append(doc)
        
        # Generate embeddings for all documents in batch
        texts = [doc["content"] for doc in documents]
        embeddings = await self.embedding_service.get_embeddings_batch(texts, batch_size=50)
        
        # Add embeddings to documents
        embedded_docs = []
        for doc, embedding in zip(documents, embeddings):
            embedded_doc = {**doc, "vector": embedding}
            embedded_docs.append(embedded_doc)
        
        return embedded_docs

    def process_single_record(self, row: pd.Series) -> dict:
        """Process a single medicine record from the dataset."""
        # Extract basic info
        med_id = str(row.get('id', ''))
        name = str(row.get('name', 'Unknown Medicine')).strip()
        chemical_class = str(row.get('Chemical Class', '')).strip()
        habit_forming = str(row.get('Habit Forming', '')).strip()
        therapeutic_class = str(row.get('Therapeutic Class', '')).strip()
        action_class = str(row.get('Action Class', '')).strip()
        
        # Extract substitutes (substitute0 to substitute4)
        substitutes = []
        for i in range(5):
            sub = str(row.get(f'substitute{i}', '')).strip()
            if sub and sub != 'nan' and sub != '':
                substitutes.append(sub)
        substitutes_text = ', '.join(substitutes) if substitutes else ''
        
        # Extract side effects (sideEffect0 to sideEffect41)
        side_effects = []
        for i in range(42):
            effect = str(row.get(f'sideEffect{i}', '')).strip()
            if effect and effect != 'nan' and effect != '':
                side_effects.append(effect)
        side_effects_text = ', '.join(side_effects) if side_effects else ''
        
        # Extract uses (use0 to use4)
        uses = []
        for i in range(5):
            use = str(row.get(f'use{i}', '')).strip()
            if use and use != 'nan' and use != '':
                uses.append(use)
        uses_text = ', '.join(uses) if uses else ''
        
        # Construct title
        title = name
        if chemical_class and chemical_class != 'NA':
            title += f" ({chemical_class})"
        
        # Construct comprehensive content for embedding
        content_parts = [f"Medicine: {name}"]
        
        if chemical_class and chemical_class != 'NA':
            content_parts.append(f"Chemical Class: {chemical_class}")
        
        if therapeutic_class and therapeutic_class != 'NA':
            content_parts.append(f"Therapeutic Class: {therapeutic_class}")
        
        if action_class and action_class != 'NA':
            content_parts.append(f"Action Class: {action_class}")
        
        if uses_text:
            content_parts.append(f"Medical Uses: {uses_text}")
        
        if side_effects_text:
            content_parts.append(f"Side Effects: {side_effects_text}")
        
        if substitutes_text:
            content_parts.append(f"Alternative Medicines: {substitutes_text}")
        
        if habit_forming and habit_forming not in ['NA', 'No']:
            content_parts.append(f"Habit Forming: {habit_forming}")
        
        content = "\n\n".join(content_parts)
        
        # Generate document ID
        doc_id = f"med_{med_id}"
        
        return {
            "id": doc_id,
            "title": title,
            "content": content,
            "chunk": content,  # For this dataset, content is the chunk
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
                "source": "medicine_dataset_csv",
                "total_side_effects": len(side_effects),
                "total_substitutes": len(substitutes),
                "total_uses": len(uses)
            },
            "created_at": datetime.utcnow().isoformat()
        }

    async def ingest_dataset(self, csv_path: str = None, batch_size: int = 500, max_records: int = None):
        """Ingest the full medicine dataset."""
        try:
            # Determine dataset path
            if not csv_path:
                current_dir = Path(__file__).parent.parent
                csv_path = current_dir / "medicine_dataset.csv"
            
            if not Path(csv_path).exists():
                raise FileNotFoundError(f"Dataset not found at {csv_path}")
            
            # Create/recreate index
            logger.info("Creating Elasticsearch index...")
            await self.es_service.delete_index()  # Clean start
            await self.es_service.create_index()
            
            # Load dataset
            logger.info(f"Loading dataset from {csv_path}")
            df = pd.read_csv(csv_path)
            
            # Apply record limit if specified
            if max_records and max_records < len(df):
                df = df.head(max_records)
                logger.info(f"Limited to first {max_records} records for testing")
            
            total_records = len(df)
            logger.info(f"Found {total_records} medicine records")
            
            # Process in batches
            start_time = time.time()
            processed_count = 0
            
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(df) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_df)} records)")
                
                try:
                    # Process batch
                    embedded_docs = await self.process_medicine_batch(batch_df)
                    
                    # Index in Elasticsearch
                    success = await self.es_service.bulk_index_documents(embedded_docs)
                    
                    if success:
                        processed_count += len(embedded_docs)
                        elapsed = time.time() - start_time
                        rate = processed_count / elapsed if elapsed > 0 else 0
                        eta = (total_records - processed_count) / rate if rate > 0 else 0
                        
                        logger.info(f"✅ Batch {batch_num} complete. "
                                   f"Progress: {processed_count}/{total_records} "
                                   f"({processed_count/total_records*100:.1f}%) "
                                   f"Rate: {rate:.1f} docs/sec "
                                   f"ETA: {eta/60:.1f}min")
                    else:
                        logger.error(f"❌ Failed to index batch {batch_num}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing batch {batch_num}: {e}")
                    continue
            
            # Final statistics
            total_time = time.time() - start_time
            logger.info(f"🎉 Ingestion complete!")
            logger.info(f"📊 Processed: {processed_count}/{total_records} records")
            logger.info(f"⏱️ Total time: {total_time/60:.1f} minutes")
            logger.info(f"🚀 Average rate: {processed_count/total_time:.1f} docs/sec")
            
            # Get final index stats
            stats = await self.es_service.get_index_stats()
            logger.info(f"📈 Index stats: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"💥 Ingestion failed: {e}")
            return False

    async def verify_ingestion(self, sample_queries: list = None):
        """Verify the ingestion by testing some queries."""
        if not sample_queries:
            sample_queries = [
                "augmentin",
                "azithromycin",
                "paracetamol",
                "headache medicine",
                "antibiotic"
            ]
        
        logger.info("🔍 Verifying ingestion with sample queries...")
        
        for query in sample_queries:
            try:
                # Get embedding for query
                query_embedding = await self.embedding_service.get_embedding(query)
                
                # Search
                results = await self.es_service.semantic_search(
                    query_vector=query_embedding,
                    query_text=query,
                    top_k=3
                )
                
                logger.info(f"Query: '{query}' -> {len(results)} results")
                if results:
                    for i, result in enumerate(results, 1):
                        logger.info(f"  {i}. {result['title']} (score: {result['score']:.3f})")
                
            except Exception as e:
                logger.error(f"Query '{query}' failed: {e}")


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest medicine dataset into MedQuery")
    parser.add_argument("--csv", type=str, help="Path to CSV file (default: backend/medicine_dataset.csv)")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size for processing")
    parser.add_argument("--max-records", type=int, help="Limit number of records for testing")
    parser.add_argument("--verify", action="store_true", help="Run verification queries after ingestion")
    
    args = parser.parse_args()
    
    ingester = MedicineDatasetIngester()
    
    # Run ingestion
    success = await ingester.ingest_dataset(
        csv_path=args.csv,
        batch_size=args.batch_size,
        max_records=args.max_records
    )
    
    if success:
        logger.info("✅ Dataset ingestion successful!")
        
        if args.verify:
            await ingester.verify_ingestion()
    else:
        logger.error("❌ Dataset ingestion failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
