#!/usr/bin/env python3
"""
Evaluation suite for MedQuery RAG system
"""

import asyncio
import json
import time
import logging
from pathlib import Path
import sys
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.services.elasticsearch_service import ElasticsearchService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.models.chat import ChatMessage, ChatMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedQueryEvaluator:
    def __init__(self):
        self.es_service = ElasticsearchService()
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()

    def get_evaluation_queries(self) -> List[Dict[str, Any]]:
        """Get evaluation queries with expected criteria based on the medicine dataset."""
        return [
            {
                "id": "q1",
                "query": "What are the side effects of Augmentin 625?",
                "expected_keywords": ["vomiting", "nausea", "diarrhea", "augmentin"],
                "category": "side_effects"
            },
            {
                "id": "q2", 
                "query": "What is Azithral 500 tablet used for?",
                "expected_keywords": ["bacterial", "infection", "azithral"],
                "category": "uses"
            },
            {
                "id": "q3",
                "query": "What are substitutes for Allegra 120mg?",
                "expected_keywords": ["lcfex", "etofex", "nexofex", "fexise", "histafree"],
                "category": "substitutes"
            },
            {
                "id": "q4",
                "query": "Is Atarax 25mg habit forming?",
                "expected_keywords": ["atarax", "habit", "forming", "no"],
                "category": "safety"
            },
            {
                "id": "q5",
                "query": "What class is Ascoril LS syrup?",
                "expected_keywords": ["respiratory", "cough", "ascoril"],
                "category": "drug_class"
            },
            {
                "id": "q6",
                "query": "Side effects of Azee 500 tablet",
                "expected_keywords": ["vomiting", "nausea", "abdominal", "diarrhea"],
                "category": "side_effects"
            },
            {
                "id": "q7",
                "query": "Medicines for bacterial infections",
                "expected_keywords": ["augmentin", "azithral", "azee", "antibiotic"],
                "category": "therapeutic_search"
            },
            {
                "id": "q8",
                "query": "Antihistamine medicines",
                "expected_keywords": ["allegra", "avil", "atarax", "antihistamine"],
                "category": "class_search"
            },
            {
                "id": "q9",
                "query": "Respiratory medicines for cough",
                "expected_keywords": ["ascoril", "respiratory", "cough", "mucus"],
                "category": "therapeutic_search"
            },
            {
                "id": "q10",
                "query": "What causes nausea as side effect?",
                "expected_keywords": ["nausea", "side", "effect"],
                "category": "adverse_effects"
            },
            {
                "id": "q11",
                "query": "Macrolide antibiotics",
                "expected_keywords": ["macrolides", "azithral", "azee"],
                "category": "chemical_class"
            },
            {
                "id": "q12",
                "query": "Medicines that cause dizziness",
                "expected_keywords": ["dizziness", "side", "allegra", "atarax"],
                "category": "adverse_effects"
            }
        ]

    async def evaluate_retrieval(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Evaluate retrieval performance for a query."""
        try:
            start_time = time.time()
            
            # Get query embedding
            query_embedding = await self.embedding_service.get_embedding(query)
            
            # Perform semantic search
            results = await self.es_service.semantic_search(
                query_vector=query_embedding,
                query_text=query,
                top_k=top_k
            )
            
            retrieval_time = time.time() - start_time
            
            return {
                "success": True,
                "num_results": len(results),
                "retrieval_time": retrieval_time,
                "results": results,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Retrieval evaluation failed for query '{query}': {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    async def evaluate_rag_response(self, query: str) -> Dict[str, Any]:
        """Evaluate end-to-end RAG response."""
        try:
            start_time = time.time()
            
            # Get retrieval results
            retrieval_result = await self.evaluate_retrieval(query)
            
            if not retrieval_result["success"]:
                return retrieval_result
            
            # Format context
            context = self.llm_service.format_rag_context(retrieval_result["results"])
            
            # Generate response
            messages = [ChatMessage(role="user", content=query)]
            
            response_text = ""
            async for chunk in self.llm_service.generate_response(
                messages=messages,
                mode=ChatMode.RAG,
                context=context,
                stream=False
            ):
                response_text += chunk
            
            total_time = time.time() - start_time
            
            return {
                "success": True,
                "query": query,
                "response": response_text,
                "context": context,
                "num_sources": len(retrieval_result["results"]),
                "retrieval_time": retrieval_result["retrieval_time"],
                "total_time": total_time,
                "sources": retrieval_result["results"]
            }
            
        except Exception as e:
            logger.error(f"RAG evaluation failed for query '{query}': {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    def evaluate_response_quality(self, response_data: Dict[str, Any], expected_keywords: List[str]) -> Dict[str, Any]:
        """Evaluate response quality based on criteria."""
        if not response_data["success"]:
            return {
                "relevance_score": 0.0,
                "keyword_coverage": 0.0,
                "has_sources": False,
                "has_disclaimer": False,
                "quality_score": 0.0
            }
        
        response = response_data["response"].lower()
        sources = response_data.get("sources", [])
        
        # Check keyword coverage
        found_keywords = []
        for keyword in expected_keywords:
            if keyword.lower() in response or any(keyword.lower() in str(source).lower() for source in sources):
                found_keywords.append(keyword)
        
        keyword_coverage = len(found_keywords) / len(expected_keywords) if expected_keywords else 0.0
        
        # Check for medical disclaimer
        disclaimer_phrases = ["not medical advice", "consult", "healthcare professional", "doctor"]
        has_disclaimer = any(phrase in response for phrase in disclaimer_phrases)
        
        # Check if sources are provided
        has_sources = len(sources) > 0
        
        # Calculate relevance score based on sources
        relevance_score = min(len(sources) / 3.0, 1.0)  # Target 3 sources
        
        # Calculate overall quality score
        quality_score = (
            keyword_coverage * 0.4 +
            relevance_score * 0.3 +
            (1.0 if has_sources else 0.0) * 0.2 +
            (1.0 if has_disclaimer else 0.0) * 0.1
        )
        
        return {
            "relevance_score": relevance_score,
            "keyword_coverage": keyword_coverage,
            "found_keywords": found_keywords,
            "has_sources": has_sources,
            "has_disclaimer": has_disclaimer,
            "quality_score": quality_score
        }

    async def run_evaluation(self, save_results: bool = True) -> Dict[str, Any]:
        """Run complete evaluation suite."""
        logger.info("Starting MedQuery evaluation...")
        
        evaluation_queries = self.get_evaluation_queries()
        results = []
        
        overall_stats = {
            "total_queries": len(evaluation_queries),
            "successful_retrievals": 0,
            "successful_responses": 0,
            "average_retrieval_time": 0.0,
            "average_response_time": 0.0,
            "average_quality_score": 0.0,
            "category_scores": {}
        }
        
        for i, eval_query in enumerate(evaluation_queries, 1):
            logger.info(f"Evaluating query {i}/{len(evaluation_queries)}: {eval_query['query']}")
            
            # Evaluate RAG response
            rag_result = await self.evaluate_rag_response(eval_query["query"])
            
            # Evaluate response quality
            quality_metrics = self.evaluate_response_quality(
                rag_result, 
                eval_query["expected_keywords"]
            )
            
            # Combine results
            result = {
                "id": eval_query["id"],
                "query": eval_query["query"],
                "category": eval_query["category"],
                "expected_keywords": eval_query["expected_keywords"],
                "rag_result": rag_result,
                "quality_metrics": quality_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            results.append(result)
            
            # Update stats
            if rag_result["success"]:
                overall_stats["successful_responses"] += 1
                overall_stats["average_response_time"] += rag_result["total_time"]
                overall_stats["average_quality_score"] += quality_metrics["quality_score"]
                
                # Category stats
                category = eval_query["category"]
                if category not in overall_stats["category_scores"]:
                    overall_stats["category_scores"][category] = []
                overall_stats["category_scores"][category].append(quality_metrics["quality_score"])
        
        # Calculate averages
        if overall_stats["successful_responses"] > 0:
            overall_stats["average_response_time"] /= overall_stats["successful_responses"]
            overall_stats["average_quality_score"] /= overall_stats["successful_responses"]
        
        # Calculate category averages
        for category, scores in overall_stats["category_scores"].items():
            overall_stats["category_scores"][category] = {
                "average_score": sum(scores) / len(scores),
                "count": len(scores)
            }
        
        # Calculate success rate
        overall_stats["success_rate"] = overall_stats["successful_responses"] / overall_stats["total_queries"]
        
        evaluation_report = {
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "medquery_version": "1.0.0",
                "evaluation_type": "rag_system"
            },
            "overall_stats": overall_stats,
            "query_results": results
        }
        
        # Save results
        if save_results:
            results_dir = Path(__file__).parent.parent / "evaluation_results"
            results_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"evaluation_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(evaluation_report, f, indent=2)
            
            logger.info(f"Evaluation results saved to {results_file}")
        
        return evaluation_report

    def print_evaluation_summary(self, report: Dict[str, Any]):
        """Print evaluation summary."""
        stats = report["overall_stats"]
        
        print("\n" + "="*50)
        print("📊 MEDQUERY EVALUATION SUMMARY")
        print("="*50)
        
        print(f"📝 Total Queries: {stats['total_queries']}")
        print(f"✅ Successful Responses: {stats['successful_responses']}")
        print(f"📈 Success Rate: {stats['success_rate']:.2%}")
        print(f"⏱️  Average Response Time: {stats['average_response_time']:.2f}s")
        print(f"🎯 Average Quality Score: {stats['average_quality_score']:.2f}")
        
        print(f"\n📂 Category Performance:")
        for category, data in stats['category_scores'].items():
            print(f"  {category}: {data['average_score']:.2f} ({data['count']} queries)")
        
        # Success criteria
        print(f"\n🎯 SUCCESS CRITERIA:")
        success_rate_pass = stats['success_rate'] >= 0.9
        quality_score_pass = stats['average_quality_score'] >= 0.7
        
        print(f"  Success Rate ≥ 90%: {'✅ PASS' if success_rate_pass else '❌ FAIL'} ({stats['success_rate']:.2%})")
        print(f"  Quality Score ≥ 0.7: {'✅ PASS' if quality_score_pass else '❌ FAIL'} ({stats['average_quality_score']:.2f})")
        
        overall_pass = success_rate_pass and quality_score_pass
        print(f"\n🏆 OVERALL: {'✅ PASS' if overall_pass else '❌ FAIL'}")
        
        if not overall_pass:
            print("\n💡 Recommendations:")
            if not success_rate_pass:
                print("  - Check Elasticsearch connectivity and index status")
                print("  - Verify embedding model configuration")
                print("  - Review data ingestion quality")
            if not quality_score_pass:
                print("  - Improve context formatting")
                print("  - Review prompt engineering")
                print("  - Consider fine-tuning retrieval parameters")


async def main():
    """Main evaluation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate MedQuery RAG system")
    parser.add_argument("--no-save", action="store_true", help="Don't save results to file")
    parser.add_argument("--query", type=str, help="Evaluate single query")
    
    args = parser.parse_args()
    
    evaluator = MedQueryEvaluator()
    
    if args.query:
        # Single query evaluation
        logger.info(f"Evaluating single query: {args.query}")
        result = await evaluator.evaluate_rag_response(args.query)
        
        if result["success"]:
            print(f"\n📝 Query: {args.query}")
            print(f"📄 Response: {result['response'][:200]}...")
            print(f"📊 Sources: {result['num_sources']}")
            print(f"⏱️  Time: {result['total_time']:.2f}s")
        else:
            print(f"❌ Query failed: {result['error']}")
    else:
        # Full evaluation
        report = await evaluator.run_evaluation(save_results=not args.no_save)
        evaluator.print_evaluation_summary(report)


if __name__ == "__main__":
    asyncio.run(main())
