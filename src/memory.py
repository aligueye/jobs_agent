from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from dotenv import load_dotenv
load_dotenv()

'''
to build the profile index, run:

python -c "import sys; sys.path.insert(0,'.'); from src.memory import build_profile_index; build_profile_index()"

'''

def build_profile_index(store_dir="data/chroma"):
    text = Path("data/profile.md").read_text(encoding="utf-8")
    splits = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100).split_text(text)
    vec = Chroma(collection_name="profile", persist_directory=store_dir,
                 embedding_function=OpenAIEmbeddings())
    vec.delete_collection(); vec = Chroma(collection_name="profile", persist_directory=store_dir,
                                          embedding_function=OpenAIEmbeddings())
    vec.add_texts(splits)
    return vec

def get_retriever(store_dir="data/chroma"):
    return Chroma(collection_name="profile", persist_directory=store_dir,
                  embedding_function=OpenAIEmbeddings()).as_retriever(k=4)