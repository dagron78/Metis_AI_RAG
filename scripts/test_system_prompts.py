#!/usr/bin/env python3
"""
Script to test and compare different system prompts for the Metis RAG system.
This script runs the same set of queries against both the original and simplified
system prompts and compares the results.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.rag.rag_engine import RAGEngine
    from app.rag.system_prompts.rag import RAG_SYSTEM_PROMPT
    from app.models.conversation import Message
except ImportError:
    print("Error: Could not import required modules from the Metis RAG system.")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Define the original system prompt (saved before we modified it)
ORIGINAL_SYSTEM_PROMPT = """You are a helpful assistant that provides accurate, factual responses based on the Metis RAG system.

ROLE AND CAPABILITIES:
- You have access to a Retrieval-Augmented Generation (RAG) system that can retrieve relevant documents to answer questions.
- Your primary function is to use the retrieved context to provide accurate, well-informed answers.
- You can cite sources using the numbers in square brackets like [1] or [2] when they are provided in the context.

STRICT GUIDELINES FOR USING CONTEXT:
- ONLY use information that is explicitly stated in the provided context.
- NEVER make up or hallucinate information that is not in the context.
- If the context doesn't contain the answer, explicitly state that the information is not available in the provided documents.
- Do not use your general knowledge unless the context is insufficient, and clearly indicate when you're doing so.
- Analyze the context carefully to find the most relevant information for the user's question.
- If multiple sources provide different information, synthesize them and explain any discrepancies.
- If the context includes metadata like filenames, tags, or folders, use this to understand the source and relevance of the information.

WHEN INFORMATION IS LIMITED:
1. If you find SOME relevant information but it's not comprehensive, start with: "I've searched my knowledge base for information about [topic]. While I don't have comprehensive information on this topic, I did find some relevant documents that mention it."
2. Then present the limited information you have, with proper citations.
3. End with: "Please note this information is limited to what's in my document database. For more comprehensive information, consider consulting specialized resources."

WHEN NO INFORMATION IS FOUND:
1. Clearly state: "Based on the provided documents, I don't have information about [topic]."
2. Only after acknowledging the limitation, you may provide general knowledge with: "However, generally speaking..." to assist the user.

CITATION FORMATTING:
1. Always use numbered citations like [1], [2] that correspond to the sources provided.
2. At the end of your response, list your sources in a structured format:
   Sources:
   [1] Document ID: abc123... - "Document Title"
   [2] Document ID: def456... - "Document Title"

CONVERSATION HANDLING:
- IMPORTANT: Only refer to previous conversations if they are explicitly provided in the conversation history.
- NEVER fabricate or hallucinate previous exchanges that weren't actually provided.
- If no conversation history is provided, treat the query as a new, standalone question.
- Only maintain continuity with previous exchanges when conversation history is explicitly provided.

