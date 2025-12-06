import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import ask_ai

class TestAIService(unittest.TestCase):

    @patch('services.ai_service.genai.Client')
    def test_ask_ai_google(self, mock_client_cls):
        # Setup mocking
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini Response"
        
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client
        
        # Test call
        response = ask_ai("Question", "Context", provider="Google (Gemini)", api_key="fake-key")
        
        self.assertEqual(response, "Gemini Response")
        mock_client.models.generate_content.assert_called_once()

    @patch('services.ai_service.openai.OpenAI')
    def test_ask_ai_openai(self, mock_openai):
        # Setup
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "GPT Response"
        
        mock_completion.choices = [MagicMock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client
        
        # Test call
        response = ask_ai("Question", "Context", provider="OpenAI", api_key="fake-key")
        
        self.assertEqual(response, "GPT Response")
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('services.ai_service.anthropic.Anthropic')
    def test_ask_ai_anthropic(self, mock_anthropic):
        # Setup
        mock_client = MagicMock()
        mock_msg_resp = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Claude Response"
        
        mock_msg_resp.content = [mock_content]
        mock_client.messages.create.return_value = mock_msg_resp
        mock_anthropic.return_value = mock_client
        
        # Test
        response = ask_ai("Question", "Context", provider="Anthropic", api_key="fake-key")
        
        self.assertEqual(response, "Claude Response")
        mock_client.messages.create.assert_called_once()

    def test_missing_api_key(self):
        response = ask_ai("Q", "C", provider="OpenAI", api_key="")
        self.assertIn("Missing OpenAI API Key", response)

if __name__ == '__main__':
    unittest.main()
