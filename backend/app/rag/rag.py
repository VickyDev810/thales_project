import json
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA

class Rag:
    def __init__(self, input_file):
        self.input_file = input_file
        self.pii_map_file = f"{input_file}_pii_map.json"  # Unique filename per run
        self.chunk_size = 500
        self.chunk_overlap = 50
        self.output_path = self._run()  # Stores path to output file

    def _run(self):
        print("📄 Loading document...")
        loader = TextLoader(self.input_file)
        docs = loader.load()

        print("✂️ Splitting text into chunks...")
        splitter = CharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        chunks = splitter.split_documents(docs)

        print("🧠 Setting up LLM and embeddings...")
        llm = OllamaLLM(model="mistral", base_url="http://localhost:11434")
        embeddings = OllamaEmbeddings(model="mistral", base_url="http://localhost:11434")

        print("📦 Creating vector store...")
        vectorstore = FAISS.from_documents(chunks, embeddings)
        retriever = vectorstore.as_retriever()

        print("🔗 Building QA chain...")
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True,
            output_key="result"
        )

        QUERY_TEMPLATE = """
        Identify all personally identifiable information (PII) in this text. 
        For each piece of PII, return the following fields:
        - "value": the actual text
        - "type": the kind of PII (e.g., Name, Email, SSN, etc.)
        - "confidence": float from 0 to 1
        - "safe_to_mask": true only

        Return the result as a JSON array.
        """.strip()

        pii_results = []

        for i, chunk in enumerate(chunks):
            print(f"🔍 Processing chunk {i+1}/{len(chunks)}...")
            query = QUERY_TEMPLATE + "\n\nText:\n" + chunk.page_content
            response = qa_chain.invoke({"query": query})

            try:
                parsed = json.loads(response["result"])
                if isinstance(parsed, list):
                    pii_results.extend(parsed)
                else:
                    raise ValueError("Response is not a JSON array.")
            except (json.JSONDecodeError, ValueError):
                print(f"⚠️ Invalid JSON for chunk {i+1}. Skipping.")
                print("Raw output:", response["result"])

        with open(self.pii_map_file, "w") as f:
            json.dump(pii_results, f, indent=4)

        print(f"\n✅ Done. PII map saved to: {self.pii_map_file}")
        return self.pii_map_file
