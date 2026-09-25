import json
from agents.orchestrator import AgentOrchestrator

def generate_training_data(topics):
    orchestrator = AgentOrchestrator()
    dataset = []

    for topic in topics:
        print(f"Generating data for: {topic}...")
        result = orchestrator.process_request(topic)

        # We create a pair: Input (Project Idea) -> Output (Full SRS & SDLC)
        entry = {
            "instruction": f"Generate a full SRS and SDLC plan for the following financial project idea: {topic}",
            "output": f"REQUIREMENTS:\n{result['requirements']}\n\nCOMPLIANCE:\n{result['compliance']}\n\nSDLC:\n{result['sdlc']}\n\nFULL_SRS:\n{result['srs_plan']}"
        }
        dataset.append(entry)

    with open("financial_sdlc_dataset.jsonl", "w") as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    # Define a wide range of financial domains to ensure the model is robust
    financial_topics = [
        "A digital KYC (Know Your Customer) system for rural banking",
        "A blockchain-based cross-border payment gateway for SMEs",
        "An AI-driven credit scoring system for micro-loans",
        "A regulatory reporting tool for Basel III compliance",
        "A real-time fraud detection system for credit card transactions",
        "A digital wealth management platform for Gen-Z investors",
        "An automated loan origination system for home mortgages",
        "A central bank digital currency (CBDC) wallet implementation",
        "An insurance claims processing system using OCR and AI",
        "A trade finance platform for automating Letters of Credit"
    ]
    generate_training_data(financial_topics)
    print("Dataset generated: financial_sdlc_dataset.jsonl")
