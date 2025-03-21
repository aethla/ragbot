# -*- coding: utf-8 -*-
"""Copy of RAG for Finance.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1fN1SbIG1vnGs0QtuRh21OjjbBZ9HN0fU

# RAG for Finance - Introduction

### Mounting Google Drive
"""

from google.colab import drive
drive.mount('/content/drive')

"""### Installing Necessary Libraries"""

# get the versions and packages for huggingface space requirements -- use pip freeze

!pip install langchain langchain-core langchain-groq langchain-community chromadb pypdf langchain-huggingface xformers
!pip uninstall transformers -y
!pip install transformers
!pip uninstall torch torchvision -y
!pip install torch torchvision

"""### Importing Necessary Libraries"""

# LLM Service and Embeddings
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

# Document Processing
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# Chain Management
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain import hub

"""### Defining Constants"""

from google.colab import userdata
# import chromadb

GROQ_API_KEY = userdata.get('GROQ_API_KEY')
MODEL_ID = "deepseek-r1-distill-llama-70b"
#PDF_PATH = "/content/drive/MyDrive/Coding/chatbot/10-Q4-2024-As-Filed.pdf"
FOLDER_PATH = "/content/drive/MyDrive/Coding/chatbot/"
device = "cuda:0" if torch.cuda.is_available() else "cpu"

# # Initialize ChromaDB client
# db = chromadb.PersistentClient(path="./chroma_db")

"""###Set up Logging"""

# Setup logging
logging.basicConfig(filename="system.log", level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filemode='a'
                    )
logging.info("System initialized.")

"""### Setting Up Chat Model Inference"""

# Initialize the LLM
llm = ChatGroq(model=MODEL_ID, api_key=GROQ_API_KEY)

# Example usage - Invoking
# result = llm.invoke("Solve me fibonacci sequence?")
# print(result.content)

# Example usage - Streaming
# for chunk in llm.stream("Solve me fibonacci sequence?"):
#   print(chunk.content, end="")

"""### Loading PDF documents"""

# Ensure the folder exists
os.makedirs(FOLDER_PATH, exist_ok=True)

# Load all PDF documents from a folder
documents = []
for filename in os.listdir(FOLDER_PATH):
    if filename.lower().endswith('.pdf'): #CHANGE loader to word file- check if google docs file is compatible with langchain loader
        pdf_loader = PyPDFLoader(os.path.join(FOLDER_PATH, filename))
        documents.extend(pdf_loader.load())

len(documents)

"""### Splitting the Document into Manageable Chunks"""

# Split text into chunks
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    return text_splitter.split_documents(documents)

docs = split_documents(documents)

"""To know more about splitters: https://medium.com/@harsh.vardhan7695/mastering-text-splitting-in-langchain-735313216e01

### Loading Embeddings from HuggingFace model hub
"""

model_name = "NovaSearch/stella_en_400M_v5"
model_kwargs = {'device': device, 'trust_remote_code': True}
encode_kwargs = {'normalize_embeddings': False}
hf = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

#optional - get HF_TOKEN from huggingface account

"""Model selected based on: https://huggingface.co/spaces/mteb/leaderboard

### Creating and Storing Embeddings in ChromaDB
"""

# Create embeddings and store them in ChromaDB
def create_vectorstore(documents):
    # embeddings = OpenAIEmbeddings()
    persist_directory = "chroma_db"
    vectorstore = Chroma.from_documents(documents, hf, persist_directory=persist_directory, collection_name="financial_docs")
    return vectorstore

vectorstore = create_vectorstore(docs)

"""For confirming if our embedding model work correctly.

"""

query = "What kind of financial risks does Apple have and how can these be mitigated?"
docs = vectorstore.similarity_search(query, k=5) #shows the numbers of search results
for doc in docs:
    print(doc.page_content, "----sep-----")

"""### Setting Up Retrieval Chain"""

retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
combine_docs_chain = create_stuff_documents_chain(
    llm, retrieval_qa_chat_prompt
)

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})
retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

"""Source of the prompt: https://smith.langchain.com/hub/langchain-ai/retrieval-qa-chat

Regular Output
"""

results = retrieval_chain.invoke({"input": "What kind of financial risks does Apple have and how can these be mitigated?"})
print(results['answer'])

"""Streaming output"""

for item in retrieval_chain.stream({"input": "What is Apple’s current ratio over the last 3 years, and how has it changed?"}):
  if item.get('answer'):
    print(item.get('answer'), end="")

for item in retrieval_chain.stream({"input": "What kind of financial risks does Apple have and how can these be mitigated?"}):
  if item.get('answer'):
    print(item.get('answer'), end="")