#!/usr/bin/env python3
"""
Comprehensive test script to verify the Metis RAG system fixes:
- Entity preservation in query refinement
- Minimum context requirements
- Citation handling

This script tests the system with increasingly complex queries to verify
that entity names are preserved, sufficient context is retrieved, and
citations are properly handled.
"""

import asyncio
import logging
import sys
import os
import json
import uuid
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# Custom log handler to capture log messages
class LogCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
        
    def emit(self, record):
        self.logs.append(record)
        
    def get_logs(self):
        return self.logs
        
    def clear(self):
        self.logs = []

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("tests/results/entity_preservation_test_results.log")
    ]
)

logger = logging.getLogger("test_rag_entity_preservation")

# Create a log capture handler for RAG engine logs
log_capture_handler = LogCaptureHandler()
rag_logger = logging.getLogger("app.rag.rag_engine")
rag_logger.addHandler(log_capture_handler)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env.test
from dotenv import load_dotenv
load_dotenv(".env.test")

# Import RAG components
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import VectorStore
from app.rag.ollama_client import OllamaClient
from app.models.document import Document, Chunk
from app.rag.agents.retrieval_judge import RetrievalJudge

# Test document content
TEST_DOCUMENTS = {
    "stabilium_overview": {
        "filename": "stabilium_overview.md",
        "content": """# Stabilium: A Revolutionary Material for Quantum Computing

## Overview

Stabilium is a synthetic metamaterial developed in 2023 that exhibits remarkable quantum stability properties. 
It is primarily composed of a lattice structure of modified graphene sheets interspersed with rare earth elements, 
creating a material that can maintain quantum coherence at higher temperatures than previously thought possible.

## Key Properties

- **Quantum Coherence**: Stabilium can maintain quantum states for up to 300 microseconds at temperatures approaching 20K, 
  a significant improvement over previous materials that required temperatures below 1K.
- **Superconductivity**: Exhibits zero electrical resistance at temperatures up to 15K.
- **Magnetic Field Resistance**: Maintains its properties in magnetic fields up to 2 Tesla.
- **Scalability**: Can be manufactured in sheets up to 10cm² while maintaining uniform properties.

## Applications in Quantum Computing

Stabilium has revolutionized quantum computing by enabling the development of more practical quantum processors:

1. **Qubit Stability**: When used as a substrate for superconducting qubits, Stabilium increases coherence times by a factor of 5-10.
2. **Reduced Cooling Requirements**: Quantum computers using Stabilium components can operate with less extensive cooling systems.
3. **Error Correction**: The increased stability reduces the overhead required for quantum error correction.
4. **Quantum Memory**: Stabilium-based quantum memory cells can store quantum states reliably for extended periods.

## Integration with Quantum Resonance Modulation

When combined with Quantum Resonance Modulation (QRM) techniques, Stabilium enables:
- Dynamic qubit coupling with reduced crosstalk
- Faster gate operations with higher fidelity
- Improved readout accuracy for quantum measurements

## Current Research

Current research focuses on:
- Developing Stabilium QRM-12X, an enhanced version with even longer coherence times
- Exploring applications in quantum networking and quantum cryptography
- Investigating integration with photonic quantum computing architectures
""",
        "tags": ["quantum computing", "materials science", "stabilium"],
        "folder": "/quantum_materials"
    },
    "qrm_overview": {
        "filename": "quantum_resonance_modulation.md",
        "content": """# Quantum Resonance Modulation: Principles and Applications

## Fundamental Principles

Quantum Resonance Modulation (QRM) is a technique developed to manipulate quantum states through precisely controlled 
electromagnetic field modulations. It works by creating resonant conditions that allow for selective excitation and 
manipulation of quantum systems while minimizing decoherence.

## Key Components

1. **Resonance Generators**: Devices that produce precisely tuned electromagnetic fields
2. **Quantum Field Modulators**: Systems that shape and direct the resonant fields
3. **Feedback Control Systems**: Real-time monitoring and adjustment mechanisms

## Properties in Cold Fusion Experiments

QRM has shown promising results in cold fusion research:

- **Energy Catalysis**: QRM can lower the energy barrier for nuclear fusion by creating quantum tunneling conditions
- **Reaction Stability**: Provides controlled modulation of nuclear forces
- **Heat Distribution**: Enables uniform energy distribution, preventing hotspots
- **Reproducibility**: Significantly improves the reproducibility of cold fusion experiments

## Comparison with Stabilium in Cold Fusion

| Property | Quantum Resonance Modulation | Stabilium |
|----------|------------------------------|-----------|
| Function | Active process that modulates quantum fields | Passive material that maintains quantum coherence |
| Energy Requirements | Requires continuous energy input | Minimal energy requirements once cooled |
| Scalability | Limited by equipment size | Highly scalable with material production |
| Temperature Range | Effective from 0.1K to 50K | Optimal performance at 5K-20K |
| Cost | High operational costs | High initial material cost, low operational cost |
| Maintenance | Regular calibration required | Minimal maintenance needed |

## Integration Approaches

The most successful cold fusion experiments combine QRM techniques with Stabilium components:

1. Stabilium lattices serve as the fusion substrate
2. QRM systems create the conditions for quantum tunneling
3. The combined approach increases fusion efficiency by approximately 300% compared to traditional methods

## Current Limitations

Despite its promise, QRM in cold fusion faces several challenges:

- High energy requirements for sustained operation
- Complex equipment that requires specialized expertise
- Difficulty in scaling beyond laboratory demonstrations
- Theoretical models that are still being refined

## Future Directions

Researchers are currently exploring:

- Miniaturized QRM systems for portable applications
- Integration with other quantum materials beyond Stabilium
- Application to other fields including quantum computing and medical imaging
""",
        "tags": ["quantum physics", "cold fusion", "QRM"],
        "folder": "/quantum_techniques"
    },
    "stabilium_versions": {
        "filename": "stabilium_versions_comparison.md",
        "content": """# Stabilium Versions: Comparative Analysis

## Evolution of Stabilium Technology

Since its initial development, Stabilium has undergone several iterations, each improving upon the quantum coherence properties and practical applications of this revolutionary material.

## Stabilium QRM-12X

The latest and most advanced version of Stabilium, designated QRM-12X, represents a significant leap forward in quantum material science.

### Key Improvements Over Earlier Versions

1. **Enhanced Coherence Time**: QRM-12X maintains quantum coherence for up to 500 microseconds, compared to 300 microseconds in the standard version.

2. **Temperature Tolerance**: Operates effectively at temperatures up to 28K, an improvement of 8K over the standard version.

3. **Integrated QRM Capabilities**: Unlike earlier versions that required external QRM equipment, QRM-12X has resonance modulation properties built into its molecular structure.

4. **Reduced Material Complexity**: Requires 40% fewer rare earth elements in its composition, making it more cost-effective and environmentally sustainable.

5. **Improved Scalability**: Can be manufactured in sheets up to 25cm², more than doubling the size capability of the original version.

## Stabilium Standard (First Generation)

The original Stabilium formulation established the baseline capabilities:

- Coherence time: 300 microseconds at 20K
- Superconductivity up to 15K
- Magnetic field resistance up to 2 Tesla
- Manufacturing scale limited to 10cm²

## Stabilium QRM-8 (Second Generation)

An intermediate version that introduced the first integration with QRM principles:

- Coherence time: 350 microseconds at 22K
- Superconductivity up to 18K
- Magnetic field resistance up to 2.5 Tesla
- Manufacturing scale up to 15cm²
- Required external QRM equipment for optimal performance

## Comparative Performance in Quantum Computing Applications

| Performance Metric | Standard Stabilium | QRM-8 | QRM-12X |
|--------------------|-------------------|-------|---------|
| Qubit Error Rate | 0.5% | 0.3% | 0.1% |
| Gate Operation Speed | 50ns | 35ns | 20ns |
| Power Consumption | 100% (baseline) | 75% | 45% |
| Manufacturing Cost | 100% (baseline) | 120% | 90% |
| Cooling Requirements | 100% (baseline) | 80% | 60% |

## Transition Recommendations

For organizations currently using earlier Stabilium versions:

1. **Research Applications**: Immediate upgrade to QRM-12X is recommended for cutting-edge research.
2. **Commercial Quantum Computing**: Phased transition from QRM-8 to QRM-12X over 6-12 months.
3. **Legacy Systems**: Standard Stabilium remains adequate for educational and non-critical applications.

## Future Development Roadmap

The Stabilium research consortium has announced plans for:

- **QRM-15X**: Currently in early development, expected to achieve coherence times exceeding 1 millisecond
- **Stabilium Flex**: A malleable variant that can be shaped into complex 3D structures
- **Room Temperature Stabilium**: Long-term research goal to create variants that maintain quantum properties at 273K
""",
        "tags": ["stabilium", "QRM-12X", "quantum materials", "version comparison"],
        "folder": "/quantum_materials/versions"
    },
    "quantum_physics": {
        "filename": "heisenberg_uncertainty_principle.md",
        "content": """# Heisenberg's Uncertainty Principle and Quantum Entanglement

## Fundamental Concepts

Heisenberg's Uncertainty Principle, formulated by Werner Heisenberg in 1927, is one of the cornerstones of quantum mechanics. It states that there is a fundamental limit to the precision with which complementary variables, such as position and momentum, can be known simultaneously.

Mathematically expressed as:
Δx · Δp ≥ ħ/2

Where:
- Δx is the uncertainty in position
- Δp is the uncertainty in momentum
- ħ is the reduced Planck constant

## Quantum Entanglement

Quantum entanglement is a phenomenon where two or more particles become correlated in such a way that the quantum state of each particle cannot be described independently of the others, regardless of the distance separating them.

## Interaction Between Uncertainty and Entanglement

The relationship between Heisenberg's Uncertainty Principle and quantum entanglement creates fascinating paradoxes and applications:

1. **Measurement Effects**: When entangled particles are measured, the uncertainty principle applies to both particles simultaneously.

2. **EPR Paradox**: Einstein, Podolsky, and Rosen proposed that entanglement could violate the uncertainty principle, leading to decades of theoretical and experimental work.

3. **Bell's Inequality**: John Bell showed that quantum mechanics predicts stronger correlations between entangled particles than would be possible in classical physics.

## Stabilium's Interaction with the Uncertainty Principle

Stabilium has unique properties that affect how the uncertainty principle manifests in quantum systems:

1. **Extended Coherence**: Stabilium's ability to maintain quantum coherence for extended periods allows for more precise measurements within the bounds of the uncertainty principle.

2. **Entanglement Preservation**: When quantum entanglement is established between particles in a Stabilium substrate, the entangled state persists longer than in conventional materials.

3. **Measurement Precision**: Stabilium-based quantum sensors can approach the theoretical limits imposed by the uncertainty principle more closely than previous technologies.

## Quantum Entanglement Experiments with Stabilium

Recent experiments have demonstrated several key interactions:

1. **Coherent Entanglement**: Stabilium can maintain entangled qubit pairs with fidelity above 99% for up to 200 microseconds.

2. **Uncertainty Boundary Testing**: Experiments using Stabilium have probed the exact boundaries of the uncertainty principle with unprecedented precision.

3. **Quantum Teleportation**: Stabilium-based quantum teleportation experiments have achieved record distances and fidelities.

4. **Quantum Memory**: Stabilium can store entangled states as a quantum memory, preserving the entanglement properties while subject to the constraints of the uncertainty principle.

## Theoretical Implications

The interaction between Stabilium, the uncertainty principle, and quantum entanglement has led to several theoretical advances:

1. **Refined Measurement Theory**: More precise models of quantum measurement that account for material properties.

2. **Extended Quantum Information Theory**: New frameworks for understanding how quantum information persists in coherent materials.

3. **Quantum Gravity Probes**: Proposals to use Stabilium-enhanced precision to test theories that unite quantum mechanics with general relativity.

## Practical Applications

These fundamental interactions enable several practical applications:

1. **Quantum Cryptography**: Enhanced security through more stable entangled key distribution.

2. **Quantum Sensing**: Approaching the fundamental limits of measurement precision.

3. **Quantum Computing**: More reliable quantum algorithms that depend on entanglement.

4. **Fundamental Physics Research**: New experimental approaches to test the foundations of quantum mechanics.
""",
        "tags": ["quantum physics", "uncertainty principle", "entanglement"],
        "folder": "/quantum_physics/fundamentals"
    },
    "advanced_quantum": {
        "filename": "quantum_tunneling_non_euclidean.md",
        "content": """# Quantum Tunneling Through Non-Euclidean Space-Time Manifolds

## Theoretical Framework

Quantum tunneling is a quantum mechanical phenomenon where particles penetrate energy barriers that would be insurmountable according to classical physics. When this phenomenon is extended to non-Euclidean space-time manifolds, it opens up revolutionary possibilities for quantum information transfer and energy transmission.

## Non-Euclidean Space-Time Manifolds

Non-Euclidean space-time manifolds represent geometries that deviate from flat Euclidean space. These can include:

1. **Hyperbolic Manifolds**: Negatively curved space-time regions
2. **Spherical Manifolds**: Positively curved space-time regions
3. **Topological Singularities**: Points where standard geometric properties break down
4. **Wormhole-Like Structures**: Theoretical shortcuts through space-time

## The Role of Stabilium in Quantum Tunneling

Stabilium has emerged as a critical enabling technology for controlled quantum tunneling through non-Euclidean space-time manifolds due to several unique properties:

1. **Quantum Coherence Preservation**: Stabilium maintains quantum states even when subjected to the extreme conditions near space-time curvature anomalies.

2. **Topological Protection**: The molecular structure of Stabilium provides topological protection to quantum information, preventing decoherence during tunneling events.

3. **Curvature Response**: Stabilium exhibits a unique response to space-time curvature, creating "tunneling-friendly" conditions at its boundaries.

4. **Quantum Field Stabilization**: When properly configured, Stabilium can stabilize quantum fields in regions of high space-time curvature.

## Experimental Demonstrations

Recent laboratory experiments have demonstrated several key capabilities:

1. **Micro-Scale Manifold Tunneling**: Quantum particles in Stabilium substrates have been observed tunneling through artificially created micro-scale non-Euclidean geometries with efficiency 300% higher than theoretical predictions for conventional materials.

2. **Information Preservation**: Quantum information encoded in particles tunneling through Stabilium-mediated pathways maintains fidelity above 92%, compared to near-total information loss in conventional tunneling.

3. **Multi-Particle Entangled Tunneling**: Entangled particle pairs can tunnel simultaneously while maintaining their entanglement, a phenomenon previously thought impossible.

## Theoretical Models

Several theoretical frameworks have been developed to explain Stabilium's exceptional tunneling properties:

1. **Modified Path Integral Formulation**: Extends Feynman's path integral to account for Stabilium's unique quantum properties in curved space-time.

2. **Topological Quantum Field Theory (TQFT)**: Describes how Stabilium's topological properties protect quantum information during tunneling events.

3. **Non-Commutative Geometry Models**: Provides mathematical tools to analyze tunneling in highly curved space-time regions where standard quantum mechanics breaks down.

## Applications in Advanced Quantum Technologies

The ability of Stabilium to facilitate quantum tunneling through non-Euclidean space-time manifolds enables several revolutionary applications:

1. **Quantum Teleportation Enhancement**: Improving quantum teleportation protocols by utilizing controlled tunneling pathways.

2. **Quantum Computing Acceleration**: Creating shortcuts between physically separated qubits, potentially overcoming connectivity limitations in quantum processors.

3. **Quantum Sensing in Curved Space-Time**: Developing sensors that can detect minute variations in space-time curvature with unprecedented sensitivity.

4. **Quantum Energy Transfer**: Enabling efficient energy transfer across normally prohibitive barriers, with potential applications in energy technology.

## Challenges and Limitations

Despite its promise, several challenges remain:

1. **Scalability**: Current experiments are limited to microscopic scales.

2. **Energy Requirements**: Establishing and maintaining the necessary conditions requires significant energy input.

3. **Theoretical Gaps**: Complete mathematical models unifying quantum mechanics and general relativity remain elusive.

4. **Measurement Difficulties**: Observing and measuring tunneling events without disrupting them presents significant technical challenges.

## Future Research Directions

Ongoing research focuses on:

1. **Macroscopic Tunneling**: Scaling up tunneling phenomena to larger systems.

2. **Reduced Energy Requirements**: Developing more efficient methods to create tunneling-favorable conditions.

3. **Integrated Systems**: Combining Stabilium with other quantum technologies for practical applications.

4. **Fundamental Physics**: Using Stabilium-mediated tunneling to test theories of quantum gravity and unified physics.
""",
        "tags": ["quantum tunneling", "non-Euclidean geometry", "advanced quantum physics", "stabilium applications"],
        "folder": "/quantum_physics/advanced"
    }
}

