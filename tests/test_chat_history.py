"""Comprehensive automated unit tests for JARVIS Chat History & Recent Conversations."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app.database import get_connection, initialize_schema
from app.services.chat_history import (
    ChatHistoryService,
    generate_conversation_title,
    get_chat_history_service,
)


class TestChatHistoryService(unittest.TestCase):
    """Test suite verifying persistent conversation and message lifecycle in SQLite."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_jarvis.db")
        # Initialize schema in temporary database
        conn = get_connection(self.db_path)
        initialize_schema(conn)
        conn.commit()
        conn.close()
        self.service = ChatHistoryService(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. Create a conversation
    def test_create_conversation(self):
        conv = self.service.create_conversation(title="Test Chat")
        self.assertTrue(conv["id"].startswith("conv_"))
        self.assertEqual(conv["title"], "Test Chat")
        self.assertIsNotNone(conv["created_at"])
        self.assertIsNotNone(conv["updated_at"])

        # Verify persisted in database
        fetched = self.service.get_conversation(conv["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], conv["id"])
        self.assertEqual(fetched["title"], "Test Chat")

    # 2. List conversations in recent-first order
    def test_list_conversations_recent_first_order(self):
        conv1 = self.service.create_conversation(title="Chat 1")
        conv2 = self.service.create_conversation(title="Chat 2")
        conv3 = self.service.create_conversation(title="Chat 3")

        # Now save a message in Chat 1 to bump its updated_at
        self.service.save_message(conv1["id"], role="user", content="Bump Chat 1")

        convs = self.service.get_conversations()
        self.assertEqual(len(convs), 3)
        # Chat 1 should be first because it was updated most recently
        self.assertEqual(convs[0]["id"], conv1["id"])

    # 3. Save user and assistant messages
    def test_save_user_and_assistant_messages(self):
        conv = self.service.create_conversation()
        user_msg = self.service.save_message(conv["id"], role="user", content="Hello Jarvis")
        asst_msg = self.service.save_message(conv["id"], role="assistant", content="Hello! How can I help?")

        self.assertEqual(user_msg["role"], "user")
        self.assertEqual(user_msg["content"], "Hello Jarvis")
        self.assertEqual(user_msg["sequence_number"], 1)

        self.assertEqual(asst_msg["role"], "assistant")
        self.assertEqual(asst_msg["content"], "Hello! How can I help?")
        self.assertEqual(asst_msg["sequence_number"], 2)

    # 4. Retrieve messages in deterministic sequence order
    def test_retrieve_messages_in_correct_order(self):
        conv = self.service.create_conversation()
        self.service.save_message(conv["id"], role="user", content="First question")
        self.service.save_message(conv["id"], role="assistant", content="First answer")
        self.service.save_message(conv["id"], role="user", content="Second question")
        self.service.save_message(conv["id"], role="assistant", content="Second answer")

        msgs = self.service.get_messages(conv["id"])
        self.assertEqual(len(msgs), 4)
        self.assertEqual([m["sequence_number"] for m in msgs], [1, 2, 3, 4])
        self.assertEqual(msgs[0]["content"], "First question")
        self.assertEqual(msgs[1]["content"], "First answer")
        self.assertEqual(msgs[2]["content"], "Second question")
        self.assertEqual(msgs[3]["content"], "Second answer")

    # 5. Restore conversation after recreating repository/service
    def test_restore_conversation_after_service_recreation(self):
        conv = self.service.create_conversation(title="Persisted Across Restarts")
        self.service.save_message(conv["id"], role="user", content="Important note")

        # Simulate fresh app startup by creating a new service instance with same DB
        fresh_service = ChatHistoryService(db_path=self.db_path)
        fetched_conv = fresh_service.get_conversation(conv["id"])
        self.assertIsNotNone(fetched_conv)
        self.assertEqual(fetched_conv["title"], "Persisted Across Restarts")

        msgs = fresh_service.get_messages(conv["id"])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["content"], "Important note")

    # 6. Continue an existing conversation without creating a new one
    def test_continue_existing_conversation(self):
        conv = self.service.create_conversation(title="Active Discussion")
        self.service.save_message(conv["id"], role="user", content="Part 1")

        # Follow up in the same session
        self.service.save_message(conv["id"], role="assistant", content="Response 1")
        self.service.save_message(conv["id"], role="user", content="Part 2")

        all_convs = self.service.get_conversations()
        self.assertEqual(len(all_convs), 1, "Only one conversation should exist")
        self.assertEqual(all_convs[0]["id"], conv["id"])

        msgs = self.service.get_messages(conv["id"])
        self.assertEqual(len(msgs), 3)

    # 7. Ensure messages from two conversations never mix
    def test_messages_from_two_conversations_never_mix(self):
        conv_a = self.service.create_conversation(title="Conversation A")
        conv_b = self.service.create_conversation(title="Conversation B")

        self.service.save_message(conv_a["id"], role="user", content="A: Question 1")
        self.service.save_message(conv_b["id"], role="user", content="B: Question 1")
        self.service.save_message(conv_a["id"], role="assistant", content="A: Answer 1")
        self.service.save_message(conv_b["id"], role="assistant", content="B: Answer 1")

        msgs_a = self.service.get_messages(conv_a["id"])
        msgs_b = self.service.get_messages(conv_b["id"])

        self.assertEqual(len(msgs_a), 2)
        self.assertEqual(len(msgs_b), 2)
        self.assertTrue(all("A:" in m["content"] for m in msgs_a))
        self.assertTrue(all("B:" in m["content"] for m in msgs_b))

    # 8. Generate title from first user message
    def test_generate_title_from_first_user_message(self):
        title = generate_conversation_title("what is the capital of Australia?")
        self.assertEqual(title, "What is the capital of Australia?")

        # Test long query truncation
        long_query = "Please write a comprehensive Python script that connects to an SQLite database and performs atomic operations."
        long_title = generate_conversation_title(long_query, max_length=40)
        self.assertLessEqual(len(long_title), 40)
        self.assertTrue(long_title.endswith("..."))

        # Test auto-titling when creating via save_message
        conv = self.service.create_conversation(title="New Conversation")
        self.service.save_message(conv["id"], role="user", content="how to write tests in python")
        updated_conv = self.service.get_conversation(conv["id"])
        self.assertEqual(updated_conv["title"], "How to write tests in python")

    # 9. Rename conversation and verify persistence
    def test_rename_conversation(self):
        conv = self.service.create_conversation(title="Original Title")
        updated = self.service.rename_conversation(conv["id"], "Updated New Title")
        self.assertEqual(updated["title"], "Updated New Title")

        persisted = self.service.get_conversation(conv["id"])
        self.assertEqual(persisted["title"], "Updated New Title")

    # 10. Delete a conversation and its messages
    def test_delete_conversation_and_messages(self):
        conv = self.service.create_conversation(title="To Be Deleted")
        self.service.save_message(conv["id"], role="user", content="Message 1")
        self.service.save_message(conv["id"], role="assistant", content="Message 2")

        deleted = self.service.delete_conversation(conv["id"])
        self.assertTrue(deleted)

        self.assertIsNone(self.service.get_conversation(conv["id"]))
        msgs = self.service.get_messages(conv["id"])
        self.assertEqual(len(msgs), 0, "All messages should be deleted")

    # 11. Reject invalid conversation IDs and malformed payloads
    def test_reject_invalid_inputs(self):
        with self.assertRaises(ValueError):
            self.service.save_message("", "user", "Hello")

        with self.assertRaises(ValueError):
            self.service.save_message("conv_123", "invalid_role", "Hello")

        with self.assertRaises(ValueError):
            self.service.save_message("conv_123", "user", "")

        with self.assertRaises(ValueError):
            self.service.rename_conversation("conv_123", "   ")

        with self.assertRaises(KeyError):
            self.service.rename_conversation("conv_nonexistent", "Valid Title")

    # 12. Verify foreign-key and transaction behavior
    def test_foreign_key_and_cascaded_deletion(self):
        conv = self.service.create_conversation(title="Cascade Check")
        self.service.save_message(conv["id"], role="user", content="Child message")

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        # Direct SQL delete on conversation table to verify SQLite ON DELETE CASCADE
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conv["id"],))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conv["id"],))
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0, "Foreign key CASCADE should delete orphan messages")

    # 13. Verify delayed response is saved to its original conversation
    def test_delayed_response_saved_to_original_conversation(self):
        conv1 = self.service.create_conversation(title="Chat 1")
        conv2 = self.service.create_conversation(title="Chat 2")

        # Request 1 starts on Conv 1
        req1_conv_id = conv1["id"]
        self.service.save_message(req1_conv_id, role="user", content="Request 1 Query")

        # User switches to Conv 2 and submits query
        req2_conv_id = conv2["id"]
        self.service.save_message(req2_conv_id, role="user", content="Request 2 Query")

        # Late response for Request 1 arrives now
        self.service.save_message(req1_conv_id, role="assistant", content="Late Answer for Request 1")

        # Response for Request 2 arrives
        self.service.save_message(req2_conv_id, role="assistant", content="Answer for Request 2")

        msgs_1 = self.service.get_messages(conv1["id"])
        msgs_2 = self.service.get_messages(conv2["id"])

        self.assertEqual(len(msgs_1), 2)
        self.assertEqual(msgs_1[1]["content"], "Late Answer for Request 1")

        self.assertEqual(len(msgs_2), 2)
        self.assertEqual(msgs_2[1]["content"], "Answer for Request 2")


