from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Optional
from langchain_core.documents import Document


class DocumentUsageTracker:
    """
    Tracks how frequently Documents are used in a Text2SQL system,
    including which user questions triggered each document.
    """

    def __init__(self, csv_path: str | Path, track_timestamp: bool = True) -> None:
        self.csv_path = Path(csv_path)
        self.track_timestamp = track_timestamp
        self.usage_counts: Counter[str] = Counter()
        self.question_log: Dict[str, List[str]] = defaultdict(list)
        self._load_existing_data()

    def _load_existing_data(self) -> None:
        """Load existing document usage and question logs from CSV file."""
        if not self.csv_path.exists():
            return

        with self.csv_path.open(mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                doc_id = row["document_id"]
                self.usage_counts[doc_id] = int(row["usage_count"])
                questions = row.get("questions", "")
                if questions:
                    self.question_log[doc_id] = questions.split(" ||| ")

    def update_usage(self, example_docs: List[Document], question: Optional[str] = None) -> None:
        """
        Update usage count for each Document in the list,
        optionally linking them to a specific user question.
        Avoids duplicate question entries for the same document.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if self.track_timestamp else None

        for doc in example_docs:
            if not doc.id:
                continue
            self.usage_counts[doc.id] += 1

            if question:
                # If timestamp tracking is on, include timestamp
                entry = f"{question} (at {timestamp})" if timestamp else question
                # Avoid duplicate entries for the same question
                existing_questions = [q.split(" (at ")[0] for q in self.question_log[doc.id]]
                if question not in existing_questions:
                    self.question_log[doc.id].append(entry)

    def save_to_csv(self) -> None:
        """Persist the document usage data and questions to CSV."""
        with self.csv_path.open(mode="w", newline="", encoding="utf-8") as file:
            fieldnames = ["document_id", "usage_count", "questions"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for doc_id, count in self.usage_counts.items():
                questions_joined = " ||| ".join(self.question_log.get(doc_id, []))
                writer.writerow({
                    "document_id": doc_id,
                    "usage_count": count,
                    "questions": questions_joined
                })

    def get_usage_summary(self) -> Dict[str, Dict[str, int | List[str]]]:
        """
        Return a structured summary containing both usage counts and question logs.
        Example:
        {
            'doc_id': {'usage_count': 3, 'questions': ['Q1', 'Q2']}
        }
        """
        summary = {}
        for doc_id, count in self.usage_counts.items():
            summary[doc_id] = {
                "usage_count": count,
                "questions": self.question_log.get(doc_id, [])
            }
        return summary

    def print_summary(self, top_n: Optional[int] = None) -> None:
        """
        Print a formatted, sorted table summary of document usage.
        Optionally limit to top_n most frequently used documents.
        """
        summary = self.get_usage_summary()
        sorted_docs = sorted(summary.items(), key=lambda x: x[1]["usage_count"], reverse=True)

        if top_n:
            sorted_docs = sorted_docs[:top_n]

        print("\n📊 Document Usage Summary")
        print("-" * 120)
        print(f"{'Document ID':<40} | {'Usage Count':<12} | Recent Questions")
        print("-" * 120)

        for doc_id, data in sorted_docs:
            usage = data["usage_count"]
            # Show last two questions for readability
            recent_questions = ", ".join(data["questions"][-2:])
            if len(recent_questions) > 70:
                recent_questions = recent_questions[:67] + "..."
            print(f"{doc_id:<40} | {usage:<12} | {recent_questions}")

        print("-" * 120)
        print(f"Total unique documents tracked: {len(summary)}\n")


# Example Usage
if __name__ == "__main__":
    # Example list of top 3 Documents (from your system)
    example_docs: List[Document] = [
        Document(id="e8039df7-5df1-4688-9a51-1ab48ee4a190", metadata={}, page_content="..."),
        Document(id="9ad45f4e-3640-47b0-97fb-b9a2d62e4784", metadata={}, page_content="..."),
        Document(id="611927b3-6692-4866-9e7e-7a829bd4b536", metadata={}, page_content="...")
    ]

    # Create tracker instance
    tracker = DocumentUsageTracker("document_usage.csv")

    # Simulate repeated user questions
    question_1 = "What is the liquidation price reported for transaction X?"
    question_2 = "What transaction fees apply for transfer Y?"

    tracker.update_usage(example_docs, question=question_1)
    tracker.update_usage(example_docs, question=question_1)  # same question again
    tracker.update_usage(example_docs, question=question_2)

    tracker.save_to_csv()
    tracker.print_summary(top_n=3)
