import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

import pandas as pd
import ollama

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ---------------- APP SETUP ----------------
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

qa_chain = None

# ---------------- HELPERS ----------------
def load_document(path):
    if path.endswith(".pdf"):
        return PyPDFLoader(path).load()
    if path.endswith(".docx"):
        return Docx2txtLoader(path).load()
    if path.endswith((".xls", ".xlsx")):
        df = pd.read_excel(path)
        return [{"page_content": df.to_string(), "metadata": {"source": path}}]
    return []

def build_chain(docs, model):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)

    embeddings = OllamaEmbeddings(model=model)
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever()

    llm = OllamaLLM(model=model)

    prompt = ChatPromptTemplate.from_template(
        """Answer the question using ONLY the context below:

        {context}

        Question: {question}
        Answer:"""
    )

    return (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    global qa_chain

    file = request.files.get("file")
    model = request.form.get("model", "llama3:latest")

    if not file:
        return jsonify({"error": "No file"}), 400

    path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(path)

    docs = load_document(path)
    qa_chain = build_chain(docs, model)

    return jsonify({"message": "Document processed successfully"})

@app.route("/chat", methods=["POST"])
def chat():
    if not qa_chain:
        return jsonify({"response": "Upload a document first."})

    query = request.json.get("query")
    answer = qa_chain.invoke(query)
    return jsonify({"response": answer})

# ---------------- RUN ----------------
if __name__ == "__main__":
    print("🚀 Flask starting on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
