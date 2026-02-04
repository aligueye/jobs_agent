import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestBuildProfileIndex:
    @patch("src.memory.Chroma")
    @patch("src.memory.OpenAIEmbeddings")
    @patch("src.memory.Path.read_text")
    def test_build_profile_index_creates_chunks(self, mock_read, mock_embeddings, mock_chroma):
        mock_read.return_value = "A" * 2000  # Text that will be chunked
        mock_vec = MagicMock()
        mock_chroma.return_value = mock_vec

        from src.memory import build_profile_index
        build_profile_index(store_dir="test_store")

        # Should call add_texts with chunked text
        mock_vec.add_texts.assert_called_once()
        added_texts = mock_vec.add_texts.call_args[0][0]
        assert len(added_texts) > 1  # Should be split into chunks

    @patch("src.memory.Chroma")
    @patch("src.memory.OpenAIEmbeddings")
    @patch("src.memory.Path.read_text")
    def test_build_profile_index_deletes_existing_collection(self, mock_read, mock_embeddings, mock_chroma):
        mock_read.return_value = "Test profile content"
        mock_vec = MagicMock()
        mock_chroma.return_value = mock_vec

        from src.memory import build_profile_index
        build_profile_index()

        # Should delete collection before adding new texts
        mock_vec.delete_collection.assert_called_once()


class TestGetRetriever:
    @patch("src.memory.Chroma")
    @patch("src.memory.OpenAIEmbeddings")
    def test_get_retriever_returns_retriever(self, mock_embeddings, mock_chroma):
        mock_vec = MagicMock()
        mock_retriever = MagicMock()
        mock_vec.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_vec

        from src.memory import get_retriever
        result = get_retriever(store_dir="test_store")

        assert result == mock_retriever
        mock_vec.as_retriever.assert_called_once_with(k=4)

    @patch("src.memory.Chroma")
    @patch("src.memory.OpenAIEmbeddings")
    def test_get_retriever_uses_correct_collection(self, mock_embeddings, mock_chroma):
        mock_chroma.return_value = MagicMock()

        from src.memory import get_retriever
        get_retriever(store_dir="custom_store")

        mock_chroma.assert_called_with(
            collection_name="profile",
            persist_directory="custom_store",
            embedding_function=mock_embeddings.return_value,
        )