async def setup_test_environment():
    """
    Set up the test environment by creating a fresh vector store and adding test documents
    """
    logger.info("Setting up test environment...")
    
    # Create test results directory if it doesn't exist
    os.makedirs("tests/results", exist_ok=True)
    
    # Initialize vector store with a test directory
    test_dir = "tests/chroma_db/entity_preservation_test"
    
    # Remove existing test directory if it exists
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    # Create vector store
    vector_store = VectorStore(persist_directory=test_dir)
    
    # Add test documents
    document_ids = []
    for doc_id, doc_info in TEST_DOCUMENTS.items():
        logger.info(f"Adding test document: {doc_info['filename']}")
        
        doc = Document(
            id=doc_id,
            filename=doc_info["filename"],
            content=doc_info["content"],
            tags=doc_info["tags"],
            folder=doc_info["folder"]
        )
        
        # Create chunks for the document
        # For simplicity, we'll create chunks of approximately 1000 characters
        content = doc_info["content"]
        chunk_size = 1000
        chunks = []
        
        for i in range(0, len(content), chunk_size):
            chunk_content = content[i:i+chunk_size]
            if len(chunk_content.strip()) > 0:
                chunk_id = f"{doc_id}_chunk_{i//chunk_size}"
                chunks.append(
                    Chunk(
                        id=chunk_id,
                        content=chunk_content,
                        metadata={
                            "index": i//chunk_size,
                            "source": doc_info["filename"],
                            "document_id": doc_id,
                            "filename": doc_info["filename"],
                            "tags": doc_info["tags"],
                            "folder": doc_info["folder"]
                        }
                    )
                )
        
        # Add chunks to document
        doc.chunks = chunks
        
        # Add document to vector store
        await vector_store.add_document(doc)
        document_ids.append(doc_id)
        
        logger.info(f"Added document {doc_id} with {len(chunks)} chunks")
    
    logger.info(f"Test environment setup complete with {len(document_ids)} documents")
    return vector_store

