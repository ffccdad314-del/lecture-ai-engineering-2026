import sys
from types import SimpleNamespace

from app import ask as ask_module


class FakeChat:
    def __init__(self):
        self.questions = []

    def send_message(self, question):
        self.questions.append(question)
        return SimpleNamespace(text=f"回答{len(self.questions)}", usage_metadata=None)


class FakeChats:
    def __init__(self, chat):
        self.chat = chat
        self.models = []

    def create(self, *, model):
        self.models.append(model)
        return self.chat


class FakeClient:
    def __init__(self, chat):
        self.chats = FakeChats(chat)


def client_factory(client):
    def create_client(*, api_key):
        assert api_key == "test-key"
        return client

    return create_client


def test_main_reuses_chat_for_follow_up_questions(monkeypatch, capsys):
    chat = FakeChat()
    client = FakeClient(chat)
    prompts = iter(["続けて質問", "exit"])
    monkeypatch.setattr(ask_module.genai, "Client", client_factory(client))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr("builtins.input", lambda _: next(prompts))
    monkeypatch.setattr(sys, "argv", ["app.ask", "最初の質問"])

    ask_module.main()

    assert client.chats.models == [ask_module.MODEL]
    assert chat.questions == ["最初の質問", "続けて質問"]
    output = capsys.readouterr().out
    assert "回答1" in output
    assert "回答2" in output


def test_ask_creates_chat_when_called_without_one(monkeypatch):
    chat = FakeChat()
    client = FakeClient(chat)
    monkeypatch.setattr(ask_module.genai, "Client", client_factory(client))
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")

    result = ask_module.ask("質問")

    assert result == "回答1"
    assert client.chats.models == [ask_module.MODEL]
    assert chat.questions == ["質問"]