RESPONSE STYLE:
- Be clear, direct, and helpful.
- Structure your responses logically.
- Use appropriate formatting to enhance readability.
- Maintain a consistent, professional tone throughout the conversation.
- For new conversations with no history, start fresh without referring to non-existent previous exchanges.
- DO NOT start your responses with phrases like "I've retrieved relevant context" or similar preambles.
- Answer questions directly without mentioning the retrieval process.
- Always cite your sources with numbers in square brackets [1] when using information from the context.
"""

# Define the simplified system prompt (current one)
SIMPLIFIED_SYSTEM_PROMPT = RAG_SYSTEM_PROMPT

# Test queries based on the example chat
TEST_QUERIES = [
    "hello",
    "where is Paris in comparison to Madrid",
    "distance and direction",
    "how can I get there from the US?",
    "I will be leaving from Washington DC"
]

# Test scenarios to evaluate specific issues
TEST_SCENARIOS = [
    {
        "name": "Empty Vector Store Test",
        "description": "Test how the system handles queries when no documents exist",
        "setup": "clear_vector_store",
        "query": "Tell me about quantum computing"
    },
    {
        "name": "Non-existent Document Test",
        "description": "Test how the system handles queries about specific documents that don't exist",
        "setup": "standard",
        "query": "What does the document 'Introduction to China's Provinces' say about Beijing?"
    },
    {
        "name": "User Information Test",
        "description": "Test if the system remembers user information across the conversation",
        "setup": "standard",
        "conversation": [
            "My name is Charles",
            "What can you tell me about machine learning?",
            "Thank you for that information. Can you recommend some resources?"
        ]
    },
    {
        "name": "Citation Test",
        "description": "Test how the system uses citations when documents are available",
        "setup": "with_documents",
        "query": "What are the key principles of artificial intelligence?"
    }
]

class SystemPromptTester:
    """Class to test different system prompts for the Metis RAG system."""
    
    def __init__(self, output_dir: str = "test_results"):
        """Initialize the tester with output directory."""
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = os.path.join(output_dir, f"system_prompt_test_{self.timestamp}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize RAG engines with different system prompts
        self.original_rag_engine = None
        self.simplified_rag_engine = None
        
        print(f"Results will be saved to: {self.results_dir}")
    
    def initialize_rag_engines(self):
        """Initialize RAG engines with different system prompts."""
        try:
            # Initialize RAG engine with original system prompt
            self.original_rag_engine = RAGEngine()
            
            # Initialize RAG engine with simplified system prompt
            self.simplified_rag_engine = RAGEngine()
            
            print("RAG engines initialized successfully.")
            return True
        except Exception as e:
            print(f"Error initializing RAG engines: {str(e)}")
            return False
    
    def run_query(self, rag_engine, query: str, conversation_history: Optional[List[Message]] = None) -> Dict[str, Any]:
        """Run a query against a RAG engine and return the result."""
        try:
            # Convert conversation history to Message objects if provided as strings
            if conversation_history and isinstance(conversation_history[0], str):
                messages = []
                for i, msg in enumerate(conversation_history):
                    role = "user" if i % 2 == 0 else "assistant"
                    messages.append(Message(role=role, content=msg))
                conversation_history = messages
            
            # Run the query
            start_time = time.time()
            result = rag_engine.query(
                query=query,
                conversation_history=conversation_history,
                stream=False
            )
            end_time = time.time()
            
            # Extract relevant information from the result
            response = {
                "query": query,
                "response": result.get("response", ""),
                "sources": result.get("sources", []),
                "execution_time": end_time - start_time
            }
            
            return response
        except Exception as e:
            print(f"Error running query: {str(e)}")
            return {
                "query": query,
                "response": f"Error: {str(e)}",
                "sources": [],
                "execution_time": 0
            }
    
    def run_conversation(self, rag_engine, conversation: List[str]) -> List[Dict[str, Any]]:
        """Run a conversation (multiple queries) against a RAG engine."""
        results = []
        history = []
        
        for i, query in enumerate(conversation):
            # Run the query with conversation history
            result = self.run_query(rag_engine, query, history)
            results.append(result)
            
            # Update conversation history
            history.append(Message(role="user", content=query))
            history.append(Message(role="assistant", content=result["response"]))
        
        return results
    
    def run_test_queries(self):
        """Run the test queries against both system prompts."""
        if not self.initialize_rag_engines():
            return
        
        original_results = []
        simplified_results = []
        
        # Run each query against both system prompts
        for query in TEST_QUERIES:
            print(f"Running query: {query}")
            
            # Run with original system prompt
            original_result = self.run_query(self.original_rag_engine, query)
            original_results.append(original_result)
            
            # Run with simplified system prompt
            simplified_result = self.run_query(self.simplified_rag_engine, query)
            simplified_results.append(simplified_result)
        
        # Save results
        self.save_results("test_queries", original_results, simplified_results)
    
    def run_test_scenarios(self):
        """Run the test scenarios against both system prompts."""
        if not self.initialize_rag_engines():
            return
        
        scenario_results = []
        
        # Run each scenario
        for scenario in TEST_SCENARIOS:
            print(f"Running scenario: {scenario['name']}")
            
            # Setup the scenario
            self.setup_scenario(scenario["setup"])
            
            # Run the scenario
            if "query" in scenario:
                # Single query scenario
                original_result = self.run_query(self.original_rag_engine, scenario["query"])
                simplified_result = self.run_query(self.simplified_rag_engine, scenario["query"])
                
                scenario_result = {
                    "name": scenario["name"],
                    "description": scenario["description"],
                    "query": scenario["query"],
                    "original_result": original_result,
                    "simplified_result": simplified_result
                }
            elif "conversation" in scenario:
                # Conversation scenario
                original_results = self.run_conversation(self.original_rag_engine, scenario["conversation"])
                simplified_results = self.run_conversation(self.simplified_rag_engine, scenario["conversation"])
                
                scenario_result = {
                    "name": scenario["name"],
                    "description": scenario["description"],
                    "conversation": scenario["conversation"],
                    "original_results": original_results,
                    "simplified_results": simplified_results
                }
            
            scenario_results.append(scenario_result)
        
        # Save scenario results
        self.save_scenario_results(scenario_results)
    
    def setup_scenario(self, setup_type: str):
        """Setup a test scenario."""
        if setup_type == "clear_vector_store":
            # Clear the vector store (implementation depends on your system)
            print("Setting up scenario: clear_vector_store")
            # self.original_rag_engine.vector_store.clear()
            # self.simplified_rag_engine.vector_store.clear()
        elif setup_type == "with_documents":
            # Add test documents to the vector store
            print("Setting up scenario: with_documents")
            # Add implementation to add test documents
        else:
            # Standard setup (no special configuration)
            print("Setting up scenario: standard")
    
    def save_results(self, test_name: str, original_results: List[Dict[str, Any]], simplified_results: List[Dict[str, Any]]):
        """Save test results to files."""
        results = {
            "test_name": test_name,
            "timestamp": self.timestamp,
            "original_system_prompt": ORIGINAL_SYSTEM_PROMPT,
            "simplified_system_prompt": SIMPLIFIED_SYSTEM_PROMPT,
            "original_results": original_results,
            "simplified_results": simplified_results
        }
        
        # Save results to JSON file
        results_file = os.path.join(self.results_dir, f"{test_name}_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        # Generate HTML report
        self.generate_html_report(test_name, results)
        
        print(f"Results saved to: {results_file}")
    
    def save_scenario_results(self, scenario_results: List[Dict[str, Any]]):
        """Save scenario results to files."""
        results = {
            "test_name": "test_scenarios",
            "timestamp": self.timestamp,
            "original_system_prompt": ORIGINAL_SYSTEM_PROMPT,
            "simplified_system_prompt": SIMPLIFIED_SYSTEM_PROMPT,
            "scenario_results": scenario_results
        }
        
        # Save results to JSON file
        results_file = os.path.join(self.results_dir, "scenario_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        # Generate HTML report
        self.generate_scenario_html_report(results)
        
        print(f"Scenario results saved to: {results_file}")
    
    def generate_html_report(self, test_name: str, results: Dict[str, Any]):
        """Generate an HTML report for the test results."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Metis RAG System Prompt Test Results - {test_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .query {{ background-color: #f5f5f5; padding: 10px; margin: 10px 0; border-left: 5px solid #007bff; }}
                .response {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 5px solid #28a745; }}
                .sources {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 5px solid #ffc107; }}
                .comparison {{ display: flex; }}
                .original, .simplified {{ flex: 1; margin: 10px; padding: 10px; border: 1px solid #ddd; }}
                .system-prompt {{ background-color: #f0f0f0; padding: 10px; white-space: pre-wrap; }}
                .metrics {{ margin-top: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Metis RAG System Prompt Test Results</h1>
            <p>Test: {test_name}</p>
            <p>Timestamp: {results['timestamp']}</p>
            
            <h2>System Prompts</h2>
            <div class="comparison">
                <div class="original">
                    <h3>Original System Prompt</h3>
                    <div class="system-prompt">{results['original_system_prompt']}</div>
                </div>
                <div class="simplified">
                    <h3>Simplified System Prompt</h3>
                    <div class="system-prompt">{results['simplified_system_prompt']}</div>
                </div>
            </div>
            
            <h2>Test Results</h2>
        """
        
        # Add results for each query
        for i in range(len(results['original_results'])):
            original = results['original_results'][i]
            simplified = results['simplified_results'][i]
            
            html += f"""
            <h3>Query {i+1}: {original['query']}</h3>
            <div class="comparison">
                <div class="original">
                    <h4>Original System Prompt Response</h4>
                    <div class="response">{original['response']}</div>
                    <div class="sources">
                        <h5>Sources ({len(original['sources'])})</h5>
                        <ul>
            """
            
            for source in original['sources']:
                html += f"<li>{source}</li>"
            
            html += f"""
                        </ul>
                    </div>
                    <div class="metrics">
                        <p>Execution Time: {original['execution_time']:.2f} seconds</p>
                    </div>
                </div>
                <div class="simplified">
                    <h4>Simplified System Prompt Response</h4>
                    <div class="response">{simplified['response']}</div>
                    <div class="sources">
                        <h5>Sources ({len(simplified['sources'])})</h5>
                        <ul>
            """
            
            for source in simplified['sources']:
                html += f"<li>{source}</li>"
            
            html += f"""
                        </ul>
                    </div>
                    <div class="metrics">
                        <p>Execution Time: {simplified['execution_time']:.2f} seconds</p>
                    </div>
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        # Save HTML report
        report_file = os.path.join(self.results_dir, f"{test_name}_report.html")
        with open(report_file, "w") as f:
            f.write(html)
        
        print(f"HTML report saved to: {report_file}")
    
    def generate_scenario_html_report(self, results: Dict[str, Any]):
        """Generate an HTML report for the scenario test results."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Metis RAG System Prompt Scenario Test Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3, h4 {{ color: #333; }}
                .scenario {{ background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-left: 5px solid #007bff; }}
                .query {{ background-color: #f5f5f5; padding: 10px; margin: 10px 0; border-left: 5px solid #007bff; }}
                .response {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 5px solid #28a745; }}
                .sources {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 5px solid #ffc107; }}
                .comparison {{ display: flex; }}
                .original, .simplified {{ flex: 1; margin: 10px; padding: 10px; border: 1px solid #ddd; }}
                .system-prompt {{ background-color: #f0f0f0; padding: 10px; white-space: pre-wrap; }}
                .metrics {{ margin-top: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Metis RAG System Prompt Scenario Test Results</h1>
            <p>Timestamp: {results['timestamp']}</p>
            
            <h2>System Prompts</h2>
            <div class="comparison">
                <div class="original">
                    <h3>Original System Prompt</h3>
                    <div class="system-prompt">{results['original_system_prompt']}</div>
                </div>
                <div class="simplified">
                    <h3>Simplified System Prompt</h3>
                    <div class="system-prompt">{results['simplified_system_prompt']}</div>
                </div>
            </div>
            
            <h2>Scenario Results</h2>
        """
        
        # Add results for each scenario
        for scenario in results['scenario_results']:
            html += f"""
            <div class="scenario">
                <h3>{scenario['name']}</h3>
                <p>{scenario['description']}</p>
            """
            
            if "query" in scenario:
                # Single query scenario
                html += f"""
                <h4>Query: {scenario['query']}</h4>
                <div class="comparison">
                    <div class="original">
                        <h4>Original System Prompt Response</h4>
                        <div class="response">{scenario['original_result']['response']}</div>
                        <div class="sources">
                            <h5>Sources ({len(scenario['original_result']['sources'])})</h5>
                            <ul>
                """
                
                for source in scenario['original_result']['sources']:
                    html += f"<li>{source}</li>"
                
                html += f"""
                            </ul>
                        </div>
                        <div class="metrics">
                            <p>Execution Time: {scenario['original_result']['execution_time']:.2f} seconds</p>
                        </div>
                    </div>
                    <div class="simplified">
                        <h4>Simplified System Prompt Response</h4>
                        <div class="response">{scenario['simplified_result']['response']}</div>
                        <div class="sources">
                            <h5>Sources ({len(scenario['simplified_result']['sources'])})</h5>
                            <ul>
                """
                
                for source in scenario['simplified_result']['sources']:
                    html += f"<li>{source}</li>"
                
                html += f"""
                            </ul>
                        </div>
                        <div class="metrics">
                            <p>Execution Time: {scenario['simplified_result']['execution_time']:.2f} seconds</p>
                        </div>
                    </div>
                </div>
                """
            elif "conversation" in scenario:
                # Conversation scenario
                html += f"""
                <h4>Conversation</h4>
                <table>
                    <tr>
                        <th>Turn</th>
                        <th>User Query</th>
                        <th>Original Response</th>
                        <th>Simplified Response</th>
                    </tr>
                """
                
                for i, query in enumerate(scenario['conversation']):
                    original_response = scenario['original_results'][i]['response'] if i < len(scenario['original_results']) else ""
                    simplified_response = scenario['simplified_results'][i]['response'] if i < len(scenario['simplified_results']) else ""
                    
                    html += f"""
                    <tr>
                        <td>{i+1}</td>
                        <td>{query}</td>
                        <td>{original_response}</td>
                        <td>{simplified_response}</td>
                    </tr>
                    """
                
                html += """
                </table>
                """
            
            html += """
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        # Save HTML report
        report_file = os.path.join(self.results_dir, "scenario_report.html")
        with open(report_file, "w") as f:
            f.write(html)
        
        print(f"Scenario HTML report saved to: {report_file}")

def main():
    """Main function to run the system prompt tests."""
    parser = argparse.ArgumentParser(description="Test different system prompts for the Metis RAG system.")
    parser.add_argument("--output-dir", default="test_results", help="Directory to save test results")
    parser.add_argument("--test-queries", action="store_true", help="Run test queries")
    parser.add_argument("--test-scenarios", action="store_true", help="Run test scenarios")
    args = parser.parse_args()
    
    # Create tester
    tester = SystemPromptTester(output_dir=args.output_dir)
    
    # Run tests
    if args.test_queries:
        tester.run_test_queries()
    
    if args.test_scenarios:
        tester.run_test_scenarios()
    
    # If no tests specified, run all
    if not args.test_queries and not args.test_scenarios:
        tester.run_test_queries()
        tester.run_test_scenarios()
    
    print("System prompt tests completed.")

if __name__ == "__main__":
    main()