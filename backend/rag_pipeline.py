"""
LangChain RAG pipeline: retrieves relevant document chunks and generates grounded answers.
"""

from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.vectorstores import FAISS


SUGGESTED_QUESTIONS = (
    "\n\nHere are some questions I can help you with:\n"
    "• What is the meal reimbursement limit?\n"
    "• What approvals are needed for vendor payments above $25,000?\n"
    "• Can I fly business class on international trips?\n"
    "• What documents are required for a procurement request?\n"
    "• How do I submit an expense report?\n"
    "• What is the hotel rate limit for business travel?\n"
    "• Are contractor payments subject to tax withholding?\n"
    "• What is the corporate purchase card spending limit?"
)

OFFTOPIC_REPLY = (
    "Hi! I'm your Finance Policy Assistant. "
    "I can only answer questions about company finance policies."
    + SUGGESTED_QUESTIONS
)

# Single-brace placeholders — required by PromptTemplate (template_format="f-string")
SYSTEM_PROMPT = (
    "You are a Finance Policy Assistant for an enterprise organization.\n"
    "You answer employee questions ONLY about company finance policies "
    "using the retrieved document context below.\n\n"
    "STRICT RULES:\n"
    "1. If the employee message is a greeting, small talk, or unrelated to finance "
    "(e.g. 'hi', 'hello', 'how are you'), respond ONLY with:\n"
    "   'Hi! I am your Finance Policy Assistant. "
    "I can only answer questions about company finance policies. "
    + SUGGESTED_QUESTIONS + "'\n"
    "   Do NOT use conversation history to generate an answer in this case.\n\n"
    "2. If the question is finance-related but the retrieved context does NOT contain "
    "relevant information, respond ONLY with:\n"
    "   'I could not find specific information about that in the finance policy documents. "
    "Please contact the Finance team at finance-help@company.com or ext. 4400."
    + SUGGESTED_QUESTIONS + "'\n\n"
    "3. If the retrieved context IS relevant, answer clearly and concisely based strictly "
    "on that context. Mention specific limits, thresholds, or approval levels when available. "
    "Do NOT invent any policy details not present in the context.\n\n"
    "Retrieved context from finance policy documents:\n{context}\n\n"
    "Conversation history:\n{chat_history}\n\n"
    "Employee question: {question}\n\n"
    "Answer:"
)

CONDENSE_PROMPT = PromptTemplate.from_template(
    "Given the conversation history and a follow-up question, rephrase the follow-up "
    "into a standalone question that captures all necessary context.\n\n"
    "Conversation history:\n{chat_history}\n\n"
    "Follow-up question: {question}\n\n"
    "Standalone question:"
)

QA_PROMPT = PromptTemplate(
    input_variables=["context", "chat_history", "question"],
    template=SYSTEM_PROMPT,
)

# Words/phrases that should bypass the LLM entirely
_OFFTOPIC_EXACT = {
    "hi", "hai", "hello", "hey", "hii", "helo", "hiya", "heya",
    "how are you", "what's up", "sup", "good morning", "good afternoon",
    "good evening", "bye", "goodbye", "thanks", "thank you", "ok", "okay",
    "great", "nice", "cool", "test", "testing",
}


def is_offtopic(question: str) -> bool:
    normalized = question.strip().lower().rstrip("!.,?")
    if len(normalized) < 3:
        return True
    return normalized in _OFFTOPIC_EXACT


def build_rag_chain(vector_store: FAISS, api_key: str) -> ConversationalRetrievalChain:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=api_key,
    )

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )

    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        output_key="answer",
        return_messages=True,
        k=6,
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        condense_question_prompt=CONDENSE_PROMPT,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        return_source_documents=True,
        verbose=False,
    )

    return chain


def query_rag(chain: ConversationalRetrievalChain, question: str) -> dict:
    # Short-circuit off-topic/greeting queries — never hits the LLM
    if is_offtopic(question):
        return {"answer": OFFTOPIC_REPLY, "sources": []}

    result = chain.invoke({"question": question})

    sources = []
    seen = set()
    for doc in result.get("source_documents", []):
        source = doc.metadata.get("source", "Unknown")
        snippet = doc.page_content[:300].strip()
        key = (source, snippet[:80])
        if key not in seen:
            seen.add(key)
            sources.append({"source": source, "snippet": snippet})

    return {"answer": result["answer"], "sources": sources}
