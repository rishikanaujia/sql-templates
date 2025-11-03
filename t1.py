import csv
from collections import Counter
from pathlib import Path
from langchain_core.documents import Document

# Simulated example_docs (replace this with your actual object in your code)
example_docs = [
    Document(id="e8039df7-5df1-4688-9a51-1ab48ee4a190", metadata={}, page_content="..."),
    Document(id="9ad45f4e-3640-47b0-97fb-b9a2d62e4784", metadata={}, page_content="..."),
    Document(id="611927b3-6692-4866-9e7e-7a829bd4b536", metadata={}, page_content="...")
]

# CSV file path
CSV_FILE = Path("document_usage.csv")

def update_usage(example_docs):
    """
    Track how many times each Document (by ID) appears in example_docs.
    Append or update the usage count in a CSV file.
    """
    # Extract document IDs
    doc_ids = [doc.id for doc in example_docs]

    # Load existing usage counts
    usage = Counter()
    if CSV_FILE.exists():
        with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                usage[row["document_id"]] = int(row["usage_count"])

    # Update usage count
    for doc_id in doc_ids:
        usage[doc_id] += 1

    # Write back to CSV
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["document_id", "usage_count"])
        writer.writeheader()
        for doc_id, count in usage.items():
            writer.writerow({"document_id": doc_id, "usage_count": count})

    print("✅ Document usage updated successfully!")
    for doc_id, count in usage.items():
        print(f"{doc_id}: {count} uses")


# Example usage
if __name__ == "__main__":
    update_usage(example_docs)