class TestEelChatHistoryEndpoints(unittest.TestCase):
    """Test suite verifying engine.command Eel-exposed endpoints."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_eel_chat.db")
        conn = get_connection(self.db_path)
        initialize_schema(conn)
        conn.commit()
        conn.close()
        self.test_service = ChatHistoryService(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("engine.command.get_chat_history_service")
    def test_eel_get_recent_conversations(self, mock_get_service):
        mock_get_service.return_value = self.test_service
        from engine.command import getRecentConversations

        self.test_service.create_conversation("Eel Chat")
        res = getRecentConversations()
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["conversations"]), 1)
        self.assertEqual(res["conversations"][0]["title"], "Eel Chat")

    @patch("engine.command.get_chat_history_service")
    def test_eel_create_and_delete_conversation(self, mock_get_service):
        mock_get_service.return_value = self.test_service
        from engine.command import createConversation, deleteConversation

        c_res = createConversation("New Session")
        self.assertEqual(c_res["status"], "success")
        conv_id = c_res["conversation"]["id"]

        d_res = deleteConversation(conv_id)
        self.assertEqual(d_res["status"], "success")
        self.assertTrue(d_res["deleted"])

    @patch("engine.command.get_chat_history_service")
    def test_eel_rename_conversation(self, mock_get_service):
        mock_get_service.return_value = self.test_service
        from engine.command import createConversation, renameConversation

        c_res = createConversation("Initial Title")
        conv_id = c_res["conversation"]["id"]

        r_res = renameConversation(conv_id, "Renamed Title")
        self.assertEqual(r_res["status"], "success")
        self.assertEqual(r_res["conversation"]["title"], "Renamed Title")


if __name__ == "__main__":
    unittest.main()
