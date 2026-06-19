import re
import nltk
from rank_bm25 import BM25Okapi


nltk.download('punkt')
nltk.download('punkt_tab')
from sentence_transformers import SparseEncoder
from sentence_transformers.util import semantic_search


class FinancialRetriever:
    def __init__(self, chunks):
        self.chunks = chunks

        # Tokenize corpus
        self.tokenized_chunks = [
            re.findall(r'\w+', chunk["text"].lower())
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(self.tokenized_chunks)

    def is_table_chunk(self, chunk):
        """
        Detect whether chunk contains a table.
        Works for both page chunks and structure-aware chunks.
        """

        # If type information already exists, trust it
        if "type" in chunk:
            return chunk["type"] == "table"

        text = chunk["text"]

        # Markdown table
        if "|" in text:
            return True

        # Numeric row heuristic
        lines = text.splitlines()

        numeric_lines = sum(
            1
            for line in lines
            if len(re.findall(r'\d', line)) >= 2
        )

        return numeric_lines >= 3

    def retrieve(self, fund_name, top_k):

        queries = [
            fund_name,
            "performance return MTD YTD",
            "net return benchmark",
            "asset names holdings securities",
        ]
        rrf_scores = {}

        for query in queries:

            query_tokens = re.findall(r'\w+', query.lower())

            scores = self.bm25.get_scores(query_tokens)

            ranked_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:20]

            for rank, idx in enumerate(ranked_indices):

                # Reciprocal Rank Fusion
                score = 1 / (60 + rank)

                chunk = self.chunks[idx]["text"].lower()

                # ---------- Business boosts ----------

                # Table boost
                performance_keywords = [
                    "return", "returns",
                    "performance",
                    "mtd", "ytd",
                    "month-to-date",
                    "year-to-date",
                    "nav",
                    "gain", "loss",
                    "%", "benchmark"
                ]

                chunk_text = self.chunks[idx]["text"].lower()

                if self.is_table_chunk(self.chunks[idx]):
                    if any(keyword in chunk_text for keyword in performance_keywords):
                        score += 0.3

                # Performance boost
                performance_words = [
                    "return",
                    "performance",
                    "mtd",
                    "ytd",
                    "benchmark",
                    "net return"
                ]

                if any(word in chunk for word in performance_words):
                    score += 0.2

                # Asset boost
                asset_words = [
                    "asset",
                    "holding",
                    "security",
                    "weight"
                ]

                if any(word in chunk for word in asset_words):
                    score += 0.2

                # Fund name boost
                if fund_name.lower() in chunk:
                    score += 0.3

                rrf_scores[idx] = rrf_scores.get(idx, 0) + score

        # Final ranking
        final_indices = sorted(
            rrf_scores,
            key=rrf_scores.get,
            reverse=True
        )[:top_k]

        results = []

        for i in final_indices:

            chunk = self.chunks[i].copy()

            chunk["score"] = round(rrf_scores[i], 4)

            results.append(chunk)

        return results