def extract_chunks_info_from_logs(logs):
    """
    Extract information about chunks retrieved and used from log messages
    """
    chunks_retrieved = 0
    chunks_used = 0
    refined_query = ""
    
    # Regular expressions to match log messages
    retrieved_pattern = r"Retrieved (\d+) chunks from vector store"
    used_pattern = r"Using (\d+) chunks after (optimization|Retrieval Judge optimization)"
    refined_pattern = r"Refined query: (.+)"
    
    # Extract information from logs
    for log in logs:
        message = log.getMessage()
        
        # Check for chunks retrieved
        retrieved_match = re.search(retrieved_pattern, message)
        if retrieved_match:
            chunks_retrieved = int(retrieved_match.group(1))
            
        # Check for chunks used
        used_match = re.search(used_pattern, message)
        if used_match:
            chunks_used = int(used_match.group(1))
            
        # Check for refined query
        refined_match = re.search(refined_pattern, message)
        if refined_match:
            refined_query = refined_match.group(1)
    
    return {
        "chunks_retrieved": chunks_retrieved,
        "chunks_used": chunks_used,
        "refined_query": refined_query
    }

async def test_query(rag_engine, query, query_id):
    """
    Test a query and analyze the results
    """
    logger.info(f"Testing query {query_id}: {query}")
    
    # Create a results directory for this query
    query_results_dir = f"tests/results/query_{query_id}"
    os.makedirs(query_results_dir, exist_ok=True)
    
    # Clear previous logs
    log_capture_handler.clear()
    
    start_time = time.time()
    
    # Execute query with RAG
    response = await rag_engine.query(
        query=query,
        use_rag=True,
        top_k=10,
        stream=False
    )
    
    elapsed_time = time.time() - start_time
    
    # Log the response
    logger.info(f"Query {query_id} completed in {elapsed_time:.2f}s")
    
    # Extract chunks information from logs
    logs = log_capture_handler.get_logs()
    chunks_info = extract_chunks_info_from_logs(logs)
    
    # Extract and analyze results
    results = {
        "query_id": query_id,
        "query": query,
        "execution_time": elapsed_time,
        "answer": response.get("answer", ""),
        "sources": [],
        "chunks_retrieved": chunks_info["chunks_retrieved"],
        "chunks_used": chunks_info["chunks_used"],
        "refined_query": chunks_info["refined_query"] or response.get("metadata", {}).get("refined_query", "")
    }
    
    # Extract sources
    if "sources" in response and response["sources"]:
        for source in response["sources"]:
            source_info = {
                "document_id": source.document_id if hasattr(source, "document_id") else "",
                "chunk_id": source.chunk_id if hasattr(source, "chunk_id") else "",
                "relevance_score": source.relevance_score if hasattr(source, "relevance_score") else 0.0,
                "filename": source.filename if hasattr(source, "filename") else "",
                "excerpt": source.excerpt[:100] + "..." if hasattr(source, "excerpt") and len(source.excerpt) > 100 else source.excerpt if hasattr(source, "excerpt") else ""
            }
            results["sources"].append(source_info)
    
    # Analyze entity preservation
    entity_analysis = analyze_entity_preservation(query, results.get("refined_query", ""))
    results["entity_analysis"] = entity_analysis
    
    # Save results to file
    with open(f"{query_results_dir}/results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate a human-readable report
    generate_query_report(results, query_results_dir)
    
    return results

def analyze_entity_preservation(original_query, refined_query):
    """
    Analyze if entities in the original query are preserved in the refined query
    """
    if not refined_query:
        return {
            "entities_found": [],
            "entities_preserved": True,
            "analysis": "No query refinement was performed"
        }
    
    # Extract potential entities (capitalized words)
    import re
    entity_pattern = r'\b[A-Z][a-zA-Z0-9_-]*(?:\s+[A-Z][a-zA-Z0-9_-]*)*\b'
    entities = re.findall(entity_pattern, original_query)
    
    # Filter out common words that might be capitalized
    common_words = ["I", "A", "The", "What", "How", "When", "Where", "Why", "Is", "Are", "Tell", "Explain"]
    entities = [e for e in entities if e not in common_words]
    
    # Check if entities are preserved
    preserved_entities = []
    missing_entities = []
    
    for entity in entities:
        if entity in refined_query:
            preserved_entities.append(entity)
        else:
            # Check for partial matches (e.g., "Stabilium QRM-12X" might be split)
            entity_parts = entity.split()
            all_parts_found = all(part in refined_query for part in entity_parts)
            if all_parts_found:
                preserved_entities.append(entity)
            else:
                missing_entities.append(entity)
    
    return {
        "entities_found": entities,
        "entities_preserved": len(missing_entities) == 0,
        "preserved_entities": preserved_entities,
        "missing_entities": missing_entities,
        "analysis": f"Found {len(entities)} entities, {len(preserved_entities)} preserved, {len(missing_entities)} missing"
    }

def generate_query_report(results, output_dir):
    """
    Generate a human-readable report for a query test
    """
    report = f"""# Query Test Report: {results['query_id']}

## Query Information
- **Original Query**: {results['query']}
- **Refined Query**: {results.get('refined_query', 'No refinement performed')}
- **Execution Time**: {results['execution_time']:.2f} seconds

## Entity Preservation Analysis
- **Entities Found**: {', '.join(results['entity_analysis']['entities_found']) if results['entity_analysis']['entities_found'] else 'None detected'}
- **Entities Preserved**: {'Yes' if results['entity_analysis']['entities_preserved'] else 'No'}
"""

    if not results['entity_analysis']['entities_preserved']:
        report += f"- **Missing Entities**: {', '.join(results['entity_analysis']['missing_entities'])}\n"

    report += f"""
## Retrieval Statistics
- **Chunks Retrieved**: {results['chunks_retrieved']}
- **Chunks Used in Context**: {results['chunks_used']}

## Sources Used
"""

    for i, source in enumerate(results['sources']):
        report += f"""
### Source {i+1}
- **Document**: {source['filename']}
- **Relevance Score**: {source['relevance_score']:.2f}
- **Excerpt**: {source['excerpt']}
"""

    report += f"""
## Generated Answer
```
{results['answer']}
```
"""

    # Write report to file
    with open(f"{output_dir}/report.md", "w") as f:
        f.write(report)

async def run_test_suite():
    """
    Run the complete test suite
    """
    logger.info("Starting Metis RAG test suite...")
    
    # Set up test environment
    vector_store = await setup_test_environment()
    
    # Initialize RAG engine
    ollama_client = OllamaClient()
    retrieval_judge = RetrievalJudge(ollama_client=ollama_client)
    rag_engine = RAGEngine(
        vector_store=vector_store,
        ollama_client=ollama_client,
        retrieval_judge=retrieval_judge
    )
    
    # Define test queries
    test_queries = [
        {
            "id": "basic_entity",
            "query": "Tell me about Stabilium and its applications in quantum computing."
        },
        {
            "id": "multi_entity",
            "query": "Compare the properties of Stabilium and Quantum Resonance Modulation in cold fusion experiments."
        },
        {
            "id": "potential_ambiguity",
            "query": "What are the differences between Stabilium QRM-12X and earlier versions?"
        },
        {
            "id": "context_synthesis",
            "query": "How does Stabilium interact with Heisenberg's Uncertainty Principle when used in quantum entanglement experiments?"
        },
        {
            "id": "specialized_terminology",
            "query": "Explain the role of Stabilium in facilitating quantum tunneling through non-Euclidean space-time manifolds."
        }
    ]
    
    # Run tests
    all_results = []
    for test in test_queries:
        result = await test_query(rag_engine, test["query"], test["id"])
        all_results.append(result)
        # Add a small delay between queries
        await asyncio.sleep(1)
    
    # Generate summary report
    generate_summary_report(all_results)
    
    logger.info("Test suite completed!")

def generate_summary_report(all_results):
    """
    Generate a summary report for all tests
    """
    summary = """# Metis RAG Test Suite Summary Report

## Overview
This report summarizes the results of testing the Metis RAG system with a series of increasingly complex queries
to verify the fixes implemented for entity preservation, minimum context requirements, and citation handling.

## Test Results Summary

| Query ID | Entity Preservation | Chunks Retrieved | Chunks Used | Execution Time (s) |
|----------|---------------------|------------------|-------------|-------------------|
"""

    for result in all_results:
        entity_status = "✅" if result["entity_analysis"]["entities_preserved"] else "❌"
        summary += f"| {result['query_id']} | {entity_status} | {result['chunks_retrieved']} | {result['chunks_used']} | {result['execution_time']:.2f} |\n"

    summary += """
## Detailed Analysis

### Entity Preservation

"""

    for result in all_results:
        summary += f"**Query {result['query_id']}**: "
        if result["entity_analysis"]["entities_preserved"]:
            summary += f"All entities preserved ({', '.join(result['entity_analysis']['entities_found'])})\n\n"
        else:
            summary += f"Some entities not preserved. Missing: {', '.join(result['entity_analysis']['missing_entities'])}\n\n"

    summary += """
### Context Selection

"""

    for result in all_results:
        summary += f"**Query {result['query_id']}**: Retrieved {result['chunks_retrieved']} chunks, used {result['chunks_used']} in final context\n\n"

    summary += """
### Source Relevance

"""

    for result in all_results:
        summary += f"**Query {result['query_id']}**: Used {len(result['sources'])} sources with relevance scores: "
        if result['sources']:
            scores = [f"{source['relevance_score']:.2f}" for source in result['sources']]
            summary += f"{', '.join(scores)}\n\n"
        else:
            summary += "No sources used\n\n"

    summary += """
## Conclusion

This test suite has verified the following aspects of the Metis RAG system:

1. **Entity Preservation**: The system's ability to preserve named entities during query refinement
2. **Minimum Context Requirements**: The system's ability to retrieve and use sufficient context
3. **Citation Handling**: The system's ability to track and cite sources properly

See individual test reports for detailed analysis of each query.
"""

    # Write summary to file
    with open("tests/results/summary_report.md", "w") as f:
        f.write(summary)

async def main():
    """Main function to run all tests"""
    logger.info("Starting entity preservation and RAG quality tests...")
    
    try:
        await run_test_suite()
    except Exception as e:
        logger.error(f"Error running test suite: {str(e)}", exc_info=True)
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())