from typing import Callable

from .store import EmbeddingStore

NO_CONTEXT_ANSWER = "Không tìm thấy thông tin liên quan trong kho tài liệu để trả lời câu hỏi này."


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            # Store rỗng: không gọi LLM vô ích.
            return NO_CONTEXT_ANSWER

        # Đánh số từng chunk kèm nguồn để câu trả lời truy vết được về đúng tài liệu.
        context_blocks = []
        for number, result in enumerate(results, start=1):
            metadata = result["metadata"]
            source = metadata.get("source_url") or metadata.get("source") or metadata.get("doc_id", result["id"])
            context_blocks.append(f"[{number}] (nguồn: {source})\n{result['content'].strip()}")
        context = "\n\n".join(context_blocks)

        prompt = (
            "Bạn là trợ lý trả lời câu hỏi dựa trên kho tài liệu.\n"
            "Quy tắc:\n"
            "- Chỉ dùng thông tin trong phần NGỮ CẢNH bên dưới, không suy đoán hay thêm kiến thức ngoài.\n"
            "- Ghi số thứ tự đoạn ngữ cảnh đã dùng, ví dụ [1] hoặc [1][3], ngay sau ý tương ứng.\n"
            f"- Nếu ngữ cảnh không đủ để trả lời, nói rõ: \"{NO_CONTEXT_ANSWER}\"\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI:"
        )
        return self.llm_fn(prompt)
