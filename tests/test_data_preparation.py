import pytest
from src.utils.data_preparation import load_dataset, save_dataset, tokenize_data, split_data, simple_tokenizer


def test_load_dataset(tmp_path):
    # Arrange
    data = [{'key': 'value'}]
    file_path = tmp_path / "test.json"
    file_path.write_text('[{"key": "value"}]')
    
    # Act
    loaded_data = load_dataset(file_path)
    
    # Assert
    assert loaded_data == data


def test_save_dataset(tmp_path):
    # Arrange
    data = [{'key': 'value'}]
    file_path = tmp_path / "test.json"
    
    # Act
    save_dataset(data, file_path)
    
    # Assert
    import json
    saved_data = json.loads(file_path.read_text())
    assert saved_data == data


def test_tokenize_data():
    # Arrange
    data = [{'code': 'print("Hello")', 'docstring': 'This prints hello'}]

    def mock_tokenizer(text):
        return text.split()

    # Act
    tokenized_data = tokenize_data(data, mock_tokenizer)

    # Assert
    assert tokenized_data == [{'input': ['print("Hello")'], 'output': ['This', 'prints', 'hello']}]


def test_split_data():
    # Arrange
    data = [{'item': i} for i in range(10)]
    
    # Act
    train, val, test = split_data(data, train_size=0.7, val_size=0.2)
    
    # Assert
    assert len(train) == 7
    assert len(val) == 2
    assert len(test) == 1


def test_simple_tokenizer():
    # Act
    tokens = simple_tokenizer('This is a test')
    
    # Assert
    assert tokens == ['This', 'is', 'a', 'test']
